"""
Voice Processing Service for WhatsApp RAG Assistant
"""
import requests
import tempfile
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from ..config import settings


class VoiceService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def download_media(self, media_url: str, access_token: str) -> bytes:
        """
        Download media from WhatsApp servers
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(media_url, headers=headers)
        response.raise_for_status()

        return response.content

    def transcribe_audio(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper
        """
        try:
            # Create a temporary file to save the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name

            try:
                # Use OpenAI Whisper to transcribe the audio
                with open(temp_file_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )

                return {
                    "text": transcript.text,
                    "success": True,
                    "confidence": 0.9  # Placeholder for actual confidence
                }
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)

        except Exception as e:
            return {
                "text": "",
                "success": False,
                "error": str(e),
                "confidence": 0.0
            }

    def convert_text_to_speech(self, text: str, voice: str = "alloy") -> Optional[bytes]:
        """
        Convert text to speech using OpenAI TTS
        """
        try:
            # Use OpenAI TTS to generate speech
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,  # Options: alloy, echo, fable, onyx, nova, shimmer
                input=text
            )

            return response.content

        except Exception as e:
            print(f"Error in text-to-speech conversion: {e}")
            return None

    def process_voice_message(self, media_url: str) -> Dict[str, Any]:
        """
        Complete process for handling a voice message
        """
        try:
            # Download the audio file
            audio_content = self.download_media(media_url, settings.whatsapp_access_token)

            # Transcribe the audio
            transcription_result = self.transcribe_audio(audio_content)

            if transcription_result["success"]:
                return {
                    "text": transcription_result["text"],
                    "success": True,
                    "confidence": transcription_result["confidence"]
                }
            else:
                return {
                    "text": "",
                    "success": False,
                    "error": transcription_result["error"],
                    "confidence": 0.0
                }

        except Exception as e:
            return {
                "text": "",
                "success": False,
                "error": str(e),
                "confidence": 0.0
            }


# Global instance
voice_service = VoiceService()