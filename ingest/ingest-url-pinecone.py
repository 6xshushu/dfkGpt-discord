import asyncio
import os,sys

import aiohttp
import pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from aiohttp import TCPConnector
from langchain.docstore.document import Document

# from langchain.document_loaders import UnstructuredHTMLLoader

import pytesseract
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

#you can remove the proxy if you want
proxy = 'http://127.0.0.1:10810' 



urls = [
    "https://medium.com/@MrZipper7/deep-dive-active-passive-genes-68315567361c",
    "https://medium.com/@Samichpunch/lost-annals-of-gaia-vol-4-nuggets-of-knowledge-from-the-discord-97c3d5c24753#1892",
    "https://medium.com/@Samichpunch/breaking-down-a-defi-kingdoms-hero-card-and-what-to-consider-when-purchasing-efd5e5222f97"

]

async def fetch_content(url, session):
    async with session.get(url, proxy=proxy) as response:
        return await response.text()

async def download_image(url, session):
    async with session.get(url, proxy=proxy) as response:
        content = await response.read()
        # print(f"Downloaded: {content}")
        result=Image.open(io.BytesIO(content))
        # print(f"Downloaded: {content}")
        return result

async def extract_text_from_image(image):
    # print(222222)
    result = ''
    try:
        result=pytesseract.image_to_string(image)
        print(f"Extracted text from image: {result}")
    except Exception as e:
        print(f"Error pytesseract image {image}: {e}")    
    
    return result

async def extract_text_from_html(html, session):
    soup = BeautifulSoup(html, 'html.parser')
    extracted_texts = []

    article = soup.find('article')
    if article:
        tagss=article.find_all(['p', 'h1'])
        # print(f"-----------{tagss}")
        for tag in tagss:
            
            if tag.name in ['h1', 'p']:
                extracted_texts.append(tag.text)
            elif tag.name == 'img':
                # print(11111111111)
                try:
                    if 'src' in tag.attrs:
                        image_url = tag['src']
                        image = await download_image(image_url, session)
                        image_text = await extract_text_from_image(image)
                        print(f"Extracted text from image {image_url}: {image_text}")
                        extracted_texts.append(image_text)
               
                except Exception as e:
                    print(f"Error processing image {image_url}: {e}")
    else:
        print("No article tag found.")

    combined_text = ' '.join(extracted_texts)
    return combined_text

async def ingest_doc(url):
    async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
        html = await fetch_content(url, session)
        text = await extract_text_from_html(html, session)
        # print(text)
        doc=Document(page_content=text,metadata={"source":url})

        print(doc)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=200)
    
    texts = text_splitter.split_documents([doc])

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
    tasks = [ingest_doc(url) for url in urls]
    await asyncio.gather(*tasks)
    print('Complete')

pytesseract.pytesseract.tesseract_cmd = 'D:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Update this path to your Tesseract executable

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(async_main())