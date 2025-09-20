import os
import tempfile
import hashlib
from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
import uvicorn
import firebase_admin
from firebase_admin import credentials, firestore
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from datetime import datetime, timedelta, timezone
from sentence_transformers import SentenceTransformer
from langchain.embeddings import HuggingFaceEmbeddings

embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# --- LangChain & Pinecone Imports ---
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from pinecone import Pinecone

# --- INITIALIZATION ---
load_dotenv()

# --- Firebase Initialization ---
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json"))
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Security & Auth Configuration ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
SECRET_KEY = os.getenv("SECRET_KEY", "a_super_secret_key_for_dev_that_should_be_in_env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Pydantic Models ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    email: EmailStr
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- CONFIGURATION ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not all([OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME]):
    raise ValueError("⚠️  Missing one or more environment variables.")

# Ensure Pinecone API key available in os.environ for LangChain
if PINECONE_API_KEY:
    os.environ['PINECONE_API_KEY'] = PINECONE_API_KEY

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.0)
pc = Pinecone(api_key=PINECONE_API_KEY)

app = FastAPI(title="VeriDoc AI Analyst API", version="2.0.0 (SaaS Ready)")

# --- Helper Functions ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        return user_email
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

# --- AUTHENTICATION ---
@app.post("/auth/signup", response_model=Token)
async def signup(user: UserCreate):
    users_ref = db.collection('users')
    user_doc = users_ref.document(user.email).get()
    if user_doc.exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user_data = {"email": user.email, "hashed_password": hashed_password}
    users_ref.document(user.email).set(new_user_data)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users_ref = db.collection('users')
    user_doc = users_ref.document(form_data.username).get()
    if not user_doc.exists:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    user_data = user_doc.to_dict()
    if not user_data or not verify_password(form_data.password, user_data.get("hashed_password")):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# --- HEALTH CHECK ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "VeriDoc API is alive!"}

# --- PDF Upload & Embedding ---
@app.post("/upload-whitepaper/")
async def upload_whitepaper(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type.")
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
        PineconeVectorStore.from_documents(
            documents=split_docs,
            embedding=embeddings_model,
            index_name=str(PINECONE_INDEX_NAME),
            namespace=session_id
        )
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

# --- Question Answering Endpoint ---
@app.post("/ask-question/")
async def ask_question(
    session_id: str = Body(...),
    query: str = Body(...),
    token: str = Depends(oauth2_scheme)
):
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
        raise HTTPException(status_code=500, detail=str(e))

# --- MAIN ENTRYPOINT ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
