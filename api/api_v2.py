# import necessary packages
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
# from werkzeug.utils import secure_filename
from langchain.chains import RetrievalQA
# import tempfile

# from langchain.document_loaders import DirectoryLoader, PyMuPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Pinecone
import pinecone
from dotenv import load_dotenv

# import prompts
from templates.qa_prompt import QA_PROMPT
from templates.condense_prompt import CONDENSE_PROMPT

# import environment variables
load_dotenv()
openai_api_key = os.environ.get('OPENAI_API_KEY')
pinecone_api_key = os.environ.get('PINECONE_API_KEY')
pinecone_environment = os.environ.get('PINECONE_ENV')
pinecone_index = os.environ.get('PINECONE_INDEX')

# set up Pinecone namespace
pinecone_namespace = 'dfkAll'

# set up Flask app
app = Flask("DFK-ChatBot")
api = Api(app)
# app.debug=True

parser = reqparse.RequestParser()

def get_answer(message, temperature=0, source_amount=8):
    if not message:
        abort(400, message="Please provide a valid question.")
    if temperature < 0 or temperature > 2:
        abort(400, message="Temperature must be between 0 and 2.")
    if source_amount < 1 or source_amount > 9:
        abort(400, message="Source amount must be between 1 and 9.")
    
    embeddings = OpenAIEmbeddings(
        model='text-embedding-ada-002', openai_api_key=openai_api_key)

    pinecone.init(api_key=pinecone_api_key,
                  environment=pinecone_environment)
    vectorstore = Pinecone.from_existing_index(
        index_name=pinecone_index, embedding=embeddings, text_key='text', namespace=pinecone_namespace)
    model = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=temperature,
                       openai_api_key=openai_api_key, streaming=False)  # max temperature is 2 least is 0
    retriever = vectorstore.as_retriever(search_kwargs={
        "k": source_amount},  qa_template=QA_PROMPT, question_generator_template=CONDENSE_PROMPT)  # 9 is the max sources
    # qa = ConversationalRetrievalChain.from_llm(
    #     llm=model, retriever=retriever, return_source_documents=True)
    qa = RetrievalQA.from_chain_type(model, chain_type="stuff", 
                                    retriever=retriever
                                    ,return_source_documents=True)
    result = qa({"query": message})
    print("Cevap Geldi")
    answer = result["result"]
    source_documents = result['source_documents']

    parsed_documents = []
    for doc in source_documents:
        parsed_doc = {
            "page_content": doc.page_content,
            "metadata": {
                "author": doc.metadata.get("author", ""),
                "creationDate": doc.metadata.get("creationDate", ""),
                "creator": doc.metadata.get("creator", ""),
                "file_path": doc.metadata.get("file_path", ""),
                "format": doc.metadata.get("format", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "modDate": doc.metadata.get("modDate", ""),
                "page_number": doc.metadata.get("page_number", 0),
                "producer": doc.metadata.get("producer", ""),
                "source": doc.metadata.get("source", ""),
                "subject": doc.metadata.get("subject", ""),
                "title": doc.metadata.get("title", ""),
                "total_pages": doc.metadata.get("total_pages", 0),
                "trapped": doc.metadata.get("trapped", "")
            }
        }
        parsed_documents.append(parsed_doc)

    # return answer and metadata as dictionary
    return {
        "answer": answer,
        "meta": parsed_documents
    }

class Ask(Resource):
    def post(self):
        try:
            question = request.form.get("question")
            temp = request.form.get("temp", default=0)
            sources = request.form.get("sources", default=6)
            result = get_answer(question, float(temp), int(sources))
            return result
        except Exception as e:
            return {'error': str(e)}, 400

api.add_resource(Ask, "/ask")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)