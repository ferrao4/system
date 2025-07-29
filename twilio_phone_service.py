from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os
import logging
from typing import Dict, Optional
import asyncio
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TwilioPhoneService:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.warning("Twilio credentials not found. Phone calling will be disabled.")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio client initialized successfully")
    
    def is_available(self) -> bool:
        """Check if Twilio service is available"""
        return self.client is not None
    
    async def make_call(self, to_number: str, webhook_url: str) -> Optional[str]:
        """Make an outbound call"""
        if not self.is_available():
            raise Exception("Twilio service not available")
        
        try:
            call = self.client.calls.create(
                twiml=f'<Response><Say>Hello, this is your AI calling bot. Please hold while I connect you.</Say><Redirect>{webhook_url}/twilio/voice</Redirect></Response>',
                to=to_number,
                from_=self.phone_number
            )
            logger.info(f"Call initiated: {call.sid}")
            return call.sid
        except Exception as e:
            logger.error(f"Failed to make call: {e}")
            raise
    
    def create_voice_response(self, message: str = None, gather_input: bool = False) -> str:
        """Create TwiML voice response"""
        response = VoiceResponse()
        
        if message:
            response.say(message, voice='alice', language='en-US')
        
        if gather_input:
            gather = response.gather(
                input='speech',
                timeout=5,
                speech_timeout=2,
                action='/twilio/process-speech',
                method='POST'
            )
            gather.say("Please speak your message after the beep.", voice='alice')
            response.say("I didn't hear anything. Please try again.", voice='alice')
        else:
            response.hangup()
        
        return str(response)
    
    def create_incoming_call_response(self, ai_message: str = None) -> str:
        """Handle incoming calls"""
        if not ai_message:
            ai_message = "Hello! You've reached the AI calling bot. How can I help you today?"
        
        return self.create_voice_response(ai_message, gather_input=True)
    
    async def get_call_status(self, call_sid: str) -> Dict:
        """Get call status and details"""
        if not self.is_available():
            return {"status": "unavailable", "error": "Twilio service not available"}
        
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "duration": call.duration,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None
            }
        except Exception as e:
            logger.error(f"Failed to get call status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def end_call(self, call_sid: str) -> bool:
        """End an active call"""
        if not self.is_available():
            return False
        
        try:
            call = self.client.calls(call_sid).update(status='completed')
            logger.info(f"Call ended: {call.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to end call: {e}")
            return False

# Global instance
twilio_service = TwilioPhoneService()