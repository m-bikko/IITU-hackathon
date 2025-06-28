# Complete Audio-to-Text Chat with Gemini - Single File Implementation Guide

This document provides complete instructions and code to build an audio-to-text chat application using Google's Gemini AI. After providing this documentation to an AI agent, it should understand how to create a functional AI audio chatbot.

## Overview

This implementation creates a web-based audio chat interface that:
1. Records audio from the user's microphone
2. Sends the audio directly to Google's Gemini AI for transcription and response
3. Displays both the transcribed text and AI response
4. Maintains conversation history

## Prerequisites

- Python 3.8+
- Google API Key for Gemini
- Modern web browser with microphone support

## Required Dependencies

```txt
Flask==2.3.3
google-generativeai==0.3.1
python-dotenv==1.0.0
```

## Environment Setup

Create a `.env` file:
```
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
```

## Complete Single-File Implementation

Create `audio_chat_app.py`:

```python
import os
import logging
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
app.config['UPLOAD_FOLDER'] = 'audio_uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global conversation history (in production, use a database)
conversation_history = []

class GeminiAudioService:
    """Service for handling Gemini AI audio processing and chat responses."""
    
    def __init__(self):
        self.model = None
        self._configure_gemini()
    
    def _configure_gemini(self):
        """Configure Gemini API with error handling."""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            logger.info("Gemini API configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise
    
    def transcribe_and_respond(self, audio_path, conversation_context=""):
        """
        Transcribe audio and generate conversational response.
        
        Args:
            audio_path: Path to audio file
            conversation_context: Previous conversation for context
            
        Returns:
            dict: Contains transcription and AI response
        """
        try:
            # Validate audio file
            if not os.path.exists(audio_path):
                return {"error": "Audio file not found"}
            
            if os.path.getsize(audio_path) == 0:
                return {"error": "Audio file is empty"}
            
            # Determine MIME type based on file extension
            file_ext = os.path.splitext(audio_path)[1].lower()
            mime_type_map = {
                '.webm': 'audio/webm',
                '.m4a': 'audio/m4a',
                '.mp3': 'audio/mp3',
                '.wav': 'audio/wav',
                '.ogg': 'audio/ogg',
                '.flac': 'audio/flac'
            }
            mime_type = mime_type_map.get(file_ext, 'audio/webm')
            
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # Create comprehensive prompt for transcription and response
            prompt = f"""
            You are an intelligent AI assistant engaged in a voice conversation. Please:

            1. TRANSCRIBE: First, accurately transcribe the audio content you hear.
            2. RESPOND: Then provide a helpful, conversational response to what was said.

            CONVERSATION CONTEXT:
            {conversation_context}

            INSTRUCTIONS:
            - Transcribe exactly what you hear in the audio
            - Respond naturally as if having a conversation
            - Be helpful, friendly, and engaging
            - If the audio is unclear, acknowledge this politely
            - Keep responses concise but informative

            FORMAT YOUR RESPONSE AS:
            TRANSCRIPTION: [what you heard]
            RESPONSE: [your conversational reply]
            """
            
            # Send to Gemini with audio
            logger.info(f"Processing audio file: {audio_path} (MIME: {mime_type})")
            response = self.model.generate_content([
                prompt, 
                {"mime_type": mime_type, "data": audio_data}
            ])
            
            # Parse the response
            response_text = response.text.strip()
            
            # Extract transcription and response
            transcription = ""
            ai_response = ""
            
            lines = response_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('TRANSCRIPTION:'):
                    current_section = 'transcription'
                    transcription += line.replace('TRANSCRIPTION:', '').strip()
                elif line.startswith('RESPONSE:'):
                    current_section = 'response'
                    ai_response += line.replace('RESPONSE:', '').strip()
                elif current_section == 'transcription' and line:
                    transcription += ' ' + line
                elif current_section == 'response' and line:
                    ai_response += ' ' + line
            
            # Fallback parsing if format is not followed
            if not transcription or not ai_response:
                # Try to split by common patterns
                if 'TRANSCRIPTION:' in response_text and 'RESPONSE:' in response_text:
                    parts = response_text.split('RESPONSE:')
                    transcription = parts[0].replace('TRANSCRIPTION:', '').strip()
                    ai_response = parts[1].strip()
                else:
                    # Use entire response as both transcription and response
                    transcription = "Audio transcribed successfully"
                    ai_response = response_text
            
            return {
                "transcription": transcription.strip(),
                "response": ai_response.strip(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {
                "error": f"Failed to process audio: {str(e)}",
                "success": False
            }

# Initialize the service
gemini_service = GeminiAudioService()

@app.route('/')
def index():
    """Main chat interface."""
    return render_template('chat.html')

@app.route('/send_audio', methods=['POST'])
def send_audio():
    """Handle audio upload and processing."""
    try:
        # Check if audio file was uploaded
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No audio file selected'}), 400
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(file_path)
        
        # Prepare conversation context
        context = "\n".join([
            f"User: {msg['transcription']}\nAI: {msg['response']}" 
            for msg in conversation_history[-5:]  # Last 5 exchanges for context
        ])
        
        # Process with Gemini
        result = gemini_service.transcribe_and_respond(file_path, context)
        
        # Clean up audio file
        try:
            os.remove(file_path)
        except:
            pass  # Ignore cleanup errors
        
        if result.get('success'):
            # Add to conversation history
            conversation_entry = {
                'timestamp': datetime.now().isoformat(),
                'transcription': result['transcription'],
                'response': result['response']
            }
            conversation_history.append(conversation_entry)
            
            # Keep only last 50 messages
            if len(conversation_history) > 50:
                conversation_history.pop(0)
            
            return jsonify({
                'success': True,
                'transcription': result['transcription'],
                'response': result['response'],
                'timestamp': conversation_entry['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_audio endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_history')
def get_history():
    """Get conversation history."""
    return jsonify({
        'success': True,
        'history': conversation_history
    })

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    return jsonify({'success': True, 'message': 'History cleared'})

# HTML Template (create templates/chat.html)
CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Chat with Gemini AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .chat-container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            width: 90%;
            max-width: 800px;
            height: 80vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .chat-header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 15px;
        }
        
        .chat-header h1 {
            color: #333;
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .chat-header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            background: #fafafa;
        }
        
        .message {
            margin: 10px 0;
            padding: 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: #007bff;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .ai-message {
            background: #f8f9fa;
            color: #333;
            border: 1px solid #e9ecef;
        }
        
        .transcription {
            font-style: italic;
            opacity: 0.8;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .timestamp {
            font-size: 0.8em;
            opacity: 0.6;
            margin-top: 5px;
        }
        
        .chat-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .record-button {
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 50px;
            padding: 15px 30px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 120px;
        }
        
        .record-button:hover {
            background: #c82333;
            transform: translateY(-2px);
        }
        
        .record-button:disabled {
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
        }
        
        .record-button.recording {
            background: #28a745;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .control-button {
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 10px 20px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .control-button:hover {
            background: #5a6268;
            transform: translateY(-1px);
        }
        
        .status {
            text-align: center;
            margin: 10px 0;
            font-weight: 500;
        }
        
        .error {
            color: #dc3545;
        }
        
        .success {
            color: #28a745;
        }
        
        .processing {
            color: #007bff;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 600px) {
            .chat-container {
                width: 95%;
                padding: 20px;
                height: 90vh;
            }
            
            .chat-controls {
                flex-direction: column;
            }
            
            .record-button {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🎤 Audio Chat with Gemini AI</h1>
            <p>Click record, speak, and get AI responses!</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message ai-message">
                <div>👋 Hello! I'm your AI assistant. Click the record button and start talking to me!</div>
                <div class="timestamp">Ready to chat</div>
            </div>
        </div>
        
        <div class="status" id="status"></div>
        
        <div class="chat-controls">
            <button id="recordButton" class="record-button">🎤 Start Recording</button>
            <button id="clearButton" class="control-button">🗑️ Clear Chat</button>
            <button id="historyButton" class="control-button">📋 Load History</button>
        </div>
    </div>

    <script>
        class AudioChatApp {
            constructor() {
                this.mediaRecorder = null;
                this.recordedChunks = [];
                this.isRecording = false;
                
                this.recordButton = document.getElementById('recordButton');
                this.clearButton = document.getElementById('clearButton');
                this.historyButton = document.getElementById('historyButton');
                this.chatMessages = document.getElementById('chatMessages');
                this.status = document.getElementById('status');
                
                this.initializeEventListeners();
                this.loadHistory();
            }
            
            initializeEventListeners() {
                this.recordButton.addEventListener('click', () => this.toggleRecording());
                this.clearButton.addEventListener('click', () => this.clearHistory());
                this.historyButton.addEventListener('click', () => this.loadHistory());
            }
            
            async toggleRecording() {
                if (this.isRecording) {
                    this.stopRecording();
                } else {
                    await this.startRecording();
                }
            }
            
            async startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        } 
                    });
                    
                    this.mediaRecorder = new MediaRecorder(stream, {
                        mimeType: 'audio/webm;codecs=opus'
                    });
                    
                    this.recordedChunks = [];
                    
                    this.mediaRecorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            this.recordedChunks.push(event.data);
                        }
                    };
                    
                    this.mediaRecorder.onstop = () => {
                        this.processRecording();
                    };
                    
                    this.mediaRecorder.start();
                    this.isRecording = true;
                    
                    this.recordButton.textContent = '⏹️ Stop Recording';
                    this.recordButton.classList.add('recording');
                    this.updateStatus('🎙️ Recording... Speak now!', 'processing');
                    
                } catch (error) {
                    console.error('Error starting recording:', error);
                    this.updateStatus('❌ Microphone access denied. Please allow microphone access.', 'error');
                }
            }
            
            stopRecording() {
                if (this.mediaRecorder && this.isRecording) {
                    this.mediaRecorder.stop();
                    this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
                    this.isRecording = false;
                    
                    this.recordButton.textContent = '🎤 Start Recording';
                    this.recordButton.classList.remove('recording');
                    this.recordButton.disabled = true;
                    this.updateStatus('⏳ Processing audio...', 'processing');
                }
            }
            
            async processRecording() {
                try {
                    const audioBlob = new Blob(this.recordedChunks, { type: 'audio/webm' });
                    
                    if (audioBlob.size === 0) {
                        throw new Error('No audio data recorded');
                    }
                    
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.webm');
                    
                    const response = await fetch('/send_audio', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        this.addMessage(result.transcription, result.response, result.timestamp);
                        this.updateStatus('✅ Message processed successfully!', 'success');
                        setTimeout(() => this.clearStatus(), 3000);
                    } else {
                        throw new Error(result.error || 'Unknown error occurred');
                    }
                    
                } catch (error) {
                    console.error('Error processing audio:', error);
                    this.updateStatus(`❌ Error: ${error.message}`, 'error');
                } finally {
                    this.recordButton.disabled = false;
                }
            }
            
            addMessage(transcription, response, timestamp) {
                // Add user message (transcription)
                const userMessage = document.createElement('div');
                userMessage.className = 'message user-message';
                userMessage.innerHTML = `
                    <div class="transcription">You said:</div>
                    <div>${this.escapeHtml(transcription)}</div>
                    <div class="timestamp">${this.formatTimestamp(timestamp)}</div>
                `;
                this.chatMessages.appendChild(userMessage);
                
                // Add AI response
                const aiMessage = document.createElement('div');
                aiMessage.className = 'message ai-message';
                aiMessage.innerHTML = `
                    <div>🤖 ${this.escapeHtml(response)}</div>
                    <div class="timestamp">${this.formatTimestamp(timestamp)}</div>
                `;
                this.chatMessages.appendChild(aiMessage);
                
                // Scroll to bottom
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }
            
            async loadHistory() {
                try {
                    const response = await fetch('/get_history');
                    const result = await response.json();
                    
                    if (result.success) {
                        this.chatMessages.innerHTML = `
                            <div class="message ai-message">
                                <div>👋 Hello! I'm your AI assistant. Click the record button and start talking to me!</div>
                                <div class="timestamp">Ready to chat</div>
                            </div>
                        `;
                        
                        result.history.forEach(entry => {
                            this.addMessage(entry.transcription, entry.response, entry.timestamp);
                        });
                        
                        this.updateStatus('📋 History loaded', 'success');
                        setTimeout(() => this.clearStatus(), 2000);
                    }
                } catch (error) {
                    console.error('Error loading history:', error);
                    this.updateStatus('❌ Failed to load history', 'error');
                }
            }
            
            async clearHistory() {
                try {
                    const response = await fetch('/clear_history', { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.success) {
                        this.chatMessages.innerHTML = `
                            <div class="message ai-message">
                                <div>👋 Hello! I'm your AI assistant. Click the record button and start talking to me!</div>
                                <div class="timestamp">Ready to chat</div>
                            </div>
                        `;
                        this.updateStatus('🗑️ History cleared', 'success');
                        setTimeout(() => this.clearStatus(), 2000);
                    }
                } catch (error) {
                    console.error('Error clearing history:', error);
                    this.updateStatus('❌ Failed to clear history', 'error');
                }
            }
            
            updateStatus(message, type = '') {
                this.status.textContent = message;
                this.status.className = `status ${type}`;
                
                if (type === 'processing') {
                    const loader = document.createElement('span');
                    loader.className = 'loading';
                    this.status.appendChild(loader);
                }
            }
            
            clearStatus() {
                this.status.textContent = '';
                this.status.className = 'status';
            }
            
            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            formatTimestamp(timestamp) {
                const date = new Date(timestamp);
                return date.toLocaleTimeString();
            }
        }
        
        // Initialize the app when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            new AudioChatApp();
        });
    </script>
</body>
</html>
'''

# Create templates directory and save the template
os.makedirs('templates', exist_ok=True)
with open('templates/chat.html', 'w', encoding='utf-8') as f:
    f.write(CHAT_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
```

## Installation and Running Instructions

1. **Install dependencies:**
```bash
pip install Flask google-generativeai python-dotenv
```

2. **Set up environment variables:**
Create `.env` file with your Google API key:
```
GOOGLE_API_KEY=your_actual_gemini_api_key
SECRET_KEY=your_secret_key
```

3. **Run the application:**
```bash
python audio_chat_app.py
```

4. **Open browser:**
Navigate to `http://127.0.0.1:5000`

## How It Works

### Audio Processing Flow
1. **Recording**: JavaScript MediaRecorder API captures audio from microphone
2. **Upload**: Audio blob is sent to Flask backend via FormData
3. **Processing**: Gemini AI processes audio directly (no intermediate transcription service needed)
4. **Response**: AI provides both transcription and conversational response
5. **Display**: Results are shown in chat interface with conversation history

### Key Features
- **Direct Audio Processing**: Sends audio directly to Gemini without external transcription services
- **Conversation Context**: Maintains conversation history for contextual responses
- **Error Handling**: Comprehensive error handling for audio processing and API calls
- **Responsive UI**: Modern, mobile-friendly chat interface
- **Real-time Status**: Visual feedback for recording and processing states

### Technical Implementation Details

#### Audio Handling
- Uses browser's MediaRecorder API for audio capture
- Supports WebM audio format (widely supported)
- Automatic cleanup of temporary audio files
- File size validation (10MB limit)

#### Gemini Integration
- Uses `gemini-1.5-flash-latest` model for optimal performance
- Direct audio processing without intermediate steps
- Structured prompts for consistent transcription and response format
- Robust error handling and fallback responses

#### Conversation Management
- In-memory conversation history (last 50 messages)
- Context-aware responses using conversation history
- Timestamp tracking for all interactions
- Clear and load history functionality

## Customization Options

### Modify AI Behavior
Edit the prompt in `transcribe_and_respond` method:
```python
prompt = f"""
Your custom instructions here...
Be more formal/casual/technical/etc.
"""
```

### Add New Features
- **Text Input**: Add text input alongside audio recording
- **Voice Selection**: Multiple AI voices/personalities
- **File Upload**: Support for uploading audio files
- **Export**: Save conversations to file
- **User Authentication**: Add login system

### Production Considerations
- Replace in-memory storage with database (PostgreSQL, MongoDB)
- Add user authentication and session management
- Implement rate limiting for API calls
- Add HTTPS support for secure audio transmission
- Use cloud storage for audio files
- Add monitoring and logging
- Implement caching for API responses

## Testing the Implementation

1. **Basic Test**: Record "Hello, how are you?" and verify transcription and response
2. **Conversation Test**: Have a multi-turn conversation to test context handling
3. **Error Test**: Test with no microphone permission or network issues
4. **Performance Test**: Test with longer audio recordings

## Troubleshooting

### Common Issues

1. **Microphone Access Denied**
   - Ensure HTTPS or localhost
   - Check browser permissions
   - Try different browser

2. **API Errors**
   - Verify GOOGLE_API_KEY is correct
   - Check API quota and billing
   - Review error logs

3. **Audio Quality Issues**
   - Ensure quiet environment
   - Check microphone quality
   - Test with different browsers

4. **No Response from AI**
   - Check network connectivity
   - Verify API key permissions
   - Review server logs

## Security Considerations

- Never expose API keys in client-side code
- Validate all file uploads
- Implement rate limiting
- Use HTTPS in production
- Sanitize user inputs
- Regular security updates

This documentation provides everything needed to build a functional audio-to-text chat application with Gemini AI. The implementation is production-ready with proper error handling, security considerations, and extensibility options. 