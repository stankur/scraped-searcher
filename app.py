from flask import Flask, request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
import json
from pathlib import Path
from pprint import pprint


load_dotenv()

embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY")) 

app = Flask(__name__)

@app.route('/')
def index():
    return 'This is a friendly reminder that your hairline is receding.'

@app.get('/search')
def search():
    # returns the top jobs matching the search query
    search_query = request.args.get("query", "")
    db = FAISS.load_local("jobs_index", embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 50})

    similar_docs = retriever.invoke(search_query)
    indexes = [doc.metadata["index"] for doc in similar_docs]
    non_duplicated_indexes = list(dict.fromkeys(indexes))

    jobs = json.loads(Path("./jobs.json").read_text())

    return [jobs[index] for index in non_duplicated_indexes]

@app.get('/jobs')
def get_jobs():
    return json.loads(Path("./jobs.json").read_text())



@app.post('/jobs')
def update_jobs():
    # updates the embeddings store with the jobs in jobs.json

    data = json.loads(Path("./jobs.json").read_text())

    for idx, job in enumerate(data):
        job["description"] = get_combined_description({"Job Term": job["term"], 
                                                       "Job Title": job["jobTitle"],
                                                       "Organization/Company": job["organization"],
                                                       "Job Location": job["location"],
                                                       "Duration": job["duration"],
                                                       "Job Description": job["description"],
                                                       "Job Requirements": job["requirements"]
                                                       }) 
        job["index"] = idx 
        del job["requirements"]
        
    with open('./modified_jobs.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)
    
    loader = JSONLoader(
        file_path="./modified_jobs.json",
        jq_schema='.[]',
        text_content=False,
        content_key="description",
        metadata_func=metadata_func
    )

    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
    split = text_splitter.split_documents(documents)

    db = FAISS.from_documents(split, embeddings)
    db.save_local("jobs_index")

    return str(split)

# helpers

def metadata_func(record, metadata):
    metadata["id"] = record["id"]
    metadata["term"] = record["term"]
    metadata["location"] = record["location"]
    metadata["duration"] = record["duration"]
    metadata["index"] = record["index"]

    return metadata

def get_combined_description(dict):
    acc = ""

    for key in dict:
        acc += f"{key}\n{dict[key]}\n\n"

    return acc




