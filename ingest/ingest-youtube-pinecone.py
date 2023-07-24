import asyncio
import os
import sys


import pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from urllib.parse import urljoin


from langchain.document_loaders import YoutubeLoader

# from langchain.document_loaders import UnstructuredHTMLLoader

from PIL import Image
import io

from dotenv import load_dotenv
load_dotenv()
openai_api_key = os.environ.get('OPENAI_API_KEY')
pinecone_api_key = os.environ.get('PINECONE_API_KEY')
pinecone_environment = os.environ.get('PINECONE_ENV')
pinecone_index = os.environ.get('PINECONE_INDEX')
pinecone_namespace1 = "dfkDocGitbook"
pinecone_namespace2 = "dfkDevGitbook"
pinecone_namespace3 = "dfkAll"

proxy = 'http://127.0.0.1:10810'


urls = [
   "https://www.youtube.com/watch?v=cOY6Fx5xycI"

]


async def ingest_youtube(url):

    loader = YoutubeLoader.from_youtube_url(
        url, add_video_info=True
    )

    docs=loader.load()

    new_source = url
    for doc in docs:
        doc.metadata["source"] = new_source


    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000, chunk_overlap=300)

    texts = text_splitter.split_documents(docs)

    print(texts)

    # return

    # for text in texts:
    #     text.page_content= text.page_content.replace("[", "").replace("]", "")

    pinecone.init(
        api_key=pinecone_api_key,
        environment=pinecone_environment
    )
    embeddings = OpenAIEmbeddings(
        model='text-embedding-ada-002', openai_api_key=openai_api_key)

    Pinecone.from_documents(
        texts, embeddings, index_name=pinecone_index, namespace=pinecone_namespace3)
    print(f'Loaded {url}!')


async def async_main():
    tasks = [ingest_youtube(url) for url in urls]
    await asyncio.gather(*tasks)
    print('Complete')

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(async_main())
