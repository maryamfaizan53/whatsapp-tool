"""
Language Detection Service for WhatsApp RAG Assistant
"""
from typing import Dict, Any
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException


# Set seed for consistent results
DetectorFactory.seed = 0


class LanguageService:
    def __init__(self):
        pass

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the given text
        """
        try:
            detected_lang = detect(text)
            return {
                "language_code": detected_lang,
                "confidence": 1.0,  # Langdetect doesn't provide confidence scores
                "success": True
            }
        except LangDetectException as e:
            # If detection fails, default to English
            return {
                "language_code": "en",
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }

    def get_language_name(self, language_code: str) -> str:
        """
        Get the full name of a language from its code
        """
        language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh-cn": "Chinese (Simplified)",
            "zh-tw": "Chinese (Traditional)",
            "ar": "Arabic",
            "hi": "Hindi",
            "ur": "Urdu",
            "bn": "Bengali",
            "pa": "Punjabi",
            "ta": "Tamil",
            "te": "Telugu",
            "ml": "Malayalam"
        }

        return language_names.get(language_code.lower(), language_code)

    def is_supported_language(self, language_code: str) -> bool:
        """
        Check if the language is supported by our system
        """
        supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko",
            "zh-cn", "zh-tw", "ar", "hi", "ur", "bn", "pa", "ta", "te", "ml"
        ]

        return language_code.lower() in supported_languages

    def normalize_language_code(self, language_code: str) -> str:
        """
        Normalize language codes to our standard format
        """
        normalization_map = {
            "zh": "zh-cn",  # Default to Simplified Chinese
            "zh-hans": "zh-cn",
            "zh-hant": "zh-tw"
        }

        return normalization_map.get(language_code.lower(), language_code.lower())


# Global instance
language_service = LanguageService()