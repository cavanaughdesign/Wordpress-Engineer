import os
from dotenv import load_dotenv
import json
from tavily import TavilyClient
import base64
from PIL import Image
import io
import re
from anthropic import Anthropic, APIStatusError, APIError
import difflib
import time
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt
from rich.markdown import Markdown
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
import glob
import speech_recognition as sr
import websockets
from pydub import AudioSegment
from pydub.playback import play
import datetime
import venv
import sys
import signal
import logging
from typing import Tuple, List, Optional, Dict, Any
import mimetypes
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import subprocess
import shutil
from typing import AsyncIterable
# Add this import at the top of the file
from tools.rag_database import RAGDatabase
from instructions.system_prompts import BASE_SYSTEM_PROMPT
from instructions.tool_schemas import tools

# Initialize RAG database
rag_db = None

# Add this global variable for the memory database path
MEMORY_DB_PATH = "data/memory.db"

# Add these to the global variable declarations section (around line 170)
php_executor = None
php_available = False
browser_automation = None

def initialize_rag_database():
    """Initialize the RAG database instance."""
    global rag_db
    try:
        rag_db = RAGDatabase("data/wp_knowledge.db") # Pass the new path for wp_knowledge.db
        console.print(Panel("RAG database initialized successfully", title="RAG Database", style="green"))
        return True
    except Exception as e:
        console.print(Panel(f"Error initializing RAG database: {str(e)}", title="Error", style="bold red"))
        logging.error(f"Error initializing RAG database: {str(e)}")
        return False

# Add the following handler functions

async def handle_rag_search(tool_input):
    """Handle RAG database search requests."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        query = tool_input.get("query")
        categories = tool_input.get("categories")
        limit = tool_input.get("limit", 10)
        use_semantic = tool_input.get("use_semantic", True)
        
        results = await rag_db.search(query, categories, limit, use_semantic)
        return results
    except Exception as e:
        logging.error(f"Error in RAG search: {str(e)}")
        return {
            "status": "error",
            "message": f"Error in RAG search: {str(e)}"
        }

async def handle_rag_add_document(tool_input):
    """Handle adding a document to the RAG database."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        title = tool_input.get("title")
        content = tool_input.get("content")
        category = tool_input.get("category")
        tags = tool_input.get("tags")
        source = tool_input.get("source")
        
        result = await rag_db.add_document(title, content, category, tags, source)
        return result
    except Exception as e:
        logging.error(f"Error adding document to RAG database: {str(e)}")
        return {
            "status": "error",
            "message": f"Error adding document to RAG database: {str(e)}"
        }

async def handle_rag_add_code_snippet(tool_input):
    """Handle adding a code snippet to the RAG database."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        title = tool_input.get("title")
        code = tool_input.get("code")
        language = tool_input.get("language")
        description = tool_input.get("description")
        tags = tool_input.get("tags")
        
        result = await rag_db.add_code_snippet(title, code, language, description, tags)
        return result
    except Exception as e:
        logging.error(f"Error adding code snippet to RAG database: {str(e)}")
        return {
            "status": "error",
            "message": f"Error adding code snippet to RAG database: {str(e)}"
        }

async def handle_rag_add_wp_function(tool_input):
    """Handle adding a WordPress function to the RAG database."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        function_name = tool_input.get("function_name")
        signature = tool_input.get("signature")
        description = tool_input.get("description")
        parameters = tool_input.get("parameters")
        return_value = tool_input.get("return_value")
        example = tool_input.get("example")
        version_added = tool_input.get("version_added")
        deprecated = tool_input.get("deprecated", False)
        source_file = tool_input.get("source_file")
        
        result = await rag_db.add_wp_function(
            function_name, signature, description, parameters, 
            return_value, example, version_added, deprecated, source_file
        )
        return result
    except Exception as e:
        logging.error(f"Error adding WordPress function to RAG database: {str(e)}")
        return {
            "status": "error",
            "message": f"Error adding WordPress function to RAG database: {str(e)}"
        }

async def handle_rag_add_wp_hook(tool_input):
    """Handle adding a WordPress hook to the RAG database."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        hook_name = tool_input.get("hook_name")
        hook_type = tool_input.get("hook_type")
        description = tool_input.get("description")
        parameters = tool_input.get("parameters")
        source_file = tool_input.get("source_file")
        example = tool_input.get("example")
        version_added = tool_input.get("version_added")
        
        result = await rag_db.add_wp_hook(
            hook_name, hook_type, description, parameters, 
            source_file, example, version_added
        )
        return result
    except Exception as e:
        logging.error(f"Error adding WordPress hook to RAG database: {str(e)}")
        return {
            "status": "error",
            "message": f"Error adding WordPress hook to RAG database: {str(e)}"
        }

async def handle_rag_get_statistics(tool_input):
    """Handle getting statistics about the RAG database."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        stats = await rag_db.get_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logging.error(f"Error getting RAG database statistics: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting RAG database statistics: {str(e)}"
        }

async def handle_rag_import_wp_documentation(tool_input):
    """Handle importing WordPress documentation to the RAG database."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        docs_path = tool_input.get("docs_path")
        result = await rag_db.import_wp_documentation(docs_path)
        return result
    except Exception as e:
        logging.error(f"Error importing documentation to RAG database: {str(e)}")
        return {
            "status": "error",
            "message": f"Error importing documentation to RAG database: {str(e)}"
        }

async def handle_rag_export_database(tool_input):
    """Handle exporting the RAG database."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        export_path = tool_input.get("export_path")
        result = await rag_db.export_database(export_path)
        return result
    except Exception as e:
        logging.error(f"Error exporting RAG database: {str(e)}")
        return {
            "status": "error",
            "message": f"Error exporting RAG database: {str(e)}"
        }

async def handle_rag_backup_database(tool_input):
    """Handle backing up the RAG database."""
    global rag_db
    if not rag_db:
        if not initialize_rag_database():
            return {
                "status": "error",
                "message": "RAG database not available"
            }
    
    try:
        backup_path = tool_input.get("backup_path")
        result = await rag_db.backup_database(backup_path)
        return result
    except Exception as e:
        logging.error(f"Error backing up RAG database: {str(e)}")
        return {
            "status": "error",
            "message": f"Error backing up RAG database: {str(e)}"
        }
# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Define a list of voice commands
VOICE_COMMANDS = {
    "exit voice mode": "exit_voice_mode",
    "save chat": "save_chat",
    "reset conversation": "reset_conversation"
}

# Initialize recognizer and microphone as None
recognizer = None
microphone = None

# 11 Labs TTS
tts_enabled = True
use_tts = False
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')
VOICE_ID = 'YOUR VOICE ID'
MODEL_ID = 'eleven_turbo_v2_5'

# Initialize with default configuration
db_manager = None

def initialize_db_manager(config: Dict[str, Any]):
    global db_manager
    db_manager = WordPressDBManager(config)


def is_installed(lib_name):
    return shutil.which(lib_name) is not None

from typing import Dict, Any 
import os 
from pathlib import Path 
import json 
import logging

class WordPressDBConfig:
    """Manages WordPress database configuration and initialization."""

    DEFAULT_CONFIG = {
        'host': 'localhost',
        'user': 'wordpress_user',
        'password': '',
        'database': 'wordpress',
        'pool_name': 'wp_pool',
        'pool_size': 5
    }

    def __init__(self):
        self.config_file = Path('config/database.json')
        self.config = self.DEFAULT_CONFIG.copy()
        
    def load_config(self) -> Dict[str, Any]:
        """Load database configuration from file or environment variables."""
        try:
            # First try environment variables
            env_config = {
                'host': os.getenv('WP_DB_HOST'),
                'user': os.getenv('WP_DB_USER'),
                'password': os.getenv('WP_DB_PASSWORD'),
                'database': os.getenv('WP_DB_NAME'),
                'pool_name': os.getenv('WP_DB_POOL_NAME'),
                'pool_size': os.getenv('WP_DB_POOL_SIZE')
            }
            
            # Update config with any set environment variables
            self.config.update({k: v for k, v in env_config.items() if v is not None})
            
            # Then try config file
            if self.config_file.exists():
                with open(self.config_file) as f:
                    file_config = json.load(f)
                self.config.update(file_config)
                
            return self.config
            
        except Exception as e:
            logging.error(f"Error loading database configuration: {str(e)}")
            raise
            
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save database configuration to file."""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving database configuration: {str(e)}")
            raise

async def text_chunker(text: str) -> AsyncIterable[str]:
    """Split text into chunks, ensuring to not break sentences."""
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    buffer = ""
    
    for char in text:
        if buffer.endswith(splitters):
            yield buffer + " "
            buffer = char
        elif char in splitters:
            yield buffer + char + " "
            buffer = ""
        else:
            buffer += char

    if buffer:
        yield buffer + " "

async def stream_audio(audio_stream):
    """Stream audio data using mpv player."""
    if not is_installed("mpv"):
        console.print("mpv not found. Installing alternative audio playback...", style="bold yellow")
        # Fall back to pydub playback if mpv is not available
        audio_data = b''.join([chunk async for chunk in audio_stream])
        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
        play(audio)
        return

    mpv_process = subprocess.Popen(
        ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    console.print("Started streaming audio", style="bold green")
    try:
        async for chunk in audio_stream:
            if chunk:
                mpv_process.stdin.write(chunk)
                mpv_process.stdin.flush()
    except Exception as e:
        console.print(f"Error during audio streaming: {str(e)}", style="bold red")
    finally:
        if mpv_process.stdin:
            mpv_process.stdin.close()
        mpv_process.wait()

async def text_to_speech(text):
    if not ELEVEN_LABS_API_KEY:
        console.print("ElevenLabs API key not found. Text-to-speech is disabled.", style="bold yellow")
        console.print(text)
        return

    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input?model_id={MODEL_ID}"
    
    try:
        async with websockets.connect(uri, extra_headers={'xi-api-key': ELEVEN_LABS_API_KEY}) as websocket:
            # Send initial message
            await websocket.send(json.dumps({
                "text": " ",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                "xi_api_key": ELEVEN_LABS_API_KEY,
            }))

            # Set up listener for audio chunks
            async def listen():
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if data.get("audio"):
                            yield base64.b64decode(data["audio"])
                        elif data.get('isFinal'):
                            break
                    except websockets.exceptions.ConnectionClosed:
                        logging.error("WebSocket connection closed unexpectedly")
                        break
                    except Exception as e:
                        logging.error(f"Error processing audio message: {str(e)}")
                        break

            # Start audio streaming task
            stream_task = asyncio.create_task(stream_audio(listen()))

            # Send text in chunks
            async for chunk in text_chunker(text):
                try:
                    await websocket.send(json.dumps({"text": chunk, "try_trigger_generation": True}))
                except Exception as e:
                    logging.error(f"Error sending text chunk: {str(e)}")
                    break

            # Send closing message
            await websocket.send(json.dumps({"text": ""}))

            # Wait for streaming to complete
            await stream_task

    except websockets.exceptions.InvalidStatusCode as e:
        logging.error(f"Failed to connect to ElevenLabs API: {e}")
        console.print(f"Failed to connect to ElevenLabs API: {e}", style="bold red")
        console.print("Fallback: Printing the text instead.", style="bold yellow")
        console.print(text)
    except Exception as e:
        logging.error(f"Error in text-to-speech: {str(e)}")
        console.print(f"Error in text-to-speech: {str(e)}", style="bold red")
        console.print("Fallback: Printing the text instead.", style="bold yellow")
        console.print(text)

def initialize_speech_recognition():
    global recognizer, microphone
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient noise
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    logging.info("Speech recognition initialized")

async def voice_input(max_retries=3):
    global recognizer, microphone

    for attempt in range(max_retries):
        # Reinitialize speech recognition objects before each attempt
        initialize_speech_recognition()

        try:
            with microphone as source:
                console.print("Listening... Speak now.", style="bold green")
                audio = recognizer.listen(source, timeout=5)
                
            console.print("Processing speech...", style="bold yellow")
            text = recognizer.recognize_google(audio)
            console.print(f"You said: {text}", style="cyan")
            return text.lower()
        except sr.WaitTimeoutError:
            console.print(f"No speech detected. Attempt {attempt + 1} of {max_retries}.", style="bold red")
            logging.warning(f"No speech detected. Attempt {attempt + 1} of {max_retries}")
        except sr.UnknownValueError:
            console.print(f"Speech was unintelligible. Attempt {attempt + 1} of {max_retries}.", style="bold red")
            logging.warning(f"Speech was unintelligible. Attempt {attempt + 1} of {max_retries}")
        except sr.RequestError as e:
            console.print(f"Could not request results from speech recognition service; {e}", style="bold red")
            logging.error(f"Could not request results from speech recognition service; {e}")
            return None
        except Exception as e:
            console.print(f"Unexpected error in voice input: {str(e)}", style="bold red")
            logging.error(f"Unexpected error in voice input: {str(e)}")
            return None
        
        # Add a short delay between attempts
        await asyncio.sleep(1)
    
    console.print("Max retries reached. Returning to text input mode.", style="bold red")
    logging.info("Max retries reached in voice input. Returning to text input mode.")
    return None

def cleanup_speech_recognition():
    global recognizer, microphone
    recognizer = None
    microphone = None
    logging.info('Speech recognition objects cleaned up')

def save_chat():
    """Placeholder function to save chat history."""
    # In a real implementation, you would save conversation_history here
    filename = f"chat_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w') as f:
            json.dump(conversation_history, f, indent=2) # Assuming conversation_history is accessible
        logging.info(f"Chat history saved to {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error saving chat history: {str(e)}")
        return "error_saving_chat.json"

def reset_conversation():
    """Placeholder function to reset conversation history."""
    global conversation_history, file_contents, code_editor_memory, code_editor_files, wordpress_editor_memory, wordpress_editor_files
    conversation_history = []
    file_contents = {}
    code_editor_memory = []
    code_editor_files = set()
    wordpress_editor_memory = []
    wordpress_editor_files = set()
    logging.info("Conversation has been reset.")

def process_voice_command(command):
    if command in VOICE_COMMANDS:
        action = VOICE_COMMANDS[command]
        if action == "exit_voice_mode":
            return False, "Exiting voice mode."
        elif action == "save_chat":
            filename = save_chat()
            return True, f"Chat saved to {filename}"
        elif action == "reset_conversation":
            reset_conversation()
            return True, "Conversation has been reset."
    return True, None

async def get_user_input(prompt="You: "):
    style = Style.from_dict({
        'prompt': 'cyan bold',
    })
    session = PromptSession(style=style)
    return await session.prompt_async(prompt, multiline=False)

def setup_virtual_environment() -> Tuple[str, str]:
    venv_name = "code_execution_env"
    venv_path = os.path.join(os.getcwd(), venv_name)
    try:
        if not os.path.exists(venv_path):
            venv.create(venv_path, with_pip=True)

        # Activate the virtual environment
        if sys.platform == "win32":
            activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        else:
            activate_script = os.path.join(venv_path, "bin", "activate")

        return venv_path, activate_script
    except Exception as e:
        logging.error(f"Error setting up virtual environment: {str(e)}")
        raise


# Initialize the Anthropic client
client = Anthropic(api_key="your-anthropic-api-key")

# Initialize the Tavily client
tavily = TavilyClient(api_key="")

console = Console()

# Token tracking variables
main_model_tokens = {'input': 0, 'output': 0, 'cache_write': 0, 'cache_read': 0}
tool_checker_tokens = {'input': 0, 'output': 0, 'cache_write': 0, 'cache_read': 0}
code_editor_tokens = {'input': 0, 'output': 0, 'cache_write': 0, 'cache_read': 0}
code_execution_tokens = {'input': 0, 'output': 0, 'cache_write': 0, 'cache_read': 0}
wordpress_analysis_tokens = {'input': 0, 'output': 0, 'cache_creation': 0, 'cache_read': 0} # Added missing variable
USE_FUZZY_SEARCH = True

# Set up the conversation memory (maintains context for MAINMODEL)
conversation_history = []

# Store file contents (part of the context for MAINMODEL)
file_contents = {}

# Code editor memory (maintains some context for CODEEDITORMODEL between calls)
code_editor_memory = []

# Files already present in code editor's context
code_editor_files = set()

# WordPress editor memory (maintains some context for WORDPRESSEDITORMODEL between calls)
wordpress_editor_memory = []

# Files already present in WordPress editor's context
wordpress_editor_files = set()

# Token tracking for WordPress editor
wordpress_editor_tokens = {'input': 0, 'output': 0, 'cache_write': 0, 'cache_read': 0}

# automode flag
automode = False

# Global dictionary to store running processes
running_processes = {}

# Constants
CONTINUATION_EXIT_PHRASE = "AUTOMODE_COMPLETE"
MAX_CONTINUATION_ITERATIONS = 25
MAX_CONTEXT_TOKENS = 200000  # Reduced to 200k tokens for context window

MAINMODEL = "claude-3-7-sonnet-latest"
TOOLCHECKERMODEL = "claude-3-7-sonnet-latest"
CODEEDITORMODEL = "claude-3-7-sonnet-latest"
CODEEXECUTIONMODEL = "claude-3-7-sonnet-latest"
WORDPRESSEDITORMODEL = "claude-3-7-sonnet-latest" 

# System prompts
# Update the BASE_SYSTEM_PROMPT to include RAG capabilities



AUTOMODE_SYSTEM_PROMPT = """
You are currently in automode. Follow these guidelines:

<goal_setting>
1. Goal Setting:
   - Set clear, achievable goals based on the user's request.
   - Break down complex tasks into smaller, manageable goals.
</goal_setting>

<goal_execution>
2. Goal Execution:
   - Work through goals systematically, using appropriate tools for each task.
   - Utilize file operations, code writing, and web searches as needed.
   - Always read a file before editing and review changes after editing.
</goal_execution>

<progress_tracking>
3. Progress Tracking:
   - Provide regular updates on goal completion and overall progress.
   - Use the iteration information to pace your work effectively.
</progress_tracking>

<task_breakdown>
Break Down Complex Tasks:
When faced with a complex task or project, break it down into smaller, manageable steps. Provide a clear outline of the steps involved, potential challenges, and how to approach each part of the task.
</task_breakdown>

<explanation_preference>
Prefer Answering Without Code:
When explaining concepts or providing solutions, prioritize clear explanations and pseudocode over full code implementations. Only provide full code snippets when explicitly requested or when it's essential for understanding.
</explanation_preference>

<code_review_process>
Code Review Process:
When reviewing code, follow these steps:
1. Understand the context and purpose of the code
2. Check for clarity and readability
3. Identify potential bugs or errors
4. Suggest optimizations or improvements
5. Ensure adherence to best practices and coding standards
6. Consider security implications
7. Provide constructive feedback with explanations
</code_review_process>

<project_planning>
Project Planning:
When planning a project, consider the following:
1. Define clear project goals and objectives
2. Break down the project into manageable tasks and subtasks
3. Estimate time and resources required for each task
4. Identify potential risks and mitigation strategies
5. Suggest appropriate tools and technologies
6. Outline a testing and quality assurance strategy
7. Consider scalability and future maintenance
</project_planning>

<security_review>
Security Review:
When conducting a security review, focus on:
1. Identifying potential vulnerabilities in the code
2. Checking for proper input validation and sanitization
3. Ensuring secure handling of sensitive data
4. Reviewing authentication and authorization mechanisms
5. Checking for secure communication protocols
6. Identifying any use of deprecated or insecure functions
7. Suggesting security best practices and improvements
</security_review>

Remember to apply these additional skills and processes when assisting users with their software development tasks and projects.

<tool_usage>
4. Tool Usage:
   - Leverage all available tools to accomplish your goals efficiently.
   - Prefer edit_and_apply_multiple for file modifications, applying changes in chunks for large edits.
   - Use tavily_search proactively for up-to-date information.
</tool_usage>

<error_handling>
5. Error Handling:
   - If a tool operation fails, analyze the error and attempt to resolve the issue.
   - For persistent errors, consider alternative approaches to achieve the goal.
</error_handling>

<automode_completion>
6. Automode Completion:
   - When all goals are completed, respond with "AUTOMODE_COMPLETE" to exit automode.
   - Do not ask for additional tasks or modifications once goals are achieved.
</automode_completion>

<iteration_awareness>
7. Iteration Awareness:
   - You have access to this {iteration_info}.
   - Use this information to prioritize tasks and manage time effectively.
</iteration_awareness>

Remember: Focus on completing the established goals efficiently and effectively. Avoid unnecessary conversations or requests for additional tasks.
"""


def update_system_prompt(current_iteration: Optional[int] = None, max_iterations: Optional[int] = None) -> str:
    global file_contents
    chain_of_thought_prompt = """
    Answer the user's request using relevant tools (if they are available). Before calling a tool, do some analysis within <thinking></thinking> tags. First, think about which of the provided tools is the relevant tool to answer the user's request. Second, go through each of the required parameters of the relevant tool and determine if the user has directly provided or given enough information to infer a value. When deciding if the parameter can be inferred, carefully consider all the context to see if it supports a specific value. If all of the required parameters are present or can be reasonably inferred, close the thinking tag and proceed with the tool call. BUT, if one of the values for a required parameter is missing, DO NOT invoke the function (not even with fillers for the missing params) and instead, ask the user to provide the missing parameters. DO NOT ask for more information on optional parameters if it is not provided.

    Do not reflect on the quality of the returned search results in your response.

    IMPORTANT: Before using the read_multiple_files tool, always check if the files you need are already in your context (system prompt).
    If the file contents are already available to you, use that information directly instead of calling the read_multiple_files tool.
    Only use the read_multiple_files tool for files that are not already in your context.
    When instructing to read a file, always use the full file path.
    """

    files_in_context = "\n".join(file_contents.keys())
    file_contents_prompt = f"\n\nFiles already in your context:\n{files_in_context}\n\nFile Contents:\n"
    for path, content in file_contents.items():
        file_contents_prompt += f"\n--- {path} ---\n{content}\n"

    if automode:
        iteration_info = ""
        if current_iteration is not None and max_iterations is not None:
            iteration_info = f"You are currently on iteration {current_iteration} out of {max_iterations} in automode."
        return BASE_SYSTEM_PROMPT + file_contents_prompt + "\n\n" + AUTOMODE_SYSTEM_PROMPT.format(iteration_info=iteration_info) + "\n\n" + chain_of_thought_prompt
    else:
        return BASE_SYSTEM_PROMPT + file_contents_prompt + "\n\n" + chain_of_thought_prompt

def create_folders(paths):
    results = []
    for path in paths:
        try:
            # Use os.makedirs with exist_ok=True to create nested directories
            os.makedirs(path, exist_ok=True)
            results.append(f"Folder(s) created: {path}")
        except Exception as e:
            results.append(f"Error creating folder(s) {path}: {str(e)}")
    return "\n".join(results)

def create_files(files):
    global file_contents
    results = []
    
    # Handle different input types
    if isinstance(files, str):
        # If a string is passed, assume it's a single file path
        files = [{"path": files, "content": ""}]
    elif isinstance(files, dict):
        # If a single dictionary is passed, wrap it in a list
        files = [files]
    elif not isinstance(files, list):
        return "Error: Invalid input type for create_files. Expected string, dict, or list."
    
    for file in files:
        try:
            if not isinstance(file, dict):
                results.append(f"Error: Invalid file specification: {file}")
                continue
            
            path = file.get('path')
            content = file.get('content', '')
            
            if path is None:
                results.append(f"Error: Missing 'path' for file")
                continue
            
            dir_name = os.path.dirname(path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
            with open(path, 'w') as f:
                f.write(content)
            
            file_contents[path] = content
            results.append(f"File created and added to system prompt: {path}")
        except Exception as e:
            results.append(f"Error creating file: {str(e)}")
    
    return "\n".join(results)

def convert_to_wordpress_theme(static_site_path: str, theme_name: str, options: Dict[str, Any]) -> bool:
    """Convert static HTML/CSS site to WordPress theme"""
    try:
        # 1. Parse HTML structure and extract components
        # 2. Generate theme.json for block themes
        # 3. Create WordPress template files (index.php, header.php, etc.)
        # 4. Convert CSS to WordPress-compatible styles
        # 5. Generate functions.php with proper theme setup
        # 6. Create block patterns from HTML sections
        
        theme_path = f"wp-content/themes/{theme_name}"
        
        # Implementation steps:
        # - Extract header/footer/sidebar from HTML
        # - Convert navigation to WordPress menus
        # - Transform content areas to template parts
        # - Generate theme.json for Full Site Editing
        # - Create style.css with theme header
        
        return True
    except Exception as e:
        logging.error(f"Error converting to WordPress theme: {str(e)}")
        return False


def configure_caching(caching_plugin: str, cache_settings: Dict[str, Any]) -> bool:
    """Configure WordPress caching plugins"""
    try:
        supported_plugins = {
            'wp-rocket': _configure_wp_rocket,
            'w3-total-cache': _configure_w3tc,
            'wp-super-cache': _configure_wp_super_cache,
            'wp-fastest-cache': _configure_wp_fastest_cache
        }
        
        if caching_plugin in supported_plugins:
            return supported_plugins[caching_plugin](cache_settings)
        else:
            raise ValueError(f"Unsupported caching plugin: {caching_plugin}")
            
    except Exception as e:
        logging.error(f"Error configuring caching: {str(e)}")
        return False

def _configure_wp_rocket(settings):
    """Configures WP Rocket by writing settings to a JSON file."""
    try:
        config_path = "wp-content/plugins/wp-rocket/config.json"
        create_files({"path": config_path, "content": json.dumps(settings, indent=4)})
        logging.info(f"WP Rocket configured with settings: {settings}")
        return True
    except Exception as e:
        logging.error(f"Error configuring WP Rocket: {str(e)}")
        return False

def _configure_w3tc(settings):
    """Configures W3 Total Cache by writing settings to a JSON file."""
    try:
        config_path = "wp-content/plugins/w3-total-cache/config.json"
        create_files({"path": config_path, "content": json.dumps(settings, indent=4)})
        logging.info(f"W3 Total Cache configured with settings: {settings}")
        return True
    except Exception as e:
        logging.error(f"Error configuring W3 Total Cache: {str(e)}")
        return False

def _configure_wp_super_cache(settings):
    """Configures WP Super Cache by writing settings to a JSON file."""
    try:
        config_path = "wp-content/plugins/wp-super-cache/config.json"
        create_files({"path": config_path, "content": json.dumps(settings, indent=4)})
        logging.info(f"WP Super Cache configured with settings: {settings}")
        return True
    except Exception as e:
        logging.error(f"Error configuring WP Super Cache: {str(e)}")
        return False

def _configure_wp_fastest_cache(settings):
    """Configures WP Fastest Cache by writing settings to a JSON file."""
    try:
        config_path = "wp-content/plugins/wp-fastest-cache/config.json"
        create_files({"path": config_path, "content": json.dumps(settings, indent=4)})
        logging.info(f"WP Fastest Cache configured with settings: {settings}")
        return True
    except Exception as e:
        logging.error(f"Error configuring WP Fastest Cache: {str(e)}")
        return False


def integrate_external_api(api_url: str, parameters: Dict[str, Any], auth_method: str) -> bool:
    """Integrate external APIs with WordPress"""
    try:
        # 1. Create custom REST API endpoints
        # 2. Handle authentication (OAuth, API keys, JWT)
        # 3. Implement rate limiting and caching
        # 4. Create WordPress hooks for API data
        # 5. Generate admin interface for API management
        
        auth_handlers = {
            'oauth': _setup_oauth_auth,
            'api_key': _setup_api_key_auth,
            'bearer': _setup_bearer_auth,
            'basic': _setup_basic_auth
        }
        
        # Generate WordPress plugin code for API integration
        plugin_code = _generate_api_plugin(api_url, parameters, auth_method)
        
        return True
    except Exception as e:
        logging.error(f"Error integrating external API: {str(e)}")
        return False

def _setup_oauth_auth(params: Dict[str, Any]) -> bool:
    """Set up OAuth authentication for external API integration."""
    try:
        client_id = params.get('client_id')
        client_secret = params.get('client_secret')
        redirect_uri = params.get('redirect_uri')
        auth_url = params.get('auth_url')
        token_url = params.get('token_url')
        
        if not all([client_id, client_secret, auth_url, token_url]):
            logging.error("Missing required OAuth parameters")
            return False
        
        # Generate OAuth handler code
        oauth_code = f"""
// OAuth 2.0 Handler
class CustomOAuthHandler {{
    private $client_id = '{client_id}';
    private $client_secret = '{client_secret}';
    private $redirect_uri = '{redirect_uri}';
    private $auth_url = '{auth_url}';
    private $token_url = '{token_url}';
    
    public function get_authorization_url() {{
        $params = array(
            'response_type' => 'code',
            'client_id' => $this->client_id,
            'redirect_uri' => $this->redirect_uri,
            'scope' => 'read write'
        );
        return $this->auth_url . '?' . http_build_query($params);
    }}
    
    public function exchange_code_for_token($code) {{
        $data = array(
            'grant_type' => 'authorization_code',
            'client_id' => $this->client_id,
            'client_secret' => $this->client_secret,
            'code' => $code,
            'redirect_uri' => $this->redirect_uri
        );
        
        $response = wp_remote_post($this->token_url, array(
            'body' => $data,
            'headers' => array('Content-Type' => 'application/x-www-form-urlencoded')
        ));
        
        if (is_wp_error($response)) {{
            return false;
        }}
        
        return json_decode(wp_remote_retrieve_body($response), true);
    }}
}}
"""
        
        # Save OAuth handler to plugin
        oauth_file = "wp-content/plugins/custom-api-integration/oauth-handler.php"
        create_files({"path": oauth_file, "content": f"<?php\n{oauth_code}"})
        
        logging.info("OAuth authentication setup completed")
        return True
        
    except Exception as e:
        logging.error(f"Error setting up OAuth: {str(e)}")
        return False

def _setup_api_key_auth(params: Dict[str, Any]) -> bool:
    """Set up API key authentication for external API integration."""
    try:
        api_key = params.get('api_key')
        header_name = params.get('header_name', 'X-API-Key')
        
        if not api_key:
            logging.error("API key is required")
            return False
        
        # Generate API key handler code
        api_key_code = f"""
// API Key Authentication Handler
class CustomAPIKeyHandler {{
    private $api_key = '{api_key}';
    private $header_name = '{header_name}';
    
    public function get_auth_headers() {{
        return array(
            $this->header_name => $this->api_key,
            'Content-Type' => 'application/json'
        );
    }}
    
    public function make_authenticated_request($url, $method = 'GET', $data = null) {{
        $args = array(
            'method' => $method,
            'headers' => $this->get_auth_headers(),
            'timeout' => 30
        );
        
        if ($data && in_array($method, array('POST', 'PUT', 'PATCH'))) {{
            $args['body'] = json_encode($data);
        }}
        
        $response = wp_remote_request($url, $args);
        
        if (is_wp_error($response)) {{
            return false;
        }}
        
        return json_decode(wp_remote_retrieve_body($response), true);
    }}
}}
"""
        
        # Save API key handler to plugin
        api_key_file = "wp-content/plugins/custom-api-integration/api-key-handler.php"
        create_files({"path": api_key_file, "content": f"<?php\n{api_key_code}"})
        
        logging.info("API key authentication setup completed")
        return True
        
    except Exception as e:
        logging.error(f"Error setting up API key auth: {str(e)}")
        return False

def _setup_bearer_auth(params: Dict[str, Any]) -> bool:
    """Set up Bearer token authentication for external API integration."""
    try:
        token = params.get('token')
        
        if not token:
            logging.error("Bearer token is required")
            return False
        
        # Generate Bearer token handler code
        bearer_code = f"""
// Bearer Token Authentication Handler
class CustomBearerHandler {{
    private $token = '{token}';
    
    public function get_auth_headers() {{
        return array(
            'Authorization' => 'Bearer ' . $this->token,
            'Content-Type' => 'application/json'
        );
    }}
    
    public function make_authenticated_request($url, $method = 'GET', $data = null) {{
        $args = array(
            'method' => $method,
            'headers' => $this->get_auth_headers(),
            'timeout' => 30
        );
        
        if ($data && in_array($method, array('POST', 'PUT', 'PATCH'))) {{
            $args['body'] = json_encode($data);
        }}
        
        $response = wp_remote_request($url, $args);
        
        if (is_wp_error($response)) {{
            return false;
        }}
        
        return json_decode(wp_remote_retrieve_body($response), true);
    }}
}}
"""
        
        # Save Bearer handler to plugin
        bearer_file = "wp-content/plugins/custom-api-integration/bearer-handler.php"
        create_files({"path": bearer_file, "content": f"<?php\n{bearer_code}"})
        
        logging.info("Bearer token authentication setup completed")
        return True
        
    except Exception as e:
        logging.error(f"Error setting up Bearer auth: {str(e)}")
        return False

def _setup_basic_auth(params: Dict[str, Any]) -> bool:
    """Set up Basic authentication for external API integration."""
    try:
        username = params.get('username')
        password = params.get('password')
        
        if not all([username, password]):
            logging.error("Username and password are required for Basic auth")
            return False
        
        # Generate Basic auth handler code
        basic_code = f"""
// Basic Authentication Handler
class CustomBasicAuthHandler {{
    private $username = '{username}';
    private $password = '{password}';
    
    public function get_auth_headers() {{
        $credentials = base64_encode($this->username . ':' . $this->password);
        return array(
            'Authorization' => 'Basic ' . $credentials,
            'Content-Type' => 'application/json'
        );
    }}
    
    public function make_authenticated_request($url, $method = 'GET', $data = null) {{
        $args = array(
            'method' => $method,
            'headers' => $this->get_auth_headers(),
            'timeout' => 30
        );
        
        if ($data && in_array($method, array('POST', 'PUT', 'PATCH'))) {{
            $args['body'] = json_encode($data);
        }}
        
        $response = wp_remote_request($url, $args);
        
        if (is_wp_error($response)) {{
            return false;
        }}
        
        return json_decode(wp_remote_retrieve_body($response), true);
    }}
}}
"""
        
        # Save Basic auth handler to plugin
        basic_file = "wp-content/plugins/custom-api-integration/basic-auth-handler.php"
        create_files({"path": basic_file, "content": f"<?php\n{basic_code}"})
        
        logging.info("Basic authentication setup completed")
        return True
        
    except Exception as e:
        logging.error(f"Error setting up Basic auth: {str(e)}")
        return False

def _generate_api_plugin(api_url: str, parameters: Dict[str, Any], auth_method: str) -> str:
    """Generates a basic WordPress plugin file for API integration."""
    plugin_content = f"""<?php
/*
Plugin Name: Custom API Integration for {api_url}
Description: Integrates with an external API using {auth_method} authentication.
Version: 1.0
Author: AI Developer
*/

if ( ! defined( 'ABSPATH' ) ) {{
    exit; // Exit if accessed directly.
}}

// Register custom REST API endpoint
add_action( 'rest_api_init', function () {{
    register_rest_route( 'custom-api/v1', '/{parameters.get("endpoint", "data")}', array(
        'methods' => 'GET',
        'callback' => 'custom_api_fetch_data',
        'permission_callback' => function () {{
            return current_user_can( 'manage_options' ); // Example permission check
        }}
    ));
}});

// Callback function to fetch data from the external API
function custom_api_fetch_data( $request ) {{
    $api_url = '{api_url}';
    $auth_method = '{auth_method}';
    $params = json_decode( '{json.dumps(parameters)}', true );

    // Basic API call example (needs more robust implementation for production)
    $response = wp_remote_get( $api_url );

    if ( is_wp_error( $response ) ) {{
        return new WP_REST_Response( array( 'message' => 'Error fetching data from API', 'details' => $response->get_error_message() ), 500 );
    }}

    $body = wp_remote_retrieve_body( $response );
    $data = json_decode( $body, true );

    return new WP_REST_Response( $data, 200 );
}}
"""
    plugin_filename = f"custom-api-integration-{auth_method}.php"
    plugin_path = os.path.join("wp-content/plugins", plugin_filename)
    create_files({"path": plugin_path, "content": plugin_content})
    logging.info(f"Generated API integration plugin at {plugin_path}")
    return plugin_path


def manage_code_snippets(code_snippet: str, short_description: str, action: str) -> bool:
    """
    Manages code snippets in a WordPress site by writing to a designated snippets file.
    Actions: 'add', 'remove'.
    """
    snippet_file_path = "wp-content/mu-plugins/custom-snippets.php"
    
    try:
        # Ensure the mu-plugins directory exists
        os.makedirs(os.path.dirname(snippet_file_path), exist_ok=True)
        
        current_snippets = ""
        if os.path.exists(snippet_file_path):
            with open(snippet_file_path, 'r') as f:
                current_snippets = f.read()

        if action == "add":
            if code_snippet not in current_snippets:
                new_content = current_snippets
                if not new_content.strip().startswith("<?php"):
                    new_content = "<?php\n\n" + new_content
                new_content += f"\n// --- Snippet: {short_description} ---\n{code_snippet}\n// --- End Snippet ---\n"
                create_files({"path": snippet_file_path, "content": new_content})
                logging.info(f"Added code snippet: {short_description}")
                return True
            else:
                logging.info(f"Code snippet already exists: {short_description}")
                return False
        
        elif action == "remove":
            # This is a simplified removal. For production, consider parsing PHP to ensure safe removal.
            if code_snippet in current_snippets:
                new_content = current_snippets.replace(f"\n// --- Snippet: {short_description} ---\n{code_snippet}\n// --- End Snippet ---\n", "")
                create_files({"path": snippet_file_path, "content": new_content})
                logging.info(f"Removed code snippet: {short_description}")
                return True
            else:
                logging.info(f"Code snippet not found for removal: {short_description}")
                return False
        
        else:
            logging.error(f"Invalid action for manage_code_snippets: {action}")
            return False
            
    except Exception as e:
        logging.error(f"Error managing code snippet: {str(e)}")
        return False


async def generate_edit_instructions(file_path, file_content, instructions, project_context, full_file_contents):
    global wordpress_editor_tokens, wordpress_editor_memory, wordpress_editor_files
    try:
        memory_context = "\n".join([f"Memory {i+1}:\n{mem}" for i, mem in enumerate(wordpress_editor_memory)])
    
        full_file_contents_context = "\n\n".join([
            f"--- {path} ---\n{content}" for path, content in full_file_contents.items()
            if path != file_path or path not in wordpress_editor_files
        ])
    
        system_prompt = f"""
        You are an expert WordPress developer specializing in theme and plugin development. Review the following information carefully:
    
        1. File Content:
        {file_content}
    
        2. Edit Instructions:
        {instructions}
    
        3. Project Context:
        {project_context}
    
        4. Previous Edit Memory:
        {memory_context}
    
        5. Full Project Files Context:
        {full_file_contents_context}
    
        Follow this process to generate edit instructions:
    
        1. <CODE_REVIEW>
        Analyze the existing WordPress code thoroughly. Describe how it works, identifying key components, 
        hooks, filters, and potential issues. Consider the broader theme or plugin context and previous edits.
        </CODE_REVIEW>
    
        2. <PLANNING>
        Construct a plan to implement the requested changes. Consider:
        - WordPress coding standards and best practices
        - Theme or plugin architecture and structure
        - Use of appropriate WordPress functions and APIs
        - Compatibility with different WordPress versions
        - Security considerations specific to WordPress
        - Performance impacts on WordPress sites
        - Outline discrete changes and suggest small tests for each stage.
        </PLANNING>
    
        3. Finally, generate SEARCH/REPLACE blocks for each necessary change:
        - Use enough context to uniquely identify the code to be changed
        - Maintain correct indentation and formatting
        - Focus on specific, targeted changes
        - Ensure consistency with WordPress standards and previous edits
    
        USE THIS FORMAT FOR CHANGES:
    
        <SEARCH>
        Code to be replaced (with sufficient context)
        </SEARCH>
        <REPLACE>
        New code to insert
        </REPLACE>
    
        IMPORTANT: ONLY RETURN CODE INSIDE THE <SEARCH> AND <REPLACE> TAGS. DO NOT INCLUDE ANY OTHER TEXT, COMMENTS, or Explanations.
        """
    
        response = client.beta.prompt_caching.messages.create(
            model=WORDPRESSEDITORMODEL,
            max_tokens=8000,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": "Generate SEARCH/REPLACE blocks for the necessary WordPress changes."}
            ],
            extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
        )
    
        wordpress_editor_tokens['input'] += response.usage.input_tokens
        wordpress_editor_tokens['output'] += response.usage.output_tokens
        wordpress_editor_tokens['cache_write'] = response.usage.cache_creation_input_tokens
        wordpress_editor_tokens['cache_read'] = response.usage.cache_read_input_tokens
    
        ai_response_text = response.content[0].text
    
        if isinstance(ai_response_text, list):
            ai_response_text = ' '.join(
                item['text'] if isinstance(item, dict) and 'text' in item else str(item)
                for item in ai_response_text
            )
        elif not isinstance(ai_response_text, str):
            ai_response_text = str(ai_response_text)
    
        try:
            if not validate_ai_response(ai_response_text):
                raise ValueError("AI response does not contain valid SEARCH/REPLACE blocks for WordPress")
        except ValueError as ve:
            logging.error(f"WordPress edit validation failed: {ve}")
            return []
    
        edit_instructions = parse_search_replace_blocks(ai_response_text)
    
        if not edit_instructions:
            raise ValueError("No valid WordPress edit instructions were generated")
    
        wordpress_editor_memory.append(f"WordPress Edit Instructions for {file_path}:\n{ai_response_text}")
    
        wordpress_editor_files.add(file_path)
    
        return edit_instructions

    except Exception as e:
        console.print(f"Error in generating edit instructions: {str(e)}", style="bold red")
        logging.error(f"Error in generating edit instructions: {str(e)}")
        return []  # Return empty list if any exception occurs


def validate_ai_response(response_text):
    if isinstance(response_text, list):
        # Extract 'text' from each dictionary in the list
        try:
            response_text = ' '.join(
                item['text'] if isinstance(item, dict) and 'text' in item else str(item)
                for item in response_text
            )
        except Exception as e:
            logging.error(f"Error processing response_text list: {str(e)}")
            raise ValueError("Invalid format in response_text list.")
    elif not isinstance(response_text, str):
        logging.debug(f"validate_ai_response received type {type(response_text)}: {response_text}")
        raise ValueError(f"Invalid type for response_text: {type(response_text)}. Expected string.")
    
    # Log the processed response_text
    logging.debug(f"Processed response_text for validation: {response_text}")
    
    if not re.search(r'<SEARCH>.*?</SEARCH>', response_text, re.DOTALL):
        raise ValueError("AI response does not contain any <SEARCH> blocks")
    if not re.search(r'<REPLACE>.*?</REPLACE>', response_text, re.DOTALL):
        raise ValueError("AI response does not contain any <REPLACE> blocks")
    return True


def parse_search_replace_blocks(response_text, use_fuzzy=USE_FUZZY_SEARCH):
    """
    Parse the response text for SEARCH/REPLACE blocks.

    Args:
    response_text (str): The text containing SEARCH/REPLACE blocks.
    use_fuzzy (bool): Whether to use fuzzy matching for search blocks.

    Returns:
    list: A list of dictionaries, each containing 'search', 'replace', and 'similarity' keys.
    """
    blocks = []
    pattern = r'<SEARCH>\s*(.*?)\s*</SEARCH>\s*<REPLACE>\s*(.*?)\s*</REPLACE>'
    matches = re.findall(pattern, response_text, re.DOTALL)

    for search, replace in matches:
        search = search.strip()
        replace = replace.strip()
        similarity = 1.0  # Default to exact match

        if use_fuzzy and search not in response_text:
            # Extract possible search targets from the response text
            possible_search_targets = re.findall(r'<SEARCH>\s*(.*?)\s*</SEARCH>', response_text, re.DOTALL)
            possible_search_targets = [target.strip() for target in possible_search_targets]
            
            best_match = difflib.get_close_matches(search, possible_search_targets, n=1, cutoff=0.6)
            if best_match:
                similarity = difflib.SequenceMatcher(None, search, best_match[0]).ratio()
            else:
                similarity = 0.0

        blocks.append({
            'search': search,
            'replace': replace,
            'similarity': similarity
        })

    return blocks


async def edit_and_apply_multiple(files, project_context, is_automode=False):
    global file_contents
    results = []
    console_outputs = []

    logging.debug(f"edit_and_apply_multiple called with files: {files}")
    logging.debug(f"Project context: {project_context}")

    try:
        files = validate_files_structure(files)
    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
        return [], f"Error: {ve}"

    logging.info(f"Starting edit_and_apply_multiple with {len(files)} file(s)")

    for file in files:
        path = file['path']
        instructions = file['instructions']
        logging.info(f"Processing file: {path}")
        try:
            original_content = file_contents.get(path, "")
            if not original_content:
                logging.info(f"Reading content for file: {path}")
                with open(path, 'r') as f:
                    original_content = f.read()
                file_contents[path] = original_content

            logging.info(f"Generating edit instructions for file: {path}")
            edit_instructions = await generate_edit_instructions(path, original_content, instructions, project_context, file_contents)

            logging.debug(f"AI response for {path}: {edit_instructions}")

            if not isinstance(edit_instructions, list) or not all(isinstance(item, dict) for item in edit_instructions):
                raise ValueError("Invalid edit_instructions format. Expected a list of dictionaries.")

            # Define apply_edits if not already defined
            async def apply_edits(path, edit_instructions, original_content):
                """
                Apply SEARCH/REPLACE edit instructions to the file content.
                Returns: (edited_content, changes_made, failed_edits, console_output)
                """
                edited_content = original_content
                changes_made = False
                failed_edits = []
                console_output = ""
                for block in edit_instructions:
                    search = block.get('search')
                    replace = block.get('replace')
                    if search and search in edited_content:
                        edited_content = edited_content.replace(search, replace)
                        changes_made = True
                        console_output += f"Applied SEARCH/REPLACE block to {path}.\n"
                    else:
                        failed_edits.append(block)
                        console_output += f"Failed to apply SEARCH block to {path}.\n"
                # Write back to file if changes were made
                if changes_made:
                    try:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(edited_content)
                    except Exception as e:
                        console_output += f"Error writing file: {str(e)}\n"
                return edited_content, changes_made, failed_edits, console_output

            if edit_instructions:
                console.print(Panel(f"File: {path}\nThe following SEARCH/REPLACE blocks have been generated:", title="Edit Instructions", style="cyan"))
                for i, block in enumerate(edit_instructions, 1):
                    console.print(f"Block {i}:")
                    console.print(Panel(f"SEARCH:\n{block['search']}\n\nREPLACE:\n{block['replace']}\nSimilarity: {block['similarity']:.2f}", expand=False))

                logging.info(f"Applying edits to file: {path}")
                edited_content, changes_made, failed_edits, console_output = await apply_edits(path, edit_instructions, original_content)

                console_outputs.append(console_output)

                if changes_made:
                    file_contents[path] = edited_content
                    console.print(Panel(f"File contents updated in system prompt: {path}", style="green"))
                    logging.info(f"Changes applied to file: {path}")

                    if failed_edits:
                        logging.warning(f"Some edits failed for file: {path}")
                        logging.debug(f"Failed edits for {path}: {failed_edits}")
                        results.append({
                            "path": path,
                            "status": "partial_success",
                            "message": f"Some changes applied to {path}, but some edits failed.",
                            "failed_edits": failed_edits,
                            "edited_content": edited_content
                        })
                    else:
                        results.append({
                            "path": path,
                            "status": "success",
                            "message": f"All changes successfully applied to {path}",
                            "edited_content": edited_content
                        })
                else:
                    logging.warning(f"No changes applied to file: {path}")
                    results.append({
                        "path": path,
                        "status": "no_changes",
                        "message": f"No changes could be applied to {path}. Please review the edit instructions and try again."
                    })
            else:
                logging.warning(f"No edit instructions generated for file: {path}")
                results.append({
                    "path": path,
                    "status": "no_instructions",
                    "message": f"No edit instructions generated for {path}"
                })
        except Exception as e:
            logging.error(f"Error editing/applying to file {path}: {str(e)}")
            logging.exception("Full traceback:")
            error_message = f"Error editing/applying to file {path}: {str(e)}"
            results.append({
                "path": path,
                "status": "error",
                "message": error_message
            })
            console_outputs.append(error_message)

    logging.info("Completed edit_and_apply_multiple")
    logging.debug(f"Results: {results}")
    return results, "\n".join(console_outputs)


def highlight_diff(diff_text):
    return Syntax(diff_text, "diff", theme="monokai", line_numbers=True)


def generate_diff(original, new, path):
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        n=3
    ))

    diff_text = ''.join(diff)
    highlighted_diff = highlight_diff(diff_text)

    return highlighted_diff

async def execute_code(code, timeout=10):
    global running_processes
    wp_root = os.getenv('WORDPRESS_ROOT', '/var/www/html')

    # Input validation
    if not isinstance(code, str):
        raise ValueError("code must be a string")
    if not isinstance(timeout, (int, float)):
        raise ValueError("timeout must be a number")

    # Generate a unique identifier for this process
    process_id = f"wp_process_{len(running_processes)}"

    # Write the code to a temporary file in the WordPress plugins directory
    plugin_dir = os.path.join(wp_root, 'wp-content', 'plugins', 'temp-executions')
    os.makedirs(plugin_dir, exist_ok=True)
    plugin_file = os.path.join(plugin_dir, f"{process_id}.php")

    try:
        with open(plugin_file, "w") as f:
            f.write(f"<?php\n{code}")
    except IOError as e:
        return process_id, f"Error writing WordPress code to file: {str(e)}"

    # Prepare the command to run the WordPress code
    wp_cli_path = shutil.which('wp')
    if not wp_cli_path:
        return process_id, "WP-CLI not found. Please install WP-CLI to execute WordPress code."

    command = f"{wp_cli_path} eval-file {plugin_file} --path={wp_root}"

    try:
        # Create a process to run the command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
            preexec_fn=None if sys.platform == "win32" else os.setsid
        )

        # Store the process in our global dictionary
        running_processes[process_id] = process

        try:
            # Wait for output or timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            stdout = stdout.decode()
            stderr = stderr.decode()
            return_code = process.returncode
        except asyncio.TimeoutError:
            stdout = "WordPress process started and running in the background."
            stderr = ""
            return_code = "Running"

        execution_result = f"WordPress Process ID: {process_id}\n\nOutput:\n{stdout}\n\nErrors:\n{stderr}\n\nReturn Code: {return_code}"
        return process_id, execution_result
    except Exception as e:
        return process_id, f"Error executing WordPress code: {str(e)}"
    finally:
        # Cleanup: remove the temporary plugin file
        try:
            os.remove(plugin_file)
        except OSError:
            pass  # Ignore errors in removing the file

# Update the read_multiple_files function to handle both single and multiple files
def read_multiple_files(paths, recursive=False):
    global file_contents
    results = []

    if isinstance(paths, str):
        paths = [paths]

    for path in paths:
        try:
            abs_path = os.path.abspath(path)
            if os.path.isdir(abs_path):
                if recursive:
                    file_paths = glob.glob(os.path.join(abs_path, '**', '*'), recursive=True)
                else:
                    file_paths = glob.glob(os.path.join(abs_path, '*'))
                file_paths = [f for f in file_paths if os.path.isfile(f)]
            else:
                file_paths = glob.glob(abs_path, recursive=recursive)

            for file_path in file_paths:
                abs_file_path = os.path.abspath(file_path)
                if os.path.isfile(abs_file_path):
                    if abs_file_path not in file_contents:
                        with open(abs_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        file_contents[abs_file_path] = content
                        results.append(f"File '{abs_file_path}' has been read and stored in the system prompt.")
                    else:
                        results.append(f"File '{abs_file_path}' is already in the system prompt. No need to read again.")
                else:
                    results.append(f"Skipped '{abs_file_path}': Not a file.")
        except Exception as e:
            results.append(f"Error reading path '{path}': {str(e)}")

    return "\n".join(results)

def list_files(path="."):
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

def tavily_search(query):
    try:
        response = tavily.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as e:
        return f"Error performing search: {str(e)}"

def stop_process(process_id):
    global running_processes
    if process_id in running_processes:
        process = running_processes[process_id]
        if sys.platform == "win32":
            process.terminate()
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        del running_processes[process_id]
        return f"Process {process_id} has been stopped."
    else:
        return f"No running process found with ID {process_id}."

def run_shell_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.CalledProcessError as e:
        return {
            "stdout": e.stdout,
            "stderr": e.stderr,
            "return_code": e.returncode,
            "error": str(e)
        }
    except Exception as e:
        return {
            "error": f"An error occurred while executing the command: {str(e)}"
        }
    
def validate_files_structure(files):
    if not isinstance(files, (dict, list)):
        raise ValueError("Invalid 'files' structure. Expected a dictionary or a list of dictionaries.")
    
    if isinstance(files, dict):
        files = [files]
    
    for file in files:
        if not isinstance(file, dict):
            raise ValueError("Each file must be a dictionary.")
        if 'path' not in file or 'instructions' not in file:
            raise ValueError("Each file dictionary must contain 'path' and 'instructions' keys.")
        if not isinstance(file['path'], str) or not isinstance(file['instructions'], str):
            raise ValueError("'path' and 'instructions' must be strings.")

    return files

def scan_folder(folder_path: str, output_file: str) -> str:
    ignored_folders = {'.git', '__pycache__', 'node_modules', 'venv', 'env'}
    markdown_content = f"# Folder Scan: {folder_path}\n\n"
    total_chars = len(markdown_content)
    max_chars = 600000  # Approximating 150,000 tokens

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in ignored_folders]

        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, folder_path)

            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith('text'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    file_content = f"## {relative_path}\n\n```\n{content}\n```\n\n"
                    if total_chars + len(file_content) > max_chars:
                        remaining_chars = max_chars - total_chars
                        if remaining_chars > 0:
                            truncated_content = file_content[:remaining_chars]
                            markdown_content += truncated_content
                            markdown_content += "\n\n... Content truncated due to size limitations ...\n"
                        else:
                            markdown_content += "\n\n... Additional files omitted due to size limitations ...\n"
                        break
                    else:
                        markdown_content += file_content
                        total_chars += len(file_content)
                except Exception as e:
                    error_msg = f"## {relative_path}\n\nError reading file: {str(e)}\n\n"
                    if total_chars + len(error_msg) <= max_chars:
                        markdown_content += error_msg
                        total_chars += len(error_msg)

        if total_chars >= max_chars:
            break

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    return f"WordPress theme scan complete. Markdown file created at: {output_file}. Total characters: {total_chars}"


class WordPressThemeAnalyzer:
    def __init__(self):
        pass

    def _read_file_content(self, file_path: str) -> str:
        """Helper to read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

    def _extract_theme_info(self, theme_path: str) -> Dict[str, Any]:
        """Extracts basic theme information from style.css."""
        style_css_path = os.path.join(theme_path, 'style.css')
        content = self._read_file_content(style_css_path)
        
        info = {
            "name": "Unknown Theme",
            "version": "1.0",
            "author": "Unknown",
            "description": ""
        }
        
        name_match = re.search(r"Theme Name:\s*(.*)", content)
        if name_match:
            info["name"] = name_match.group(1).strip()
        
        version_match = re.search(r"Version:\s*(.*)", content)
        if version_match:
            info["version"] = version_match.group(1).strip()

        author_match = re.search(r"Author:\s*(.*)", content)
        if author_match:
            info["author"] = author_match.group(1).strip()

        description_match = re.search(r"Description:\s*(.*)", content)
        if description_match:
            info["description"] = description_match.group(1).strip()
            
        return info

    def _analyze_template_files(self, theme_path: str) -> List[str]:
        """Lists and categorizes theme template files."""
        template_files = []
        for root, _, files in os.walk(theme_path):
            for file in files:
                if file.endswith('.php') and 'wp-content' not in root: # Avoid scanning wp-admin, wp-includes etc.
                    template_files.append(os.path.relpath(os.path.join(root, file), theme_path))
        return template_files

    def _analyze_functions_php(self, theme_path: str) -> Dict[str, Any]:
        """Analyzes functions.php for common issues and registered items."""
        functions_php_path = os.path.join(theme_path, 'functions.php')
        content = self._read_file_content(functions_php_path)
        
        analysis = {
            "hooks": [],
            "filters": [],
            "shortcodes": [],
            "enqueued_scripts": [],
            "enqueued_styles": [],
            "issues": []
        }
        
        # Simple regex for common WordPress functions/hooks
        hooks = re.findall(r"add_action\s*\(\s*['\"](.*?)['\"]", content)
        analysis["hooks"].extend(hooks)
        
        filters = re.findall(r"add_filter\s*\(\s*['\"](.*?)['\"]", content)
        analysis["filters"].extend(filters)

        shortcodes = re.findall(r"add_shortcode\s*\(\s*['\"](.*?)['\"]", content)
        analysis["shortcodes"].extend(shortcodes)

        scripts = re.findall(r"wp_enqueue_script\s*\(\s*['\"](.*?)['\"]", content)
        analysis["enqueued_scripts"].extend(scripts)

        styles = re.findall(r"wp_enqueue_style\s*\(\s*['\"](.*?)['\"]", content)
        analysis["enqueued_styles"].extend(styles)

        # Basic security/best practice checks
        if "eval(" in content:
            analysis["issues"].append("Contains 'eval()' - potential security risk.")
        if "mysql_connect" in content:
            analysis["issues"].append("Uses deprecated MySQL functions.")
        
        return analysis

    def _scan_security_issues(self, theme_path: str) -> List[str]:
        """Scans for potential security vulnerabilities (basic checks)."""
        issues = []
        for root, _, files in os.walk(theme_path):
            for file in files:
                file_path = os.path.join(root, file)
                content = self._read_file_content(file_path)

                if re.search(r"<\?php\s*die", content, re.IGNORECASE) or re.search(r"<\?php\s*exit", content, re.IGNORECASE):
                    pass # Common and often safe usage
                else:
                    if re.search(r"$_GET\[(.*?)\]", content) or re.search(r"$_POST\[(.*?)\]", content) or re.search(r"$_REQUEST\[(.*?)\]", content):
                        if not re.search(r"sanitize_text_field|esc_attr|esc_html|wp_kses", content):
                            issues.append(f"Potential unsanitized input in {os.path.relpath(file_path, theme_path)}")
                
                if re.search(r"base64_decode\s*\(", content):
                    issues.append(f"Possible obfuscated code in {os.path.relpath(file_path, theme_path)}")
        return issues

    def _analyze_performance(self, theme_path: str) -> Dict[str, Any]:
        """Analyzes theme performance aspects (placeholder for complex analysis)."""
        # In a real scenario, this would involve more detailed static analysis
        # or integration with performance testing tools.
        return {"score": 75, "recommendations": ["Optimize images", "Minify CSS/JS", "Leverage browser caching"]}

    def _check_accessibility(self, theme_path: str) -> Dict[str, Any]:
        """Checks theme accessibility score (placeholder for real testing)."""
        # This would require a browser automation tool with accessibility testing capabilities (e.g., Axe-core).
        return {"score": 80, "recommendations": ["Ensure proper contrast ratios", "Add alt text to images"]}

    def _check_responsive_design(self, theme_path: str) -> Dict[str, Any]:
        """Checks for mobile responsiveness (placeholder for real testing)."""
        # This would typically involve browser automation and screenshot comparisons at different viewports.
        return {"responsive": "Needs manual verification", "issues": []}

    def _generate_theme_report(self, analysis: Dict[str, Any], output_file: str) -> None:
        """Generates a detailed theme analysis report."""
        report_content = f"# WordPress Theme Analysis Report: {analysis['theme_info']['name']}\n\n"
        report_content += "## Theme Information\n"
        for key, value in analysis['theme_info'].items():
            report_content += f"- **{key.replace('_', ' ').title()}**: {value}\n"
        report_content += "\n"

        report_content += "## Template Files Found\n"
        for f in analysis['template_files']:
            report_content += f"- `{f}`\n"
        report_content += "\n"

        report_content += "## functions.php Analysis\n"
        func_analysis = analysis['functions_analysis']
        report_content += "- **Hooks Registered**: " + ", ".join(func_analysis['hooks']) + "\n"
        report_content += "- **Filters Registered**: " + ", ".join(func_analysis['filters']) + "\n"
        report_content += "- **Shortcodes Registered**: " + ", ".join(func_analysis['shortcodes']) + "\n"
        report_content += "- **Enqueued Scripts**: " + ", ".join(func_analysis['enqueued_scripts']) + "\n"
        report_content += "- **Enqueued Styles**: " + ", ".join(func_analysis['enqueued_styles']) + "\n"
        if func_analysis['issues']:
            report_content += "- **Identified Issues**:\n"
            for issue in func_analysis['issues']:
                report_content += f"  - {issue}\n"
        else:
            report_content += "- No major issues identified in functions.php.\n"
        report_content += "\n"

        report_content += "## Security Scan\n"
        if analysis['security_issues']:
            for issue in analysis['security_issues']:
                report_content += f"- {issue}\n"
        else:
            report_content += "- No critical security issues found (basic scan).\n"
        report_content += "\n"

        report_content += "## Performance Analysis\n"
        report_content += f"- **Score**: {analysis['performance_issues']['score']}/100\n"
        report_content += "- **Recommendations**:\n"
        for rec in analysis['performance_issues']['recommendations']:
            report_content += f"  - {rec}\n"
        report_content += "\n"

        report_content += "## Accessibility Check\n"
        report_content += f"- **Score**: {analysis['accessibility_score']['score']}/100\n"
        report_content += "- **Recommendations**:\n"
        for rec in analysis['accessibility_score']['recommendations']:
            report_content += f"  - {rec}\n"
        report_content += "\n"

        report_content += "## Responsive Design\n"
        report_content += f"- **Status**: {analysis['mobile_responsive']['responsive']}\n"
        if analysis['mobile_responsive']['issues']:
            report_content += "- **Issues**:\n"
            for issue in analysis['mobile_responsive']['issues']:
                report_content += f"  - {issue}\n"
        report_content += "\n"

        create_files({"path": output_file, "content": report_content})
        logging.info(f"Report generated at {output_file}")


    def scan_wordpress_theme(self, theme_path: str, output_file: str) -> str:
        """Comprehensive WordPress theme analysis."""
        if not os.path.isdir(theme_path):
            return f"Error: Theme path '{theme_path}' does not exist or is not a directory."

        analysis = {
            'theme_info': self._extract_theme_info(theme_path),
            'template_files': self._analyze_template_files(theme_path),
            'functions_analysis': self._analyze_functions_php(theme_path),
            'security_issues': self._scan_security_issues(theme_path),
            'performance_issues': self._analyze_performance(theme_path),
            'accessibility_score': self._check_accessibility(theme_path),
            'mobile_responsive': self._check_responsive_design(theme_path)
        }
        
        self._generate_theme_report(analysis, output_file)
        return f"Theme analysis completed. Report saved to: {output_file}"

def manage_theme_customizer(theme_path: str, settings: List[Dict], controls: List[Dict], sections: List[Dict], actions: List[str]) -> bool:
    """Use the WordPress Theme Customization API to create and manage settings, sections, and controls for theme options."""
    try:
        # Placeholder for WP-CLI or direct file manipulation
        # This is where you would add the logic to interact with the WordPress customizer
        # For example, using WP-CLI commands or directly modifying theme files
        
        # Example using WP-CLI (this is a placeholder and may not work directly)
        # command = f"wp theme customize {theme_path} --settings='{json.dumps(settings)}' --controls='{json.dumps(controls)}' --sections='{json.dumps(sections)}' --actions='{json.dumps(actions)}'"
        # result = subprocess.run(command, shell=True, capture_output=True, text=True)
        # return result.returncode == 0
        
        # For now, just log the input
        logging.info(f"Theme Customizer Input: theme_path={theme_path}, settings={settings}, controls={controls}, sections={sections}, actions={actions}")
        return True
    except Exception as e:
        logging.error(f"Error managing theme customizer: {str(e)}")
        return False

def _create_block_json(block_dir: str, block_name: str, attributes: Dict[str, Any]):
    """Creates block.json file."""
    block_json_content = json.dumps({
        "apiVersion": 2,
        "name": f"create-block/{block_name}",
        "title": block_name.replace('-', ' ').title(),
        "category": "widgets",
        "icon": "smiley",
        "description": f"Example block for {block_name}.",
        "supports": {
            "html": False
        },
        "attributes": attributes,
        "editorScript": "file:./index.js",
        "editorStyle": "file:./index.css",
        "style": "file:./style-index.css"
    }, indent=4)
    file_path = os.path.join(block_dir, "block.json")
    create_files({"path": file_path, "content": block_json_content})
    logging.info(f"Created block.json for {block_name} at {file_path}")

def _create_block_js(block_dir: str, block_name: str, editor_ui: str):
    """Creates JavaScript files for editor interface."""
    js_content = f"""
import {{ registerBlockType }} from '@wordpress/blocks';
import {{ __ }} from '@wordpress/i18n';
import './editor.scss';
import './style.scss';

registerBlockType('{block_name}/{block_name}', {{
    title: __('{block_name.replace('-', ' ').title()}'),
    icon: 'smiley',
    category: 'widgets',
    edit: () => {{
        return (
            <div className="wp-block-{block_name}-block">
                {{ __('{block_name.replace('-', ' ').title()} Block Editor') }}
            </div>
        );
    }},
    save: () => {{
        return (
            <div className="wp-block-{block_name}-block">
                {{ __('{block_name.replace('-', ' ').title()} Block Frontend') }}
            </div>
        );
    }},
}});
"""
    file_path = os.path.join(block_dir, "index.js")
    create_files({"path": file_path, "content": js_content})
    logging.info(f"Created index.js for {block_name} at {file_path}")

def _create_block_php(block_dir: str, block_name: str, server_side_render: str):
    """Generates PHP render function."""
    php_content = f"""<?php
/**
 * PHP file to render the {block_name} block.
 */

function {block_name.replace('-', '_')}_block_render_callback( $attributes, $content ) {{
    ob_start();
    ?>
    <div class="wp-block-{block_name}-block">
        <?php echo esc_html( '{block_name.replace('-', ' ').title()} Block Content' ); ?>
        <?php echo $server_side_render; ?>
    </div>
    <?php
    return ob_get_clean();
}}

function {block_name.replace('-', '_')}_block_init() {{
    register_block_type( __DIR__ );
}}
add_action( 'init', '{block_name.replace('-', '_')}_block_init' );
"""
    file_path = os.path.join(block_dir, "index.php")
    create_files({"path": file_path, "content": php_content})
    logging.info(f"Created index.php for {block_name} at {file_path}")

def _create_block_styles(block_dir: str, block_name: str):
    """Creates CSS styles for frontend/backend."""
    editor_scss_content = f"""
.wp-block-{block_name}-block {{
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    padding: 20px;
    text-align: center;
}}
"""
    style_scss_content = f"""
.wp-block-{block_name}-block {{
    color: #333;
}}
"""
    create_files([
        {"path": os.path.join(block_dir, "editor.scss"), "content": editor_scss_content},
        {"path": os.path.join(block_dir, "style.scss"), "content": style_scss_content}
    ])
    logging.info(f"Created editor.scss and style.scss for {block_name} at {block_dir}")

def create_gutenberg_block(block_name: str, attributes: Dict[str, Any], 
                          editor_ui: str, server_side_render: str) -> bool:
    """Create custom Gutenberg block"""
    try:
        # 1. Generate block.json with metadata
        # 2. Create JavaScript files for editor interface
        # 3. Generate PHP render function
        # 4. Set up block registration
        # 5. Create CSS styles for frontend/backend
        
        block_dir = f"wp-content/plugins/custom-blocks/{block_name}"
        
        # Generate block files
        _create_block_json(block_dir, block_name, attributes)
        _create_block_js(block_dir, block_name, editor_ui)
        _create_block_php(block_dir, block_name, server_side_render)
        _create_block_styles(block_dir, block_name)
        
        return True
    except Exception as e:
        logging.error(f"Error creating Gutenberg block: {str(e)}")
        return False
    
def manage_widgets(widget_id: str, widget_area: str, settings: Dict[str, Any], actions: List[str]) -> bool:
    """
    Manages WordPress widgets using WP-CLI commands.
    Actions: 'add', 'remove', 'update'.
    """
    try:
        wp_cli_path = shutil.which('wp')
        if not wp_cli_path:
            logging.error("WP-CLI not found. Please install WP-CLI to manage widgets.")
            return False

        if "add" in actions:
            command = f"{wp_cli_path} widget add {widget_id} {widget_area}"
            if settings:
                command += f" --settings='{json.dumps(settings)}'"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Widget '{widget_id}' added to '{widget_area}'.")
                return True
            else:
                logging.error(f"Error adding widget: {result.stderr}")
                return False
        
        if "remove" in actions:
            command = f"{wp_cli_path} widget delete {widget_id} {widget_area}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Widget '{widget_id}' removed from '{widget_area}'.")
                return True
            else:
                logging.error(f"Error removing widget: {result.stderr}")
                return False

        if "update" in actions:
            command = f"{wp_cli_path} widget update {widget_id} {widget_area}"
            if settings:
                command += f" --settings='{json.dumps(settings)}'"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Widget '{widget_id}' updated in '{widget_area}'.")
                return True
            else:
                logging.error(f"Error updating widget: {result.stderr}")
                return False
        
        logging.info(f"Widget Management: No specific action (add/remove/update) requested for widget_id={widget_id}, widget_area={widget_area}, settings={settings}, actions={actions}")
        return False # No specific action was performed
    except Exception as e:
        logging.error(f"Error managing widgets: {str(e)}")
        return False

def create_shortcode(shortcode_name: str, callback_function: str) -> bool:
    """
    Creates a WordPress shortcode by adding it to the theme's functions.php or a custom plugin file.
    """
    try:
        # Determine where to add the shortcode: functions.php or a new plugin file
        # For simplicity, let's assume we're adding to an existing functions.php
        # In a real-world scenario, you might want to create a dedicated plugin for custom shortcodes.
        
        # Path to the active theme's functions.php (this would need to be dynamically determined)
        # For now, let's assume a generic path or create a new plugin for it
        plugin_dir = f"wp-content/plugins/custom-shortcodes-{shortcode_name}"
        os.makedirs(plugin_dir, exist_ok=True)
        plugin_file = os.path.join(plugin_dir, f"{shortcode_name}.php")

        shortcode_php_content = f"""<?php
/*
Plugin Name: Custom Shortcode: {shortcode_name}
Description: Adds a custom shortcode for dynamic content.
Version: 1.0
Author: AI Developer
*/

if ( ! defined( 'ABSPATH' ) ) {{
    exit; // Exit if accessed directly.
}}

function {shortcode_name.replace('-', '_')}_shortcode_callback( $atts ) {{
    ob_start();
    ?>
    <!-- Shortcode content generated by AI -->
    <div class="custom-shortcode custom-shortcode-{shortcode_name}">
        <?php
        // Execute the provided callback function
        {callback_function}
        ?>
    </div>
    <?php
    return ob_get_clean();
}}
add_shortcode( '{shortcode_name}', '{shortcode_name.replace('-', '_')}_shortcode_callback' );
"""
        create_files({"path": plugin_file, "content": shortcode_php_content})
        logging.info(f"Created shortcode '{shortcode_name}' in plugin file: {plugin_file}")
        return True
    except Exception as e:
        logging.error(f"Error creating shortcode: {str(e)}")
        return False

def manage_taxonomies(taxonomy_name: str, post_types: List[str], settings: Dict[str, Any], actions: List[str]) -> bool:
    """
    Manages custom taxonomies using WP-CLI commands.
    Actions: 'register', 'update', 'delete'.
    """
    try:
        wp_cli_path = shutil.which('wp')
        if not wp_cli_path:
            logging.error("WP-CLI not found. Please install WP-CLI to manage taxonomies.")
            return False

        if "register" in actions:
            command = f"{wp_cli_path} taxonomy create {taxonomy_name}"
            if post_types:
                command += f" --object-type={','.join(post_types)}"
            if settings:
                command += f" --args='{json.dumps(settings)}'"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Taxonomy '{taxonomy_name}' registered successfully.")
                return True
            else:
                logging.error(f"Error registering taxonomy: {result.stderr}")
                return False
        
        if "update" in actions:
            # WP-CLI does not have a direct 'taxonomy update' command like 'post type update'.
            # Updates usually mean re-registering with new settings or managing terms.
            # For this context, we'll assume updating settings means re-registering.
            # Managing terms would involve separate WP-CLI commands like 'term create/update/delete'.
            command = f"{wp_cli_path} taxonomy update {taxonomy_name}" # This command might not exist directly
            if settings:
                command += f" --args='{json.dumps(settings)}'"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Taxonomy '{taxonomy_name}' updated successfully.")
                return True
            else:
                logging.error(f"Error updating taxonomy: {result.stderr}")
                return False

        if "delete" in actions:
            command = f"{wp_cli_path} taxonomy delete {taxonomy_name}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Taxonomy '{taxonomy_name}' deleted successfully.")
                return True
            else:
                logging.error(f"Error deleting taxonomy: {result.stderr}")
                return False
        
        logging.info(f"Taxonomy Management: No specific action (register/update/delete) requested for taxonomy_name={taxonomy_name}, post_types={post_types}, settings={settings}, actions={actions}")
        return False # No specific action was performed
    except Exception as e:
        logging.error(f"Error managing taxonomies: {str(e)}")
        return False


def manage_menus(menu_name: str, menu_location: str, items: List[Dict], actions: List[str]) -> bool:
    """
    Manages WordPress menus using WP-CLI commands.
    Actions: 'create', 'update', 'delete', 'assign', 'add_items'.
    """
    try:
        wp_cli_path = shutil.which('wp')
        if not wp_cli_path:
            logging.error("WP-CLI not found. Please install WP-CLI to manage menus.")
            return False

        success = True
        
        if "create" in actions:
            command = [wp_cli_path, "menu", "create", menu_name]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Menu '{menu_name}' created successfully.")
            else:
                logging.error(f"Error creating menu: {result.stderr}")
                success = False
        
        if "add_items" in actions and items and success:
            # Get menu ID first
            get_menu_cmd = [wp_cli_path, "menu", "list", "--fields=term_id,name", "--format=json"]
            menu_list_result = subprocess.run(get_menu_cmd, capture_output=True, text=True)
            
            if menu_list_result.returncode != 0:
                logging.error(f"Error listing menus: {menu_list_result.stderr}")
                return False
            
            try:
                menus = json.loads(menu_list_result.stdout)
                menu_id = next((str(m['term_id']) for m in menus if m['name'] == menu_name), None)
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"Error parsing menu list: {str(e)}")
                return False

            if not menu_id:
                logging.error(f"Menu '{menu_name}' not found to add items.")
                return False
            
            for item in items:
                title = item.get('title', 'Menu Item')
                item_type = item.get('type', 'post')
                object_id = item.get('object_id')
                url = item.get('url')
                
                if item_type == 'custom' and url:
                    item_cmd = [wp_cli_path, "menu", "item", "add-custom", menu_id, title, url]
                elif item_type == 'post' and object_id:
                    item_cmd = [wp_cli_path, "menu", "item", "add-post", menu_id, str(object_id)]
                elif item_type == 'page' and object_id:
                    item_cmd = [wp_cli_path, "menu", "item", "add-page", menu_id, str(object_id)]
                else:
                    logging.warning(f"Skipping menu item: Invalid configuration for '{title}'.")
                    continue
                
                item_result = subprocess.run(item_cmd, capture_output=True, text=True)
                if item_result.returncode != 0:
                    logging.error(f"Error adding menu item '{title}': {item_result.stderr}")
                    success = False

        if "assign" in actions and menu_location and success:
            command = [wp_cli_path, "menu", "location", "assign", menu_name, menu_location]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Menu '{menu_name}' assigned to location '{menu_location}'.")
            else:
                logging.error(f"Error assigning menu: {result.stderr}")
                success = False

        if "delete" in actions:
            command = [wp_cli_path, "menu", "delete", menu_name]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Menu '{menu_name}' deleted successfully.")
            else:
                logging.error(f"Error deleting menu: {result.stderr}")
                success = False
        
        return success
        
    except Exception as e:
        logging.error(f"Error managing menus: {str(e)}")
        return False

def encode_image_to_base64(image_path):
    try:
        with Image.open(image_path) as img:
            max_size = (1024, 1024)
            img.thumbnail(max_size, Image.DEFAULT_STRATEGY)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    except Exception as e:
        return f"Error encoding image: {str(e)}"


async def send_to_ai_for_analysis(code, execution_result):
    global wordpress_analysis_tokens

    try:
        system_prompt = f"""
        You are a WordPress development expert. Analyze the provided WordPress code and its execution result, then provide a concise summary focusing on WordPress-specific aspects. Follow these steps:

        1. Review the WordPress code that was executed:
        {code}

        2. Analyze the execution result:
        {execution_result}

        3. Provide a brief summary of:
           - WordPress hooks, actions, and filters used correctly
           - Any WordPress coding standards violations
           - Potential security issues in the WordPress context
           - Performance considerations for WordPress sites
           - Compatibility with current WordPress version and common plugins
           - Suggestions for improving WordPress-specific functionality

        Be concise and focus on WordPress-specific aspects of the code execution.

        IMPORTANT: PROVIDE ONLY YOUR WORDPRESS-FOCUSED ANALYSIS. DO NOT INCLUDE ANY PREFACING STATEMENTS OR EXPLANATIONS OF YOUR ROLE.
        """

        response = client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=2000,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": f"Analyze this WordPress code execution:\n\nCode:\n{code}\n\nExecution Result:\n{execution_result}"}
            ],
           
        )

        # Update token usage for WordPress analysis
        wordpress_analysis_tokens['input'] += response.usage.input_tokens
        wordpress_analysis_tokens['output'] += response.usage.output_tokens
        wordpress_analysis_tokens['cache_creation'] = response.usage.cache_creation_input_tokens
        wordpress_analysis_tokens['cache_read'] = response.usage.cache_read_input_tokens

        analysis = response.content[0].text

        return analysis

    except Exception as e:
        console.print(f"Error in WordPress code analysis: {str(e)}", style="bold red")
        return f"Error analyzing WordPress code: {str(e)}"

def create_wordpress_theme(theme_name):
    theme_dir = f"wp-content/themes/{theme_name}"
    create_folders(theme_dir)
    create_files(f"{theme_dir}/style.css", f"/*\nTheme Name: {theme_name}\nAuthor: AI Developer\nDescription: A custom WordPress theme\nVersion: 1.0\n*/")
    create_files(f"{theme_dir}/index.php", "<?php get_header(); ?>\n<!-- Add your theme content here -->\n<?php get_footer(); ?>")
    create_files(f"{theme_dir}/functions.php", "<?php\n// Add theme support and functions here\n")
    create_files(f"{theme_dir}/header.php", "<!DOCTYPE html>\n<html <?php language_attributes(); ?>>\n<head>\n    <meta charset=\"<?php bloginfo( 'charset' ); ?>\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n    <?php wp_head(); ?>\n</head>\n<body <?php body_class(); ?>>\n")
    create_files(f"{theme_dir}/footer.php", "    <?php wp_footer(); ?>\n</body>\n</html>")
    return f"WordPress theme '{theme_name}' structure created successfully."

def create_wordpress_plugin(plugin_name):
    plugin_dir = f"wp-content/plugins/{plugin_name}"
    create_folders(plugin_dir)
    plugin_file = f"{plugin_dir}/{plugin_name}.php"
    plugin_content = f"""<?php
/*
Plugin Name: {plugin_name}
Description: A custom WordPress plugin
Version: 1.0
Author: AI Developer
*/

// Add your plugin code here
"""
    create_files({"path": plugin_file, "content": plugin_content}) # <-- corrected call
    return f"WordPress plugin '{plugin_name}' structure created successfully."

def validate_wordpress_code(code):
    issues = []
    if "<?php" not in code:
        issues.append("Missing PHP opening tag")
    if "wp_" in code and not any(hook in code for hook in ["add_action", "add_filter"]):
        issues.append("WordPress function used without proper action/filter hook")
    if "echo" in code and "esc_html" not in code:
        issues.append("Potential unescaped output detected")
    
    if issues:
        return "Code validation issues:\n" + "\n".join(issues)
    else:
        return "Code passes basic WordPress validation."
    
    
# WordPress Database Operations
def wp_db_query(query: str, database_config: dict) -> List[Dict]:
    """Execute WordPress database queries safely"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(**database_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        return []

def backup_wp_database(backup_path: str, database_config: dict) -> bool:
    """Create a backup of WordPress database"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_path}/wp_backup_{timestamp}.sql"
        command = f"mysqldump -h {database_config['host']} -u {database_config['user']} -p{database_config['password']} {database_config['database']} > {backup_file}"
        subprocess.run(command, shell=True, check=True)
        return True
    except Exception as e:
        logging.error(f"Backup error: {str(e)}")
        return False

# Theme Customization
def customize_theme(theme_path: str, customizations: Dict[str, Any]) -> bool:
    """Apply customizations to WordPress theme"""
    try:
        # Update theme styles
        style_path = os.path.join(theme_path, 'style.css')
        with open(style_path, 'a') as f:
            for selector, properties in customizations.items():
                f.write(f"\n{selector} {{\n")
                for prop, value in properties.items():
                    f.write(f"    {prop}: {value};\n")
                f.write("}\n")
        return True
    except Exception as e:
        logging.error(f"Theme customization error: {str(e)}")
        return False

# Plugin Management
def manage_plugins(wp_path: str, action: str, plugin_name: str) -> bool:
    """Manage WordPress plugins using WP-CLI"""
    try:
        valid_actions = ['install', 'activate', 'deactivate', 'delete']
        if action not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of {valid_actions}")
        
        command = f"wp plugin {action} {plugin_name}"
        result = subprocess.run(command, shell=True, cwd=wp_path, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Plugin management error: {str(e)}")
        return False

# Security Tools
def security_scan(wp_path: str) -> Dict[str, Any]:
    """Perform security scan on WordPress installation"""
    security_issues = {
        'file_permissions': [],
        'vulnerable_plugins': [],
        'core_integrity': [],
        'security_headers': []
    }
    
    try:
        # Check file permissions
        critical_files = ['wp-config.php', '.htaccess']
        for file in critical_files:
            file_path = os.path.join(wp_path, file)
            if os.path.exists(file_path):
                perms = oct(os.stat(file_path).st_mode)[-3:]
                if perms not in ['400', '440']:
                    security_issues['file_permissions'].append(f"{file}: {perms}")
        
        # Check WordPress core integrity
        result = subprocess.run(['wp', 'core', 'verify-checksums'], 
                              cwd=wp_path, capture_output=True, text=True)
        if result.returncode != 0:
            security_issues['core_integrity'].append(result.stderr)
        
        return security_issues
    except Exception as e:
        logging.error(f"Security scan error: {str(e)}")
        return security_issues

# Performance Optimization
def optimize_performance(wp_path: str) -> Dict[str, Any]:
    """Optimize WordPress performance"""
    optimization_results = {
        'cache_enabled': False,
        'media_optimized': False,
        'db_optimized': False
    }
    
    try:
        # Enable caching
        cache_command = "wp plugin install wp-super-cache --activate"
        result = subprocess.run(cache_command, shell=True, cwd=wp_path)
        optimization_results['cache_enabled'] = result.returncode == 0
        
        # Optimize database
        db_command = "wp db optimize"
        result = subprocess.run(db_command, shell=True, cwd=wp_path)
        optimization_results['db_optimized'] = result.returncode == 0
        
        return optimization_results
    except Exception as e:
        logging.error(f"Performance optimization error: {str(e)}")
        return optimization_results

# Custom Post Type Management
def register_custom_post_type(wp_path: str, post_type: str, options: Dict[str, Any]) -> bool:
    """Register a new custom post type"""
    try:
        template = f"""
<?php
function create_custom_post_type_{post_type}() {{
    register_post_type('{post_type}',
        array(
            'labels' => array(
                'name' => __('{options.get("name", post_type)}'),
                'singular_name' => __('{options.get("singular_name", post_type)}')
            ),
            'public' => {str(options.get("public", True)).lower()},
            'has_archive' => {str(options.get("has_archive", True)).lower()},
            'supports' => {options.get("supports", ["title", "editor", "thumbnail"])}
        )
    );
}}
add_action('init', 'create_custom_post_type_{post_type}');
?>
"""
        # Write to functions.php
        functions_path = os.path.join(wp_path, 'wp-content/themes/active-theme/functions.php')
        with open(functions_path, 'a') as f:
            f.write(template)
        return True
    except Exception as e:
        logging.error(f"Custom post type creation error: {str(e)}")
        return False

# Media Management
def optimize_media(wp_path: str, image_path: str) -> bool:
    """Optimize WordPress media files"""
    try:
        from PIL import Image
        
        # Open and optimize image
        img = Image.open(image_path)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        # Save optimized image
        optimized_path = image_path.rsplit('.', 1)[0] + '_optimized.' + image_path.rsplit('.', 1)[1]
        img.save(optimized_path, quality=85, optimize=True)
        
        return True
    except Exception as e:
        logging.error(f"Media optimization error: {str(e)}")
        return False
    
def create_block_theme(theme_name: str, options: Dict[str, Any] = None) -> bool:
    """Create a modern block-based WordPress theme"""
    try:
        # Set default options if none provided
        if options is None:
            options = {
                "version": 2,
                "settings": {
                    "layout": {
                        "contentSize": "840px",
                        "wideSize": "1100px"
                    }
                }
            }
        
        # Create theme directory
        theme_path = os.path.join("wp-content/themes", theme_name)
        os.makedirs(theme_path, exist_ok=True)
        
        # Create theme.json for Full Site Editing support
        with open(os.path.join(theme_path, "theme.json"), "w") as f:
            json.dump(options, f, indent=4)
            
        # Create essential theme files
        with open(os.path.join(theme_path, "style.css"), "w") as f:
            f.write(f"""/*
Theme Name: {theme_name}
Theme URI: 
Author: WordPress Engineer
Description: A modern block-based WordPress theme
Version: 1.0
License: GNU General Public License v2 or later
License URI: http://www.gnu.org/licenses/gpl-2.0.html
Text Domain: {theme_name.lower()}
*/""")
            
        # Create templates directory for block patterns
        os.makedirs(os.path.join(theme_path, "templates"), exist_ok=True)
        os.makedirs(os.path.join(theme_path, "parts"), exist_ok=True)
        
        return True
    except Exception as e:
        logging.error(f"Error creating block theme: {str(e)}")
        return False
    
def setup_woocommerce_integration(theme_path: str, features: List[str]) -> bool:
    """Add WooCommerce support to a theme"""
    try:
        # Create WooCommerce template directory
        woo_dir = os.path.join(theme_path, "woocommerce")
        os.makedirs(woo_dir, exist_ok=True)
        
        # Add WooCommerce support to functions.php
        functions_file = os.path.join(theme_path, "functions.php")
        woo_support = """
// WooCommerce Support
function theme_add_woocommerce_support() {
    add_theme_support('woocommerce');
"""
        
        # Add requested features
        if "product-gallery" in features:
            woo_support += "    add_theme_support('wc-product-gallery-zoom');\n"
            woo_support += "    add_theme_support('wc-product-gallery-lightbox');\n"
            woo_support += "    add_theme_support('wc-product-gallery-slider');\n"
            
        if "checkout" in features:
            # Create custom checkout template
            checkout_dir = os.path.join(woo_dir, "checkout")
            os.makedirs(checkout_dir, exist_ok=True)
            
        if "cart" in features:
            # Create custom cart template
            cart_dir = os.path.join(woo_dir, "cart")
            os.makedirs(cart_dir, exist_ok=True)
            
        woo_support += "}\nadd_action('after_setup_theme', 'theme_add_woocommerce_support');\n"
        
        # Append or create functions.php
        with open(functions_file, "a") as f:
            f.write(woo_support)
            
        return True
    except Exception as e:
        logging.error(f"Error setting up WooCommerce: {str(e)}")
        return False

def setup_custom_endpoints(plugin_path: str, endpoints: Dict[str, Any]) -> bool:
    """Create custom WordPress REST API endpoints"""
    try:
        # Create the main plugin file if it doesn't exist
        plugin_file = os.path.join(plugin_path, "custom-endpoints.php")
        
        endpoint_code = """<?php
/*
Plugin Name: Custom REST API Endpoints
Description: Adds custom REST API endpoints
Version: 1.0
Author: WordPress Engineer
*/

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

function register_custom_endpoints() {
"""
        
        # Add each endpoint
        for endpoint, config in endpoints.items():
            route = config.get('route', f'/custom/v1/{endpoint}')
            methods = config.get('methods', ['GET'])
            callback = config.get('callback', 'get_items')
            
            endpoint_code += f"""
    register_rest_route('custom/v1', '{route}', array(
        'methods' => array({', '.join([f"'{m}'" for m in methods])}),
        'callback' => '{callback}',
        'permission_callback' => function () {{
            return current_user_can('edit_posts');
        }}
    ));"""
            
        endpoint_code += """
}
add_action('rest_api_init', 'register_custom_endpoints');
"""
        
        # Write the plugin file
        with open(plugin_file, "w") as f:
            f.write(endpoint_code)
            
        return True
    except Exception as e:
        logging.error(f"Error setting up endpoints: {str(e)}")
        return False

import subprocess
import tempfile
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import php
import logging
from typing import Dict, Any, Optional, Tuple, List

class PHPExecutor:
    def __init__(self, wordpress_root: str = '/var/www/html'):
        self.wordpress_root = wordpress_root
        self.php_executable = self._find_php_executable()
        
    async def execute_php(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute PHP code with WordPress context"""
        try:
            # Create temporary PHP file with WordPress bootstrap
            temp_file = self._create_temp_php_file(code, context)
            
            # Execute PHP with proper WordPress environment
            process = await asyncio.create_subprocess_exec(
                self.php_executable,
                temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.wordpress_root
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'output': stdout.decode('utf-8'),
                'error': stderr.decode('utf-8'),
                'exit_code': process.returncode
            }
        except Exception as e:
            return {
                'output': '',
                'error': str(e),
                'exit_code': -1
            }
        finally:
            # Clean up temporary file
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.unlink(temp_file)

    def _create_temp_php_file(self, code, context):
        """Creates a temporary PHP file with the provided code and context."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as temp_file:
            if context and context.get('wordpress_context', False):
                bootstrap = f"""<?php
                define('WP_DEBUG', true);
                require_once('{self.wordpress_root}/wp-load.php');
                """
                temp_file.write(bootstrap)
            temp_file.write(code)
        return temp_file.name

    def _find_php_executable(self) -> str:
        """Find the PHP executable path."""
        try:
            # Try to find PHP in common locations
            php_locations = [
                'php',  # System PATH
                '/usr/bin/php',
                '/usr/local/bin/php',
                'C:\\xampp\\php\\php.exe',  # Default XAMPP location
                'C:\\wamp\\bin\\php\\php7.4.9\\php.exe',  # Default WAMP location
                'C:\\php\\php.exe',
                # Add more potential XAMPP locations
                'D:\\xampp\\php\\php.exe',
                'E:\\xampp\\php\\php.exe'
            ]
            
            # Check if XAMPP_PATH environment variable is set
            xampp_path = os.environ.get('XAMPP_PATH')
            if xampp_path:
                php_locations.insert(0, os.path.join(xampp_path, 'php', 'php.exe'))
            
            for location in php_locations:
                try:
                    result = subprocess.run([location, '--version'], capture_output=True, text=True)
                    if result.returncode == 0:
                        logging.info(f"PHP found at: {location}")
                        return location
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            
            # If we didn't find PHP in the default locations, try to find all drives and check for XAMPP
            if sys.platform == "win32":
                import string
                for drive in string.ascii_uppercase:
                    xampp_php = f"{drive}:\\xampp\\php\\php.exe"
                    if os.path.exists(xampp_php):
                        try:
                            result = subprocess.run([xampp_php, '--version'], capture_output=True, text=True)
                            if result.returncode == 0:
                                logging.info(f"PHP found at: {xampp_php}")
                                return xampp_php
                        except (subprocess.SubprocessError, FileNotFoundError):
                            continue
                    
            # Allow user to manually specify PHP path if we couldn't find it automatically
            console.print("PHP executable not found in common locations.")
            php_path = Prompt.ask("Please enter the full path to your PHP executable (e.g., C:\\xampp\\php\\php.exe)")
            
            if os.path.exists(php_path):
                try:
                    result = subprocess.run([php_path, '--version'], capture_output=True, text=True)
                    if result.returncode == 0:
                        logging.info(f"PHP found at user-specified path: {php_path}")
                        return php_path
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
            
            raise RuntimeError("PHP executable not found")
        except Exception as e:
            logging.error(f"Error finding PHP executable: {str(e)}")
            raise

class BrowserAutomation:
    """Handles browser automation for WordPress testing and interaction."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        
    async def initialize(self) -> None:
        """Initialize the browser driver."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
        except Exception as e:
            logging.error(f"Error initializing browser: {str(e)}")
            raise
            
    async def close(self) -> None:
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.error(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None
                
    async def test_wordpress_page(self, url: str, test_type: str = 'basic') -> Dict[str, Any]:
        """Test a WordPress page or functionality."""
        if not self.driver:
            await self.initialize()
            
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            results = {
                'url': url,
                'title': self.driver.title,
                'status': 'success',
                'tests': {}
            }
            
            if test_type == 'basic':
                # Basic page load test
                results['tests']['page_load'] = {
                    'status': 'success',
                    'time': self.driver.execute_script('return performance.timing.loadEventEnd - performance.timing.navigationStart;')
                }
                
            elif test_type == 'responsive':
                # Test different viewport sizes
                viewports = [(1920, 1080), (1366, 768), (768, 1024), (375, 812)]
                results['tests']['responsive'] = {}
                
                for width, height in viewports:
                    self.driver.set_window_size(width, height)
                    # Check for horizontal overflow
                    has_overflow = self.driver.execute_script(
                        'return document.documentElement.scrollWidth > document.documentElement.clientWidth'
                    )
                    results['tests']['responsive'][f'{width}x{height}'] = {
                        'status': 'fail' if has_overflow else 'success',
                        'has_overflow': has_overflow
                    }
                    
            elif test_type == 'performance':
                # Collect performance metrics
                performance_metrics = self.driver.execute_script("""
                    return {
                        timing: performance.timing.toJSON(),
                        memory: performance.memory ? performance.memory.toJSON() : null,
                        navigation: performance.navigation.toJSON()
                    }
                """)
                results['tests']['performance'] = performance_metrics
                
            return results
            
        except TimeoutException:
            return {
                'url': url,
                'status': 'error',
                'error': 'Page load timeout'
            }
        except WebDriverException as e:
            return {
                'url': url,
                'status': 'error',
                'error': str(e)
            }
        finally:
            await self.close()

# Add these new tools to the existing tools list
new_tools = [
    {
        "name": "execute_php",
        "description": "Execute PHP code with optional WordPress context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "PHP code to execute"
                },
                "context": {
                    "type": "object",
                    "description": "Execution context settings",
                    "properties": {
                        "wordpress_context": {
                            "type": "boolean",
                            "description": "Whether to include WordPress bootstrap"
                        }
                    }
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "test_wordpress_page",
        "description": "Test a WordPress page or functionality using browser automation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the WordPress page to test"
                },
                "test_type": {
                    "type": "string",
                    "description": "Type of test to perform (basic, responsive, or performance)",
                    "enum": ["basic", "responsive", "performance"]
                }
            },
            "required": ["url"]
        }
    }
]
tools.extend(new_tools)
# Initialize the PHP and Browser handlers
php_executor = PHPExecutor()
browser_automation = BrowserAutomation()

# Add these functions to handle the new tools
async def handle_execute_php(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Handle PHP code execution requests."""
    try:
        code = tool_input['code']
        context = tool_input.get('context', {})
        return await php_executor.execute_php(code, context)
    except Exception as e:
        logging.error(f"Error in PHP execution: {str(e)}")
        return {
            'output': '',
            'error': str(e),
            'exit_code': -1
        }

async def handle_test_wordpress_page(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Handle WordPress page testing requests."""
    try:
        url = tool_input['url']
        test_type = tool_input.get('test_type', 'basic')
        return await browser_automation.test_wordpress_page(url, test_type)
    except Exception as e:
        logging.error(f"Error in WordPress page testing: {str(e)}")
        return {
            'url': tool_input['url'],
            'status': 'error',
            'error': str(e)
        }

import mysql.connector
from mysql.connector import pooling
import logging
from typing import Optional, Dict, List, Any, Union
from contextlib import contextmanager
import json
import os
from datetime import datetime
import asyncio

class WordPressDBManager:
    """
    Manages database connections and operations for WordPress installations.
    Implements connection pooling and provides common WordPress database operations.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the database manager with configuration.
        
        Args:
            config: Dictionary containing database configuration:
                - host: Database host
                - user: Database username
                - password: Database password
                - database: Database name
                - pool_name: Name for the connection pool
                - pool_size: Size of the connection pool
        """
        self.config = {
            'host': config.get('host', 'localhost'),
            'user': config.get('user', 'root'),
            'password': config.get('password', ''),
            'database': config.get('database', 'wordpress'),
            'pool_name': config.get('pool_name', 'wordpress_pool'),
            'pool_size': config.get('pool_size', 5)
        }
        
        try:
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=self.config['pool_name'],
                pool_size=self.config['pool_size'],
                **{k: v for k, v in self.config.items() if k not in ['pool_name', 'pool_size']}
            )
            logging.info(f"Database pool initialized with {self.config['pool_size']} connections")
        except mysql.connector.Error as e:
            logging.error(f"Error initializing database pool: {str(e)}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections from the pool.
        Automatically handles connection acquisition and release.
        """
        conn = None
        try:
            conn = self.pool.get_connection()
            yield conn
        except mysql.connector.Error as e:
            logging.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    async def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute SQL query with proper async handling"""
        return await asyncio.to_thread(self._execute_query_sync, query, params)
    
    def _execute_query_sync(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Synchronous implementation of execute_query"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return results
            except mysql.connector.Error as e:
                logging.error(f"Query execution error: {str(e)}")
                raise
            finally:
                cursor.close()

    async def backup_database(self, backup_path: str) -> str:
        """
        Create a backup of the WordPress database.
        
        Args:
            backup_path: Directory to store the backup
            
        Returns:
            Path to the backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_path, f"wp_backup_{timestamp}.sql")
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            # Build mysqldump command
            command = (
                f"mysqldump -h {self.config['host']} -u {self.config['user']} "
                f"-p{self.config['password']} {self.config['database']} > {backup_file}"
            )
            
            # Execute mysqldump
            result = await asyncio.create_subprocess_shell(
                command,
                shell=True,
                check=True
            )
            if result.returncode != 0:
                raise Exception("Database backup failed")
                
            logging.info(f"Database backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logging.error(f"Backup error: {str(e)}")
            raise

    async def get_wp_options(self) -> Dict[str, Any]:
        """
        Retrieve WordPress options from wp_options table.
        
        Returns:
            Dictionary of WordPress options
        """
        query = "SELECT option_name, option_value FROM wp_options"
        results = await self.execute_query(query)
        return {row['option_name']: row['option_value'] for row in results}

    async def update_wp_option(self, option_name: str, option_value: str) -> bool:
        """
        Update a WordPress option in wp_options table.
        
        Args:
            option_name: Name of the option to update
            option_value: New value for the option
            
        Returns:
            True if successful, False otherwise
        """
        query = """
            INSERT INTO wp_options (option_name, option_value, autoload)
            VALUES (%s, %s, 'yes')
            ON DUPLICATE KEY UPDATE
            option_value = VALUES(option_value)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                await cursor.execute(query, (option_name, option_value))
                conn.commit()
                return True
        except mysql.connector.Error as e:
            logging.error(f"Error updating option {option_name}: {str(e)}")
            return False

    async def get_post_meta(self, post_id: int) -> Dict[str, Any]:
        """
        Retrieve post metadata for a specific post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            Dictionary of post metadata
        """
        query = "SELECT meta_key, meta_value FROM wp_postmeta WHERE post_id = %s"
        results = await self.execute_query(query, (post_id,))
        return {row['meta_key']: row['meta_value'] for row in results}

    async def optimize_tables(self) -> List[Dict[str, Any]]:
        """
        Optimize all WordPress database tables.
        
        Returns:
            List of optimization results for each table
        """
        results = []
        tables_query = "SHOW TABLES"
        tables = await self.execute_query(tables_query)
        
        for table in tables:
            table_name = list(table.values())[0]
            try:
                optimize_query = f"OPTIMIZE TABLE {table_name}"
                result = await self.execute_query(optimize_query)
                results.append({
                    'table': table_name,
                    'result': result[0] if result else None
                })
            except mysql.connector.Error as e:
                results.append({
                    'table': table_name,
                    'error': str(e)
                })
        
        return results

    async def repair_tables(self) -> List[Dict[str, Any]]:
        """
        Repair WordPress database tables that might be corrupted.
        
        Returns:
            List of repair results for each table
        """
        results = []
        tables_query = "SHOW TABLES"
        tables = await self.execute_query(tables_query)
        
        for table in tables:
            table_name = list(table.values())[0]
            try:
                repair_query = f"REPAIR TABLE {table_name}"
                result = await self.execute_query(repair_query)
                results.append({
                    'table': table_name,
                    'result': result[0] if result else None
                })
            except mysql.connector.Error as e:
                results.append({
                    'table': table_name,
                    'error': str(e)
                })
        
        return results

    async def get_table_status(self) -> List[Dict[str, Any]]:
        """
        Get status information for all WordPress database tables.
        
        Returns:
            List of table status information
        """
        query = "SHOW TABLE STATUS"
        return await self.execute_query(query)

    async def close(self):
        """
        Close the database connection pool.
        """
        if hasattr(self, 'pool'):
            self.pool._remove_connections()
            logging.info("Database connection pool closed")

import subprocess
import os
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class WordPressConfig:
    path: str
    url: str
    title: str
    admin_user: str
    admin_password: str
    admin_email: str
    db_name: str
    db_user: str
    db_password: str
    locale: str = "en_US"
    version: Optional[str] = None

class WordPressInstaller:
    def __init__(self, config: WordPressConfig):
        self.config = config
        
    async def run_wp_cli(self, command: str) -> Tuple[bool, str]:
        """Execute a WP-CLI command and return success status and output."""
        try:
            result = await asyncio.create_subprocess_shell(
                f"wp {command}",
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=self.config.path if os.path.exists(self.config.path) else None
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            logging.error(f"WP-CLI command failed: {e.stderr}")
            return False, e.stderr

    async def download_wordpress(self) -> Dict[str, Any]:
        """Step 1: Download WordPress core files."""
        command = f"core download"
        if self.config.locale != "en_US":
            command += f" --locale={self.config.locale}"
        if self.config.version:
            command += f" --version={self.config.version}"
            
        success, output = await self.run_wp_cli(command)
        return {"success": success, "message": output}

    async def create_config(self) -> Dict[str, Any]:
        """Step 2: Generate wp-config.php file."""
        command = (f"config create --dbname={self.config.db_name} "
                  f"--dbuser={self.config.db_user} "
                  f"--dbpass={self.config.db_password}")
        
        success, output = await self.run_wp_cli(command)
        return {"success": success, "message": output}

    async def create_database(self) -> Dict[str, Any]:
        """Step 3: Create WordPress database."""
        success, output = await self.run_wp_cli("db create")
        return {"success": success, "message": output}

    async def install_wordpress(self) -> Dict[str, Any]:
        """Step 4: Run WordPress installation."""
        command = (f"core install --url={self.config.url} "
                  f"--title=\"{self.config.title}\" "
                  f"--admin_user={self.config.admin_user} "
                  f"--admin_password={self.config.admin_password} "
                  f"--admin_email={self.config.admin_email}")
        
        success, output = await self.run_wp_cli(command)
        return {"success": success, "message": output}

    async def install(self) -> Dict[str, Any]:
        """Run complete WordPress installation process."""
        steps = [
            (self.download_wordpress, "Downloading WordPress"),
            (self.create_config, "Creating configuration file"),
            (self.create_database, "Creating database"),
            (self.install_wordpress, "Installing WordPress")
        ]

        results = []
        for step_func, step_name in steps:
            result = await step_func()
            results.append({
                "step": step_name,
                "success": result["success"],
                "message": result["message"]
            })
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed during {step_name}",
                    "details": results
                }

        return {
            "success": True,
            "message": "WordPress installation completed successfully",
            "details": results
        }

async def install_wordpress_site(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to install WordPress with dictionary configuration."""
    try:
        config = WordPressConfig(**config_dict)
        installer = WordPressInstaller(config)
        return await installer.install()
    except Exception as e:
        logging.error(f"WordPress installation error: {str(e)}")
        return {
            "success": False,
            "message": f"Installation failed: {str(e)}",
            "details": []
        }

async def decide_retry(tool_checker_response, edit_results, tool_input):
    try:
        if not edit_results:
            console.print(Panel("No edits were made or an error occurred. Skipping retry.", title="Info", style="bold yellow"))
            return {"retry": False, "files_to_retry": []}

        response = client.messages.create(
            model=TOOLCHECKERMODEL,
            max_tokens=1000,
            system="""You are an AI assistant tasked with deciding whether to retry editing files based on the previous edit results and the AI's response. Respond with a JSON object containing 'retry' (boolean) and 'files_to_retry' (list of file paths).

Example of the expected JSON response:
{
    "retry": true,
    "files_to_retry": ["/path/to/file1.py", "/path/to/file2.py"]
}

Only return the JSON object, nothing else. Ensure that the JSON is properly formatted with double quotes around property names and string values.""",
            messages=[
                {"role": "user", "content": f"Previous edit results: {json.dumps(edit_results)}\n\nAI's response: {tool_checker_response}\n\nDecide whether to retry editing any files."}
            ]
        )
        
        response_text = response.content[0].text.strip()
        
        # Handle list of dicts if necessary
        if isinstance(response_text, list):
            response_text = ' '.join(
                item['text'] if isinstance(item, dict) and 'text' in item else str(item)
                for item in response_text
            )
        elif not isinstance(response_text, str):
            response_text = str(response_text)
        
        try:
            decision = json.loads(response_text)
        except json.JSONDecodeError:
            console.print(Panel("Failed to parse JSON from AI response. Using fallback decision.", title="Warning", style="bold yellow"))
            decision = {
                "retry": "retry" in response_text.lower(),
                "files_to_retry": []
            }
        
        files = tool_input.get('files', [])
        if isinstance(files, dict):
            files = [files]
        elif not isinstance(files, list):
            console.print(Panel("Error: 'files' must be a dictionary or a list of dictionaries.", title="Error", style="bold red"))
            return {"retry": False, "files_to_retry": []}
        
        if not all(isinstance(item, dict) for item in files):
            console.print(Panel("Error: Each file must be a dictionary with 'path' and 'instructions'.", title="Error", style="bold red"))
            return {"retry": False, "files_to_retry": []}
        
        valid_file_paths = set(file['path'] for file in files)
        files_to_retry = [
            file_path for file_path in decision.get("files_to_retry", [])
            if file_path in valid_file_paths
        ]
        
        retry_decision = {
            "retry": decision.get("retry", False),
            "files_to_retry": files_to_retry
        }
        
        console.print(Panel(f"Retry decision: {json.dumps(retry_decision, indent=2)}", title="Retry Decision", style="bold cyan"))
        return retry_decision

    except Exception as e:
        console.print(Panel(f"Error in decide_retry: {str(e)}", title="Error", style="bold red"))
        return {"retry": False, "files_to_retry": []}

def handle_analyze_wordpress_code(tool_input):
    """
    Analyzes WordPress code for issues, security vulnerabilities, and best practices.
    """
    try:
        code_to_analyze = tool_input.get("code", "")
        file_path = tool_input.get("file_path", "")
        
        if not code_to_analyze:
            return {
                "status": "error",
                "message": "No code provided for analysis"
            }
        
        analysis_results = {
            "security_issues": [],
            "performance_issues": [],
            "best_practices": [],
            "compatibility_issues": [],
            "code_quality": []
        }
        
        # Security Analysis
        security_patterns = {
            r'\$_GET\[.*?\](?!\s*\))': "Potentially unsanitized GET input",
            r'\$_POST\[.*?\](?!\s*\))': "Potentially unsanitized POST input",
            r'\$_REQUEST\[.*?\](?!\s*\))': "Potentially unsanitized REQUEST input",
            r'eval\s*\(': "Use of eval() function (security risk)",
            r'base64_decode\s*\(': "Possible obfuscated code",
            r'mysql_connect\s*\(': "Deprecated MySQL function",
            r'mysql_query\s*\(': "Deprecated MySQL function",
            r'<\?php\s*echo\s+\$[^;]+;': "Potentially unescaped output"
        }
        
        for pattern, issue in security_patterns.items():
            if re.search(pattern, code_to_analyze, re.IGNORECASE):
                analysis_results["security_issues"].append(issue)
        
        # WordPress Best Practices
        best_practice_checks = {
            r'wp_enqueue_script\s*\(': "✓ Using wp_enqueue_script for scripts",
            r'wp_enqueue_style\s*\(': "✓ Using wp_enqueue_style for styles",
            r'add_action\s*\(': "✓ Using WordPress hooks",
            r'esc_html\s*\(': "✓ Using output escaping",
            r'sanitize_text_field\s*\(': "✓ Using input sanitization",
            r'wp_nonce_field\s*\(': "✓ Using nonce for security"
        }
        
        for pattern, practice in best_practice_checks.items():
            if re.search(pattern, code_to_analyze, re.IGNORECASE):
                analysis_results["best_practices"].append(practice)
        
        # Performance Issues
        performance_patterns = {
            r'WP_Query\s*\([^)]*posts_per_page[^)]*-1': "Potentially unlimited query results",
            r'get_posts\s*\([^)]*numberposts[^)]*-1': "Potentially unlimited post retrieval",
            r'SELECT\s+\*\s+FROM': "Using SELECT * in queries",
            r'wp_query\s*\([^)]*meta_query': "Complex meta queries (consider caching)"
        }
        
        for pattern, issue in performance_patterns.items():
            if re.search(pattern, code_to_analyze, re.IGNORECASE):
                analysis_results["performance_issues"].append(issue)
        
        # Code Quality
        if not re.search(r'^\s*<\?php', code_to_analyze, re.MULTILINE):
            analysis_results["code_quality"].append("Missing PHP opening tag")
        
        if re.search(r'\?\>\s*$', code_to_analyze):
            analysis_results["code_quality"].append("Unnecessary PHP closing tag in included file")
        
        # Calculate overall score
        total_issues = sum(len(issues) for key, issues in analysis_results.items() 
                          if key != "best_practices")
        total_good_practices = len(analysis_results["best_practices"])
        
        if total_issues == 0 and total_good_practices > 0:
            score = "Excellent"
        elif total_issues <= 2:
            score = "Good"
        elif total_issues <= 5:
            score = "Fair"
        else:
            score = "Needs Improvement"
        
        return {
            "status": "success",
            "score": score,
            "file_path": file_path,
            "analysis": analysis_results,
            "summary": f"Found {total_issues} potential issues and {total_good_practices} good practices"
        }
        
    except Exception as e:
        logging.error(f"Error analyzing WordPress code: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def handle_analyze_database_queries(tool_input):
    """
    Analyzes database queries for performance and security issues.
    """
    try:
        query = tool_input.get("query", "")
        
        if not query:
            return {
                "status": "error",
                "message": "No query provided for analysis"
            }
        
        analysis_results = {
            "performance_issues": [],
            "security_issues": [],
            "recommendations": [],
            "query_type": "",
            "estimated_complexity": ""
        }
        
        # Determine query type
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            analysis_results["query_type"] = "SELECT"
        elif query_upper.startswith('INSERT'):
            analysis_results["query_type"] = "INSERT"
        elif query_upper.startswith('UPDATE'):
            analysis_results["query_type"] = "UPDATE"
        elif query_upper.startswith('DELETE'):
            analysis_results["query_type"] = "DELETE"
        else:
            analysis_results["query_type"] = "OTHER"
        
        # Performance Analysis
        performance_patterns = {
            r'SELECT\s+\*': "Using SELECT * - specify only needed columns",
            r'ORDER\s+BY.*RAND\(\)': "ORDER BY RAND() is slow on large tables",
            r'LIKE\s+[\'"]%.*%[\'"]': "LIKE with leading wildcard prevents index usage",
            r'!=|<>': "Using != or <> - consider alternatives",
            r'OR': "OR conditions can prevent index usage",
            r'LIMIT\s+\d+\s*,\s*\d+': "Consider using OFFSET for better performance"
        }
        
        for pattern, issue in performance_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                analysis_results["performance_issues"].append(issue)
        
        # Security Analysis
        security_patterns = {
            r'\$[a-zA-Z_][a-zA-Z0-9_]*': "Possible variable injection - use prepared statements",
            r'[\'"][^\'\"]*\$[^\'\"]*[\'"]': "String concatenation with variables",
            r'UNION': "UNION statements - verify against SQL injection",
            r'--': "SQL comments detected - verify legitimacy"
        }
        
        for pattern, issue in security_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                analysis_results["security_issues"].append(issue)
        
        # Generate recommendations
        if 'wp_' in query:
            analysis_results["recommendations"].append("✓ Using WordPress table prefixes")
        
        if re.search(r'LIMIT\s+\d+', query, re.IGNORECASE):
            analysis_results["recommendations"].append("✓ Query has LIMIT clause")
        
        if re.search(r'WHERE', query, re.IGNORECASE):
            analysis_results["recommendations"].append("✓ Query uses WHERE clause")
        
        # Estimate complexity
        complexity_indicators = len(re.findall(r'JOIN|UNION|SUBQUERY|\(SELECT', query, re.IGNORECASE))
        if complexity_indicators == 0:
            analysis_results["estimated_complexity"] = "Simple"
        elif complexity_indicators <= 2:
            analysis_results["estimated_complexity"] = "Moderate"
        else:
            analysis_results["estimated_complexity"] = "Complex"
        
        total_issues = len(analysis_results["performance_issues"]) + len(analysis_results["security_issues"])
        
        return {
            "status": "success",
            "query": query,
            "analysis": analysis_results,
            "total_issues": total_issues,
            "summary": f"Query analysis complete: {total_issues} issues found"
        }
        
    except Exception as e:
        logging.error(f"Error analyzing database queries: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = None
        is_error = False
        console_output = None

        if tool_name == "create_files":
            if isinstance(tool_input, dict) and 'files' in tool_input:
                files = tool_input['files']
            else:
                files = tool_input
            result = create_files(files)
        elif tool_name == "edit_and_apply_multiple":
            files = tool_input.get("files")
            if not files:
                result = "Error: 'files' key is missing or empty."
                is_error = True
            else:
                # Ensure 'files' is a list of dictionaries
                if isinstance(files, str):
                    try:
                        # Attempt to parse the JSON string
                        files = json.loads(files)
                        if isinstance(files, dict):
                            files = [files]
                        elif isinstance(files, list):
                            if not all(isinstance(file, dict) for file in files):
                                result = "Error: Each file must be a dictionary with 'path' and 'instructions'."
                                is_error = True
                    except json.JSONDecodeError:
                        result = "Error: 'files' must be a dictionary or a list of dictionaries, and should not be a string."
                        is_error = True
                elif isinstance(files, dict):
                    files = [files]
                elif isinstance(files, list):
                    if not all(isinstance(file, dict) for file in files):
                        result = "Error: Each file must be a dictionary with 'path' and 'instructions'."
                        is_error = True
                else:
                    result = "Error: 'files' must be a dictionary or a list of dictionaries."
                    is_error = True

                if not is_error:
                    # Validate the structure of 'files'
                    try:
                        files = validate_files_structure(files)
                    except ValueError as ve:
                        result = f"Error: {str(ve)}"
                        is_error = True

            if not is_error:
                result, console_output = await edit_and_apply_multiple(files, tool_input["project_context"], is_automode=automode)
        elif tool_name == "create_folders":
            result = create_folders(tool_input["paths"])
        elif tool_name == "read_multiple_files":
            paths = tool_input.get("paths")
            recursive = tool_input.get("recursive", False)
            if paths is None:
                result = "Error: No file paths provided"
                is_error = True
            else:
                files_to_read = [p for p in (paths if isinstance(paths, list) else [paths]) if p not in file_contents]
                if not files_to_read:
                    result = "All requested files are already in the system prompt. No need to read from disk."
                else:
                    result = read_multiple_files(files_to_read, recursive)
        elif tool_name == "list_files":
            result = list_files(tool_input.get("path", "."))
        elif tool_name == "tavily_search":
            result = tavily_search(tool_input["query"])
        elif tool_name == "stop_process":
            result = stop_process(tool_input["process_id"])
        elif tool_name == "execute_code":
            process_id, execution_result = await execute_code(tool_input["code"])
            if execution_result.startswith("Process started and running"):
                analysis = "The process is still running in the background."
            else:
                analysis_task = asyncio.create_task(send_to_ai_for_analysis(tool_input["code"], execution_result))
                analysis = await analysis_task
            result = f"{execution_result}\n\nAnalysis:\n{analysis}"
            if process_id in running_processes:
                result += "\n\nNote: The process is still running in the background."
        elif tool_name == "scan_folder":
            result = scan_folder(tool_input["folder_path"], tool_input["output_file"])
        elif tool_name == "run_shell_command":
            result = run_shell_command(tool_input["command"])    
        elif tool_name == "wp_db_query":
            # This tool seems to be handled by 'execute_wp_query' via handle_wp_db_tools later
            # If it's distinct, it needs its own handler. Assuming it's covered by the db_tools section.
            # For now, let's assume it will be caught by the expanded DB section or needs to be removed if redundant.
            pass  # Placeholder, will be handled by expanded DB section if names match
        elif tool_name == "backup_wp_database":
            result = backup_wp_database(tool_input['backup_path'], tool_input['database_config'])
        elif tool_name == "manage_theme_customizer":
            result = manage_theme_customizer(
                tool_input['theme_path'], 
                tool_input.get('settings', []), 
                tool_input.get('controls', []), 
                tool_input.get('sections', []), 
                tool_input.get('actions', [])
            )
        elif tool_name == "manage_plugins": # This is a duplicate of an earlier manage_plugins, check original file structure
            result = manage_plugins(tool_input['wp_path'], tool_input['action'], tool_input['plugin_name'])
        elif tool_name == "security_scan":
            result = security_scan(tool_input['wp_path'])
        elif tool_name == "optimize_wordpress_performance": # MODIFIED tool name
            result = optimize_performance(tool_input['site_path']) # MODIFIED parameter
        elif tool_name == "register_custom_post_type":
            result = register_custom_post_type(tool_input['wp_path'], tool_input['post_type'], tool_input['options'])
        elif tool_name == "optimize_media":
            result = optimize_media(tool_input['wp_path'], tool_input['image_path'])
        elif tool_name == "create_wordpress_theme":
            result = create_wordpress_theme(tool_input["theme_name"])
        elif tool_name == "create_wordpress_plugin":
            result = create_wordpress_plugin(tool_input["plugin_name"])
        elif tool_name == "validate_wordpress_code":
            result = validate_wordpress_code(tool_input["code"])        
        elif tool_name == "analyze_wordpress_code":
            result = handle_analyze_wordpress_code(tool_input) # Ensure this handler is defined
        elif tool_name == "analyze_database_queries":
            result = handle_analyze_database_queries(tool_input) # Ensure this handler is defined
        elif tool_name == "create_block_theme":
            result = create_block_theme(tool_input["theme_name"], tool_input.get("options"))
        elif tool_name == "configure_caching":
            result = configure_caching(tool_input["caching_plugin"], tool_input["cache_settings"])
        elif tool_name == "integrate_external_api":
            result = integrate_external_api(tool_input["api_url"], tool_input["parameters"], tool_input["authentication_method"])
        elif tool_name == "manage_code_snippets":
            result = manage_code_snippets(tool_input["code_snippet"], tool_input["short_description"], tool_input["action"])
        elif tool_name == "rag_search":
            result = await handle_rag_search(tool_input)
        elif tool_name == "rag_add_document":
            result = await handle_rag_add_document(tool_input)
        elif tool_name == "rag_add_code_snippet":
            result = await handle_rag_add_code_snippet(tool_input)
        elif tool_name == "rag_add_wp_function":
            result = await handle_rag_add_wp_function(tool_input)
        elif tool_name == "rag_add_wp_hook":
            result = await handle_rag_add_wp_hook(tool_input)
        elif tool_name == "rag_get_statistics":
            result = await handle_rag_get_statistics(tool_input)
        elif tool_name == "rag_import_wp_documentation":
            result = await handle_rag_import_wp_documentation(tool_input)
        elif tool_name == "rag_export_database":
            result = await handle_rag_export_database(tool_input)
        elif tool_name == "rag_backup_database":
            result = await handle_rag_backup_database(tool_input)
            result = handle_analyze_wordpress_code(tool_input) # Ensure this handler is defined
        elif tool_name == "analyze_database_queries":
            result = handle_analyze_database_queries(tool_input) # Ensure this handler is defined
        elif tool_name == "create_block_theme":
            result = create_block_theme(tool_input["theme_name"], tool_input.get("options"))
        elif tool_name == "configure_caching":
            result = configure_caching(tool_input["caching_plugin"], tool_input["cache_settings"])
        elif tool_name == "integrate_external_api":
            result = integrate_external_api(tool_input["api_url"], tool_input["parameters"], tool_input["authentication_method"])
        elif tool_name == "manage_code_snippets":
            result = manage_code_snippets(tool_input["code_snippet"], tool_input["short_description"], tool_input["action"])
        elif tool_name == "init_wp_database":
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "execute_wp_query":
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "backup_wp_db": # Distinct from backup_wp_database
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "get_wp_options":
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "update_wp_option":
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "get_post_meta":
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "optimize_wp_tables":
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "repair_wp_tables":
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "get_table_status":
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "test_wordpress_page":
            result = await handle_test_wordpress_page(tool_input)    
        elif tool_name == "install_wordpress":
            result = await install_wordpress_site(tool_input) # MODIFIED: added await
        elif tool_name == "execute_php": # MODIFIED: was 'if', now 'elif'
            result = await handle_execute_php(tool_input)
        # Inside execute_tool function
        elif tool_name in ["init_wp_database", "execute_wp_query", "backup_wp_db", 
                        "get_wp_options", "update_wp_option", "get_post_meta",
                        "optimize_wp_tables", "repair_wp_tables", "get_table_status"]:
            return await handle_wp_db_tools(tool_name, tool_input, db_manager)
        elif tool_name == "install_wordpress":
            result = await install_wordpress_site(tool_input) # MODIFIED: added await
        elif tool_name == "execute_php": # MODIFIED: was 'if', now 'elif'
            result = await handle_execute_php(tool_input)
            return {
                "content": result,
                "is_error": bool(result.get('error')),
                "console_output": result.get('output', '')
            }
        elif tool_name == "test_wordpress_page":
            result = await handle_test_wordpress_page(tool_input)
            return {
                "content": result,
                "is_error": result.get('status') == 'error',
                "console_output": json.dumps(result, indent=2)
            }
        else:
            is_error = True
            result = f"Unknown tool: {tool_name}"

        return {
            "content": result,
            "is_error": is_error,
            "console_output": console_output
        }
    except KeyError as e:
        logging.error(f"Missing required parameter {str(e)} for tool {tool_name}")
        return {
            "content": f"Error: Missing required parameter {str(e)} for tool {tool_name}",
            "is_error": True,
            "console_output": None
        }
    except Exception as e:
        logging.error(f"Error executing tool {tool_name}: {str(e)}")
        return {
            "content": f"Error executing tool {tool_name}: {str(e)}",
            "is_error": True,
            "console_output": None
        }

# Add these new tools to the tools list
db_tools = [
    {
        "name": "init_wp_database",
        "description": "Initialize WordPress database connection pool",
        "input_schema": {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "Database host"
                },
                "user": {
                    "type": "string",
                    "description": "Database username"
                },
                "password": {
                    "type": "string",
                    "description": "Database password"
                },
                "database": {
                    "type": "string",
                    "description": "Database name"
                },
                "pool_name": {
                    "type": "string",
                    "description": "Name for the connection pool"
                },
                "pool_size": {
                    "type": "integer",
                    "description": "Size of the connection pool"
                }
            },
            "required": ["host", "user", "password", "database"]
        }
    },
    {
        "name": "execute_wp_query",
        "description": "Execute a WordPress database query",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                },
                "params": {
                    "type": "array",
                    "description": "Query parameters",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "backup_wp_db",
        "description": "Create a backup of WordPress database",
        "input_schema": {
            "type": "object",
            "properties": {
                "backup_path": {
                    "type": "string",
                    "description": "Directory to store the backup"
                }
            },
            "required": ["backup_path"]
        }
    },
    {
        "name": "get_wp_options",
        "description": "Retrieve WordPress options from wp_options table",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "update_wp_option",
        "description": "Update a WordPress option in wp_options table",
        "input_schema": {
            "type": "object",
            "properties": {
                "option_name": {
                    "type": "string",
                    "description": "Name of the option to update"
                },
                "option_value": {
                    "type": "string",
                    "description": "New value for the option"
                }
            },
            "required": ["option_name", "option_value"]
        }
    },
    {
        "name": "get_post_meta",
        "description": "Retrieve post metadata for a specific post",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "integer",
                    "description": "ID of the post"
                }
            },
            "required": ["post_id"]
        }
    },
    {
        "name": "optimize_wp_tables",
        "description": "Optimize all WordPress database tables",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "repair_wp_tables",
        "description": "Repair WordPress database tables that might be corrupted",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_table_status",
        "description": "Get status information for all WordPress database tables",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
]
tools.extend(db_tools)
# Add these tool handlers to the execute_tool function
async def handle_wp_db_tools(tool_name: str, tool_input: Dict[str, Any], db_manager: WordPressDBManager) -> Dict[str, Any]:
    """Handle WordPress database tool requests."""
    try:
        if tool_name == "init_wp_database":
            db_manager = WordPressDBManager(tool_input)
            return {
                "content": "Database connection pool initialized successfully",
                "is_error": False
            }
            
        elif tool_name == "execute_wp_query":
            results = db_manager.execute_query(
                tool_input["query"],
                tuple(tool_input.get("params", []))
            )
            return {
                "content": results,
                "is_error": False
            }
            
        elif tool_name == "backup_wp_db":
            backup_file = db_manager.backup_database(tool_input["backup_path"])
            return {
                "content": f"Database backed up to: {backup_file}",
                "is_error": False
            }
            
        elif tool_name == "get_wp_options":
            options = db_manager.get_wp_options()
            return {
                "content": options,
                "is_error": False
            }
            
        elif tool_name == "update_wp_option":
            success = db_manager.update_wp_option(
                tool_input["option_name"],
                tool_input["option_value"]
            )
            return {
                "content": "Option updated successfully" if success else "Failed to update option",
                "is_error": not success
            }
            
        elif tool_name == "get_post_meta":
            meta = db_manager.get_post_meta(tool_input["post_id"])
            return {
                "content": meta,
                "is_error": False
            }
            
        elif tool_name == "optimize_wp_tables":
            results = db_manager.optimize_tables()
            return {
                "content": results,
                "is_error": False
            }
            
        elif tool_name == "repair_wp_tables":
            results = db_manager.repair_tables()
            return {
                "content": results,
                "is_error": False
            }
            
        elif tool_name == "get_table_status":
            status = db_manager.get_table_status()
            return {
                "content": status,
                "is_error": False
            }
            
    except Exception as e:
        logging.error(f"Database tool error: {str(e)}")
        return {
            "content": f"Error executing database tool: {str(e)}",
            "is_error": True
        }

async def chat_with_mike(user_input, image_path=None, current_iteration=None, max_iterations=None):
    global conversation_history, automode, main_model_tokens, use_tts, tts_enabled

    # Input validation
    if not isinstance(user_input, str):
        raise ValueError("user_input must be a string")
    if image_path is not None and not isinstance(image_path, str):
        raise ValueError("image_path must be a string or None")
    if current_iteration is not None and not isinstance(current_iteration, int):
        raise ValueError("current_iteration must be an integer or None")
    if max_iterations is not None and not isinstance(max_iterations, int):
        raise ValueError("max_iterations must be an integer or None")

    current_conversation = []

    if image_path:
        console.print(Panel(f"Processing image at path: {image_path}", title_align="left", title="Image Processing", expand=False, style="yellow"))
        image_base64 = encode_image_to_base64(image_path)

        if image_base64.startswith("Error"):
            console.print(Panel(f"Error encoding image: {image_base64}", title="Error", style="bold red"))
            return "I'm sorry, there was an error processing the image. Please try again.", False

        image_message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": f"User input for image: {user_input}"
                }
            ]
        }
        current_conversation.append(image_message)
        console.print(Panel("Image message added to conversation history", title_align="left", title="Image Added", style="green"))
    else:
        current_conversation.append({"role": "user", "content": user_input})

    # Filter conversation history to maintain context
    filtered_conversation_history = []
    for message in conversation_history:
        if isinstance(message['content'], list):
            filtered_content = [
                content for content in message['content']
                if content.get('type') != 'tool_result' or (
                    content.get('type') == 'tool_result' and
                    not any(keyword in content.get('output', '') for keyword in [
                        "File contents updated in system prompt",
                        "File created and added to system prompt",
                        "has been read and stored in the system prompt"
                    ])
                )
            ]
            if filtered_content:
                filtered_conversation_history.append({**message, 'content': filtered_content})
        else:
            filtered_conversation_history.append(message)

    # Combine filtered history with current conversation to maintain context
    messages = filtered_conversation_history + current_conversation

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            # MAINMODEL call with prompt caching
            response = client.messages.create(
                model=MAINMODEL,
                max_tokens=8000,
                system=[
                    {
                        "type": "text",
                        "text": update_system_prompt(current_iteration, max_iterations),
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": json.dumps(tools),
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=messages,
                tools=tools,
                tool_choice={"type": "auto"},
                extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
            )
            # Update token usage for MAINMODEL
            main_model_tokens['input'] += response.usage.input_tokens
            main_model_tokens['output'] += response.usage.output_tokens
            main_model_tokens['cache_write'] = response.usage.cache_creation_input_tokens
            main_model_tokens['cache_read'] = response.usage.cache_read_input_tokens
            break  # If successful, break out of the retry loop
        except APIStatusError as e:
            if e.status_code == 429 and attempt < max_retries - 1:
                console.print(Panel(f"Rate limit exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})", title="API Error", style="bold yellow"))
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                console.print(Panel(f"API Error: {str(e)}", title="API Error", style="bold red"))
                return "I'm sorry, there was an error communicating with the AI. Please try again.", False
        except APIError as e:
            console.print(Panel(f"API Error: {str(e)}", title="API Error", style="bold red"))
            return "I'm sorry, there was an error communicating with the AI. Please try again.", False
    else:
        console.print(Panel("Max retries reached. Unable to communicate with the AI.", title="Error", style="bold red"))
        return "I'm sorry, there was a persistent error communicating with the AI. Please try again later.", False

    assistant_response = ""
    exit_continuation = False
    tool_uses = []

    for content_block in response.content:
        if content_block.type == "text":
            assistant_response += content_block.text
            if CONTINUATION_EXIT_PHRASE in content_block.text:
                exit_continuation = True
        elif content_block.type == "tool_use":
            tool_uses.append(content_block)

    console.print(Panel(Markdown(assistant_response), title="Mike's Response", title_align="left", border_style="blue", expand=False))
    
    if tts_enabled and use_tts:
        await text_to_speech(assistant_response)

    # Display files in context
    if file_contents:
        files_in_context = "\n".join(file_contents.keys())
    else:
        files_in_context = "No files in context. Read, create, or edit files to add."
    console.print(Panel(files_in_context, title="Files in Context", title_align="left", border_style="white", expand=False))

    for tool_use in tool_uses:
        tool_name = tool_use.name
        tool_input = tool_use.input
        tool_use_id = tool_use.id

        console.print(Panel(f"Tool Used: {tool_name}", style="green"))
        console.print(Panel(f"Tool Input: {json.dumps(tool_input, indent=2)}", style="green"))

        # Always use execute_tool for all tools
        tool_result = await execute_tool(tool_name, tool_input)

        if isinstance(tool_result, dict) and tool_result.get("is_error"):
            console.print(Panel(tool_result["content"], title="Tool Execution Error", style="bold red"))
            edit_results = []  # Assign empty list due to error
        else:
            # Assuming tool_result["content"] is a list of results
            edit_results = tool_result.get("content", [])

        # Prepare the tool_result_content for conversation history
        tool_result_content = {
            "type": "text",
            "text": json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)
        }

        current_conversation.append({
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": tool_use_id,
                    "name": tool_name,
                    "input": tool_input
                }
            ]
        })

        current_conversation.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": [tool_result_content],
                    "is_error": tool_result.get("is_error", False) if isinstance(tool_result, dict) else False
                }
            ]
        })

        # Update the file_contents dictionary if applicable
        if tool_name in ['create_files', 'edit_and_apply_multiple', 'read_multiple_files'] and not (isinstance(tool_result, dict) and tool_result.get("is_error")):
            if tool_name == 'create_files':
                for file in tool_input['files']:
                    if "File created and added to system prompt" in str(tool_result):
                        file_contents[file['path']] = file['content']
            elif tool_name == 'edit_and_apply_multiple':
                edit_results = tool_result if isinstance(tool_result, list) else [tool_result]
                for result in edit_results:
                    if isinstance(result, dict) and result.get("status") in ["success", "partial_success"]:
                        file_contents[result["path"]] = result.get("edited_content", file_contents.get(result["path"], ""))
            elif tool_name == 'read_multiple_files':
                # The file_contents dictionary is already updated in the read_multiple_files function
                pass

        messages = filtered_conversation_history + current_conversation

        try:
            tool_response = client.messages.create(
                model=TOOLCHECKERMODEL,
                max_tokens=8000,
                system=update_system_prompt(current_iteration, max_iterations),
                extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"},
                messages=messages,
                tools=tools,
                tool_choice={"type": "auto"}
            )
            # Update token usage for tool checker
            tool_checker_tokens['input'] += tool_response.usage.input_tokens
            tool_checker_tokens['output'] += tool_response.usage.output_tokens

            tool_checker_response = ""
            for tool_content_block in tool_response.content:
                if tool_content_block.type == "text":
                    tool_checker_response += tool_content_block.text
            console.print(Panel(Markdown(tool_checker_response), title="Mike's Response to Tool Result",  title_align="left", border_style="blue", expand=False))
            if use_tts:
                await text_to_speech(tool_checker_response)
            assistant_response += "\n\n" + tool_checker_response

            # If the tool was edit_and_apply_multiple, let the AI decide whether to retry
            if tool_name == 'edit_and_apply_multiple':
                retry_decision = await decide_retry(tool_checker_response, edit_results, tool_input)
                if retry_decision["retry"] and retry_decision['files_to_retry']:
                    console.print(Panel(f"AI has decided to retry editing for files: {', '.join(retry_decision['files_to_retry'])}", style="yellow"))
                    retry_files = [
                        file for file in tool_input['files'] 
                        if file['path'] in retry_decision['files_to_retry']
                    ]
                    
                    # Ensure 'instructions' are present
                    for file in retry_files:
                        if 'instructions' not in file:
                            file['instructions'] = "Please reapply the previous instructions."
                    
                    if retry_files:
                        retry_result, retry_console_output = await edit_and_apply_multiple(retry_files, tool_input['project_context'])
                        console.print(Panel(retry_console_output, title="Retry Result", style="cyan"))
                        assistant_response += f"\n\nRetry result: {json.dumps(retry_result, indent=2)}"
                    else:
                        console.print(Panel("No files to retry. Skipping retry.", style="yellow"))
                else:
                    console.print(Panel("Mike has decided not to retry editing", style="green"))

        except APIError as e:
            error_message = f"Error in tool response: {str(e)}"
            console.print(Panel(error_message, title="Error", style="bold red"))
            assistant_response += f"\n\n{error_message}"

    if assistant_response:
        current_conversation.append({"role": "assistant", "content": assistant_response})

    conversation_history = messages + [{"role": "assistant", "content": assistant_response}]

    # Display token usage at the end
    display_token_usage()

    return assistant_response, exit_continuation

def reset_code_editor_memory():
    global code_editor_memory
    code_editor_memory = []
    console.print(Panel("Code editor memory has been reset.", title="Reset", style="bold green"))


def reset_conversation():
    global conversation_history, main_model_tokens, tool_checker_tokens, code_editor_tokens, code_execution_tokens, file_contents, code_editor_files
    conversation_history = []
    main_model_tokens = {'input': 0, 'output': 0}
    tool_checker_tokens = {'input': 0, 'output': 0}
    code_editor_tokens = {'input': 0, 'output': 0}
    code_execution_tokens = {'input': 0, 'output': 0}
    file_contents = {}
    code_editor_files = set()
    reset_code_editor_memory()
    console.print(Panel("Conversation history, token counts, file contents, code editor memory, and code editor files have been reset.", title="Reset", style="bold green"))
    display_token_usage()

def display_token_usage():
    from rich.table import Table
    from rich.panel import Panel
    from rich.box import ROUNDED

    table = Table(box=ROUNDED)
    table.add_column("Model", style="cyan")
    table.add_column("Input", style="magenta")
    table.add_column("Output", style="magenta")
    table.add_column("Cache Write", style="blue")
    table.add_column("Cache Read", style="blue")
    table.add_column("Total", style="green")
    table.add_column(f"% of Context ({MAX_CONTEXT_TOKENS:,})", style="yellow")
    table.add_column("Cost ($)", style="red")

    model_costs = {
        "Main Model": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30, "has_context": True},
        "Tool Checker": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30, "has_context": False},
        "Code Editor": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30, "has_context": True},
        "Code Execution": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30, "has_context": False}
        
    }

    total_input = 0
    total_output = 0
    total_cache_write = 0
    total_cache_read = 0
    total_cost = 0
    total_context_tokens = 0

    for model, tokens in [("Main Model", main_model_tokens),
                          ("Tool Checker", tool_checker_tokens),
                          ("Code Editor", code_editor_tokens),
                          ("Code Execution", code_execution_tokens)]:
        input_tokens = tokens['input']
        output_tokens = tokens['output']
        cache_write_tokens = tokens['cache_write']
        cache_read_tokens = tokens['cache_read']
        total_tokens = input_tokens + output_tokens + cache_write_tokens + cache_read_tokens

        total_input += input_tokens
        total_output += output_tokens
        total_cache_write += cache_write_tokens
        total_cache_read += cache_read_tokens

        input_cost = (input_tokens / 1_000_000) * model_costs[model]["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs[model]["output"]
        cache_write_cost = (cache_write_tokens / 1_000_000) * model_costs[model]["cache_write"]
        cache_read_cost = (cache_read_tokens / 1_000_000) * model_costs[model]["cache_read"]
        model_cost = input_cost + output_cost + cache_write_cost + cache_read_cost
        total_cost += model_cost

        if model_costs[model]["has_context"]:
            total_context_tokens += total_tokens
            percentage = (total_tokens / MAX_CONTEXT_TOKENS) * 100
        else:
            percentage = 0

        table.add_row(
            model,
            f"{input_tokens:,}",
            f"{output_tokens:,}",
            f"{cache_write_tokens:,}",
            f"{cache_read_tokens:,}",
            f"{total_tokens:,}",
            f"{percentage:.2f}%" if model_costs[model]["has_context"] else "Doesn't save context",
            f"${model_cost:.3f}"
        )

    grand_total = total_input + total_output + total_cache_write + total_cache_read
    total_percentage = (total_context_tokens / MAX_CONTEXT_TOKENS) * 100

    table.add_row(
        "Total",
        f"{total_input:,}",
        f"{total_output:,}",
        f"{total_cache_write:,}",
        f"{total_cache_read:,}",
        f"{grand_total:,}",
        f"{total_percentage:.2f}%",
        f"${total_cost:.3f}",
        style="bold"
    )

    console.print(table)

async def test_voice_mode():
    global voice_mode
    voice_mode = True
    initialize_speech_recognition()
    console.print(Panel("Entering voice input test mode. Say a few phrases, then say 'exit voice mode' to end the test.", style="bold green"))
    
    while voice_mode:
        user_input = await voice_input()
        if user_input is None:
            voice_mode = False
            cleanup_speech_recognition()
            console.print(Panel("Exited voice input test mode due to error.", style="bold yellow"))
            break
        
        stay_in_voice_mode, command_result = process_voice_command(user_input)
        if not stay_in_voice_mode:
            voice_mode = False
            cleanup_speech_recognition()
            console.print(Panel("Exited voice input test mode.", style="bold green"))
            break
        elif command_result:
            console.print(Panel(command_result, style="cyan"))
    
    console.print(Panel("Voice input test completed.", style="bold green"))

import psutil
import statistics
from contextlib import contextmanager

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'response_times': [],
            'memory_usage': [],
            'database_queries': [],
            'cache_hit_rate': 0
        }
    
    @contextmanager
    def measure_performance(self, operation: str):
        """Context manager for performance measurement"""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss
            
            self.metrics['response_times'].append({
                'operation': operation,
                'duration': end_time - start_time,
                'timestamp': datetime.now()
            })
            
            self.metrics['memory_usage'].append({
                'operation': operation,
                'memory_used': end_memory - start_memory,
                'timestamp': datetime.now()
            })
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance analysis report"""
        return {
            'avg_response_time': statistics.mean([m['duration'] for m in self.metrics['response_times']]),
            'memory_efficiency': self._calculate_memory_efficiency(),
            'bottlenecks': self._identify_bottlenecks(),
            'recommendations': self._generate_recommendations()
        }

    def _calculate_memory_efficiency(self):
        # Placeholder
        return "N/A"

    def _identify_bottlenecks(self):
        # Placeholder
        return []

    def _generate_recommendations(self):
        # Placeholder
        return []

class SecurityValidator:
    def __init__(self):
        self.sanitizers = {
            'text': self._sanitize_text,
            'html': self._sanitize_html,
            'sql': self._sanitize_sql,
            'file_path': self._sanitize_file_path,
            'url': self._sanitize_url
        }
    
    def validate_input(self, data: Any, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive input validation"""
        errors = []
        sanitized_data = {}
        
        for field, value in data.items():
            if field in validation_rules:
                rule = validation_rules[field]
                
                # Type validation
                if not self._validate_type(value, rule.get('type')):
                    errors.append(f"Invalid type for {field}")
                    continue
                
                # Sanitization
                sanitized_value = self._sanitize_value(value, rule.get('sanitize', 'text'))
                
                # Custom validation
                if 'validator' in rule:
                    if not rule['validator'](sanitized_value):
                        errors.append(f"Validation failed for {field}")
                        continue
                
                sanitized_data[field] = sanitized_value
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': sanitized_data
        }

    def _sanitize_text(self, value):
        return str(value)

    def _sanitize_html(self, value):
        # Basic sanitization, consider a more robust library for production
        return re.sub(r'<script.*?>.*?</script>', '', value, flags=re.IGNORECASE)

    def _sanitize_sql(self, value):
        # This is a placeholder. Use prepared statements instead of sanitizing.
        return value

    def _sanitize_file_path(self, value):
        return os.path.normpath(value)

    def _sanitize_url(self, value):
        # Basic URL sanitization
        return value

    def _validate_type(self, value, expected_type):
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'integer':
            return isinstance(value, int)
        # Add more type validations as needed
        return True

    def _sanitize_value(self, value, sanitize_type):
        return self.sanitizers.get(sanitize_type, self._sanitize_text)(value)

async def main():
    global automode, conversation_history, use_tts, tts_enabled, php_executor, php_available
    console.print(Panel("Welcome to the Claude 4 WordPress Engineer Chat with Multi-Agent, Image, Voice, and Text-to-Speech Support!", title="Welcome", style="bold green"))
    
    # General commands section
    console.print(Panel("General Commands:", style="bold blue"))
    console.print("Type 'exit' to end the conversation")
    console.print("Type 'reset' to clear the conversation history")
    console.print("Type 'save chat' to save the conversation to a Markdown file")
    
    # Input/output options section
    console.print(Panel("Input/Output Options:", style="bold cyan"))
    console.print("Type 'image' to include an image in your message")
    console.print("Type 'voice' to enter voice input mode")
    console.print("Type 'test voice' to run a voice input test")
    console.print("Type '11labs on' to enable text-to-speech")
    console.print("Type '11labs off' to disable text-to-speech")
    
    # WordPress specific commands section
    console.print(Panel("WordPress Features:", style="bold green"))
    console.print("Type 'wp create theme [name]' to create a new WordPress theme structure")
    console.print("Type 'wp create plugin [name]' to create a new WordPress plugin structure")
    console.print("Type 'wp create block [name]' to scaffold a new Gutenberg block")
    console.print("Type 'wp validate [path]' to validate WordPress code against standards")
    # RAG database commands section
    console.print(Panel("Knowledge Database:", style="bold magenta"))
    console.print("Type 'rag status' to view WordPress knowledge database statistics")
    console.print("Type 'rag search [query]' to search the WordPress knowledge database")
    console.print("Type 'rag backup [path]' to back up the WordPress knowledge database")
    console.print("Type 'rag export [path]' to export the WordPress knowledge database content")
    
    # Automation section
    console.print(Panel("Automation:", style="bold yellow"))
    console.print("Type 'automode [number]' to enter Autonomous mode with a specific number of iterations")
    console.print("While in automode, press Ctrl+C at any time to exit the automode to return to regular chat")
    console.print("Type 'automode off' to exit Autonomous mode")
    
    # Initialize RAG database
    initialize_rag_database()
     # Initialize PHP executor (if PHP is available)
    global php_executor, php_available
    try:
        php_executor = PHPExecutor()
        php_available = True
    except RuntimeError:
        console.print(Panel("PHP executable not found. PHP-related features will be disabled.", title="Warning", style="bold yellow"))
        php_available = False

    # Also initialize browser automation only if needed
    global browser_automation
    browser_automation = BrowserAutomation()

    voice_mode = False

    while True:
        if voice_mode:
            user_input = await voice_input()
            if user_input is None:
                voice_mode = False
                cleanup_speech_recognition()
                console.print(Panel("Exited voice input mode due to error. Returning to text input.", style="bold yellow"))
                continue
            
            stay_in_voice_mode, command_result = process_voice_command(user_input)
            if not stay_in_voice_mode:
                voice_mode = False
                cleanup_speech_recognition()
                console.print(Panel("Exited voice input mode. Returning to text input.", style="bold green"))
                if command_result:
                    console.print(Panel(command_result, style="cyan"))
                continue
            elif command_result:
                console.print(Panel(command_result, style="cyan"))
                continue
        else:
            user_input = await get_user_input()

        if user_input.lower() == 'exit':
            console.print(Panel("Thank you for chatting. Goodbye!", title_align="left", title="Goodbye", style="bold green"))
            break

        if user_input.lower() == 'test voice':
            await test_voice_mode()
            continue

        if user_input.lower() == '11labs on':
            use_tts = True
            tts_enabled = True
            console.print(Panel("Text-to-speech enabled.", style="bold green"))
            continue

        if user_input.lower() == '11labs off':
            use_tts = False
            tts_enabled = False
            console.print(Panel("Text-to-speech disabled.", style="bold yellow"))
            continue

        if user_input.lower() == 'reset':
            reset_conversation()
            continue

        if user_input.lower() == 'save chat':
            filename = save_chat()
            console.print(Panel(f"Chat saved to {filename}", title="Chat Saved", style="bold green"))
            continue

        if user_input.lower() == 'voice':
            voice_mode = True
            initialize_speech_recognition()
            console.print(Panel("Entering voice input mode. Say 'exit voice mode' to return to text input.", style="bold green"))
            continue

        if user_input.lower() == 'image':
            image_path = (await get_user_input("Drag and drop your image here, then press enter: ")).strip().replace("'", "")

            if os.path.isfile(image_path):
                user_input = await get_user_input("You (prompt for image): ")
                response, _ = await chat_with_mike(user_input, image_path)
            else:
                console.print(Panel("Invalid image path. Please try again.", title="Error", style="bold red"))
                continue
        elif user_input.lower().startswith('automode'):
            try:
                parts = user_input.split()
                if len(parts) > 1 and parts[1].isdigit():
                    max_iterations = int(parts[1])
                else:
                    max_iterations = MAX_CONTINUATION_ITERATIONS

                automode = True
                console.print(Panel(f"Entering automode with {max_iterations} iterations. Please provide the goal of the automode.", title_align="left", title="Automode", style="bold yellow"))
                console.print(Panel("Press Ctrl+C at any time to exit the automode loop.", style="bold yellow"))
                user_input = await get_user_input()

                iteration_count = 0
                error_count = 0
                max_errors = 3  # Maximum number of consecutive errors before exiting automode
                try:
                    while automode and iteration_count < max_iterations:
                        try:
                            response, exit_continuation = await chat_with_mike(user_input, current_iteration=iteration_count+1, max_iterations=max_iterations)
                            error_count = 0  # Reset error count on successful iteration
                        except Exception as e:
                            console.print(Panel(f"Error in automode iteration: {str(e)}", style="bold red"))
                            error_count += 1
                            if error_count >= max_errors:
                                console.print(Panel(f"Exiting automode due to {max_errors} consecutive errors.", style="bold red"))
                                automode = False
                                break
                            continue

                        if exit_continuation or CONTINUATION_EXIT_PHRASE in response:
                            console.print(Panel("Automode completed.", title_align="left", title="Automode", style="green"))
                            automode = False
                        else:
                            console.print(Panel(f"Continuation iteration {iteration_count + 1} completed. Press Ctrl+C to exit automode. ", title_align="left", title="Automode", style="yellow"))
                            user_input = "Continue with the next step. Or STOP by saying 'AUTOMODE_COMPLETE' if you think you've achieved the results established in the original request."
                        iteration_count += 1

                        if iteration_count >= max_iterations:
                            console.print(Panel("Max iterations reached. Exiting automode.", title_align="left", title="Automode", style="bold red"))
                            automode = False
                except KeyboardInterrupt:
                    console.print(Panel("\nAutomode interrupted by user. Exiting automode.", title_align="left", title="Automode", style="bold red"))
                    automode = False
                    if conversation_history and conversation_history[-1]["role"] == "user":
                        conversation_history.append({"role": "assistant", "content": "Automode interrupted. How can I assist you further?"})
            except KeyboardInterrupt:
                console.print(Panel("\nAutomode interrupted by user. Exiting automode.", title_align="left", title="Automode", style="bold red"))
                automode = False
                if conversation_history and conversation_history[-1]["role"] == "user":
                    conversation_history.append({"role": "assistant", "content": "Automode interrupted. How can I assist you further?"})

            console.print(Panel("Exited automode. Returning to regular chat.", style="green"))
        else:
            response, _ = await chat_with_mike(user_input)



    # Add more tests for other functions as needed

if __name__ == "__main__":


    # Run the main program
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\nProgram interrupted by user. Exiting...", style="bold red")
    except Exception as e:
        console.print(f"An unexpected error occurred: {str(e)}", style="bold red")
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        console.print("Program finished. Goodbye!", style="bold green")
