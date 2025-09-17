import os
import tempfile
import hashlib
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from dotenv import load_dotenv
import uvicorn

# --- LangChain Core Components (Modern Imports) ---
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA

# Pinecone's modern client is just 'Pinecone'
from pinecone import Pinecone

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION & VALIDATION ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# This check ensures the variables are not None.
if not all([OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME]):
    raise ValueError("⚠️  Missing one or more environment variables. Please check your .env file.")

# Set Pinecone API key as environment variable for the library to pick up
if PINECONE_API_KEY:
    os.environ['PINECONE_API_KEY'] = PINECONE_API_KEY


# --- INITIALIZATION (TYPE-SAFE) ---
# Initialize OpenAI components - they will automatically pick up the API key from the environment
embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.0)

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

app = FastAPI(
    title="VeriDoc AI Analyst API",
    description="API for processing and querying crypto whitepapers.",
    version="1.4.0" # Final Working Version
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "VeriDoc API is alive!"}

@app.post("/upload-whitepaper/")
async def upload_whitepaper(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")

    tmp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        file_hash = hashlib.sha256(content).hexdigest()
        session_id = f"doc_{file_hash}"

        loader = PyPDFLoader(tmp_file_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.split_documents(docs)
        
        # Create vector store
        PineconeVectorStore.from_documents(
            documents=split_docs,
            embedding=embeddings_model,
            index_name=str(PINECONE_INDEX_NAME),
            namespace=session_id
        )

        return {"status": "success", "message": f"File '{file.filename}' processed successfully.", "session_id": session_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

@app.post("/ask-question/")
async def ask_question(session_id: str = Body(...), query: str = Body(...)):
    if not session_id or not query:
        raise HTTPException(status_code=400, detail="session_id and query are required.")

    try:
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=str(PINECONE_INDEX_NAME),
            embedding=embeddings_model,
            namespace=session_id
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )

        result = qa_chain.invoke(query)
        
        return {"status": "success", "answer": result.get('result', 'No answer found.')}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

