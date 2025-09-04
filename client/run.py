import argparse
import os

from pathlib import Path
import time
from typing import Any, List, Optional, Tuple, Union

from llama_stack_client import LlamaStackClient
from llama_stack_client.types.model import Model
from llama_stack_client.types.shared_params.document import Document as RAGDocument
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger as AgentEventLogger

# EMBEDDING_MODEL = "granite-embedding-125m"
# EMBEDDING_DIMENSION = "768"
# EMBEDDING_MODEL_PROVIDER = "sentence-transformers"
# CHUNK_SIZE_IN_TOKENS = 512
# LLAMA_STACK_HOST = "localhost"
# LLAMA_STACK_PORT = "8080"
# LLAMA_STACK_SECURE = "False"
# DOCS_FOLDER = "./docs"

DEFAULT_DELAY_SECONDS = 5


def create_client(host: str, port: int, secure: bool = False) -> LlamaStackClient:
    """Initialize and return the LlamaStack client"""
    if secure:
        protocol: str = "https"
    else:
        protocol: str = "http"

    if not (1 <= port <= 65535):
        raise ValueError(f"Port number {port} is out of valid range (1-65535).")
    if not host:
        raise ValueError("Host must be specified and cannot be empty.")
    
    print(f"Creating LlamaStack client with base URL: {protocol}://{host}:{port}")
    return LlamaStackClient(base_url=f"{protocol}://{host}:{port}")


def get_embedding_model(
    client: LlamaStackClient,
    embedding_model_id: str,
    embedding_model_provider: str
) -> Model:
    """Fetch and return the embedding model by ID and provider"""
    if not embedding_model_id:
        raise ValueError("Embedding model ID is required")
    if not embedding_model_provider:
        raise ValueError("Embedding model provider is required")
    
    models = client.models.list()
    for model in models:
        if model.identifier == embedding_model_id and model.provider_id == embedding_model_provider and model.api_model_type == "embedding":
            return model
    
    raise ValueError(f"Embedding model {embedding_model_id} not found for provider {embedding_model_provider}")


def register_vector_db(
    client: LlamaStackClient, 
    embedding_model: Model, 
    vector_db_id: str = "milvus_db", 
    provider_id: str = "milvus"
) -> str:
    """Register vector database"""
    if not vector_db_id:
        raise ValueError("Vector DB ID is required for registration")
    if not provider_id:
        raise ValueError("Provider ID is required for vector DB registration")
    
    if not embedding_model:
        raise ValueError("Embedding model is required for vector DB registration")
    
    embedding_model_id: str = embedding_model.identifier
    if not embedding_model_id:
        raise ValueError("Embedding model ID is required for vector DB registration")
    
    # Check it model api type is 'embedding'
    if embedding_model.api_model_type != "embedding":
        raise ValueError("Provided model is not an embedding model")

    # Check if embedding model metadata contains 'embedding_dimension' and if it's a str, int or float
    if not hasattr(embedding_model, 'metadata') or not isinstance(embedding_model.metadata, dict):
        raise ValueError("Embedding model metadata must be a dictionary")
    if not isinstance(embedding_model.metadata, dict):
        raise ValueError("Embedding model metadata must be a dictionary")
    if not isinstance(embedding_model.metadata.get("embedding_dimension"), (str, int, float)):
        raise ValueError("Embedding model metadata 'embedding_dimension' must be a str, int or float")
    
    embedding_dimension: int = embedding_model.metadata["embedding_dimension"] # type: ignore
    
    print(f"Registering vector DB: {vector_db_id} with embedding model {embedding_model_id} (dimension: {embedding_dimension})")
    client.vector_dbs.register(
        vector_db_id=vector_db_id,
        embedding_model=embedding_model_id,
        # embedding_dimension=embedding_dimension,
        provider_id=provider_id,
    )
    print(f"Registered vector DB: {vector_db_id}")
    return vector_db_id


def get_mime_type(extension: str) -> str:
    """Get MIME type based on file extension"""
    mime_types: dict[str, str] = {
        '.txt': 'text/plain',
        '.md': 'text/markdown', 
        '.py': 'text/plain',
        '.json': 'application/json',
        '.html': 'text/html',
        '.csv': 'text/csv'
    }
    return mime_types.get(extension.lower(), 'text/plain')


def load_documents_from_folder(
    folder_path: str, 
    file_extensions: List[str] = ['.txt', '.md']
) -> List[RAGDocument]:
    """Load documents from a local folder and return RAGDocument objects"""
    documents: List[RAGDocument] = []
    folder: Path = Path(folder_path)
    
    if not folder.exists():
        print(f"Warning: Folder {folder_path} does not exist")
        return documents
    
    print(f"Loading documents from: {folder_path}")
    
    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in file_extensions:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content: str = f.read()
                
                mime_type: str = get_mime_type(file_path.suffix)
                
                doc: RAGDocument = RAGDocument(
                    document_id=file_path.stem,
                    content=content,
                    mime_type=mime_type,
                    metadata={
                        "filename": file_path.name,
                        "filepath": str(file_path),
                        "file_size": file_path.stat().st_size
                    }
                )
                documents.append(doc)
                print(f"Loaded: {file_path.name}")
                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    print(f"Successfully loaded {len(documents)} documents")
    return documents


def insert_documents(
    client: LlamaStackClient, 
    documents: List[RAGDocument], 
    vector_db_id: str, 
    chunk_size_in_tokens: int = 512
) -> None:
    """Insert documents into the vector database"""
    if not documents:
        print("No documents to insert")
        return
    
    client.tool_runtime.rag_tool.insert(
        documents=documents,
        vector_db_id=vector_db_id,
        chunk_size_in_tokens=chunk_size_in_tokens,
    )
    print(f"Inserted {len(documents)} documents into vector DB")


def main() -> None:
    """Main function to load documents and insert them into the vector database"""

    # Takes an optional argument which adds a delay if the task fails using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=str, default="0", help="Delay in seconds before raising error on failure")
    args = parser.parse_args()
    
    # Convert delay to integer, handling string input gracefully
    try:
        delay_seconds = int(args.delay)
        if delay_seconds < 0:
            raise ValueError("Delay must be a positive integer")
    except (ValueError, TypeError) as e:
        print(f"Warning: Invalid delay value '{args.delay}', defaulting to 0 seconds. Error: {e}")
        delay_seconds = DEFAULT_DELAY_SECONDS
    
    print(f"Delaying for {delay_seconds} seconds if task fails")
    
    try:
        # Get embedding model id, dimension and provider
        embedding_model_id = os.environ.get("EMBEDDING_MODEL")
        if embedding_model_id is None:
            raise ValueError("EMBEDDING_MODEL environment variable must be set")
        embedding_model_dimension = os.environ.get("EMBEDDING_DIMENSION")
        if embedding_model_dimension is None:
            raise ValueError("EMBEDDING_DIMENSION environment variable must be set")
        embedding_model_provider = os.environ.get("EMBEDDING_MODEL_PROVIDER")
        if embedding_model_provider is None:
            raise ValueError("EMBEDDING_MODEL_PROVIDER environment variable must be set")

        # Get chunk size in tokens
        chunk_size_in_tokens = os.environ.get("CHUNK_SIZE_IN_TOKENS", "512")
        chunk_size_in_tokens = int(chunk_size_in_tokens)

        # Get LlamaStack host, port and secure
        host = os.environ.get("LLAMA_STACK_HOST")
        if not host:
            raise ValueError("LLAMA_STACK_HOST environment variable must be set")
        port = os.environ.get("LLAMA_STACK_PORT")
        if not port:
            raise ValueError("LLAMA_STACK_PORT environment variable must be set")
        secure = os.environ.get("LLAMA_STACK_SECURE", "false").lower() in ["true", "1", "yes"]
        
        # Add this after line ~195 where you read the environment variables
        print(f"DEBUG - Environment variables:")
        print(f"  HOST: '{host}'")
        print(f"  PORT: '{port}' (type: {type(port)})")
        print(f"  SECURE: '{secure}'")

        # Get documents folder
        docs_folder: str = os.environ.get("DOCS_FOLDER", "./docs")
        if not docs_folder:
            raise ValueError("DOCS_FOLDER environment variable must be set")

        # Initialize client
        client: LlamaStackClient = create_client(host=host, port=int(port), secure=secure)
        print(f"Connected to LlamaStack at {host}:{port}")
        
        # Register vector database
        embedding_model = get_embedding_model(client, embedding_model_id, embedding_model_provider)
        if not embedding_model:
            raise ValueError(f"Embedding model {embedding_model_id} not found for provider {embedding_model_provider}")
        print(f"Using embedding model: {embedding_model.identifier} (dimension: {embedding_model.metadata['embedding_dimension']})")
        vector_db_id: str = register_vector_db(client, embedding_model)
        
        # Load documents from folder
        documents: List[RAGDocument] = load_documents_from_folder(docs_folder)
        
        # Insert documents into the vector database
        insert_documents(client, documents, vector_db_id, chunk_size_in_tokens=512)
        
        print(f"Documents inserted into the vector database {vector_db_id} with chunk size in tokens {chunk_size_in_tokens}")
    except Exception as e:
        print(f"Error: {e}")
        if delay_seconds > 0:
            print(f"Delaying for {delay_seconds} seconds before raising error")
            time.sleep(delay_seconds)
        raise e

if __name__ == "__main__":
    main()