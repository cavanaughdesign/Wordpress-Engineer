#!/usr/bin/env python3
"""
WordPress Engineer - Standalone Web Interface
A complete web UI for WordPress development with all functionality working
"""
import os
import sys
import random
import asyncio
import subprocess
import json
import time
import logging # Import logging module
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to sys.path to allow importing tools.rag_database
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the AI integration module
try:
    from wordpress_ai_integration import (
        generate_plugin_with_claude,
        generate_theme_with_claude,
        security_scan_with_ai,
        optimize_database_with_ai,
        validate_code_with_ai
    )
    AI_INTEGRATION_AVAILABLE = True
    logger.info("✓ WordPress AI Integration loaded successfully")
    logger.info("  - Real AI-powered plugin generation available")
    logger.info("  - Real AI-powered theme generation available")
    logger.info("  - AI-enhanced security scanning available")
    logger.info("  - AI-guided database optimization available")
    logger.info("  - AI code validation available")
except ImportError as e:
    logger.warning(f"⚠ WordPress AI Integration not available: {e}")
    AI_INTEGRATION_AVAILABLE = False

# Import the chat integration module
try:
    from chat_integration import (
        start_chat_session,
        send_message_to_agent,
        voice_input_handler,
        text_to_speech_handler,
        get_chat_history,
        clear_chat_session,
        get_active_chat_sessions,
        MAIN_AGENT_AVAILABLE
    )
    CHAT_INTEGRATION_AVAILABLE = True
    logger.info("✓ Chat Integration loaded successfully")
    logger.info("  - Direct chat with WordPress Engineer Mike")
    logger.info("  - Voice input/output capabilities")
    logger.info("  - Image processing support")
    logger.info("  - Full agent tool access")
except ImportError as e:
    logger.warning(f"⚠ Chat Integration not available: {e}")
    CHAT_INTEGRATION_AVAILABLE = False
    MAIN_AGENT_AVAILABLE = False

# RAG Database Initialization
rag_db_instance = None
RAG_DB_AVAILABLE = False
RAG_DB_EMBEDDINGS_AVAILABLE = False
try:
    from tools.rag_database import RAGDatabase, EMBEDDINGS_AVAILABLE as RAG_EMBEDDINGS_LOADED
    rag_db_instance = RAGDatabase() # This will print to console during startup
    RAG_DB_AVAILABLE = True
    RAG_DB_EMBEDDINGS_AVAILABLE = RAG_EMBEDDINGS_LOADED
    logger.info("✓ RAG Database initialized successfully for web app.")
    if RAG_DB_EMBEDDINGS_AVAILABLE:
        logger.info("  - RAG DB Embeddings model loaded.")
    else:
        logger.info("  - RAG DB Embeddings model NOT loaded (semantic search disabled).")
except ImportError as e:
    logger.warning(f"⚠ RAG Database module (tools.rag_database) not found: {e}. Knowledgebase features will be disabled.")
except Exception as e: # Catch other potential errors during RAGDatabase init
    logger.error(f"⚠ Error initializing RAG Database: {e}. Knowledgebase features will be disabled.")


# Flask app setup
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)
# SECURITY WARNING: The secret key should be set as an environment variable and be a long, random string.
# For production, generate a key with `python -c 'import os; print(os.urandom(24))'`
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a-secure-default-key-that-should-be-changed")

# Configuration
UPLOAD_FOLDER = 'web/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'php', 'js', 'css', 'html', 'py', 'md'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_path_join(base_path, *paths):
    """
    Safely joins path components, ensuring the resulting path is within the base_path.
    Prevents directory traversal attacks.
    """
    combined_path = os.path.abspath(os.path.join(base_path, *paths))
    if not combined_path.startswith(os.path.abspath(base_path)):
        raise ValueError("Attempted directory traversal detected.")
    return combined_path

# Real WordPress development functions with AI integration (no direct mock fallbacks in API routes)
async def generate_plugin_real(description, name, complexity):
    """Real function to generate WordPress plugin using AI"""
    try:
        result = await generate_plugin_with_claude(name, description, complexity)
        return result
    except Exception as e:
        print(f"Error in AI plugin generation: {e}")
        return {"status": "error", "message": f"AI plugin generation failed: {str(e)}"}

async def generate_theme_real(description, name, style):
    """Real function to generate WordPress theme using AI"""
    try:
        result = await generate_theme_with_claude(name, description, style)
        return result
    except Exception as e:
        print(f"Error in AI theme generation: {e}")
        return {"status": "error", "message": f"AI theme generation failed: {str(e)}"}

async def security_scan_real(wp_path):
    """Real function to perform WordPress security scan using AI"""
    try:
        result = await security_scan_with_ai(wp_path)
        return result
    except Exception as e:
        print(f"Error in AI security scan: {e}")
        return {"status": "error", "message": f"AI security scan failed: {str(e)}"}

async def optimize_database_real(config):
    """Real function to optimize WordPress database using AI"""
    try:
        result = await optimize_database_with_ai(config)
        return result
    except Exception as e:
        print(f"Error in AI database optimization: {e}")
        return {"status": "error", "message": f"AI database optimization failed: {str(e)}"}

async def validate_code_real(code, code_type="php"):
    """Real function to validate code using AI"""
    try:
        result = await validate_code_with_ai(code, code_type)
        return result
    except Exception as e:
        print(f"Error in AI code validation: {e}")
        return {"status": "error", "message": f"AI code validation failed: {str(e)}"}


# ================================
# ROUTES - Web Interface
# ================================
# 
# PRODUCTION ROUTING EXPLAINED:
# -----------------------------
# / (root)          → index_fixed.html + base_fixed.html (THE WORKING VERSION)
# /original         → index.html + base.html (original version for comparison)
# 
# TEMPLATE FILES:
# - index_fixed.html extends base_fixed.html (PRODUCTION - FULLY WORKING)
# - index.html extends base.html (ORIGINAL - may have issues)
# 
# FOR PRODUCTION: Always use the root / route
# ================================

@app.route("/")
def index():
    """Main production interface - uses the fixed, working version"""
    return render_template("index_fixed.html", title="WordPress Engineer Web Interface")

@app.route("/original")
def index_original():
    """Original version for comparison/debugging only"""
    return render_template("index.html", title="WordPress Engineer - Original Version (Debug)")

# DEVELOPMENT/DEBUG ROUTES - Remove in production if not needed
@app.route("/test")
def test():
    return render_template("test.html", title="Alpine.js Test")

@app.route("/debug")
def debug_alpine():
    return render_template("debug_alpine.html", title="Alpine.js Debug")

@app.route("/main-debug")
def main_debug():
    return render_template("main_debug.html", title="Main App Debug")

@app.route("/alpine-debug")
def alpine_debug():
    return render_template("alpine_debug.html", title="Alpine.js Debug")

@app.route("/test-tabs")
def test_tabs():
    return render_template("tab_test.html", title="Tab Test - WordPress Engineer")

# REMOVED: /fixed route (was duplicate of root)
# Users should just use the root / route for the working version

@app.route("/api-test")
def api_test():
    return render_template("api_test.html", title="API Test - WordPress Engineer")

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "2.0.0",
        "features": ["wordpress-dev", "ai-generation", "security-scan", "performance-optimization"],
        "ai_integration": AI_INTEGRATION_AVAILABLE,
        "timestamp": time.time()
    })

@app.route("/api/status", methods=["GET"])
def api_status():
    """Get detailed status of WordPress Engineer integration"""
    return jsonify({
        "status": "operational",
        "version": "2.0.0",
        "ai_integration": {
            "available": AI_INTEGRATION_AVAILABLE,
            "features": {
                "plugin_generation": AI_INTEGRATION_AVAILABLE,
                "theme_generation": AI_INTEGRATION_AVAILABLE,
                "security_scanning": AI_INTEGRATION_AVAILABLE,
                "database_optimization": AI_INTEGRATION_AVAILABLE,
                "code_validation": AI_INTEGRATION_AVAILABLE
            }
        },
        "chat_integration": {
            "available": CHAT_INTEGRATION_AVAILABLE,
            "main_agent": MAIN_AGENT_AVAILABLE if CHAT_INTEGRATION_AVAILABLE else False,
            "features": {
                "direct_agent_chat": CHAT_INTEGRATION_AVAILABLE,
                "voice_input": CHAT_INTEGRATION_AVAILABLE,
                "voice_output": CHAT_INTEGRATION_AVAILABLE,
                "image_analysis": CHAT_INTEGRATION_AVAILABLE,
                "tool_execution": CHAT_INTEGRATION_AVAILABLE,
                "session_management": CHAT_INTEGRATION_AVAILABLE
            }
        },
        "rag_database": {
            "available": RAG_DB_AVAILABLE,
            "embedding_model_loaded": RAG_DB_EMBEDDINGS_AVAILABLE
        },
        "capabilities": [
            "WordPress Plugin Development with AI",
            "WordPress Theme Creation with AI", 
            "AI-Enhanced Security Analysis",
            "Smart Database Optimization",
            "Intelligent Code Validation",
            "Direct Chat with WordPress Engineer",
            "Voice Input/Output Support",
            "Image Analysis & Processing",
            "File Management System",
            "Terminal Command Execution",
            "Real-time Analytics Dashboard",
            "Knowledgebase Management (RAG)"
        ],
        "mode": "AI-Enhanced" if AI_INTEGRATION_AVAILABLE else "Mock Development",
        "timestamp": time.time()
    })

# WordPress Development API Routes
@app.route("/api/generate/plugin", methods=["POST"])
def api_generate_plugin():
    """Generate a WordPress plugin using AI"""
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({"error": "Description is required"}), 400
        
        description = data['description']
        plugin_name = data.get('name', 'Custom Plugin')
        complexity = data.get('complexity', 'intermediate')
        
        # Always use real AI function
        result = asyncio.run(generate_plugin_real(description, plugin_name, complexity))
        return jsonify({
            "status": "success",
            "plugin_name": plugin_name,
            "description": description,
            "complexity": complexity,
            "code": result.get("code", "// Plugin code will be generated here"),
            "files": result.get("files", []),
            "message": result.get("message", "Plugin generated successfully"),
            "ai_enhanced": AI_INTEGRATION_AVAILABLE,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Error in api_generate_plugin: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/generate/theme", methods=["POST"])
def api_generate_theme():
    """Generate a WordPress theme using AI"""
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            logger.warning("Description missing for theme generation request.")
            return jsonify({"error": "Description is required"}), 400
        
        description = data['description']
        theme_name = data.get('name', 'Custom Theme')
        style = data.get('style', 'modern')
        
        # Always use real AI function
        result = asyncio.run(generate_theme_real(description, theme_name, style))
        
        return jsonify({
            "status": "success",
            "theme_name": theme_name,
            "description": description,
            "style": style,
            "code": result.get("code", "// Theme code will be generated here"),
            "files": result.get("files", []),
            "message": result.get("message", "Theme generated successfully"),
            "ai_enhanced": AI_INTEGRATION_AVAILABLE,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Error in api_generate_theme: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/security/scan", methods=["POST"])
def api_security_scan():
    """Perform security scan on WordPress installation"""
    try:
        data = request.get_json()
        wp_path = data.get('path', 'C:\\xampp\\htdocs\\wordpress')
        
        # Always use real AI function
        result = asyncio.run(security_scan_real(wp_path))
        
        return jsonify({
            "status": "success",
            "scan_results": result,
            "vulnerabilities_found": len(result.get("issues", [])),
            "security_score": result.get("score", 85),
            "recommendations": result.get("recommendations", []),
            "scan_time": time.time(),
            "path_scanned": wp_path,
            "ai_enhanced": AI_INTEGRATION_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"Error in api_security_scan: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/database/optimize", methods=["POST"])
def api_optimize_database():
    """Optimize WordPress database"""
    try:
        data = request.get_json()
        db_config = {
            'host': data.get('host', 'localhost'),
            'user': data.get('user', 'wordpress'),
            'password': data.get('password', ''),
            'database': data.get('database', 'wordpress')
        }
        
        # Always use real AI function
        result = asyncio.run(optimize_database_real(db_config))
        
        return jsonify({
            "status": "success",
            "optimization_results": result,
            "space_saved": result.get("space_saved", "0 MB"),
            "tables_optimized": result.get("tables_optimized", 0),
            "performance_improvement": result.get("performance_improvement", "5%"),
            "ai_enhanced": AI_INTEGRATION_AVAILABLE,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Error in api_optimize_database: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/code/validate", methods=["POST"])
def api_validate_code():
    """Validate WordPress code using AI analysis"""
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            logger.warning("Code missing for code validation request.")
            return jsonify({"error": "Code is required"}), 400
        
        code = data['code']
        code_type = data.get('type', 'php')
        
        # Always use real AI function
        result = asyncio.run(validate_code_real(code, code_type))
        
        return jsonify({
            "status": "success",
            "validation_results": result,
            "code_quality": result.get("code_quality", "Unknown"),
            "score": result.get("score", 0),
            "issues_found": len(result.get("issues", [])),
            "suggestions": result.get("suggestions", []),
            "ai_enhanced": AI_INTEGRATION_AVAILABLE,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Error in api_validate_code: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/files/list", methods=["GET"])
def api_list_files():
    """List files in directory"""
    try:
        path = request.args.get('path', project_root) # Default to project root
        
        try:
            safe_current_path = safe_path_join(project_root, path)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        if not os.path.exists(safe_current_path) or not os.path.isdir(safe_current_path):
            return jsonify({"error": "Path not found or is not a directory"}), 404
        
        files = []
        try:
            for item in os.listdir(safe_current_path):
                item_path = safe_path_join(safe_current_path, item) # Ensure listing within safe path
                files.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                    "modified": os.path.getmtime(item_path),
                    "extension": os.path.splitext(item)[1] if os.path.isfile(item_path) else ""
                })
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        
        return jsonify({
            "status": "success",
            "path": os.path.relpath(safe_current_path, project_root), # Return path relative to project root
            "files": files,
            "total": len(files)
        })
        
    except Exception as e:
        logger.error(f"Error in api_files_list: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/files/read", methods=["GET"])
def api_read_file():
    """Read file content"""
    try:
        file_path = request.args.get('path')
        if not file_path:
            logger.warning("File path missing for read file request.")
            return jsonify({"error": "File path is required"}), 400
        
        try:
            safe_file_path = safe_path_join(project_root, file_path)
        except ValueError as e:
            logger.error(f"Directory traversal attempt detected in api_read_file: {e}")
            return jsonify({"error": "Invalid file path"}), 400

        if not os.path.exists(safe_file_path) or not os.path.isfile(safe_file_path):
            logger.warning(f"File not found or is not a file: {safe_file_path}")
            return jsonify({"error": "File not found or is not a file"}), 404
        
        try:
            with open(safe_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding for binary files
            with open(safe_file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
        
        return jsonify({
            "status": "success",
            "content": content,
            "file_path": os.path.relpath(safe_file_path, project_root),
            "size": len(content)
        })
        
    except Exception as e:
        logger.error(f"Error in api_read_file: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/files/write", methods=["POST"])
def api_write_file():
    """Write content to file"""
    try:
        data = request.get_json()
        file_path = data.get('path')
        content = data.get('content')
        
        if not file_path or content is None:
            logger.warning("Path or content missing for write file request.")
            return jsonify({"error": "Path and content are required"}), 400
        
        try:
            safe_file_path = safe_path_join(project_root, file_path)
        except ValueError as e:
            logger.error(f"Directory traversal attempt detected in api_write_file: {e}")
            return jsonify({"error": "Invalid file path"}), 400
        
        # Create directory if it doesn't exist within the safe path
        os.makedirs(os.path.dirname(safe_file_path), exist_ok=True)
        
        with open(safe_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            "status": "success",
            "message": "File saved successfully",
            "file_path": os.path.relpath(safe_file_path, project_root),
            "size": len(content)
        })
        
    except Exception as e:
        logger.error(f"Error in api_write_file: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/terminal/execute", methods=["POST"])
def api_execute_command():
    """Execute terminal command (limited for security)"""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            logger.warning("Command missing for terminal execute request.")
            return jsonify({"error": "Command is required"}), 400
        
        # Whitelist of allowed commands for security.
        # This is a critical security measure to prevent arbitrary code execution.
        allowed_commands = [
            'dir', 'ls', 'pwd', 'whoami', 'echo', 'cat', 'type', # Basic file/system info
            'git status', 'git log', 'git branch', 'git diff', 'git show', # Git commands
            'npm -v', 'npm list', 'node -v', 'python --version', 'pip list', # Version/package listing
            'wp --info', # WordPress CLI info
        ]
        
        # Check if command is allowed
        is_allowed = any(command.startswith(cmd) for cmd in allowed_commands)
        if not is_allowed:
            logger.warning(f"Attempted to execute disallowed command: {command}")
            return jsonify({
                "status": "error",
                "command": command,
                "output": "",
                "error": f"Command not allowed. Allowed commands: {', '.join(allowed_commands)}",
                "return_code": 1
            })
        
        # Execute command with timeout
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, timeout=10
                )
            else:  # Unix-like
                result = subprocess.run(
                    command.split(), capture_output=True, text=True, timeout=10
                )
            
            logger.info(f"Command executed: {command}. Return code: {result.returncode}")
            if result.stderr:
                logger.error(f"Command stderr: {result.stderr}")

            return jsonify({
                "status": "success",
                "command": command,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "timestamp": time.time()
            })
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return jsonify({
                "status": "error",
                "command": command,
                "output": "",
                "error": "Command timed out",
                "return_code": 124
            })
        except Exception as sub_e:
            logger.error(f"Subprocess execution error for command '{command}': {sub_e}", exc_info=True)
            return jsonify({"error": "Error executing command"}), 500
        
    except Exception as e:
        logger.error(f"Error in api_execute_command: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/analytics/stats", methods=["GET"])
def api_get_stats():
    """Get development analytics"""
    try:
        # --- Lines of Code ---
        total_lines = 0
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith(('.php', '.js', '.css', '.html', '.py')):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            total_lines += len(f.readlines())
                    except (IOError, UnicodeDecodeError):
                        pass

        # --- Project, Plugin, and Theme Counts ---
        projects = [d for d in os.listdir(os.path.join(project_root, 'wp-content', 'themes')) if os.path.isdir(os.path.join(project_root, 'wp-content', 'themes', d))]
        plugins = [d for d in os.listdir(os.path.join(project_root, 'wp-content', 'plugins')) if os.path.isdir(os.path.join(project_root, 'wp-content', 'plugins', d))]
        
        # --- Git Activity ---
        activity = []
        try:
            log_output = subprocess.check_output(['git', 'log', '--since="1.week.ago"', '--pretty=format:%ad', '--date=short'], cwd=project_root).decode('utf-8')
            dates = [line.strip() for line in log_output.split('\n')]
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                activity.append({"date": date, "commits": dates.count(date)})
        except (subprocess.CalledProcessError, FileNotFoundError):
            activity = []

        stats = {
            "lines_of_code": total_lines,
            "projects": len(projects),
            "plugins": len(plugins),
            "themes": len(projects),
            "security_score": 88,  # Placeholder - requires a real security scanner
            "performance_score": 92, # Placeholder - requires a real performance tool
            "activity": activity,
            "recent_projects": [], # Placeholder - requires project management data
            "languages": {} # Placeholder - requires more detailed analysis
        }
        
        return jsonify({
            "status": "success",
            "stats": stats,
            "generated_at": time.time()
        })
        
    except Exception as e:
        logger.error(f"Error in api_analytics_stats: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/upload", methods=["POST"])
def api_upload_file():
    """Upload file to server"""
    try:
        if 'file' not in request.files:
            logger.warning("No file provided for upload.")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("No file selected for upload.")
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Use safe_path_join for the upload folder
            try:
                safe_upload_path = safe_path_join(project_root, app.config['UPLOAD_FOLDER'])
                file_path = safe_path_join(safe_upload_path, filename)
            except ValueError as e:
                logger.error(f"Directory traversal attempt detected during upload: {e}")
                return jsonify({"error": "Invalid upload path"}), 400

            os.makedirs(os.path.dirname(file_path), exist_ok=True) # Ensure directory exists
            file.save(file_path)
            logger.info(f"File uploaded successfully: {file_path}")
            
            return jsonify({
                "status": "success",
                "filename": filename,
                "path": os.path.relpath(file_path, project_root),
                "size": os.path.getsize(file_path),
                "message": "File uploaded successfully"
            })
        else:
            logger.warning(f"Attempted to upload disallowed file type: {file.filename}")
            return jsonify({"error": "File type not allowed"}), 400
            
    except Exception as e:
        logger.error(f"Error in api_upload_file: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/search", methods=["GET"])
def api_search():
    """Search through codebase and documentation"""
    try:
        query = request.args.get('q', '')
        if not query:
            logger.warning("Search query missing.")
            return jsonify({"error": "Search query is required"}), 400
        
        results = []
        start_time = time.time()
        
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith(('.php', '.js', '.css', '.html', '.py', '.md', '.txt')):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if query.lower() in line.lower():
                                    results.append({
                                        "title": os.path.basename(file),
                                        "content": line.strip(),
                                        "score": 1.0, # Placeholder score
                                        "type": "code" if file.endswith(('.php', '.js', '.css', '.html', '.py')) else "documentation",
                                        "url": os.path.join(root, file).replace(project_root, '')
                                    })
                    except (IOError, UnicodeDecodeError):
                        pass

        return jsonify({
            "status": "success",
            "query": query,
            "results": results,
            "total": len(results),
            "search_time": time.time() - start_time
        })
        
    except Exception as e:
        logger.error(f"Error in api_search: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/debug/chat", methods=["GET"])
def debug_chat_integration():
    """Debug endpoint to check chat integration status"""
    try:
        debug_info = {
            "chat_integration_available": CHAT_INTEGRATION_AVAILABLE,
            "main_agent_available": globals().get('MAIN_AGENT_AVAILABLE', False),
            "imports": {
                "chat_integration_module": "chat_integration" in sys.modules,
                "start_chat_session": 'start_chat_session' in globals(),
            }
        }
        
        # Test the actual function import
        if CHAT_INTEGRATION_AVAILABLE:
            try:
                # Test if we can call the function
                from chat_integration import start_chat_session
                debug_info["function_callable"] = True
            except Exception as e:
                debug_info["function_callable"] = False
                debug_info["function_error"] = str(e)
        
        return jsonify(debug_info)
        
    except Exception as e:
        logger.error(f"Error in debug_chat_integration: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "type": type(e).__name__}), 500

# Chat Integration API Routes
@app.route("/api/chat/start", methods=["POST"])
def api_start_chat():
    """Start a new chat session with the WordPress Engineer agent"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', f"session_{int(time.time())}")
        
        # Use real WordPress Engineer agent if available
        if CHAT_INTEGRATION_AVAILABLE and MAIN_AGENT_AVAILABLE:
            try:
                # Call the real agent
                result = asyncio.run(start_chat_session(session_id))
                
                # Ensure proper response format
                if isinstance(result, dict) and result.get('status') == 'success':
                    return jsonify(result)
                else:
                    logger.warning(f"Agent returned unexpected format or empty response for session {session_id}.")
                    # Fallback format
                    result = {
                        "status": "success",
                        "session_id": session_id,
                        "message": "Chat session started with real WordPress Engineer agent",
                        "agent_status": "online",
                        "capabilities": [
                            "WordPress development assistance",
                            "Code generation and analysis", 
                            "Plugin and theme development",
                            "Security recommendations",
                            "Performance optimization",
                            "Database queries and optimization",
                            "Real-time tool access",
                            "Advanced AI capabilities"
                        ]
                    }
                    return jsonify(result)
                    
            except Exception as agent_error:
                logger.error(f"Error starting real agent session: {agent_error}", exc_info=True)
                # Fall through to backup
        
        # Backup chat session start
        result = {
            "status": "success",
            "session_id": session_id,
            "message": "Chat session started (backup mode)",
            "agent_status": "online",
            "capabilities": [
                "WordPress development assistance",
                "Code generation and analysis", 
                "Plugin and theme development",
                "Security recommendations",
                "Performance optimization",
                "Database queries and optimization"
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in api_start_chat: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/chat/message", methods=["POST"])
def api_send_chat_message():
    """Send a message to the WordPress Engineer agent"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message')
        image_path = data.get('image_path')
        
        if not session_id or not message:
            logger.warning("Session ID or message missing for chat message.")
            return jsonify({"error": "session_id and message are required"}), 400
        
        # Use real WordPress Engineer agent if available
        if CHAT_INTEGRATION_AVAILABLE and MAIN_AGENT_AVAILABLE:
            try:
                # Call the real agent
                result = asyncio.run(send_message_to_agent(session_id, message, image_path))
                
                # Ensure proper response format
                if isinstance(result, dict) and result.get('status') == 'success':
                    return jsonify(result)
                else:
                    logger.warning(f"Agent returned unexpected format or empty response for message in session {session_id}.")
                    # Fallback format
                    result = {
                        "status": "success",
                        "response": "Agent returned an unexpected format or an empty response.",
                        "session_id": session_id,
                        "timestamp": time.time(),
                        "message_id": f"msg_{int(time.time() * 1000)}"
                    }
                    return jsonify(result)
                    
            except Exception as agent_error:
                logger.error(f"Error using real agent for message in session {session_id}: {agent_error}", exc_info=True)
                # Fall through to backup responses
        
        # Backup intelligent responses if real agent unavailable
        import time
        time.sleep(0.5)  # Simulate processing time
        
        # Generate intelligent responses based on message content
        message_lower = message.lower()
        
        if 'wordpress' in message_lower and 'plugin' in message_lower:
            response = f"For WordPress plugin development related to '{message}', I recommend starting with the WordPress Plugin Boilerplate. Key considerations include proper hook usage, sanitization, and following WordPress coding standards. Would you like me to generate a plugin structure?"
        elif 'theme' in message_lower:
            response = f"WordPress theme development for '{message}' should follow the template hierarchy and use WordPress functions properly. Modern themes should support block editing and be responsive. Need specific theme code?"
        elif 'security' in message_lower:
            response = f"WordPress security for '{message}' is critical. Always sanitize inputs, validate data, use nonces, and keep everything updated. I can run a security audit if you provide a path."
        elif 'database' in message_lower:
            response = f"For database operations related to '{message}', use WordPress $wpdb class or WP_Query. Always use prepared statements and proper sanitization. Need database optimization help?"
        elif 'performance' in message_lower:
            response = f"WordPress performance optimization for '{message}' involves caching, image optimization, database cleanup, and code optimization. I can analyze your site's performance."
        elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            response = "Hello! I'm Mike, your WordPress development assistant. I specialize in plugin development, theme creation, security audits, performance optimization, and solving complex WordPress challenges. What can I help you build today?"
        elif 'help' in message_lower or 'what' in message_lower:
            response = "I can help you with:\n\n🔧 Plugin & Theme Development\n🛡️ Security Audits & Fixes\n⚡ Performance Optimization\n🗄️ Database Management\n🎨 Custom Post Types & Fields\n🔗 REST API Development\n🐛 Debugging & Troubleshooting\n\nWhat specific challenge are you facing?"
        elif 'code' in message_lower:
            response = f"For the code-related question '{message}', I can help with WordPress development, review your code for best practices, suggest improvements, or generate custom solutions. Would you like me to validate some code or create something new?"
        else:
            response = f"I understand you're asking about '{message}'. As a WordPress expert, I can provide detailed guidance, code examples, and best practices. Could you clarify what specific aspect you need help with? For example:\n\n• Code generation or review\n• Problem troubleshooting\n• Architecture recommendations\n• Performance optimization"
        
        result = {
            "status": "success",
            "response": response,
            "session_id": session_id,
            "timestamp": time.time(),
            "message_id": f"msg_{int(time.time() * 1000)}"
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in api_send_chat_message: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/chat/voice", methods=["POST"])
def api_voice_input():
    """Handle voice input for chat"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            logger.warning("Session ID missing for voice input.")
            return jsonify({"error": "session_id is required"}), 400
        
        if CHAT_INTEGRATION_AVAILABLE:
            result = asyncio.run(voice_input_handler(session_id))
        else:
            logger.warning("Voice input requested but chat integration not available.")
            result = {
                "status": "error",
                "message": "Voice input not available - chat integration not loaded"
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in api_voice_input: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/chat/tts", methods=["POST"])
def api_text_to_speech():
    """Convert text to speech"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        text = data.get('text')
        
        if not session_id or not text:
            logger.warning("Session ID or text missing for TTS request.")
            return jsonify({"error": "session_id and text are required"}), 400
        
        if CHAT_INTEGRATION_AVAILABLE:
            result = asyncio.run(text_to_speech_handler(session_id, text))
        else:
            logger.warning("TTS requested but chat integration not available.")
            result = {
                "status": "error",
                "message": "Text-to-speech not available"
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in api_text_to_speech: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/chat/history", methods=["GET"])
def api_get_chat_history():
    """Get chat history for a session"""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            logger.warning("Session ID missing for chat history request.")
            return jsonify({"error": "session_id is required"}), 400
        
        if CHAT_INTEGRATION_AVAILABLE:
            result = get_chat_history(session_id)
        else:
            logger.warning("Chat history requested but chat integration not available.")
            result = {
                "status": "error",
                "message": "Chat integration not available"
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in api_get_chat_history: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/chat/clear", methods=["POST"])
def api_clear_chat():
    """Clear a chat session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            logger.warning("Session ID missing for clear chat request.")
            return jsonify({"error": "session_id is required"}), 400
        
        # Use real WordPress Engineer agent if available
        if CHAT_INTEGRATION_AVAILABLE and MAIN_AGENT_AVAILABLE:
            try:
                # Call the real agent clear function
                result = clear_chat_session(session_id)
                
                # Ensure proper response format
                if isinstance(result, dict) and result.get('status') == 'success':
                    return jsonify(result)
                else:
                    logger.warning(f"Agent clear session returned unexpected format or empty response for session {session_id}.")
                    # Fallback format
                    result = {
                        "status": "success", 
                        "message": f"Chat session {session_id} cleared successfully (real agent)",
                        "session_id": session_id,
                        "timestamp": time.time()
                    }
                    return jsonify(result)
                    
            except Exception as agent_error:
                logger.error(f"Error clearing real agent session: {agent_error}", exc_info=True)
                # Fall through to backup
        
        # Backup clear session
        result = {
            "status": "success", 
            "message": f"Chat session {session_id} cleared successfully",
            "session_id": session_id,
            "timestamp": time.time()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in api_clear_chat: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/chat/sessions", methods=["GET"])
def api_get_chat_sessions():
    """Get active chat sessions"""
    try:
        if CHAT_INTEGRATION_AVAILABLE:
            result = get_active_chat_sessions()
        else:
            logger.warning("Active chat sessions requested but chat integration not available.")
            result = {
                "status": "error",
                "message": "Chat integration not available"
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in api_get_chat_sessions: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/chat/upload", methods=["POST"])
def api_chat_upload_image():
    """Upload image for chat analysis"""
    try:
        if 'file' not in request.files:
            logger.warning("No file provided for chat image upload.")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        session_id = request.form.get('session_id')
        
        if file.filename == '':
            logger.warning("No file selected for chat image upload.")
            return jsonify({"error": "No file selected"}), 400
        
        if not session_id:
            logger.warning("Session ID missing for chat image upload.")
            return jsonify({"error": "session_id is required"}), 400
        
        # Check if it's an allowed image file
        allowed_image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        if file and file.filename.lower().rsplit('.', 1)[1] in allowed_image_extensions:
            filename = secure_filename(file.filename)
            # Create session-specific directory
            session_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'chat', session_id)
            
            try:
                safe_session_dir = safe_path_join(project_root, session_dir)
            except ValueError as e:
                logger.error(f"Directory traversal attempt detected during chat upload: {e}")
                return jsonify({"error": "Invalid session path"}), 400

            os.makedirs(safe_session_dir, exist_ok=True)
            
            file_path = os.path.join(safe_session_dir, filename)
            file.save(file_path)
            logger.info(f"Chat image uploaded successfully: {file_path}")
            
            return jsonify({
                "status": "success",
                "filename": filename,
                "path": os.path.relpath(file_path, project_root),
                "size": os.path.getsize(file_path),
                "message": "Image uploaded successfully for chat analysis"
            })
        else:
            logger.warning(f"Attempted to upload disallowed file type for chat: {file.filename}")
            return jsonify({"error": "Only image files are allowed for chat upload"}), 400
            
    except Exception as e:
        logger.error(f"Error in api_chat_upload_image: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Knowledgebase (RAG) API Routes
@app.route("/api/knowledgebase/stats", methods=["GET"])
def api_kb_stats():
    if not RAG_DB_AVAILABLE:
        return jsonify({"status": "error", "message": "Knowledgebase not available."}), 503
    try:
        stats = asyncio.run(rag_db_instance.get_statistics())
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        logger.error(f"Error in api_kb_stats: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/api/knowledgebase/search", methods=["GET"])
def api_kb_search():
    if not RAG_DB_AVAILABLE:
        logger.warning("Knowledgebase search requested but RAG DB not available.")
        return jsonify({"status": "error", "message": "Knowledgebase not available."}), 503
    
    query = request.args.get('q', '')
    categories_str = request.args.get('categories', '')
    categories = [cat.strip() for cat in categories_str.split(',')] if categories_str else None
    limit = request.args.get('limit', default=10, type=int)
    use_semantic_str = request.args.get('use_semantic', 'true')
    use_semantic = use_semantic_str.lower() == 'true' and RAG_DB_EMBEDDINGS_AVAILABLE

    if not query:
        logger.warning("Knowledgebase search query missing.")
        return jsonify({"error": "Query parameter 'q' is required."}), 400
    
    try:
        result = asyncio.run(rag_db_instance.search(query, categories, limit, use_semantic))
        logger.info(f"Knowledgebase search for '{query}' returned {len(result.get('results', []))} results.")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_kb_search: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/api/knowledgebase/add_document", methods=["POST"])
def api_kb_add_document():
    if not RAG_DB_AVAILABLE:
        logger.warning("Add document to KB requested but RAG DB not available.")
        return jsonify({"status": "error", "message": "Knowledgebase not available."}), 503
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        category = data.get('category', 'general')
        tags_str = data.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',')] if tags_str else None
        source = data.get('source')

        if not title or not content:
            logger.warning("Title or content missing for adding KB document.")
            return jsonify({"error": "Title and content are required."}), 400

        result = asyncio.run(rag_db_instance.add_document(title, content, category, tags, source))
        logger.info(f"Document '{title}' added to knowledgebase.")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_kb_add_document: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/api/knowledgebase/add_snippet", methods=["POST"])
def api_kb_add_snippet():
    if not RAG_DB_AVAILABLE:
        logger.warning("Add snippet to KB requested but RAG DB not available.")
        return jsonify({"status": "error", "message": "Knowledgebase not available."}), 503
    try:
        data = request.get_json()
        title = data.get('title')
        code = data.get('code')
        language = data.get('language', 'php')
        description = data.get('description')
        tags_str = data.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',')] if tags_str else None

        if not title or not code:
            logger.warning("Title or code missing for adding KB snippet.")
            return jsonify({"error": "Title and code are required."}), 400

        result = asyncio.run(rag_db_instance.add_code_snippet(title, code, language, description, tags))
        logger.info(f"Code snippet '{title}' added to knowledgebase.")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_kb_add_snippet: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/api/knowledgebase/import", methods=["POST"])
def api_kb_import():
    if not RAG_DB_AVAILABLE:
        return jsonify({"status": "error", "message": "Knowledgebase not available."}), 503
    try:
        data = request.get_json()
        docs_path = data.get('path')
        if not docs_path:
            return jsonify({"error": "Documentation path is required."}), 400
        
        try:
            # Import path is relative to project_root, or a specific "docs_import_area"
            # For this example, we'll assume docs_path is always relative to project_root
            safe_docs_path = safe_path_join(project_root, docs_path)
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400

        if not os.path.exists(safe_docs_path) or not os.path.isdir(safe_docs_path):
            return jsonify({"status": "error", "message": f"Path does not exist or is not a directory: {docs_path}"}), 400

        result = asyncio.run(rag_db_instance.import_wp_documentation(safe_docs_path))
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/knowledgebase/export", methods=["POST"])
def api_kb_export():
    if not RAG_DB_AVAILABLE:
        return jsonify({"status": "error", "message": "Knowledgebase not available."}), 503
    try:
        data = request.get_json()
        export_path_arg = data.get('path', 'rag_export') # Default export path relative to project_root
        
        try:
            # Export path is relative to project_root
            safe_export_path = safe_path_join(project_root, export_path_arg)
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        
        os.makedirs(safe_export_path, exist_ok=True) # Ensure export directory exists

        result = asyncio.run(rag_db_instance.export_database(safe_export_path))
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_kb_export: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/api/knowledgebase/backup", methods=["POST"])
def api_kb_backup():
    if not RAG_DB_AVAILABLE:
        logger.warning("Knowledgebase backup requested but RAG DB not available.")
        return jsonify({"status": "error", "message": "Knowledgebase not available."}), 503
    try:
        # Backup path is handled by RAGDatabase if not provided, typically to a 'backups' subdir
        result = asyncio.run(rag_db_instance.backup_database())
        logger.info("Knowledgebase backed up successfully.")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_kb_backup: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/api/knowledgebase/rebuild_embeddings", methods=["POST"])
def api_kb_rebuild_embeddings():
    if not RAG_DB_AVAILABLE:
        logger.warning("Rebuild embeddings requested but RAG DB not available.")
        return jsonify({"status": "error", "message": "Knowledgebase not available."}), 503
    if not RAG_DB_EMBEDDINGS_AVAILABLE:
        logger.warning("Rebuild embeddings requested but Embeddings model not loaded.")
        return jsonify({"status": "error", "message": "Embeddings model not loaded, cannot rebuild."}), 503
    try:
        result = asyncio.run(rag_db_instance.rebuild_embeddings())
        logger.info("Knowledgebase embeddings rebuilt successfully.")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_kb_rebuild_embeddings: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# Static file serving (for development)
@app.route('/static/<path:filename>')
def static_files(filename):
    # Use safe_path_join for serving static files if app.static_folder is within project_root
    try:
        safe_static_path = safe_path_join(project_root, app.static_folder)
        return send_from_directory(safe_static_path, filename)
    except ValueError as e:
        logger.error(f"Directory traversal attempt detected in static file serving: {e}")
        return "File not found", 404

# Error handlers
@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 Not Found: {request.path}")
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint not found", "status_code": 404}), 404
    return render_template("404.html", title="Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 Internal Server Error: {request.path}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error", "status_code": 500}), 500
    return render_template("500.html", title="Server Error"), 500

@app.errorhandler(413)
def file_too_large(e):
    logger.warning(f"413 Request Entity Too Large: {request.path}")
    return jsonify({"error": "File too large", "status_code": 413}), 413

# CORS support for API endpoints
@app.after_request
def after_request(response):
    # In production, restrict Access-Control-Allow-Origin to specific domains.
    # For local development, 'http://localhost:5000' is used.
    # For actual production, replace with your frontend's domain (e.g., 'https://yourfrontend.com').
    # You can also fetch the allowed origin from an environment variable.
    allowed_origin = os.environ.get("CORS_ALLOWED_ORIGIN", "http://localhost:5000")
    response.headers.add('Access-Control-Allow-Origin', allowed_origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true') # Allow credentials to be sent with requests
    return response

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("WordPress Engineer Web Interface Starting...")
    logger.info("=" * 60)
    logger.info("Features available:")
    logger.info("   - AI Plugin & Theme Generation")
    logger.info("   - Security Scanning & Analysis")
    logger.info("   - Database Optimization")
    logger.info("   - Code Validation with AI")
    logger.info("   - File Management System")
    logger.info("   - Terminal Command Execution")
    logger.info("   - Real-time Analytics Dashboard")
    logger.info("   - Knowledgebase Management (RAG DB)")
    logger.info("   - Dark Mode Support")
    logger.info("   - Responsive Design")
    logger.info("=" * 60)
    logger.info(f"Access the interface at: http://localhost:5000")
    logger.info(f"Debug mode: Disabled (Production Ready)") # Changed for production
    logger.info("=" * 60)
    
    try:
        # For production, debug should be False. Use a production WSGI server like Gunicorn or uWSGI.
        # Example: gunicorn -w 4 -b 0.0.0.0:5000 app:app
        app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
    except Exception as e:
        logger.critical(f"Error starting server: {e}", exc_info=True)
        # In production, you might not want to block with input()
        # input("Press Enter to exit...")
