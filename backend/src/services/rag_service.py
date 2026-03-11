"""
RAG Service for WhatsApp RAG Assistant
"""
from typing import List, Dict, Any
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from pinecone import Pinecone
from ..config import settings


class RAGService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.embedding_model = OpenAIEmbedding(model="text-embedding-3-small")
        self.llm = OpenAI(model="gpt-4-turbo")

    def query_knowledge_base(
        self,
        vector_index_name: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Query a knowledge base using RAG and return a response
        """
        try:
            # Get the Pinecone index
            pinecone_index = self.pc.Index(vector_index_name)

            # Create vector store
            vector_store = PineconeVectorStore(
                pinecone_index=pinecone_index,
                embed_dim=1536
            )

            # Create service context
            service_context = ServiceContext.from_defaults(
                llm=self.llm,
                embed_model=self.embedding_model
            )

            # Create index
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                service_context=service_context
            )

            # Create retriever
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=top_k,
            )

            # Create query engine
            query_engine = RetrieverQueryEngine(
                retriever=retriever,
                node_postprocessors=[
                    SimilarityPostprocessor(similarity_cutoff=similarity_threshold)
                ],
            )

            # Query and get response
            response = query_engine.query(query)

            # Extract nodes for context
            source_nodes = [str(node.node.text) for node in response.source_nodes]

            return {
                "response": str(response),
                "source_nodes": source_nodes,
                "confidence": calculate_confidence(response)
            }

        except Exception as e:
            # If there's an error, return a default response
            return {
                "response": "I couldn't find relevant information in the knowledge base to answer your question.",
                "source_nodes": [],
                "confidence": 0.0,
                "error": str(e)
            }


def calculate_confidence(response) -> float:
    """
    Calculate confidence score based on the response
    """
    # This is a simplified confidence calculation
    # In a real implementation, this would be more sophisticated
    if hasattr(response, 'source_nodes') and response.source_nodes:
        # If we have source nodes, we have some confidence
        return 0.8
    else:
        # If no source nodes, lower confidence
        return 0.3


# Global instance
rag_service = RAGService()