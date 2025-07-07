tools = [
    {
        "name": "create_folders",
        "description": "Create new folders at the specified paths, including nested directories. This tool should be used when you need to create one or more directories (including nested ones) in the project structure. It will create all necessary parent directories if they don't exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "An array of absolute or relative paths where the folders should be created. Use forward slashes (/) for path separation, even on Windows systems. For nested directories, simply include the full path (e.g., 'parent/child/grandchild')."
                }
            },
            "required": ["paths"]
        }
    },
        {
        "name": "wp_db_query",
        "description": "Execute WordPress database queries safely with proper validation and error handling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL query to execute"
                },
                "database_config": {
                    "type": "object",
                    "description": "Database connection configuration",
                    "properties": {
                        "host": {"type": "string"},
                        "user": {"type": "string"},
                        "password": {"type": "string"},
                        "database": {"type": "string"}
                    },
                    "required": ["host", "user", "password", "database"]
                }
            },
            "required": ["query", "database_config"]
        }
    },
    {
    "name": "convert_to_wordpress_theme",
    "description": "Convert a static HTML/CSS/JS website to a WordPress theme",
    "input_schema": {
        "type": "object",  # Add this line
        "properties": {
            "static_site_path": {
                "type": "string",
                "description": "Path to the static website files"
            },
            "theme_name": {
                "type": "string",
                "description": "Name for the new WordPress theme"
            },
            "options": {
                "type": "object",
                "properties": {
                    "include_customizer": {"type": "boolean"},
                    "create_block_templates": {"type": "boolean"},
                    "responsive": {"type": "boolean"},
                    "menu_locations": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "widget_areas": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "required": ["static_site_path", "theme_name"]
    }
},
    {
        "name": "backup_wp_database",
        "description": "Create a backup of WordPress database",
        "input_schema": {
            "type": "object",
            "properties": {
                "backup_path": {
                    "type": "string",
                    "description": "Path where the backup file should be saved"
                },
                "database_config": {
                    "type": "object",
                    "description": "Database connection configuration",
                    "properties": {
                        "host": {"type": "string"},
                        "user": {"type": "string"},
                        "password": {"type": "string"},
                        "database": {"type": "string"}
                    },
                    "required": ["host", "user", "password", "database"]
                }
            },
            "required": ["backup_path", "database_config"]
        }
    },
    {
        "name": "customize_theme",
        "description": "Apply customizations to WordPress theme styles",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme_path": {
                    "type": "string",
                    "description": "Path to the theme directory"
                },
                "customizations": {
                    "type": "object",
                    "description": "CSS customizations as key-value pairs"
                }
            },
            "required": ["theme_path", "customizations"]
        }
    },
    {
        "name": "manage_plugins",
        "description": "Manage WordPress plugins using WP-CLI",
        "input_schema": {
            "type": "object",
            "properties": {
                "wp_path": {
                    "type": "string",
                    "description": "Path to WordPress installation"
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform (install, activate, deactivate, delete)",
                    "enum": ["install", "activate", "deactivate", "delete"]
                },
                "plugin_name": {
                    "type": "string",
                    "description": "Name of the plugin"
                }
            },
            "required": ["wp_path", "action", "plugin_name"]
        }
    },
    {
        "name": "security_scan",
        "description": "Perform security scan on WordPress installation",
        "input_schema": {
            "type": "object",
            "properties": {
                "wp_path": {
                    "type": "string",
                    "description": "Path to WordPress installation"
                }
            },
            "required": ["wp_path"]
        }
    },
    {
        "name": "optimize_performance",
        "description": "Optimize WordPress performance through caching and database optimization",
        "input_schema": {
            "type": "object",
            "properties": {
                "wp_path": {
                    "type": "string",
                    "description": "Path to WordPress installation"
                }
            },
            "required": ["wp_path"]
        }
    },
    {
        "name": "register_custom_post_type",
        "description": "Register a new custom post type in WordPress",
        "input_schema": {
            "type": "object",
            "properties": {
                "wp_path": {
                    "type": "string",
                    "description": "Path to WordPress installation"
                },
                "post_type": {
                    "type": "string",
                    "description": "Name of the custom post type"
                },
                "options": {
                    "type": "object",
                    "description": "Custom post type options"
                }
            },
            "required": ["wp_path", "post_type", "options"]
        }
    },
    {
        "name": "optimize_media",
        "description": "Optimize WordPress media files",
        "input_schema": {
            "type": "object",
            "properties": {
                "wp_path": {
                    "type": "string",
                    "description": "Path to WordPress installation"
                },
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                }
            },
            "required": ["wp_path", "image_path"]
        }
    },
    {
        "name": "scan_folder",
        "description": "Scan a specified folder and create a Markdown file with the contents of all coding text files, excluding binary files and common ignored folders.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder_path": {
                    "type": "string",
                    "description": "The absolute or relative path of the folder to scan. Use forward slashes (/) for path separation, even on Windows systems."
                },
                "output_file": {
                    "type": "string",
                    "description": "The name of the output Markdown file to create with the scanned contents."
                }
            },
            "required": ["folder_path", "output_file"]
        }
    },
    {
        "name": "create_files",
        "description": "Create one or more new files with the given contents. This tool should be used when you need to create files in the project structure. It will create all necessary parent directories if they don't exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "files": {
                    "oneOf": [
                        {
                            "type": "string",
                            "description": "A single file path to create an empty file."
                        },
                        {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["path"]
                        },
                        {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "content": {"type": "string"}
                                },
                                "required": ["path"]
                            }
                        }
                    ]
                }
            },
            "required": ["files"]
        }
    },
    {
        "name": "edit_and_apply_multiple",
        "description": "Apply AI-powered improvements to multiple files based on specific instructions and detailed project context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The absolute or relative path of the file to edit."
                            },
                            "instructions": {
                                "type": "string",
                                "description": "Specific instructions for editing this file."
                            }
                        },
                        "required": ["path", "instructions"]
                    }
                },
                "project_context": {
                    "type": "string",
                    "description": "Comprehensive context about the project, including recent changes, new variables or functions, interconnections between files, coding standards, and any other relevant information that might affect the edits."
                }
            },
            "required": ["files", "project_context"]
        }
    },
    {
        "name": "execute_code",
        "description": "Execute Python code in the 'code_execution_env' virtual environment and return the output. This tool should be used when you need to run code and see its output or check for errors. All code execution happens exclusively in this isolated environment. The tool will return the standard output, standard error, and return code of the executed code. Long-running processes will return a process ID for later management.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute in the 'code_execution_env' virtual environment. Include all necessary imports and ensure the code is complete and self-contained."
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "stop_process",
        "description": "Stop a running process by its ID. This tool should be used to terminate long-running processes that were started by the execute_code tool. It will attempt to stop the process gracefully, but may force termination if necessary. The tool will return a success message if the process is stopped, and an error message if the process doesn't exist or can't be stopped.",
        "input_schema": {
            "type": "object",
            "properties": {
                "process_id": {
                    "type": "string",
                    "description": "The ID of the process to stop, as returned by the execute_code tool for long-running processes."
                }
            },
            "required": ["process_id"]
        }
    },
    {
        "name": "read_multiple_files",
        "description": "Read the contents of one or more existing files, supporting wildcards and recursive directory reading.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paths": {
                    "oneOf": [
                        {
                            "type": "string",
                            "description": "A single file path, directory path, or wildcard pattern."
                        },
                        {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "An array of file paths, directory paths, or wildcard patterns."
                        }
                    ],
                    "description": "The path(s) of the file(s) to read. Use forward slashes (/) for path separation, even on Windows systems. Supports wildcards (e.g., '*.py') and directory paths."
                },
                "recursive": {
                    "type": "boolean",
                    "description": "If true, read files recursively from directories. Default is false.",
                    "default": False
                }
            },
            "required": ["paths"]
        }
    },
    {
        "name": "list_files",
        "description": "List all files and directories in the specified folder. This tool should be used when you need to see the contents of a directory. It will return a list of all files and subdirectories in the specified path. If the directory doesn't exist or can't be read, an appropriate error message will be returned.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative path of the folder to list. Use forward slashes (/) for path separation, even on Windows systems. If not provided, the current working directory will be used."
                }
            }
        }
    },
    {
        "name": "tavily_search",
        "description": "Perform a web search using the Tavily API to get up-to-date information or additional context. This tool should be used when you need current information or feel a search could provide a better answer to the user's query. It will return a summary of the search results, including relevant snippets and source URLs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be as specific and detailed as possible to get the most relevant results."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "run_shell_command",
        "description": "Execute a shell command and return its output. This tool should be used when you need to run system commands or interact with the operating system. It will return the standard output, standard error, and return code of the executed command.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute. Ensure the command is safe and appropriate for the current operating system."
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "create_wordpress_theme",
        "description": "Create a basic WordPress theme structure with essential files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme_name": {
                    "type": "string",
                    "description": "The name of the WordPress theme"
                }
            },
            "required": ["theme_name"]
        }
    },
    {
        "name": "create_wordpress_plugin",
        "description": "Create a basic WordPress plugin structure with essential files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plugin_name": {
                    "type": "string",
                    "description": "The name of the WordPress plugin"
                }
            },
            "required": ["plugin_name"]
        }
    },
    {
        "name": "analyze_wordpress_code",
        "description": "Analyze WordPress code for best practices and potential issues",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "WordPress code to analyze"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "optimize_wordpress_performance",
        "description": "Optimize WordPress site performance",
        "input_schema": {
            "type": "object",
            "properties": {
                "site_path": {
                    "type": "string",
                    "description": "Path to WordPress installation"
                }
            },
            "required": ["site_path"]
        }
    },
    {
        "name": "validate_wordpress_code",
        "description": "Validate WordPress code against coding standards",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "WordPress code to validate"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "create_block_theme",
        "description": "Create a modern block-based WordPress theme",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme_name": {
                    "type": "string",
                    "description": "The name of the block theme"
                },
                "options": {
                    "type": "object",
                    "description": "Additional theme options"
                }
            },
            "required": ["theme_name"]
        }
    },
    {
        "name": "setup_woocommerce_integration",
        "description": "Add WooCommerce support to a WordPress theme",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme_path": {
                    "type": "string",
                    "description": "Path to the WordPress theme"
                },
                "features": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of WooCommerce features to integrate"
                }
            },
            "required": ["theme_path", "features"]
        }
    },
    {
        "name": "setup_custom_endpoints",
        "description": "Create custom WordPress REST API endpoints",
        "input_schema": {
            "type": "object",
            "properties": {
                "plugin_path": {
                    "type": "string",
                    "description": "Path to the WordPress plugin"
                },
                "endpoints": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "route": {
                                "type": "string",
                                "description": "The endpoint route"
                            },
                            "methods": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["GET", "POST", "PUT", "DELETE"]
                                },
                                "description": "HTTP methods supported by the endpoint"
                            },
                            "callback": {
                                "type": "string",
                                "description": "Name of the callback function"
                            }
                        }
                    },
                    "description": "Configuration for custom endpoints"
                }
            },
            "required": ["plugin_path", "endpoints"]
        }
    },
   {
       "name": "manage_theme_customizer",
       "description": "Use the WordPress Theme Customization API to create and manage settings, sections, and controls for theme options.",
       "input_schema": {
           "type": "object",
           "properties": {
                "theme_path": { # ADDED
                   "type": "string", 
                   "description": "Path to the theme directory"
               },
               "settings": {
                   "type": "array",
                   "description": "Array of settings to add or modify",
                   "items": {
                       "type": "object",
                       "properties": {
                           "id": {"type": "string", "description": "Setting ID"},
                           "default": {"type": "string", "description": "Default value"},
                           "transport": {"type": "string", "description": "Transport method"}
                       },
                       "required": ["id"]
                   }
               },
               "controls": {
                   "type": "array",
                   "description": "Array of controls to add or modify",
                   "items": {
                       "type": "object",
                       "properties": {
                           "id": {"type": "string", "description": "Control ID"},
                           "label": {"type": "string", "description": "Control label"},
                           "section": {"type": "string", "description": "Section ID"},
                           "type": {"type": "string", "description": "Control type"},
                           "setting": {"type": "string", "description": "Setting ID"}
                       },
                       "required": ["id", "label", "section", "type", "setting"]
                   }
               },
               "sections": {
                   "type": "array",
                   "description": "Array of sections to add or modify",
                   "items": {
                       "type": "object",
                       "properties": {
                           "id": {"type": "string", "description": "Section ID"},
                           "title": {"type": "string", "description": "Section title"},
                           "priority": {"type": "integer", "description": "Section priority"}
                       },
                       "required": ["id", "title"]
                   }
               },
               "actions": {
                   "type": "array",
                   "description": "Array of actions to perform (add, remove)",
                   "items": {
                       "type": "string",
                       "enum": ["add", "remove"]
                   }
               }
           },
           "required": ["theme_path", "actions"]
       }
   },
   {
       "name": "create_gutenberg_block",
       "description": "Generate custom Gutenberg blocks, including block.json, PHP render files, and JavaScript code.",
       "input_schema": {
           "type": "object",
           "properties": {
               "block_name": {"type": "string", "description": "Block name"},
               "attributes": {
                   "type": "object",
                   "description": "Block attributes",
                   "additionalProperties": {
                       "type": "object",
                       "properties": {
                           "type": {"type": "string"},
                           "default": {"type": "string"}
                       }
                   }
               },
               "editor_ui": {
                   "type": "string",
                   "description": "JavaScript code for editor UI elements"
               },
               "server_side_render": {
                   "type": "string",
                   "description": "PHP code for server-side rendering logic"
               }
           },
           "required": ["block_name", "attributes", "editor_ui", "server_side_render"]
       }
   },
   {
       "name": "manage_menus",
       "description": "Create, edit, and manage WordPress menus and their items.",
       "input_schema": {
           "type": "object",
           "properties": {
               "menu_name": {"type": "string", "description": "Menu name"},
               "menu_location": {"type": "string", "description": "Menu location"},
               "items": {
                   "type": "array",
                   "description": "Array of menu items",
                   "items": {
                       "type": "object",
                       "properties": {
                           "title": {"type": "string", "description": "Menu item title"},
                           "url": {"type": "string", "description": "Menu item URL"},
                           "parent": {"type": "string", "description": "Parent menu item ID"}
                       },
                       "required": ["title", "url"]
                   }
               },
               "actions": {
                   "type": "array",
                   "description": "Array of actions to perform (create, update, delete)",
                   "items": {
                       "type": "string",
                       "enum": ["create", "update", "delete"]
                   }
               }
           },
           "required": ["menu_name", "actions"]
       }
   },
   {
       "name": "manage_widgets",
       "description": "Register, add, and manipulate WordPress widgets.",
       "input_schema": {
           "type": "object",
           "properties": {
               "widget_id": {"type": "string", "description": "Widget ID"},
               "widget_area": {"type": "string", "description": "Widget area"},
               "settings": {
                   "type": "object",
                   "description": "Widget settings"
               },
               "actions": {
                   "type": "array",
                   "description": "Array of actions to perform (register, add, remove)",
                   "items": {
                       "type": "string",
                       "enum": ["register", "add", "remove"]
                   }
               }
           },
           "required": ["widget_id", "widget_area", "actions"]
       }
   },
   {
       "name": "create_shortcode",
       "description": "Create WordPress shortcodes for dynamic content.",
       "input_schema": {
           "type": "object",
           "properties": {
               "shortcode_name": {"type": "string", "description": "Shortcode name"},
               "callback_function": {"type": "string", "description": "PHP code for the callback function"}
           },
           "required": ["shortcode_name", "callback_function"]
       }
   },
   {
       "name": "manage_taxonomies",
       "description": "Create custom taxonomies (categories, tags), set their properties, and assign them to post types.",
       "input_schema": {
           "type": "object",
           "properties": {
               "taxonomy_name": {"type": "string", "description": "Taxonomy name"},
               "post_types": {
                   "type": "array",
                   "description": "Array of post types to assign the taxonomy to",
                   "items": {"type": "string"}
               },
               "settings": {
                   "type": "object",
                   "description": "Taxonomy settings"
               },
                "actions": {
                   "type": "array",
                   "description": "Array of actions to perform (create, update, delete)",
                   "items": {
                       "type": "string",
                       "enum": ["create", "update", "delete"]
                   }
               }
           },
           "required": ["taxonomy_name", "post_types", "actions"]
       }
   },
   {
       "name": "analyze_database_queries",
       "description": "Analyze WordPress database queries for performance bottlenecks and suggest improvements.",
       "input_schema": {
           "type": "object",
           "properties": {
               "query": {"type": "string", "description": "Specific query or WordPress code snippet"}
           },
           "required": ["query"]
       }
   },
   {
       "name": "configure_caching",
       "description": "Configure caching plugins or mechanisms for better WordPress performance.",
       "input_schema": {
           "type": "object",
           "properties": {
               "caching_plugin": {"type": "string", "description": "Caching plugin to use"},
               "cache_settings": {
                   "type": "object",
                   "description": "Cache settings"
               }
           },
           "required": ["caching_plugin", "cache_settings"]
       }
   },
   {
       "name": "integrate_external_api",
       "description": "Integrate with external APIs through custom hooks and endpoints.",
       "input_schema": {
           "type": "object",
           "properties": {
               "api_url": {"type": "string", "description": "API URL"},
               "parameters": {
                   "type": "object",
                   "description": "API parameters"
               },
               "authentication_method": {"type": "string", "description": "Authentication method"}
           },
           "required": ["api_url", "parameters", "authentication_method"]
       }
   },
   {
       "name": "manage_code_snippets",
       "description": "Save and retrieve code snippets to be added to WordPress theme's functions.php file.",
       "input_schema": {
           "type": "object",
           "properties": {
               "code_snippet": {"type": "string", "description": "Code snippet"},
               "short_description": {"type": "string", "description": "Short description of the code snippet"},
               "action": {
                   "type": "string",
                   "description": "Action to perform (save or retrieve)",
                   "enum": ["save", "retrieve"]
               }
           },
           "required": ["code_snippet", "short_description", "action"]
       }
   },
   {
       "name": "install_wordpress",
       "description": "Install a WordPress site with preconfigured settings.",
       "input_schema": {
           "type": "object",
           "properties": {
               "path": {"type": "string", "description": "Path to install WordPress"},
               "url": {"type": "string", "description": "Base URL of the WordPress site"},
               "title": {"type": "string", "description": "Title of the WordPress site"},
               "admin_user": {"type": "string", "description": "Initial admin user"},
               "admin_password": {"type": "string", "description": "Initial admin password"},
               "admin_email": {"type": "string", "description": "Initial admin email"},
               "db_name": {"type": "string", "description": "Database name"}
           },
           "required": ["path", "url", "title", "admin_user", "admin_password", "admin_email", "db_name"]
       }
   },
    {
        "name": "rag_search",
        "description": "Search the WordPress knowledge database for relevant information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Categories to search in ('documents', 'code_snippets', 'wp_functions', 'wp_hooks')",
                    "default": ["documents", "code_snippets", "wp_functions", "wp_hooks"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results per category",
                    "default": 10
                },
                "use_semantic": {
                    "type": "boolean",
                    "description": "Whether to use semantic search if available",
                    "default": True
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "rag_add_document",
        "description": "Add a document to the WordPress knowledge database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Document title"
                },
                "content": {
                    "type": "string",
                    "description": "Document content"
                },
                "category": {
                    "type": "string",
                    "description": "Document category (e.g., 'tutorial', 'reference', 'guide')"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags"
                },
                "source": {
                    "type": "string",
                    "description": "Source of the document"
                }
            },
            "required": ["title", "content", "category"]
        }
    },
    {
        "name": "rag_add_code_snippet",
        "description": "Add a code snippet to the WordPress knowledge database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Snippet title"
                },
                "code": {
                    "type": "string",
                    "description": "Code content"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the snippet"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags"
                }
            },
            "required": ["title", "code", "language"]
        }
    },
    {
        "name": "rag_add_wp_function",
        "description": "Add a WordPress function to the knowledge database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string",
                    "description": "Name of the function"
                },
                "signature": {
                    "type": "string",
                    "description": "Function signature"
                },
                "description": {
                    "type": "string",
                    "description": "Function description"
                },
                "parameters": {
                    "type": "object",
                    "description": "Dictionary of parameter names and descriptions"
                },
                "return_value": {
                    "type": "string",
                    "description": "Description of return value"
                },
                "example": {
                    "type": "string",
                    "description": "Example usage"
                },
                "version_added": {
                    "type": "string",
                    "description": "WordPress version when added"
                },
                "deprecated": {
                    "type": "boolean",
                    "description": "Whether the function is deprecated"
                },
                "source_file": {
                    "type": "string",
                    "description": "Source file where the function is defined"
                }
            },
            "required": ["function_name", "signature"]
        }
    },
    {
        "name": "rag_add_wp_hook",
        "description": "Add a WordPress hook to the knowledge database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hook_name": {
                    "type": "string",
                    "description": "Name of the hook"
                },
                "hook_type": {
                    "type": "string",
                    "description": "Type of hook ('action' or 'filter')"
                },
                "description": {
                    "type": "string",
                    "description": "Hook description"
                },
                "parameters": {
                    "type": "object",
                    "description": "Dictionary of parameter names and descriptions"
                },
                "source_file": {
                    "type": "string",
                    "description": "Source file where the hook is defined"
                },
                "example": {
                    "type": "string",
                    "description": "Example usage"
                },
                "version_added": {
                    "type": "string",
                    "description": "WordPress version when added"
                }
            },
            "required": ["hook_name", "hook_type"]
        }
    },
    {
        "name": "rag_get_statistics",
        "description": "Get statistics about the WordPress knowledge database.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "rag_import_wp_documentation",
        "description": "Import WordPress documentation from a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "docs_path": {
                    "type": "string",
                    "description": "Path to documentation directory"
                }
            },
            "required": ["docs_path"]
        }
    },
    {
        "name": "rag_export_database",
        "description": "Export the knowledge database content to a directory.",
        "input_schema": {
            "type": "object", 
            "properties": {
                "export_path": {
                    "type": "string",
                    "description": "Path to export directory"
                }
            },
            "required": ["export_path"]
        }
    },
    {
        "name": "rag_backup_database",
        "description": "Create a backup of the WordPress knowledge database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "backup_path": {
                    "type": "string", 
                    "description": "Path to save the backup file"
                }
            }
        }
    }
]
