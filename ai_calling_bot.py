from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import aiofiles
import speech_recognition as sr
import pyttsx3
import threading
import wave
import pyaudio
from pathlib import Path
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Calling Bot", description="Advanced AI-powered calling bot with voice capabilities")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
active_calls: Dict[str, dict] = {}
call_history: List[dict] = []
tts_engine = None

# Initialize TTS engine
def init_tts():
    global tts_engine
    try:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 150)  # Speed of speech
        tts_engine.setProperty('volume', 0.8)  # Volume level (0.0 to 1.0)
        voices = tts_engine.getProperty('voices')
        if voices:
            tts_engine.setProperty('voice', voices[0].id)  # Use first available voice
        logger.info("TTS engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize TTS engine: {e}")

# Initialize TTS on startup
init_tts()

class CallManager:
    def __init__(self):
        self.active_calls = {}
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
    async def start_call(self, call_id: str, config: dict):
        """Start a new call session"""
        self.active_calls[call_id] = {
            "id": call_id,
            "status": "active",
            "start_time": datetime.now().isoformat(),
            "config": config,
            "conversation": [],
            "audio_buffer": []
        }
        logger.info(f"Started call {call_id}")
        
    async def end_call(self, call_id: str):
        """End a call session"""
        if call_id in self.active_calls:
            call_data = self.active_calls[call_id]
            call_data["status"] = "ended"
            call_data["end_time"] = datetime.now().isoformat()
            call_history.append(call_data)
            del self.active_calls[call_id]
            logger.info(f"Ended call {call_id}")
            
    async def process_audio(self, call_id: str, audio_data: bytes):
        """Process incoming audio data"""
        if call_id not in self.active_calls:
            raise HTTPException(status_code=404, detail="Call not found")
            
        try:
            # Save audio temporarily
            audio_file = f"temp_audio_{call_id}.wav"
            with open(audio_file, "wb") as f:
                f.write(audio_data)
            
            # Speech to text
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                
            # Add to conversation
            self.active_calls[call_id]["conversation"].append({
                "timestamp": datetime.now().isoformat(),
                "speaker": "caller",
                "text": text
            })
            
            # Generate AI response
            ai_response = await self.generate_ai_response(call_id, text)
            
            # Add AI response to conversation
            self.active_calls[call_id]["conversation"].append({
                "timestamp": datetime.now().isoformat(),
                "speaker": "ai",
                "text": ai_response
            })
            
            # Convert response to speech
            audio_response = await self.text_to_speech(ai_response)
            
            # Clean up temporary file
            os.remove(audio_file)
            
            return {"text": text, "ai_response": ai_response, "audio_response": audio_response}
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
    
    async def generate_ai_response(self, call_id: str, user_input: str) -> str:
        """Generate AI response using OpenAI or fallback to rule-based responses"""
        try:
            # Try OpenAI if API key is available
            if os.getenv("OPENAI_API_KEY"):
                openai.api_key = os.getenv("OPENAI_API_KEY")
                
                conversation_history = self.active_calls[call_id]["conversation"]
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant for phone calls. Be conversational, helpful, and keep responses concise for voice interaction."}
                ]
                
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    role = "user" if msg["speaker"] == "caller" else "assistant"
                    messages.append({"role": role, "content": msg["text"]})
                
                messages.append({"role": "user", "content": user_input})
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=150,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
            else:
                # Fallback to rule-based responses
                return self.get_fallback_response(user_input)
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self.get_fallback_response(user_input)
    
    def get_fallback_response(self, user_input: str) -> str:
        """Fallback rule-based responses"""
        user_input_lower = user_input.lower()
        
        if any(greeting in user_input_lower for greeting in ["hello", "hi", "hey"]):
            return "Hello! How can I help you today?"
        elif any(word in user_input_lower for word in ["how are you", "how's it going"]):
            return "I'm doing great, thank you for asking! How can I assist you?"
        elif any(word in user_input_lower for word in ["weather", "temperature"]):
            return "I don't have access to current weather data, but you can check your local weather app or website for the most up-to-date information."
        elif any(word in user_input_lower for word in ["time", "what time"]):
            current_time = datetime.now().strftime("%H:%M")
            return f"The current time is {current_time}."
        elif any(word in user_input_lower for word in ["bye", "goodbye", "end call"]):
            return "Thank you for calling! Have a great day. Goodbye!"
        else:
            return "I understand you're asking about something, but I'm not sure how to help with that specific request. Could you please rephrase or ask something else?"
    
    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech audio"""
        try:
            if tts_engine:
                # Save to temporary file
                audio_file = f"temp_tts_{uuid.uuid4()}.wav"
                tts_engine.save_to_file(text, audio_file)
                tts_engine.runAndWait()
                
                # Read the audio file
                async with aiofiles.open(audio_file, "rb") as f:
                    audio_data = await f.read()
                
                # Clean up
                os.remove(audio_file)
                return audio_data
            else:
                # Return empty audio if TTS not available
                return b""
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return b""

call_manager = CallManager()

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main web interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Calling Bot</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }
            h1 {
                text-align: center;
                margin-bottom: 40px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .call-controls {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-bottom: 40px;
                flex-wrap: wrap;
            }
            .btn {
                padding: 15px 30px;
                border: none;
                border-radius: 50px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px 0 rgba(31, 38, 135, 0.2);
            }
            .btn-primary {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
            }
            .btn-danger {
                background: linear-gradient(45deg, #ff416c, #ff4757);
                color: white;
            }
            .btn-success {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px 0 rgba(31, 38, 135, 0.4);
            }
            .status {
                text-align: center;
                margin: 20px 0;
                padding: 15px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.1);
            }
            .conversation {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                max-height: 400px;
                overflow-y: auto;
            }
            .message {
                margin: 10px 0;
                padding: 10px;
                border-radius: 10px;
            }
            .caller {
                background: rgba(255, 255, 255, 0.2);
                margin-left: 20px;
            }
            .ai {
                background: rgba(102, 126, 234, 0.3);
                margin-right: 20px;
            }
            .call-history {
                margin-top: 40px;
            }
            .call-item {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
            }
            .hidden {
                display: none;
            }
            .audio-controls {
                display: flex;
                justify-content: center;
                gap: 15px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Calling Bot</h1>
            
            <div class="call-controls">
                <button class="btn btn-primary" onclick="startCall()">📞 Start Call</button>
                <button class="btn btn-danger" onclick="endCall()" id="endCallBtn" disabled>📞 End Call</button>
                <button class="btn btn-success" onclick="refreshHistory()">🔄 Refresh</button>
            </div>
            
            <div class="audio-controls hidden" id="audioControls">
                <button class="btn btn-primary" onclick="startRecording()" id="recordBtn">🎤 Start Recording</button>
                <button class="btn btn-danger" onclick="stopRecording()" id="stopBtn" disabled>⏹️ Stop Recording</button>
                <audio controls id="audioPlayer" style="margin: 10px;"></audio>
            </div>
            
            <div class="status" id="status">
                Ready to start a call
            </div>
            
            <div class="conversation" id="conversation">
                <p style="text-align: center; opacity: 0.7;">Conversation will appear here...</p>
            </div>
            
            <div class="call-history">
                <h2>📋 Call History</h2>
                <div id="historyContainer">
                    <p style="text-align: center; opacity: 0.7;">No calls yet</p>
                </div>
            </div>
        </div>

        <script>
            let currentCallId = null;
            let mediaRecorder = null;
            let audioChunks = [];
            
            async function startCall() {
                try {
                    const response = await fetch('/api/calls/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            config: {
                                voice_enabled: true,
                                ai_model: "gpt-3.5-turbo"
                            }
                        })
                    });
                    
                    const data = await response.json();
                    currentCallId = data.call_id;
                    
                    document.getElementById('status').textContent = `Call started: ${currentCallId}`;
                    document.getElementById('endCallBtn').disabled = false;
                    document.getElementById('audioControls').classList.remove('hidden');
                    document.querySelector('.btn-primary').disabled = true;
                    
                    updateConversation();
                } catch (error) {
                    console.error('Error starting call:', error);
                    document.getElementById('status').textContent = 'Error starting call';
                }
            }
            
            async function endCall() {
                if (!currentCallId) return;
                
                try {
                    await fetch(`/api/calls/${currentCallId}/end`, {method: 'POST'});
                    
                    document.getElementById('status').textContent = 'Call ended';
                    document.getElementById('endCallBtn').disabled = true;
                    document.getElementById('audioControls').classList.add('hidden');
                    document.querySelector('.btn-primary').disabled = false;
                    
                    currentCallId = null;
                    refreshHistory();
                } catch (error) {
                    console.error('Error ending call:', error);
                }
            }
            
            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        await sendAudio(audioBlob);
                    };
                    
                    mediaRecorder.start();
                    document.getElementById('recordBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                } catch (error) {
                    console.error('Error starting recording:', error);
                }
            }
            
            function stopRecording() {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    document.getElementById('recordBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                }
            }
            
            async function sendAudio(audioBlob) {
                if (!currentCallId) return;
                
                const formData = new FormData();
                formData.append('audio', audioBlob, 'audio.wav');
                
                try {
                    const response = await fetch(`/api/calls/${currentCallId}/audio`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    updateConversation();
                    
                    // Play AI response if available
                    if (data.audio_response) {
                        const audioUrl = URL.createObjectURL(new Blob([data.audio_response]));
                        const audio = new Audio(audioUrl);
                        audio.play();
                    }
                } catch (error) {
                    console.error('Error sending audio:', error);
                }
            }
            
            async function updateConversation() {
                if (!currentCallId) return;
                
                try {
                    const response = await fetch(`/api/calls/${currentCallId}`);
                    const callData = await response.json();
                    
                    const conversationDiv = document.getElementById('conversation');
                    conversationDiv.innerHTML = '';
                    
                    if (callData.conversation.length === 0) {
                        conversationDiv.innerHTML = '<p style="text-align: center; opacity: 0.7;">Say something to start the conversation...</p>';
                        return;
                    }
                    
                    callData.conversation.forEach(message => {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = `message ${message.speaker}`;
                        messageDiv.innerHTML = `
                            <strong>${message.speaker === 'caller' ? 'You' : 'AI'}:</strong>
                            <p>${message.text}</p>
                            <small>${new Date(message.timestamp).toLocaleTimeString()}</small>
                        `;
                        conversationDiv.appendChild(messageDiv);
                    });
                    
                    conversationDiv.scrollTop = conversationDiv.scrollHeight;
                } catch (error) {
                    console.error('Error updating conversation:', error);
                }
            }
            
            async function refreshHistory() {
                try {
                    const response = await fetch('/api/calls/history');
                    const history = await response.json();
                    
                    const historyContainer = document.getElementById('historyContainer');
                    
                    if (history.length === 0) {
                        historyContainer.innerHTML = '<p style="text-align: center; opacity: 0.7;">No calls yet</p>';
                        return;
                    }
                    
                    historyContainer.innerHTML = '';
                    history.reverse().forEach(call => {
                        const callDiv = document.createElement('div');
                        callDiv.className = 'call-item';
                        const duration = call.end_time ? 
                            Math.round((new Date(call.end_time) - new Date(call.start_time)) / 1000) + 's' : 
                            'Ongoing';
                        
                        callDiv.innerHTML = `
                            <strong>Call ID:</strong> ${call.id}<br>
                            <strong>Start:</strong> ${new Date(call.start_time).toLocaleString()}<br>
                            <strong>Duration:</strong> ${duration}<br>
                            <strong>Messages:</strong> ${call.conversation.length}
                        `;
                        historyContainer.appendChild(callDiv);
                    });
                } catch (error) {
                    console.error('Error refreshing history:', error);
                }
            }
            
            // Auto-refresh conversation every 2 seconds during active call
            setInterval(() => {
                if (currentCallId) {
                    updateConversation();
                }
            }, 2000);
            
            // Load history on page load
            refreshHistory();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/calls/start")
async def start_call(config: dict = None):
    """Start a new call"""
    call_id = str(uuid.uuid4())
    await call_manager.start_call(call_id, config or {})
    return {"call_id": call_id, "status": "started"}

@app.post("/api/calls/{call_id}/end")
async def end_call(call_id: str):
    """End a call"""
    await call_manager.end_call(call_id)
    return {"status": "ended"}

@app.get("/api/calls/{call_id}")
async def get_call(call_id: str):
    """Get call details"""
    if call_id in call_manager.active_calls:
        return call_manager.active_calls[call_id]
    
    # Check in history
    for call in call_history:
        if call["id"] == call_id:
            return call
    
    raise HTTPException(status_code=404, detail="Call not found")

@app.get("/api/calls/history")
async def get_call_history():
    """Get call history"""
    return call_history

@app.post("/api/calls/{call_id}/audio")
async def process_call_audio(call_id: str, audio: UploadFile = File(...)):
    """Process audio from a call"""
    if call_id not in call_manager.active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    
    audio_data = await audio.read()
    result = await call_manager.process_audio(call_id, audio_data)
    return result

@app.websocket("/ws/call/{call_id}")
async def websocket_call(websocket: WebSocket, call_id: str):
    """WebSocket endpoint for real-time call communication"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio":
                # Process audio data
                audio_data = message["data"]
                # Process audio here
                response = {"type": "audio_response", "data": "processed"}
                await websocket.send_text(json.dumps(response))
            elif message["type"] == "text":
                # Process text message
                text = message["data"]
                ai_response = await call_manager.generate_ai_response(call_id, text)
                response = {"type": "text_response", "data": ai_response}
                await websocket.send_text(json.dumps(response))
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Include phone integration routes
from phone_integration import router as phone_router
app.include_router(phone_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)