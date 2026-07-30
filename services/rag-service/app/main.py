"""rag-service: turns uploaded documents into searchable knowledge.

Flow: upload file -> (optional) archive raw file to Cloud Storage -> split into
chunks -> Gemini embeddings -> store vectors in Chroma -> /retrieve does
similarity search so the agent can ground its answers in YOUR documents.
"""
import io
import logging

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-service")

app = FastAPI(title="rag-service")

_vectorstore = None


def get_vectorstore():
    """Lazy init so the service can boot even before the API key is set."""
    global _vectorstore
    if _vectorstore is None:
        from langchain_chroma import Chroma
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model, google_api_key=settings.google_api_key
        )
        _vectorstore = Chroma(
            collection_name="documents",
            embedding_function=embeddings,
            persist_directory=settings.chroma_dir,
        )
    return _vectorstore


def extract_text(filename: str, data: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return data.decode("utf-8", errors="ignore")


def archive_to_gcs(filename: str, data: bytes) -> str | None:
    if not settings.gcs_bucket:
        return None
    from google.cloud import storage

    client = storage.Client(project=settings.gcp_project_id or None)
    blob = client.bucket(settings.gcs_bucket).blob(f"uploads/{filename}")
    blob.upload_from_string(data)
    return f"gs://{settings.gcs_bucket}/uploads/{filename}"


class RetrieveRequest(BaseModel):
    query: str
    k: int = 4


@app.get("/health")
def health():
    return {"status": "ok", "service": "rag-service"}


@app.post("/upload")
async def upload(file: UploadFile):
    data = await file.read()
    text = extract_text(file.filename, data)
    if not text.strip():
        raise HTTPException(400, "Could not extract any text from this file")

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    chunks = splitter.split_text(text)
    get_vectorstore().add_texts(chunks, metadatas=[{"source": file.filename}] * len(chunks))
    gcs_path = archive_to_gcs(file.filename, data)
    logger.info("Indexed %s: %d chunks", file.filename, len(chunks))
    return {"filename": file.filename, "chunks_indexed": len(chunks), "gcs_path": gcs_path}


@app.post("/retrieve")
def retrieve(req: RetrieveRequest):
    try:
        docs = get_vectorstore().similarity_search(req.query, k=req.k)
    except Exception as e:
        raise HTTPException(500, f"Retrieval failed: {e}") from e
    return {
        "results": [
            {"text": d.page_content, "source": d.metadata.get("source", "unknown")} for d in docs
        ]
    }
