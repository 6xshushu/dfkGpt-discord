
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
import pinecone
from langchain.document_loaders import GitbookLoader
import os

from dotenv import load_dotenv
load_dotenv()
openai_api_key = os.environ.get('OPENAI_API_KEY')
pinecone_api_key = os.environ.get('PINECONE_API_KEY')
pinecone_environment = os.environ.get('PINECONE_ENV')
pinecone_index = os.environ.get('PINECONE_INDEX')
pinecone_namespace1="dfkDocGitbook"
pinecone_namespace2="dfkDevGitbook"
pinecone_namespace3="dfkAll"


def lodDataFromGitbook(url):
    loader = GitbookLoader(url,load_all_paths=True)
    # 将数据转成 document 对象，每个文件会作为一个 document
    documents = loader.load()
    # split it into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    return docs

def ingestDocs(docs, embeddings, namespace):
    # save to disk
    pinecone.init(
            api_key=pinecone_api_key,
            environment=pinecone_environment
        )
    Pinecone.from_documents(docs, embeddings, index_name=pinecone_index, namespace=namespace)

def main():
    # url1="https://docs.defikingdoms.com/"
    url2="https://devs.defikingdoms.com/"

    # docs1=lodDataFromGitbook(url1)
    docs2=lodDataFromGitbook(url2)

    embeddings = OpenAIEmbeddings()

    # ingestDocs(docs1, embeddings, pinecone_namespace1)
    # ingestDocs(docs2, embeddings, pinecone_namespace2)
    ingestDocs(docs2, embeddings, pinecone_namespace3)

main()