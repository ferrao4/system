# AI Calling Bot Setup Guide

This guide will help you set up and run the AI Calling Bot in your environment.

## Environment Setup

### Option 1: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv ai_calling_bot_env

# Activate virtual environment
source ai_calling_bot_env/bin/activate  # Linux/Mac
# or
ai_calling_bot_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using System Packages (Linux)

```bash
# Install system packages
sudo apt update
sudo apt install python3-fastapi python3-uvicorn python3-websockets
sudo apt install python3-aiofiles python3-requests python3-dotenv

# For audio processing
sudo apt install python3-pyaudio portaudio19-dev
sudo apt install espeak espeak-data libespeak-dev

# Install remaining packages with pip
pip install --user speech-recognition pyttsx3 twilio openai
```

### Option 3: Using Docker (Alternative)

```dockerfile
# Create Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "ai_calling_bot.py"]
```

## Configuration

1. **Copy Environment File**
   ```bash
   cp .env .env.local
   ```

2. **Edit Configuration**
   Update `.env.local` with your API keys:
   ```env
   # Required for advanced AI features
   OPENAI_API_KEY=sk-your-openai-key-here
   
   # Required for phone calling
   TWILIO_ACCOUNT_SID=AC1234567890abcdef
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   ```

## Running the Application

### Method 1: Direct Python Execution

```bash
# Activate virtual environment if using one
source ai_calling_bot_env/bin/activate

# Run the application
python ai_calling_bot.py
```

### Method 2: Using Uvicorn

```bash
uvicorn ai_calling_bot:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Using the Startup Script

```bash
chmod +x start.sh
./start.sh
```

## Accessing the Application

Once running, you can access:

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## Features Available

### Without API Keys (Basic Mode)
- ✅ Web interface
- ✅ Call session management
- ✅ Basic conversation with fallback responses
- ✅ Audio recording interface
- ✅ Call history

### With OpenAI API Key
- ✅ Advanced AI conversations
- ✅ Context-aware responses
- ✅ Natural language processing

### With Twilio Credentials
- ✅ Real phone calling
- ✅ Incoming call handling
- ✅ TwiML voice responses
- ✅ Call status tracking

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install missing packages
   pip install --user package_name
   
   # Or use virtual environment
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Audio Not Working**
   ```bash
   # Install audio dependencies
   sudo apt install portaudio19-dev python3-pyaudio
   pip install --user pyaudio
   ```

3. **Permission Errors**
   ```bash
   # Use --user flag for pip
   pip install --user package_name
   
   # Or create virtual environment
   python3 -m venv myenv
   ```

4. **Port Already in Use**
   ```bash
   # Use different port
   uvicorn ai_calling_bot:app --port 8001
   
   # Or kill existing process
   sudo lsof -t -i tcp:8000 | xargs kill
   ```

### Testing the Setup

1. **Check Dependencies**
   ```bash
   python -c "import fastapi, uvicorn; print('✅ FastAPI available')"
   python -c "import speech_recognition; print('✅ Speech Recognition available')"
   ```

2. **Test Web Interface**
   - Open http://localhost:8000
   - Click "Start Call"
   - Try recording audio

3. **Test API**
   ```bash
   curl -X POST http://localhost:8000/api/calls/start \
        -H "Content-Type: application/json" \
        -d '{"config": {"voice_enabled": true}}'
   ```

## Development Mode

For development with auto-reload:

```bash
uvicorn ai_calling_bot:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

For production deployment:

1. **Use Production WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn ai_calling_bot:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Configure Environment Variables**
   ```bash
   export OPENAI_API_KEY="your_key"
   export TWILIO_ACCOUNT_SID="your_sid"
   # etc.
   ```

3. **Set Up Reverse Proxy** (nginx, Apache, etc.)

4. **Configure HTTPS** for Twilio webhooks

## Next Steps

1. Configure your API keys in `.env`
2. Test the web interface
3. Set up Twilio webhooks for phone integration
4. Customize AI responses in the code
5. Deploy to production server

For detailed documentation, see README.md