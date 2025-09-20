import os
import shutil
import stat
import uuid # New import for generating unique IDs
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from git import Repo
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain.text_splitter import Language
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFacePipeline

# --- Helper function for Windows file deletion ---
def handle_remove_readonly(func, path, exc_info):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

# --- Pydantic Models ---
class AnalyzeRequest(BaseModel):
    repo_url: str

class QueryRequest(BaseModel):
    question: str

# --- FastAPI App Setup ---
app = FastAPI(
    title="CodeScribe AI Core Service",
    description="The core service for analyzing and querying codebases.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core AI Logic Class ---
class CodebaseService:
    def __init__(self):
        self.repo_path_base = "./repo_data"
        self.vector_store = None
        self.qa_chain = None
        self.embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.llm = HuggingFacePipeline.from_model_id(
            model_id="google/flan-t5-base",
            task="text2text-generation",
            pipeline_kwargs={"max_new_tokens": 250, "temperature": 0.1},
        )

    def analyze_repo(self, repo_url: str):
        repo_path = f"{self.repo_path_base}_{uuid.uuid4()}" # Create a unique path for each analysis
        
        try:
            print(f"[Analyze] Starting analysis for repo: {repo_url}")
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, onerror=handle_remove_readonly)

            print(f"[Analyze] Cloning repo into temporary path: {repo_path}")
            Repo.clone_from(repo_url, to_path=repo_path)

            print(f"[Analyze] Loading code files...")
            loader = GenericLoader.from_filesystem(
                repo_path,
                glob="**/*",
                suffixes=[".py", ".js", ".go", ".java", ".ts", ".md"],
                parser=LanguageParser(language=Language.PYTHON, parser_threshold=500),
            )
            documents = loader.load()

            print(f"[Analyze] Splitting {len(documents)} documents into chunks...")
            python_splitter = RecursiveCharacterTextSplitter.from_language(
                language=Language.PYTHON, chunk_size=2000, chunk_overlap=200
            )
            texts = python_splitter.split_documents(documents)

            print(f"[Analyze] Creating in-memory vector store...")
            self.vector_store = Chroma.from_documents(texts, self.embedding_function)
            
            print(f"[Analyze] Initializing QA chain...")
            self._initialize_qa_chain()

            print(f"[Analyze] Success! Ready for questions.")
            return {"status": "success", "message": f"Repository analyzed successfully. Ready for questions."}
        
        except Exception as e:
            print(f"[Analyze] ERROR: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {str(e)}")
        
        finally:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, onerror=handle_remove_readonly)

    def _initialize_qa_chain(self):
        if self.vector_store is None:
            raise Exception("Vector store not initialized. Please analyze a repository first.")
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )

    def query_repo(self, question: str):
        if self.qa_chain is None:
             raise HTTPException(status_code=400, detail="No repository has been analyzed yet.")

        try:
            print(f"[Query] Invoking QA chain with question: {question}")
            result = self.qa_chain.invoke({"query": question})
            return {"question": question, "answer": result["result"]}
        except Exception as e:
            print(f"[Query] ERROR: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to query repository: {str(e)}")

# --- API Endpoints ---
codebase_service = CodebaseService()

@app.post("/analyze")
def analyze_repository(request: AnalyzeRequest):
    return codebase_service.analyze_repo(request.repo_url)

@app.post("/query")
def query_repository(request: QueryRequest):
    return codebase_service.query_repo(request.question)

@app.get("/")
def read_root():
    return {"message": "AI Core is running"}
import os
import shutil
import stat # New import for file permissions
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from git import Repo
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain.text_splitter import Language
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFacePipeline

# --- NEW: Helper function to handle read-only files on Windows ---
def handle_remove_readonly(func, path, exc_info):
    """
    Error handler for shutil.rmtree.

    If the error is for a read-only file, it changes the permissions and retries.
    If the error is for another reason, it re-raises the error.
    """
    if not os.access(path, os.W_OK):
        # Is the error an access error?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

# --- Pydantic Models ---
class AnalyzeRequest(BaseModel):
    repo_url: str

class QueryRequest(BaseModel):
    question: str

# --- FastAPI App Setup ---
app = FastAPI(
    title="CodeScribe AI Core Service",
    description="The core service for analyzing and querying codebases.",
    version="0.1.0",
)

# --- Add CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core AI Logic Class ---
class CodebaseService:
    def __init__(self, repo_path: str = "./repo_data", db_path: str = "./chroma_db"):
        self.repo_path = repo_path
        self.db_path = db_path
        self.vector_store = None
        self.qa_chain = None
        self.embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def analyze_repo(self, repo_url: str):
        try:
            print(f"[Analyze] Starting analysis for repo: {repo_url}")
            # --- MODIFIED: Use the error handler when deleting directories ---
            if os.path.exists(self.repo_path):
                shutil.rmtree(self.repo_path, onerror=handle_remove_readonly)
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path, onerror=handle_remove_readonly)

            print(f"[Analyze] Cloning repo...")
            Repo.clone_from(repo_url, to_path=self.repo_path)

            print(f"[Analyze] Loading code files...")
            loader = GenericLoader.from_filesystem(
                self.repo_path,
                glob="**/*",
                suffixes=[".py", ".js", ".go", ".java", ".ts", ".md"],
                parser=LanguageParser(language=Language.PYTHON, parser_threshold=500),
            )
            documents = loader.load()

            print(f"[Analyze] Splitting {len(documents)} documents into chunks...")
            python_splitter = RecursiveCharacterTextSplitter.from_language(
                language=Language.PYTHON, chunk_size=2000, chunk_overlap=200
            )
            texts = python_splitter.split_documents(documents)

            print(f"[Analyze] Creating and persisting vector store...")
            self.vector_store = Chroma.from_documents(
                texts, self.embedding_function, persist_directory=self.db_path
            )
            self.vector_store.persist()
            
            print(f"[Analyze] Initializing QA chain...")
            self._initialize_qa_chain()

            print(f"[Analyze] Success!")
            return {"status": "success", "message": f"Repository analyzed successfully. Ready for questions."}
        except Exception as e:
            print(f"[Analyze] ERROR: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {str(e)}")

    def _initialize_qa_chain(self):
        if self.vector_store is None:
            if not os.path.exists(self.db_path):
                raise Exception("Vector store not found. Please analyze a repository first.")
            self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embedding_function)
        
        llm = HuggingFacePipeline.from_model_id(
            model_id="google/flan-t5-base",
            task="text2text-generation",
            pipeline_kwargs={"max_new_tokens": 250, "temperature": 0.1},
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )

    def query_repo(self, question: str):
        print(f"[Query] Received question: {question}")
        if self.qa_chain is None:
            try:
                print("[Query] QA chain not found, initializing...")
                self._initialize_qa_chain()
            except Exception as e:
                 print(f"[Query] ERROR initializing chain: {str(e)}")
                 raise HTTPException(status_code=400, detail=str(e))

        try:
            print("[Query] Invoking QA chain...")
            result = self.qa_chain.invoke({"query": question})
            print(f"[Query] Success.")
            return {"question": question, "answer": result["result"]}
        except Exception as e:
            print(f"[Query] ERROR during query: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to query repository: {str(e)}")

# --- API Endpoints ---
codebase_service = CodebaseService()

@app.post("/analyze")
def analyze_repository(request: AnalyzeRequest):
    return codebase_service.analyze_repo(request.repo_url)

@app.post("/query")
def query_repository(request: QueryRequest):
    return codebase_service.query_repo(request.question)

@app.get("/")
def read_root():
    return {"message": "AI Core is running"}