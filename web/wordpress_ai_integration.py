#!/usr/bin/env python3
"""
WordPress AI Integration Module
Integrates real WordPress Engineer functionality with the Web UI
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add the parent directory to the Python path to import main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary functions from main.py
from main import (
    chat_with_mike,
    execute_tool,
    create_wordpress_theme,
    create_wordpress_plugin,
    create_block_theme,
    validate_wordpress_code,
    console
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordPressAIGenerator:
    """AI-powered WordPress development generator using the real WordPress Engineer."""
    
    def __init__(self):
        """Initialize the WordPress AI Generator."""
        self.console = console
        
    async def generate_plugin_with_claude(self, plugin_name: str, description: str, 
                                        complexity: str = "simple") -> Dict[str, Any]:
        """
        Generate a WordPress plugin using Claude AI and the WordPress Engineer.
        
        Args:
            plugin_name: Name of the plugin
            description: Description of what the plugin should do
            complexity: Complexity level (simple, moderate, advanced)
            
        Returns:
            Dict containing the plugin generation results
        """
        if not plugin_name or not description:
            logger.error("Plugin name and description are required.")
            return {"status": "error", "message": "Plugin name and description cannot be empty."}

        try:
            logger.info(f"Generating plugin '{plugin_name}' with complexity '{complexity}'...")
            # Create a prompt that leverages the AI conversation system
            prompt = f"""
            Create a WordPress plugin with the following specifications:
            
            Plugin Name: {plugin_name}
            Description: {description}
            Complexity Level: {complexity}
            
            Please:
            1. Create the basic plugin structure using create_wordpress_plugin
            2. Generate appropriate PHP code based on the description
            3. Include proper WordPress hooks and functions
            4. Add security features and validation
            5. Create necessary CSS and JavaScript files if needed
            6. Ensure the code follows WordPress coding standards
            
            Make this a complete, functional WordPress plugin that implements the described functionality.
            """
            
            # Use the chat_with_mike function to generate the plugin
            response, _ = await chat_with_mike(prompt)
            
            # Also create the basic structure using the direct tool
            basic_result = await execute_tool("create_wordpress_plugin", {"plugin_name": plugin_name})
            
            return {
                "status": "success",
                "message": f"Plugin '{plugin_name}' generated successfully with AI assistance",
                "ai_response": response,
                "basic_structure": basic_result,
                "plugin_name": plugin_name,
                "description": description,
                "complexity": complexity
            }
            
        except Exception as e:
            logger.error(f"Error generating plugin with Claude: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to generate plugin: {str(e)}",
                "plugin_name": plugin_name,
                "error": str(e)
            }
    
    async def generate_theme_with_claude(self, theme_name: str, description: str, 
                                       style: str = "modern") -> Dict[str, Any]:
        """
        Generate a WordPress theme using Claude AI and the WordPress Engineer.
        
        Args:
            theme_name: Name of the theme
            description: Description of the theme style and features
            style: Style type (modern, classic, minimal, etc.)
            
        Returns:
            Dict containing the theme generation results
        """
        if not theme_name or not description:
            logger.error("Theme name and description are required.")
            return {"status": "error", "message": "Theme name and description cannot be empty."}
            
        try:
            logger.info(f"Generating theme '{theme_name}' with style '{style}'...")
            # Create a prompt that leverages the AI conversation system
            prompt = f"""
            Create a WordPress theme with the following specifications:
            
            Theme Name: {theme_name}
            Description: {description}
            Style: {style}
            
            Please:
            1. Create a modern block-based theme using create_block_theme
            2. Generate appropriate CSS styling based on the description
            3. Include responsive design features
            4. Add custom block patterns if relevant
            5. Create template parts for header, footer, etc.
            6. Ensure accessibility and performance optimization
            7. Follow WordPress theme development best practices
            
            Make this a complete, modern WordPress theme that implements the described design and functionality.
            """
            
            # Use the chat_with_mike function to generate the theme
            response, _ = await chat_with_mike(prompt)
            
            # Also create the basic structure using the direct tool
            basic_result = await execute_tool("create_block_theme", {
                "theme_name": theme_name,
                "options": {
                    "description": description,
                    "style": style
                }
            })
            
            return {
                "status": "success",
                "message": f"Theme '{theme_name}' generated successfully with AI assistance",
                "ai_response": response,
                "basic_structure": basic_result,
                "theme_name": theme_name,
                "description": description,
                "style": style
            }
            
        except Exception as e:
            logger.error(f"Error generating theme with Claude: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to generate theme: {str(e)}",
                "theme_name": theme_name,
                "error": str(e)
            }
    
    async def security_scan_with_ai(self, wp_path: str) -> Dict[str, Any]:
        """
        Perform a WordPress security scan using AI analysis.
        
        Args:
            wp_path: Path to the WordPress installation
            
        Returns:
            Dict containing security scan results
        """
        try:
            # Create a prompt for security analysis
            prompt = f"""
            Perform a comprehensive security scan of the WordPress installation at: {wp_path}
            
            Please:
            1. Use the secure_wordpress_installation tool to analyze security settings
            2. Check file permissions and ownership
            3. Analyze wp-config.php for security issues
            4. Check for vulnerable plugins and themes
            5. Validate core file integrity
            6. Provide specific recommendations for improvements
            
            Generate a detailed security report with prioritized recommendations.
            """
            
            # Use the chat_with_mike function for AI-powered analysis
            response, _ = await chat_with_mike(prompt)
            
            # Also run the direct security tool
            security_result = await execute_tool("secure_wordpress_installation", {"wp_path": wp_path})
            
            return {
                "status": "success",
                "message": "Security scan completed with AI analysis",
                "ai_analysis": response,
                "security_data": security_result,
                "recommendations": self._extract_recommendations(response)
            }
            
        except Exception as e:
            logger.error(f"Error performing security scan: {str(e)}")
            return {
                "status": "error",
                "message": f"Security scan failed: {str(e)}",
                "error": str(e)
            }
    
    async def optimize_database_with_ai(self, db_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Optimize WordPress database using AI-guided analysis.
        
        Args:
            db_config: Database configuration parameters
            
        Returns:
            Dict containing optimization results
        """
        try:
            # Create a prompt for database optimization
            prompt = f"""
            Optimize the WordPress database with the following configuration:
            Host: {db_config.get('host', 'localhost')}
            Database: {db_config.get('database', 'wordpress')}
            
            Please:
            1. Initialize the database connection using init_wp_database
            2. Analyze database performance using get_table_status
            3. Optimize tables using optimize_wp_tables
            4. Check for and repair any corrupted tables
            5. Analyze query performance and suggest improvements
            6. Provide recommendations for database maintenance
            
            Generate a comprehensive database optimization report.
            """
            
            # Use the chat_with_mike function for AI-powered optimization
            response, _ = await chat_with_mike(prompt)
            
            return {
                "status": "success",
                "message": "Database optimization completed with AI guidance",
                "ai_analysis": response,
                "optimization_summary": self._extract_optimization_summary(response)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing database: {str(e)}")
            return {
                "status": "error",
                "message": f"Database optimization failed: {str(e)}",
                "error": str(e)
            }
    
    async def validate_code_with_ai(self, code: str, code_type: str = "php") -> Dict[str, Any]:
        """
        Validate WordPress code using AI analysis.
        
        Args:
            code: The code to validate
            code_type: Type of code (php, css, js, etc.)
            
        Returns:
            Dict containing validation results
        """
        try:
            # Use the direct validation tool first
            validation_result = await execute_tool("validate_wordpress_code", {"code": code})
            
            # Create a prompt for enhanced AI analysis
            prompt = f"""
            Analyze and validate the following WordPress {code_type} code:
            
            ```{code_type}
            {code}
            ```
            
            Please provide:
            1. Code quality assessment
            2. WordPress coding standards compliance
            3. Security vulnerability analysis
            4. Performance optimization suggestions
            5. Best practices recommendations
            6. Specific improvements with code examples
            
            Generate a comprehensive code review report.
            """
            
            # Use the chat_with_mike function for enhanced analysis
            response, _ = await chat_with_mike(prompt)
            
            return {
                "status": "success",
                "message": "Code validation completed with AI analysis",
                "validation_result": validation_result,
                "ai_analysis": response,
                "recommendations": self._extract_code_recommendations(response)
            }
            
        except Exception as e:
            logger.error(f"Error validating code: {str(e)}")
            return {
                "status": "error",
                "message": f"Code validation failed: {str(e)}",
                "error": str(e)
            }
    
    def _extract_recommendations(self, ai_response: str) -> List[str]:
        """Extract security recommendations from AI response."""
        # Simple extraction logic - can be enhanced with NLP
        recommendations = []
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'should', 'must', 'improve', 'fix']):
                if len(line) > 10 and not line.startswith('#'):
                    recommendations.append(line)
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _extract_optimization_summary(self, ai_response: str) -> Dict[str, Any]:
        """Extract optimization summary from AI response."""
        summary = {
            "tables_optimized": 0,
            "space_saved": "0 MB",
            "performance_improvement": "Unknown",
            "recommendations": []
        }
        
        # Simple extraction logic - can be enhanced
        lines = ai_response.split('\n')
        for line in lines:
            if 'optimized' in line.lower() and 'table' in line.lower():
                summary["tables_optimized"] += 1
            elif 'saved' in line.lower() and ('mb' in line.lower() or 'gb' in line.lower()):
                summary["space_saved"] = line.strip()
        
        summary["recommendations"] = self._extract_recommendations(ai_response)
        return summary
    
    def _extract_code_recommendations(self, ai_response: str) -> List[Dict[str, str]]:
        """Extract code recommendations from AI response."""
        recommendations = []
        lines = ai_response.split('\n')
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            if line.startswith('##') or line.startswith('###'):
                if current_rec:
                    recommendations.append(current_rec)
                    current_rec = {}
                current_rec['title'] = line.replace('#', '').strip()
            elif line and current_rec and 'title' in current_rec:
                if 'description' not in current_rec:
                    current_rec['description'] = line
                else:
                    current_rec['description'] += ' ' + line
        
        if current_rec:
            recommendations.append(current_rec)
        
        return recommendations[:5]  # Limit to top 5 recommendations

# Create a global instance for use in the web app
wordpress_ai = WordPressAIGenerator()

# Export the functions for use in app_standalone.py
async def generate_plugin_with_claude(plugin_name: str, description: str, complexity: str = "simple"):
    """Export function for plugin generation."""
    return await wordpress_ai.generate_plugin_with_claude(plugin_name, description, complexity)

async def generate_theme_with_claude(theme_name: str, description: str, style: str = "modern"):
    """Export function for theme generation."""
    return await wordpress_ai.generate_theme_with_claude(theme_name, description, style)

async def security_scan_with_ai(wp_path: str):
    """Export function for security scanning."""
    return await wordpress_ai.security_scan_with_ai(wp_path)

async def optimize_database_with_ai(db_config: Dict[str, str]):
    """Export function for database optimization."""
    return await wordpress_ai.optimize_database_with_ai(db_config)

async def validate_code_with_ai(code: str, code_type: str = "php"):
    """Export function for code validation."""
    return await wordpress_ai.validate_code_with_ai(code, code_type)
