"""
WhatsApp Service for WhatsApp RAG Assistant
"""
import requests
from typing import Dict, Any, Optional
from ..config import settings


class WhatsAppService:
    def __init__(self):
        self.api_url = "https://graph.facebook.com/v18.0"
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id

    def send_message(self, recipient_id: str, message: str, message_type: str = "text") -> Dict[str, Any]:
        """
        Send a message to a WhatsApp user
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": message_type,
            "text": {
                "body": message
            }
        }

        if message_type == "text":
            payload["text"] = {"body": message}
        elif message_type == "voice":
            # For voice messages, we'd need to upload the media first
            # This is a simplified implementation
            payload["audio"] = {"id": message}  # Assuming message contains media ID

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def validate_webhook(self, hub_verify_token: str, challenge: str) -> Optional[str]:
        """
        Validate the webhook verification request from WhatsApp
        """
        if hub_verify_token == settings.whatsapp_verify_token:
            return challenge
        return None

    def validate_access_token(self, token: str) -> bool:
        """
        Validate the WhatsApp access token
        """
        url = f"{self.api_url}/me/accounts"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except Exception:
            return False

    def get_phone_number_details(self) -> Dict[str, Any]:
        """
        Get details about the WhatsApp phone number
        """
        url = f"{self.api_url}/{self.phone_number_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(url, headers=headers)
        return response.json()

    def mark_message_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()