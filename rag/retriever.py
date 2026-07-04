"""
ChromaDB Retrieval Engine.
Queries the ChromaDB collection to retrieve relevant chunks based on vector distance.
"""

import os
import chromadb
from core.config import settings
from core.logger import logger

class ChromaRetriever:
    def __init__(self):
        self.client = self._init_client()
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        
    def _init_client(self):
        """Initializes the correct Chroma client according to settings."""
        mode = os.getenv("CHROMA_MODE", "remote").strip().lower()
        
        if mode == "remote":
            host = os.getenv("CHROMA_HOST", "api.trychroma.com").strip()
            api_key = settings.CHROMA_API_KEY.strip()
            tenant = settings.CHROMA_TENANT.strip()
            database = settings.CHROMA_DATABASE.strip()
            
            if "trychroma.com" in host.lower():
                logger.info(f"Retriever connecting to Chroma Cloud at {host}")
                return chromadb.CloudClient(
                    api_key=api_key,
                    tenant=tenant,
                    database=database,
                    cloud_host=host
                )
            else:
                logger.info(f"Retriever connecting to self-hosted Chroma at {host}")
                # Fallback to HttpClient for self-hosted
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
            logger.info(f"Retriever connecting to local Chroma DB (persist: {persist_dir})")
            return chromadb.PersistentClient(path=persist_dir)

    def retrieve(self, query_text: str, n_results: int | None = None) -> list[dict]:
        """
        Retrieves matching document chunks from the collection.
        Returns a list of dictionaries: [{"document": ..., "metadata": ..., "distance": ...}]
        """
        if n_results is None:
            n_results = settings.RAG_TOP_K
            
        logger.info(f"Retrieving top {n_results} chunks from collection '{self.collection_name}' for query")
        
        try:
            collection = self.client.get_collection(name=self.collection_name)
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Reformat to structured list
            formatted_results = []
            if results and results["documents"] and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
                dists = results["distances"][0] if results["distances"] else [0.0] * len(docs)
                ids = results["ids"][0] if results["ids"] else [""] * len(docs)
                
                for i in range(len(docs)):
                    formatted_results.append({
                        "id": ids[i],
                        "document": docs[i],
                        "metadata": metas[i] if metas[i] else {},
                        "distance": dists[i]
                    })
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            return []
