# WordPress Engineer AI Agent User Guide

This guide provides detailed instructions on how to set up and use the WordPress Engineer AI Agent.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
    - [Interacting with the Agent](#interacting-with-the-agent)
    - [Available Commands/Tools](#available-commandstools)
5. [Troubleshooting](#troubleshooting)
6. [Contributing](#contributing)

## 1. Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.7 or higher
- A local WordPress development environment (e.g., Local by Flywheel, XAMPP, MAMP, Docker)
- Composer (for PHP dependency management, if needed)
- npm or yarn (for JavaScript dependency management, if needed)

## 2. Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-repo/wordpress-engineer-agent.git
    cd wordpress-engineer-agent
    ```

2. **Set up a Python virtual environment:**

    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3. **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure environment variables:**

    Create a `.env` file in the root directory of the project and add necessary API keys (e.g., for AI models, search APIs). Refer to `.env.example` (if available) for required variables.

    ```dotenv
    # Example .env content
    ANTHROPIC_API_KEY=your_anthropic_api_key
    TAVILY_API_KEY=your_tavily_api_key
    # Add other necessary variables
    ```

## 3. Configuration

- **WordPress Path:** Ensure the agent is configured with the correct path to your WordPress installation. This is often done via an environment variable or a configuration file.
- **RAG Database:** The agent uses a RAG database for WordPress knowledge. This database will be initialized automatically on first run. You may need to import documentation or code snippets into it.

## 4. Usage

The WordPress Engineer AI Agent can be used in two ways: through the command-line interface (CLI) or the web interface.

### Command-Line Interface (CLI)

To start the AI agent in the CLI, activate your virtual environment and run the main script:

```bash
# Ensure you are in the project root directory
# Activate virtual environment if not already active
# .\venv\Scripts\activate  # Windows
# source venv/bin/activate # macOS/Linux

python main.py
```

The agent will start and provide a prompt for you to interact with.

#### Interacting with the Agent in the CLI

You can type your requests or questions related to WordPress development. The agent will use its tools and knowledge base to assist you.

Examples:

- `create a new WordPress theme named "My Custom Theme" in C:\path\to\wordpress`
- `how do I register a custom post type in WordPress?`
- `debug the error in functions.php`
- `create a simple plugin that adds a shortcode`

### Web Interface

The web interface provides a graphical user interface (GUI) for interacting with the WordPress Engineer AI Agent. To start the web interface, navigate to the `web` directory and run the `app.py` script:

```bash
cd web
python app.py
```

Then, open your web browser and navigate to `http://127.0.0.1:5000`.

#### Web Interface Features

- **Dashboard**: A central hub for your WordPress development projects, showing key statistics and quick actions.
- **WordPress Dev**: Tools for security scanning and database optimization.
- **Chat with Mike**: A direct chat interface with the WordPress Engineer AI.
- **Code Generator**: AI-powered tools for generating WordPress plugins and themes.
- **File Manager**: A file browser and editor for your project files.
- **Code Validator**: An AI-powered tool for analyzing and validating your code.
- **Terminal**: An integrated terminal for running commands.
- **Analytics**: A dashboard for visualizing your development activity.
- **Settings**: A page for configuring the application.

### Available Commands/Tools

The agent has access to various tools to perform tasks. You can typically describe what you want to achieve in natural language, and the agent will select the appropriate tool. Some core capabilities include:

- Creating WordPress themes and plugins.
- Reading and writing code files (PHP, CSS, JS, HTML).
- Searching WordPress documentation and code snippets (via RAG).
- Running shell commands (with necessary precautions).
- Performing web searches.
- Managing the file system (creating, deleting, and moving files and folders).
- Interacting with the user through a web interface.

## 5. Troubleshooting

- **API Key Errors:** Ensure your `.env` file is correctly set up with valid API keys.
- **Dependency Issues:** Make sure all Python dependencies from `requirements.txt` are installed and your virtual environment is active.
- **WordPress Path:** Double-check that the WordPress installation path provided to the agent is correct.
- **Database Errors:** If you encounter issues with the RAG database, try deleting the `wp_knowledge.db` file (or whatever you named it) and restarting the agent to re-initialize it.

## 6. Contributing

If you wish to contribute to the project, please refer to the `CONTRIBUTING.md` file (if available) for guidelines on submitting issues, feature requests, and pull requests.
