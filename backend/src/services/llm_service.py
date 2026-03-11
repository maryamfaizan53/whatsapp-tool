"""
LLM Service for WhatsApp RAG Assistant
"""
from typing import Dict, Any, List
from openai import OpenAI
from ..config import settings


class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate_response(
        self,
        query: str,
        context: List[str],
        language: str = "en",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a response using the LLM with provided context
        """
        try:
            # Construct the prompt with context
            context_str = "\n\n".join(context) if context else "No specific context provided."

            prompt = f"""
            You are an AI assistant for a WhatsApp chatbot that helps users with information
            based on a provided knowledge base. Answer the user's question based on the context provided.

            Context:
            {context_str}

            User's question: {query}

            Please provide a helpful, accurate response based on the context. If the context
            doesn't contain relevant information to answer the question, politely say that you
            don't have that information and suggest contacting a human representative if needed.

            Respond in the same language as the user's query ({language}).
            """

            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides accurate information based on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=500
            )

            # Extract the response
            generated_text = response.choices[0].message.content.strip()

            # Calculate confidence based on whether the response acknowledges lack of information
            confidence = self.calculate_response_confidence(generated_text, context)

            return {
                "response": generated_text,
                "confidence": confidence,
                "success": True,
                "model_used": response.model
            }

        except Exception as e:
            return {
                "response": "I'm sorry, but I'm having trouble generating a response right now. Please try again later.",
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }

    def calculate_response_confidence(self, response: str, context: List[str]) -> float:
        """
        Calculate confidence in the response based on various heuristics
        """
        response_lower = response.lower()

        # Check if response indicates lack of information
        if any(phrase in response_lower for phrase in [
            "i don't have that information",
            "i don't know",
            "i'm not sure",
            "no specific information",
            "not mentioned in the context",
            "not found in the context"
        ]):
            return 0.3  # Low confidence when acknowledging lack of info

        # Check if context was empty
        if not context or len(context) == 0:
            return 0.4  # Lower confidence when no context was provided

        # Check if response seems substantive
        if len(response.split()) < 10:
            return 0.5  # Medium-low confidence for very short responses

        # High confidence if we have context and a substantial response
        return 0.8

    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate the user query for appropriateness
        """
        # Basic validation to check for inappropriate content
        query_lower = query.lower()

        # Check for common inappropriate patterns
        inappropriate_patterns = [
            "joke about",
            "make fun of",
            "offensive",
            "harmful",
            "discriminatory",
            "threatening",
            "harassment"
        ]

        for pattern in inappropriate_patterns:
            if pattern in query_lower:
                return {
                    "valid": False,
                    "reason": "Query contains potentially inappropriate content",
                    "confidence": 0.9
                }

        # If no issues found
        return {
            "valid": True,
            "reason": "Query appears appropriate",
            "confidence": 1.0
        }

    def generate_fallback_response(self, query: str, language: str = "en") -> Dict[str, Any]:
        """
        Generate a fallback response when RAG doesn't provide good results
        """
        fallback_prompt = f"""
        A user asked: "{query}"

        The system couldn't find relevant information in the knowledge base to answer this question.
        Please provide a polite response acknowledging this limitation and suggesting alternatives.
        Respond in the same language as the query ({language}).
        """

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. When you don't have specific information, acknowledge this politely and suggest alternatives like contacting human support."},
                    {"role": "user", "content": fallback_prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )

            return {
                "response": response.choices[0].message.content.strip(),
                "confidence": 0.6,  # Lower confidence for fallback responses
                "success": True
            }
        except Exception as e:
            return {
                "response": "I'm unable to process your request at the moment. Please contact human support for assistance.",
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }


# Global instance
llm_service = LLMService()