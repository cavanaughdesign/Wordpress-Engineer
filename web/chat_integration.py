#!/usr/bin/env python3
"""
WordPress Engineer Chat Integration
Direct interface to the main WordPress Engineer agent for web UI
"""
import os
import sys
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add the parent directory to the Python path to import main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import the main chat function and utilities from main.py
    from main import (
        chat_with_mike,
        console,
        conversation_history,
        voice_input,
        initialize_speech_recognition,
        cleanup_speech_recognition,
        text_to_speech,
        encode_image_to_base64,
        get_user_input,
        VOICE_COMMANDS,
        use_tts,
        tts_enabled
    )
    MAIN_AGENT_AVAILABLE = True
    print("✓ Main WordPress Engineer agent integration loaded successfully")
    print("  - Direct chat with Mike available")
    print("  - Voice input/output capabilities")
    print("  - Image processing support")
    print("  - Full tool access")
except ImportError as e:
    print(f"⚠ Main agent integration not available: {e}")
    print("  - Falling back to limited chat functionality")
    MAIN_AGENT_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordPressEngineerChat:
    """Direct chat interface to the WordPress Engineer agent."""
    
    def __init__(self):
        """Initialize the chat interface."""
        self.active_sessions = {}
        self.session_histories = {}
        
    async def start_chat_session(self, session_id: str) -> Dict[str, Any]:
        """Start a new chat session with the agent."""
        try:
            if not MAIN_AGENT_AVAILABLE:
                return {
                    "status": "error",
                    "message": "Main agent not available. Please ensure main.py dependencies are installed."
                }
            
            self.active_sessions[session_id] = {
                "created": asyncio.get_event_loop().time(),
                "message_count": 0,
                "voice_enabled": False
            }
            self.session_histories[session_id] = []
            
            return {
                "status": "success",
                "session_id": session_id,
                "message": "Chat session started with WordPress Engineer Mike",
                "capabilities": [
                    "WordPress development assistance",
                    "Code generation and analysis",
                    "File management",
                    "Voice input/output",
                    "Image analysis",
                    "Tool execution",
                    "Database operations"
                ]
            }
        except Exception as e:
            logger.error(f"Error starting chat session: {str(e)}")
            return {
                "status": "error",
                "message": f"Error starting chat session: {str(e)}"
            }
    
    async def send_message(self, session_id: str, message: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to the WordPress Engineer agent."""
        try:
            if not MAIN_AGENT_AVAILABLE:
                return {
                    "status": "error",
                    "message": "Main agent not available"
                }
            
            if session_id not in self.active_sessions:
                # Auto-create session if it doesn't exist
                await self.start_chat_session(session_id)
            
            # Update session info
            self.active_sessions[session_id]["message_count"] += 1
            
            # Add user message to session history
            user_message = {
                "role": "user",
                "content": message,
                "timestamp": asyncio.get_event_loop().time(),
                "image_path": image_path
            }
            self.session_histories[session_id].append(user_message)
            
            # Call the main agent
            response, tool_used = await chat_with_mike(message, image_path)
            
            # Add agent response to session history
            agent_message = {
                "role": "assistant",
                "content": response,
                "timestamp": asyncio.get_event_loop().time(),
                "tool_used": tool_used
            }
            self.session_histories[session_id].append(agent_message)
            
            return {
                "status": "success",
                "response": response,
                "tool_used": tool_used,
                "session_info": self.active_sessions[session_id],
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {
                "status": "error",
                "message": f"Error sending message: {str(e)}"
            }
    
    async def voice_input_session(self, session_id: str) -> Dict[str, Any]:
        """Handle voice input for a chat session."""
        try:
            if not MAIN_AGENT_AVAILABLE:
                return {
                    "status": "error",
                    "message": "Voice input not available - main agent not loaded"
                }
            
            # Initialize speech recognition
            initialize_speech_recognition()
            
            # Get voice input
            voice_text = await voice_input()
            
            if voice_text:
                # Process voice command or send as message
                if voice_text in VOICE_COMMANDS:
                    return {
                        "status": "success",
                        "voice_command": voice_text,
                        "action": VOICE_COMMANDS[voice_text],
                        "message": f"Voice command recognized: {voice_text}"
                    }
                else:
                    # Send voice input as regular message
                    result = await self.send_message(session_id, voice_text)
                    result["voice_input"] = voice_text
                    return result
            else:
                return {
                    "status": "error",
                    "message": "No voice input detected or recognition failed"
                }
                
        except Exception as e:
            logger.error(f"Error in voice input: {str(e)}")
            return {
                "status": "error",
                "message": f"Error in voice input: {str(e)}"
            }
        finally:
            cleanup_speech_recognition()
    
    async def text_to_speech_session(self, session_id: str, text: str) -> Dict[str, Any]:
        """Convert text to speech for a session."""
        try:
            if not MAIN_AGENT_AVAILABLE or not tts_enabled:
                return {
                    "status": "error",
                    "message": "Text-to-speech not available"
                }
            
            await text_to_speech(text)
            
            return {
                "status": "success",
                "message": "Text converted to speech successfully",
                "text": text
            }
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            return {
                "status": "error",
                "message": f"Error in text-to-speech: {str(e)}"
            }
    
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Get the chat history for a session."""
        try:
            if session_id not in self.session_histories:
                return {
                    "status": "error",
                    "message": "Session not found"
                }
            
            return {
                "status": "success",
                "session_id": session_id,
                "history": self.session_histories[session_id],
                "session_info": self.active_sessions.get(session_id, {}),
                "message_count": len(self.session_histories[session_id])
            }
            
        except Exception as e:
            logger.error(f"Error getting session history: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting session history: {str(e)}"
            }
    
    def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear a chat session."""
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            if session_id in self.session_histories:
                del self.session_histories[session_id]
            
            return {
                "status": "success",
                "message": f"Session {session_id} cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
            return {
                "status": "error",
                "message": f"Error clearing session: {str(e)}"
            }
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get list of active chat sessions."""
        try:
            return {
                "status": "success",
                "active_sessions": list(self.active_sessions.keys()),
                "session_count": len(self.active_sessions),
                "sessions": self.active_sessions
            }
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting active sessions: {str(e)}"
            }

# Create a global instance for use in the web app
wordpress_chat = WordPressEngineerChat()

# Export functions for use in app_standalone.py
async def start_chat_session(session_id: str):
    """Export function for starting a chat session."""
    return await wordpress_chat.start_chat_session(session_id)

async def send_message_to_agent(session_id: str, message: str, image_path: Optional[str] = None):
    """Export function for sending messages to the agent."""
    return await wordpress_chat.send_message(session_id, message, image_path)

async def voice_input_handler(session_id: str):
    """Export function for voice input."""
    return await wordpress_chat.voice_input_session(session_id)

async def text_to_speech_handler(session_id: str, text: str):
    """Export function for text-to-speech."""
    return await wordpress_chat.text_to_speech_session(session_id, text)

def get_chat_history(session_id: str):
    """Export function for getting chat history."""
    return wordpress_chat.get_session_history(session_id)

def clear_chat_session(session_id: str):
    """Export function for clearing a session."""
    return wordpress_chat.clear_session(session_id)

def get_active_chat_sessions():
    """Export function for getting active sessions."""
    return wordpress_chat.get_active_sessions()
