"""
Text message integration examples (SMS, WhatsApp, Telegram).
These are template implementations - actual integration depends on platform APIs.
"""
import os
import requests
from typing import Dict, Optional
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Flask app for webhook
app = Flask(__name__)


def generate_reply(context: str, api_url: str = None) -> Optional[str]:
    """
    Generate reply using digital twin API.
    
    Args:
        context: Conversation context
        api_url: Base URL for digital twin API
    
    Returns:
        Generated reply or None
    """
    api_url = api_url or API_BASE_URL
    
    try:
        response = requests.post(
            f"{api_url}/generate",
            json={
                "context": context,
                "use_rag": True,
                "max_length": 200  # Shorter for texts
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result['reply']
    except Exception as e:
        print(f"Failed to generate reply: {e}")
        return None


# WhatsApp Webhook Example
@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    WhatsApp webhook endpoint.
    Configure in WhatsApp Business API settings.
    """
    data = request.json
    
    # Extract message (format depends on WhatsApp API)
    message = data.get('messages', [{}])[0]
    from_number = message.get('from', '')
    body = message.get('text', {}).get('body', '')
    message_id = message.get('id', '')
    
    # Build context
    context = f"From: {from_number}\n\n{body}"
    
    # Generate reply
    reply = generate_reply(context)
    
    if reply:
        # Send reply via WhatsApp API
        # This is a placeholder - implement actual WhatsApp API call
        return jsonify({
            "status": "success",
            "reply": reply,
            "message_id": message_id
        })
    
    return jsonify({"status": "error", "message": "Failed to generate reply"}), 500


# Telegram Bot Example
@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """
    Telegram webhook endpoint.
    Configure in Telegram Bot API settings.
    """
    data = request.json
    
    # Extract message
    message = data.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')
    from_user = message.get('from', {}).get('username', '')
    
    # Build context
    context = f"From: {from_user}\n\n{text}"
    
    # Generate reply
    reply = generate_reply(context)
    
    if reply:
        # Send reply via Telegram Bot API
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if telegram_token:
            send_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            requests.post(send_url, json={
                "chat_id": chat_id,
                "text": reply
            })
        
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error"}), 500


# SMS Webhook Example (Twilio, etc.)
@app.route('/webhook/sms', methods=['POST'])
def sms_webhook():
    """
    SMS webhook endpoint (e.g., Twilio).
    """
    # Extract SMS data (format depends on provider)
    from_number = request.form.get('From', '')
    body = request.form.get('Body', '')
    
    # Build context
    context = f"From: {from_number}\n\n{body}"
    
    # Generate reply
    reply = generate_reply(context)
    
    if reply:
        # Send SMS reply (implement based on provider)
        return jsonify({
            "status": "success",
            "reply": reply
        })
    
    return jsonify({"status": "error"}), 500


def main():
    """Run Flask webhook server."""
    port = int(os.getenv("WEBHOOK_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()