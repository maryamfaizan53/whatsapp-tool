"""
Knowledge Base Service for WhatsApp RAG Assistant
"""
import tempfile
import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import UploadFile
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from pinecone import Pinecone
from ..config import settings
from ..models.knowledge_base import KnowledgeBase
from ..models.document import Document as DocumentModel


class KnowledgeBaseService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.embedding_model = OpenAIEmbedding(model="text-embedding-3-small")
        self.llm = OpenAI(model="gpt-4-turbo")

    def add_document_to_knowledge_base(
        self,
        file: UploadFile,
        kb_id: str,
        db: Session
    ) -> DocumentModel:
        """
        Add a document to a knowledge base
        """
        # Create a temporary file to save the uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(file.file.read())
            temp_file_path = temp_file.name

        try:
            # Create document record in database
            document = DocumentModel(
                kb_id=kb_id,
                filename=file.filename,
                status="processing"
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            # Index the document using LlamaIndex
            documents = SimpleDirectoryReader(input_files=[temp_file_path]).load_data()

            # Get the knowledge base to retrieve or create vector index
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.kb_id == kb_id).first()

            if not kb.vector_index_name:
                # Create a new vector index name
                vector_index_name = f"kb_{kb_id.replace('-', '_')}"
                kb.vector_index_name = vector_index_name
                db.commit()

            # Create or get Pinecone index
            if kb.vector_index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=kb.vector_index_name,
                    dimension=1536,  # Default for text-embedding-3-small
                    metric="cosine"
                )

            # Create vector store
            vector_store = PineconeVectorStore(
                pinecone_index=self.pc.Index(kb.vector_index_name),
                embed_dim=1536
            )

            # Create index and add documents
            index = VectorStoreIndex.from_vector_store(vector_store)
            for doc in documents:
                index.insert(doc)

            # Update document status
            document.status = "indexed"
            document.indexed_chunks = len(documents)
            db.commit()

            return document

        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    def crawl_and_index_website(self, kb_id: str, url: str):
        """
        Crawl a website and index its content
        """
        # This would use a web crawler like LlamaIndex's WebPageReader
        # For now, we'll create a placeholder implementation

        print(f"Crawling and indexing website: {url} for knowledge base: {kb_id}")

        # In a real implementation, we would:
        # 1. Use LlamaIndex's WebPageReader to crawl the website
        # 2. Process the content
        # 3. Add it to the appropriate vector store

        # Placeholder for actual implementation
        pass

    def reindex_knowledge_base(self, kb_id: str):
        """
        Re-index all documents in a knowledge base
        """
        print(f"Re-indexing knowledge base: {kb_id}")

        # In a real implementation, we would:
        # 1. Get all documents for this knowledge base
        # 2. Remove all vectors from the vector store
        # 3. Re-index all documents
        # 4. Update the status of the knowledge base

        # Placeholder for actual implementation
        pass

    def query_knowledge_base(
        self,
        kb_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query a knowledge base and return relevant results
        """
        # Get the knowledge base from database
        # This would need to be passed from the calling function

        # For now, return an empty list
        # In a real implementation, we would:
        # 1. Get the vector index name from the database
        # 2. Query the appropriate Pinecone index
        # 3. Return the results

        return []

    def delete_knowledge_base(self, kb_id: str):
        """
        Delete a knowledge base and its associated data
        """
        # This would delete the vector index from Pinecone
        # and remove all related records from the database
        print(f"Deleting knowledge base: {kb_id}")

        # Placeholder for actual implementation
        pass