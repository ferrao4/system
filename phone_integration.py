from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import Response
import logging
from typing import Optional
from twilio_phone_service import twilio_service
from ai_calling_bot import call_manager
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/phone", tags=["phone"])

@router.post("/make-call")
async def make_phone_call(
    to_number: str,
    webhook_base_url: str = "https://your-domain.com"  # Replace with your actual domain
):
    """Make an outbound phone call"""
    if not twilio_service.is_available():
        raise HTTPException(status_code=503, detail="Phone service not available")
    
    try:
        # Create a new call session
        call_id = str(uuid.uuid4())
        await call_manager.start_call(call_id, {
            "type": "phone_call",
            "phone_number": to_number,
            "direction": "outbound"
        })
        
        # Make the call via Twilio
        twilio_call_sid = await twilio_service.make_call(
            to_number=to_number,
            webhook_url=webhook_base_url
        )
        
        # Update call with Twilio SID
        if call_id in call_manager.active_calls:
            call_manager.active_calls[call_id]["twilio_sid"] = twilio_call_sid
        
        return {
            "call_id": call_id,
            "twilio_sid": twilio_call_sid,
            "status": "initiated",
            "to_number": to_number
        }
        
    except Exception as e:
        logger.error(f"Failed to make phone call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/twilio/voice")
async def handle_twilio_voice(request: Request):
    """Handle incoming Twilio voice webhook"""
    # This endpoint receives calls from Twilio
    call_sid = request.query_params.get('CallSid')
    from_number = request.query_params.get('From')
    to_number = request.query_params.get('To')
    
    # Create a new call session for incoming call
    call_id = str(uuid.uuid4())
    await call_manager.start_call(call_id, {
        "type": "phone_call",
        "phone_number": from_number,
        "direction": "inbound",
        "twilio_sid": call_sid
    })
    
    # Generate initial AI response
    initial_message = "Hello! You've reached the AI calling bot. How can I help you today?"
    
    # Create TwiML response
    twiml_response = twilio_service.create_incoming_call_response(initial_message)
    
    return Response(content=twiml_response, media_type="application/xml")

@router.post("/twilio/process-speech")
async def process_twilio_speech(
    request: Request,
    SpeechResult: str = Form(None),
    CallSid: str = Form(None)
):
    """Process speech input from Twilio"""
    if not SpeechResult:
        # No speech detected, ask again
        twiml_response = twilio_service.create_voice_response(
            "I didn't hear anything. Could you please repeat that?",
            gather_input=True
        )
        return Response(content=twiml_response, media_type="application/xml")
    
    try:
        # Find the call session by Twilio SID
        call_id = None
        for cid, call_data in call_manager.active_calls.items():
            if call_data.get("twilio_sid") == CallSid:
                call_id = cid
                break
        
        if not call_id:
            # Create new call session if not found
            call_id = str(uuid.uuid4())
            await call_manager.start_call(call_id, {
                "type": "phone_call",
                "twilio_sid": CallSid,
                "direction": "inbound"
            })
        
        # Process the speech with AI
        ai_response = await call_manager.generate_ai_response(call_id, SpeechResult)
        
        # Add conversation to call history
        call_manager.active_calls[call_id]["conversation"].extend([
            {
                "timestamp": "now",
                "speaker": "caller",
                "text": SpeechResult
            },
            {
                "timestamp": "now", 
                "speaker": "ai",
                "text": ai_response
            }
        ])
        
        # Check if call should end
        if any(word in SpeechResult.lower() for word in ["goodbye", "bye", "end call", "hang up"]):
            twiml_response = twilio_service.create_voice_response(
                ai_response + " Have a great day!",
                gather_input=False
            )
            # End the call session
            await call_manager.end_call(call_id)
        else:
            # Continue conversation
            twiml_response = twilio_service.create_voice_response(
                ai_response,
                gather_input=True
            )
        
        return Response(content=twiml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        error_response = twilio_service.create_voice_response(
            "I'm sorry, I encountered an error. Please try again.",
            gather_input=True
        )
        return Response(content=error_response, media_type="application/xml")

@router.post("/twilio/status")
async def handle_call_status(
    request: Request,
    CallSid: str = Form(None),
    CallStatus: str = Form(None)
):
    """Handle call status updates from Twilio"""
    logger.info(f"Call {CallSid} status: {CallStatus}")
    
    # Find and update call session
    for call_id, call_data in call_manager.active_calls.items():
        if call_data.get("twilio_sid") == CallSid:
            call_data["twilio_status"] = CallStatus
            
            # End call session if call is completed
            if CallStatus in ["completed", "busy", "failed", "no-answer", "canceled"]:
                await call_manager.end_call(call_id)
            break
    
    return {"status": "ok"}

@router.get("/calls/{call_id}/phone-status")
async def get_phone_call_status(call_id: str):
    """Get phone call status via Twilio"""
    if call_id not in call_manager.active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    
    call_data = call_manager.active_calls[call_id]
    twilio_sid = call_data.get("twilio_sid")
    
    if not twilio_sid:
        return {"status": "no_phone_call", "message": "This is not a phone call"}
    
    twilio_status = await twilio_service.get_call_status(twilio_sid)
    return {
        "call_id": call_id,
        "twilio_status": twilio_status,
        "local_status": call_data
    }