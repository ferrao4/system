# AI Calling Bot 🤖📞

A sophisticated AI-powered calling bot with voice recognition, text-to-speech, and real phone calling capabilities using Twilio integration.

## Features

- 🎤 **Voice Recognition**: Real-time speech-to-text conversion
- 🔊 **Text-to-Speech**: Natural AI voice responses
- 📱 **Phone Integration**: Make and receive actual phone calls via Twilio
- 🤖 **AI Conversations**: Powered by OpenAI GPT models with fallback responses
- 💻 **Web Interface**: Beautiful, modern web dashboard
- 📊 **Call Management**: Track call history and manage active calls
- 🔗 **WebSocket Support**: Real-time communication
- 🌐 **REST API**: Complete API for integration

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-calling-bot

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```env
# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Twilio Configuration (for phone calling)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Speech Services
GOOGLE_CLOUD_API_KEY=your_google_cloud_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 3. Run the Application

```bash
# Start the server
python ai_calling_bot.py

# Or use uvicorn directly
uvicorn ai_calling_bot:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the Web Interface

Open your browser and navigate to: `http://localhost:8000`

## API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- `POST /api/calls/start` - Start a new call session
- `POST /api/calls/{call_id}/end` - End a call session
- `POST /api/calls/{call_id}/audio` - Upload audio for processing
- `GET /api/calls/history` - Get call history
- `POST /phone/make-call` - Make an outbound phone call
- `POST /twilio/voice` - Twilio webhook for incoming calls

## Setup Instructions

### Twilio Setup (for Real Phone Calls)

1. **Create a Twilio Account**
   - Sign up at [twilio.com](https://www.twilio.com)
   - Get your Account SID and Auth Token

2. **Get a Phone Number**
   - Purchase a phone number in the Twilio Console
   - Configure webhooks for voice calls

3. **Configure Webhooks**
   - Set your webhook URL to: `https://your-domain.com/phone/twilio/voice`
   - Set status callback URL to: `https://your-domain.com/phone/twilio/status`

### OpenAI Setup (for Advanced AI Responses)

1. **Get API Key**
   - Create an account at [platform.openai.com](https://platform.openai.com)
   - Generate an API key

2. **Add to Environment**
   - Set `OPENAI_API_KEY` in your `.env` file

## Usage

### Web Interface

1. **Start a Call**
   - Click "Start Call" to begin a new session
   - Use microphone controls to record voice messages
   - View real-time conversation

2. **Make Phone Calls**
   - Use the API endpoint to make outbound calls
   - Configure Twilio webhooks for incoming calls

### Voice Commands

The AI bot responds to various voice commands:
- Greetings: "Hello", "Hi", "Hey"
- Questions: "How are you?", "What time is it?"
- Ending: "Goodbye", "Bye", "End call"

### API Integration

```python
import requests

# Start a call
response = requests.post('http://localhost:8000/api/calls/start', 
                        json={"config": {"voice_enabled": True}})
call_id = response.json()["call_id"]

# Make a phone call
response = requests.post('http://localhost:8000/phone/make-call',
                        params={"to_number": "+1234567890"})
```

## Architecture

```
ai_calling_bot.py          # Main FastAPI application
├── CallManager            # Handles call sessions and AI responses
├── TTS/STT Integration    # Speech processing
└── WebSocket Support      # Real-time communication

twilio_phone_service.py    # Twilio integration service
├── Phone Call Management  # Make/receive calls
├── TwiML Generation      # Voice response creation
└── Call Status Tracking   # Monitor call progress

phone_integration.py       # Phone API endpoints
├── Outbound Calls        # Make phone calls
├── Webhook Handlers      # Process Twilio callbacks
└── Status Management     # Track call states
```

## Troubleshooting

### Common Issues

1. **Audio not working**
   - Check microphone permissions in browser
   - Ensure PyAudio is properly installed
   - Try reinstalling: `pip install pyaudio`

2. **Phone calls not working**
   - Verify Twilio credentials in `.env`
   - Check webhook URLs are publicly accessible
   - Ensure phone number is verified

3. **AI responses not working**
   - Check OpenAI API key
   - Verify internet connection
   - Review API usage limits

### Dependencies Issues

**PyAudio Installation (if needed):**

```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Windows
pip install pipwin
pipwin install pyaudio
```

## Advanced Configuration

### Custom AI Models

You can customize the AI responses by:
1. Modifying the system prompt in `generate_ai_response()`
2. Adding custom response patterns in `get_fallback_response()`
3. Integrating different AI providers

### Webhook Security

For production, add webhook validation:

```python
from twilio.request_validator import RequestValidator

def validate_twilio_request(request):
    validator = RequestValidator(auth_token)
    return validator.validate(url, post_data, signature)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review Twilio and OpenAI documentation

---

Built with ❤️ using FastAPI, Twilio, and OpenAI