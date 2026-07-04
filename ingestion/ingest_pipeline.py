"""
Ingestion Pipeline.
Coordinates parsing, chunking, and uploading of PDFs to the ChromaDB vector store.
"""

import os
from pathlib import Path
import chromadb
from ingestion.pdf_parser import FacultyPDFParser
from ingestion.chunker import Chunker
from core.config import settings
from core.logger import logger

class IngestPipeline:
    def __init__(self):
        self.parser = FacultyPDFParser()
        self.chunker = Chunker()
        self.client = self._init_client()
        self.collection_name = settings.CHROMA_COLLECTION_NAME

    def _init_client(self):
        """Initializes ChromaDB client based on env config."""
        mode = os.getenv("CHROMA_MODE", "remote").strip().lower()
        if mode == "remote":
            host = os.getenv("CHROMA_HOST", "api.trychroma.com").strip()
            api_key = settings.CHROMA_API_KEY.strip()
            tenant = settings.CHROMA_TENANT.strip()
            database = settings.CHROMA_DATABASE.strip()
            
            if "trychroma.com" in host.lower():
                logger.info(f"Ingest connecting to Chroma Cloud at {host}")
                return chromadb.CloudClient(
                    api_key=api_key,
                    tenant=tenant,
                    database=database,
                    cloud_host=host
                )
            else:
                logger.info(f"Ingest connecting to self-hosted Chroma at {host}")
                from chromadb.config import Settings as ChromaSettings
                chroma_settings = ChromaSettings()
                if api_key:
                    chroma_settings = ChromaSettings(
                        chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                        chroma_client_auth_credentials=api_key,
                        tenant=tenant,
                        database=database
                    )
                return chromadb.HttpClient(
                    host=host,
                    port=int(os.getenv("CHROMA_PORT", "443")),
                    ssl=os.getenv("CHROMA_SSL", "true").lower() == "true",
                    settings=chroma_settings
                )
        else:
            persist_dir = settings.CHROMA_PERSIST_DIRECTORY
            logger.info(f"Ingest connecting to local Chroma DB (persist: {persist_dir})")
            return chromadb.PersistentClient(path=persist_dir)

    def ingest_pdf(self, pdf_path: str) -> int:
        """
        Parses, chunks, and uploads a single PDF file to ChromaDB.
        Returns the count of chunks uploaded.
        """
        path = Path(pdf_path)
        if not path.exists():
            logger.error(f"Cannot ingest: PDF file not found at {pdf_path}")
            return 0

        # 1. Parse pages
        pages = self.parser.parse_faculty_profile(str(path))
        
        documents = []
        metadatas = []
        ids = []
        pdf_name = path.name

        # 2. Chunk each page
        for page in pages:
            page_num = page["page_number"]
            page_chunks = self.chunker.split_text(page["text"])
            
            for idx, chunk in enumerate(page_chunks):
                chunk_id = f"{pdf_name}_p{page_num}_c{idx}"
                documents.append(chunk)
                metadatas.append({
                    "source": pdf_name,
                    "page": page_num,
                    "chunk": idx
                })
                ids.append(chunk_id)

        if not documents:
            logger.warning(f"No content extracted from {pdf_name}. Nothing to upload.")
            return 0

        # 3. Upload to ChromaDB
        logger.info(f"Uploading {len(documents)} chunks to collection '{self.collection_name}'...")
        collection = self.client.get_or_create_collection(name=self.collection_name)
        
        # Batch uploads to avoid size limits
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_metas = metadatas[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            
            collection.upsert(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            
        logger.info(f"Successfully ingested {pdf_name} ({len(documents)} chunks).")
        return len(documents)

    def ingest_directory(self, directory_path: str) -> int:
        """
        Batch ingests all PDFs in the given directory.
        Returns the total count of chunks uploaded.
        """
        dir_path = Path(directory_path)
        if not dir_path.is_dir():
            logger.error(f"Cannot ingest batch: {directory_path} is not a directory.")
            return 0

        pdf_files = list(dir_path.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in directory for batch ingestion.")
        
        total_chunks = 0
        for pdf_file in pdf_files:
            chunks_count = self.ingest_pdf(str(pdf_file))
            total_chunks += chunks_count
            
        logger.info(f"Batch ingestion complete. Total chunks uploaded: {total_chunks}")
        return total_chunks
