import os
import json
import logging
import datetime
import shutil
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import sqlite3
import pickle
import hashlib

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

# Try to import optional dependencies
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

console = Console()

class RAGDatabase:
    """
    Retrieval-Augmented Generation (RAG) database for WordPress knowledge.
    Stores documentation, code snippets, and other WordPress-related information
    for retrieval during agent operations.
    """
    
    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize the RAG database.
        
        Args:
            database_path: Path to the database file (default: wp_knowledge.db in current directory)
        """
        self.logger = logging.getLogger("RAGDatabase")
        
        if database_path is None:
            database_path = os.path.join(os.getcwd(), "wp_knowledge.db")
        
        self.database_path = database_path
        self.conn = None
        self.embedding_model = None
        
        # Initialize database
        self._initialize_database()
        
        # Load embedding model if available
        if EMBEDDINGS_AVAILABLE:
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Loading embedding model..."),
                    console=console
                ) as progress:
                    progress.add_task("load", total=None)
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                console.print("[bold green]Embedding model loaded successfully[/bold green]")
            except Exception as e:
                self.logger.error(f"Error loading embedding model: {str(e)}")
                console.print(f"[bold yellow]Warning: Embedding model could not be loaded. Semantic search will be disabled.[/bold yellow]")
                self.embedding_model = None
        else:
            console.print("[bold yellow]Warning: sentence-transformers not installed. Semantic search will be disabled.[/bold yellow]")
            console.print("To enable semantic search, install the required packages:")
            console.print("[bold]pip install sentence-transformers numpy[/bold]")
    
    def _initialize_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        try:
            self.conn = sqlite3.connect(self.database_path)
            cursor = self.conn.cursor()
            
            # Create documents table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,
                source TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create code_snippets table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                code TEXT NOT NULL,
                language TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create wp_functions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS wp_functions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT NOT NULL UNIQUE,
                signature TEXT NOT NULL,
                description TEXT,
                parameters TEXT,
                return_value TEXT,
                example TEXT,
                version_added TEXT,
                deprecated BOOLEAN DEFAULT 0,
                source_file TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create wp_hooks table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS wp_hooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hook_name TEXT NOT NULL UNIQUE,
                hook_type TEXT NOT NULL,
                description TEXT,
                parameters TEXT,
                source_file TEXT,
                example TEXT,
                version_added TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create search_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _generate_embedding(self, text: str) -> Optional[bytes]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Pickled embedding vector or None if embedding is not available
        """
        if not self.embedding_model:
            return None
        
        try:
            embedding = self.embedding_model.encode(text)
            return pickle.dumps(embedding)
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def _compute_similarity(self, embedding1: bytes, embedding2: bytes) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0-1)
        """
        if not EMBEDDINGS_AVAILABLE:
            return 0.0
        
        try:
            vec1 = pickle.loads(embedding1)
            vec2 = pickle.loads(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            self.logger.error(f"Error computing similarity: {str(e)}")
            return 0.0
    
    async def add_document(self, title: str, content: str, category: str, 
                          tags: Optional[List[str]] = None, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a document to the database.
        
        Args:
            title: Document title
            content: Document content
            category: Document category (e.g., 'tutorial', 'reference', 'guide')
            tags: List of tags
            source: Source of the document
            
        Returns:
            Dict with operation status
        """
        try:
            cursor = self.conn.cursor()
            
            # Generate embedding
            embedding = self._generate_embedding(f"{title} {content}")
            
            # Convert tags to string
            tags_str = None
            if tags:
                tags_str = ','.join(tags)
            
            # Insert document
            cursor.execute('''
            INSERT INTO documents (title, content, category, tags, source, embedding, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (title, content, category, tags_str, source, embedding))
            
            self.conn.commit()
            document_id = cursor.lastrowid
            
            console.print(f"[bold green]Added document: {title}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Added document: {title}",
                "document_id": document_id
            }
            
        except Exception as e:
            error_msg = f"Error adding document: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def add_code_snippet(self, title: str, code: str, language: str, 
                              description: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Add a code snippet to the database.
        
        Args:
            title: Snippet title
            code: Code content
            language: Programming language
            description: Description of the snippet
            tags: List of tags
            
        Returns:
            Dict with operation status
        """
        try:
            cursor = self.conn.cursor()
            
            # Generate embedding
            embedding_text = f"{title} {description or ''} {code}"
            embedding = self._generate_embedding(embedding_text)
            
            # Convert tags to string
            tags_str = None
            if tags:
                tags_str = ','.join(tags)
            
            # Insert code snippet
            cursor.execute('''
            INSERT INTO code_snippets (title, code, language, description, tags, embedding, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (title, code, language, description, tags_str, embedding))
            
            self.conn.commit()
            snippet_id = cursor.lastrowid
            
            console.print(f"[bold green]Added code snippet: {title}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Added code snippet: {title}",
                "snippet_id": snippet_id
            }
            
        except Exception as e:
            error_msg = f"Error adding code snippet: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def add_wp_function(self, function_name: str, signature: str, description: Optional[str] = None,
                             parameters: Optional[Dict[str, str]] = None, return_value: Optional[str] = None,
                             example: Optional[str] = None, version_added: Optional[str] = None,
                             deprecated: bool = False, source_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a WordPress function to the database.
        
        Args:
            function_name: Name of the function
            signature: Function signature
            description: Function description
            parameters: Dictionary of parameter names and descriptions
            return_value: Description of return value
            example: Example usage
            version_added: WordPress version when added
            deprecated: Whether the function is deprecated
            source_file: Source file where the function is defined
            
        Returns:
            Dict with operation status
        """
        try:
            cursor = self.conn.cursor()
            
            # Convert parameters to JSON string
            parameters_json = None
            if parameters:
                parameters_json = json.dumps(parameters)
            
            # Generate embedding
            embedding_text = f"{function_name} {signature} {description or ''}"
            embedding = self._generate_embedding(embedding_text)
            
            # Insert function
            cursor.execute('''
            INSERT OR REPLACE INTO wp_functions 
            (function_name, signature, description, parameters, return_value, example, 
             version_added, deprecated, source_file, embedding, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (function_name, signature, description, parameters_json, return_value, 
                  example, version_added, deprecated, source_file, embedding))
            
            self.conn.commit()
            function_id = cursor.lastrowid
            
            console.print(f"[bold green]Added WordPress function: {function_name}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Added WordPress function: {function_name}",
                "function_id": function_id
            }
            
        except Exception as e:
            error_msg = f"Error adding WordPress function: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def add_wp_hook(self, hook_name: str, hook_type: str, description: Optional[str] = None,
                         parameters: Optional[Dict[str, str]] = None, source_file: Optional[str] = None,
                         example: Optional[str] = None, version_added: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a WordPress hook to the database.
        
        Args:
            hook_name: Name of the hook
            hook_type: Type of hook ('action' or 'filter')
            description: Hook description
            parameters: Dictionary of parameter names and descriptions
            source_file: Source file where the hook is defined
            example: Example usage
            version_added: WordPress version when added
            
        Returns:
            Dict with operation status
        """
        try:
            cursor = self.conn.cursor()
            
            # Convert parameters to JSON string
            parameters_json = None
            if parameters:
                parameters_json = json.dumps(parameters)
            
            # Generate embedding
            embedding_text = f"{hook_name} {hook_type} {description or ''}"
            embedding = self._generate_embedding(embedding_text)
            
            # Insert hook
            cursor.execute('''
            INSERT OR REPLACE INTO wp_hooks 
            (hook_name, hook_type, description, parameters, source_file, example, 
             version_added, embedding, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (hook_name, hook_type, description, parameters_json, source_file, 
                  example, version_added, embedding))
            
            self.conn.commit()
            hook_id = cursor.lastrowid
            
            console.print(f"[bold green]Added WordPress hook: {hook_name}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Added WordPress hook: {hook_name}",
                "hook_id": hook_id
            }
            
        except Exception as e:
            error_msg = f"Error adding WordPress hook: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def search(self, query: str, categories: Optional[List[str]] = None, 
                    limit: int = 10, use_semantic: bool = True) -> Dict[str, Any]:
        """
        Search the database for relevant information.
        
        Args:
            query: Search query
            categories: List of categories to search in ('documents', 'code_snippets', 'wp_functions', 'wp_hooks')
            limit: Maximum number of results per category
            use_semantic: Whether to use semantic search (if available)
            
        Returns:
            Dict with search results
        """
        try:
            # Record search in history
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO search_history (query, result_count)
            VALUES (?, 0)
            ''', (query,))
            self.conn.commit()
            search_id = cursor.lastrowid
            
            # Default to all categories if none specified
            if not categories:
                categories = ['documents', 'code_snippets', 'wp_functions', 'wp_hooks']
            
            results = {}
            total_results = 0
            
            # Generate query embedding for semantic search
            query_embedding = None
            if use_semantic and self.embedding_model:
                query_embedding = self._generate_embedding(query)
            
            # Search in each category
            for category in categories:
                if category == 'documents':
                    results['documents'] = await self._search_documents(query, query_embedding, limit)
                    total_results += len(results['documents'])
                
                elif category == 'code_snippets':
                    results['code_snippets'] = await self._search_code_snippets(query, query_embedding, limit)
                    total_results += len(results['code_snippets'])
                
                elif category == 'wp_functions':
                    results['wp_functions'] = await self._search_wp_functions(query, query_embedding, limit)
                    total_results += len(results['wp_functions'])
                
                elif category == 'wp_hooks':
                    results['wp_hooks'] = await self._search_wp_hooks(query, query_embedding, limit)
                    total_results += len(results['wp_hooks'])
            
            # Update search history with result count
            cursor.execute('''
            UPDATE search_history
            SET result_count = ?
            WHERE id = ?
            ''', (total_results, search_id))
            self.conn.commit()
            
            # Display results summary
            console.print(f"[bold green]Found {total_results} results for query: {query}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Found {total_results} results",
                "query": query,
                "results": results,
                "total_results": total_results
            }
            
        except Exception as e:
            error_msg = f"Error searching database: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def _search_documents(self, query: str, query_embedding: Optional[bytes], limit: int) -> List[Dict[str, Any]]:
        """
        Search for documents matching the query.
        
        Args:
            query: Search query
            query_embedding: Query embedding for semantic search
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        cursor = self.conn.cursor()
        results = []
        
        # First try keyword search
        cursor.execute('''
        SELECT id, title, content, category, tags, source, embedding
        FROM documents
        WHERE title LIKE ? OR content LIKE ?
        LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        rows = cursor.fetchall()
        
        for row in rows:
            doc = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "category": row[3],
                "tags": row[4].split(',') if row[4] else [],
                "source": row[5],
                "relevance": 1.0  # Default relevance for keyword match
            }
            results.append(doc)
        
        # If semantic search is enabled and we have embeddings
        if query_embedding and len(results) < limit:
            # Get all documents not already in results
            existing_ids = [doc["id"] for doc in results]
            id_exclusion = f"AND id NOT IN ({','.join('?' for _ in existing_ids)})" if existing_ids else ""
            
            cursor.execute(f'''
            SELECT id, title, content, category, tags, source, embedding
            FROM documents
            WHERE embedding IS NOT NULL {id_exclusion}
            ''', existing_ids)
            
            semantic_candidates = cursor.fetchall()
            semantic_results = []
            
            for row in semantic_candidates:
                if row[6]:  # If embedding exists
                    similarity = self._compute_similarity(query_embedding, row[6])
                    if similarity > 0.7:  # Threshold for semantic similarity
                        doc = {
                            "id": row[0],
                            "title": row[1],
                            "content": row[2],
                            "category": row[3],
                            "tags": row[4].split(',') if row[4] else [],
                            "source": row[5],
                            "relevance": similarity
                        }
                        semantic_results.append(doc)
            
            # Sort by relevance and add to results
            semantic_results.sort(key=lambda x: x["relevance"], reverse=True)
            results.extend(semantic_results[:limit - len(results)])
        
        return results
    
    async def _search_code_snippets(self, query: str, query_embedding: Optional[bytes], limit: int) -> List[Dict[str, Any]]:
        """
        Search for code snippets matching the query.
        
        Args:
            query: Search query
            query_embedding: Query embedding for semantic search
            limit: Maximum number of results
            
        Returns:
            List of matching code snippets
        """
        cursor = self.conn.cursor()
        results = []
        
        # First try keyword search
        cursor.execute('''
        SELECT id, title, code, language, description, tags, embedding
        FROM code_snippets
        WHERE title LIKE ? OR code LIKE ? OR description LIKE ?
        LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        rows = cursor.fetchall()
        
        for row in rows:
            snippet = {
                "id": row[0],
                "title": row[1],
                "code": row[2],
                "language": row[3],
                "description": row[4],
                "tags": row[5].split(',') if row[5] else [],
                "relevance": 1.0  # Default relevance for keyword match
            }
            results.append(snippet)
        
        # If semantic search is enabled and we have embeddings
        if query_embedding and len(results) < limit:
            # Get all snippets not already in results
            existing_ids = [snippet["id"] for snippet in results]
            id_exclusion = f"AND id NOT IN ({','.join('?' for _ in existing_ids)})" if existing_ids else ""
            
            cursor.execute(f'''
            SELECT id, title, code, language, description, tags, embedding
            FROM code_snippets
            WHERE embedding IS NOT NULL {id_exclusion}
            ''', existing_ids)
            
            semantic_candidates = cursor.fetchall()
            semantic_results = []
            
            for row in semantic_candidates:
                if row[6]:  # If embedding exists
                    similarity = self._compute_similarity(query_embedding, row[6])
                    if similarity > 0.7:  # Threshold for semantic similarity
                        snippet = {
                            "id": row[0],
                            "title": row[1],
                            "code": row[2],
                            "language": row[3],
                            "description": row[4],
                            "tags": row[5].split(',') if row[5] else [],
                            "relevance": similarity
                        }
                        semantic_results.append(snippet)
            
            # Sort by relevance and add to results
            semantic_results.sort(key=lambda x: x["relevance"], reverse=True)
            results.extend(semantic_results[:limit - len(results)])
        
        return results
    
    async def _search_wp_functions(self, query: str, query_embedding: Optional[bytes], limit: int) -> List[Dict[str, Any]]:
        """
        Search for WordPress functions matching the query.
        
        Args:
            query: Search query
            query_embedding: Query embedding for semantic search
            limit: Maximum number of results
            
        Returns:
            List of matching WordPress functions
        """
        cursor = self.conn.cursor()
        results = []
        
        # First try keyword search
        cursor.execute('''
        SELECT id, function_name, signature, description, parameters, return_value, 
               example, version_added, deprecated, source_file, embedding
        FROM wp_functions
        WHERE function_name LIKE ? OR signature LIKE ? OR description LIKE ?
        LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        rows = cursor.fetchall()
        
        for row in rows:
            func = {
                "id": row[0],
                "function_name": row[1],
                "signature": row[2],
                "description": row[3],
                "parameters": json.loads(row[4]) if row[4] else {},
                "return_value": row[5],
                "example": row[6],
                "version_added": row[7],
                "deprecated": bool(row[8]),
                "source_file": row[9],
                "relevance": 1.0  # Default relevance for keyword match
            }
            results.append(func)
        
        # If semantic search is enabled and we have embeddings
        if query_embedding and len(results) < limit:
            # Get all functions not already in results
            existing_ids = [func["id"] for func in results]
            id_exclusion = f"AND id NOT IN ({','.join('?' for _ in existing_ids)})" if existing_ids else ""
            
            cursor.execute(f'''
            SELECT id, function_name, signature, description, parameters, return_value, 
                   example, version_added, deprecated, source_file, embedding
            FROM wp_functions
            WHERE embedding IS NOT NULL {id_exclusion}
            ''', existing_ids)
            
            semantic_candidates = cursor.fetchall()
            semantic_results = []
            
            for row in semantic_candidates:
                if row[10]:  # If embedding exists
                    similarity = self._compute_similarity(query_embedding, row[10])
                    if similarity > 0.7:  # Threshold for semantic similarity
                        func = {
                            "id": row[0],
                            "function_name": row[1],
                            "signature": row[2],
                            "description": row[3],
                            "parameters": json.loads(row[4]) if row[4] else {},
                            "return_value": row[5],
                            "example": row[6],
                            "version_added": row[7],
                            "deprecated": bool(row[8]),
                            "source_file": row[9],
                            "relevance": similarity
                        }
                        semantic_results.append(func)
            
            # Sort by relevance and add to results
            semantic_results.sort(key=lambda x: x["relevance"], reverse=True)
            results.extend(semantic_results[:limit - len(results)])
        
        return results
    
    async def _search_wp_hooks(self, query: str, query_embedding: Optional[bytes], limit: int) -> List[Dict[str, Any]]:
        """
        Search for WordPress hooks matching the query.
        
        Args:
            query: Search query
            query_embedding: Query embedding for semantic search
            limit: Maximum number of results
            
        Returns:
            List of matching WordPress hooks
        """
        cursor = self.conn.cursor()
        results = []
        
        # First try keyword search
        cursor.execute('''
        SELECT id, hook_name, hook_type, description, parameters, source_file, 
               example, version_added, embedding
        FROM wp_hooks
        WHERE hook_name LIKE ? OR description LIKE ?
        LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        rows = cursor.fetchall()
        
        for row in rows:
            hook = {
                "id": row[0],
                "hook_name": row[1],
                "hook_type": row[2],
                "description": row[3],
                "parameters": json.loads(row[4]) if row[4] else {},
                "source_file": row[5],
                "example": row[6],
                "version_added": row[7],
                "relevance": 1.0  # Default relevance for keyword match
            }
            results.append(hook)
        
        # If semantic search is enabled and we have embeddings
        if query_embedding and len(results) < limit:
            # Get all hooks not already in results
            existing_ids = [hook["id"] for hook in results]
            id_exclusion = f"AND id NOT IN ({','.join('?' for _ in existing_ids)})" if existing_ids else ""
            
            cursor.execute(f'''
            SELECT id, hook_name, hook_type, description, parameters, source_file, 
                   example, version_added, embedding
            FROM wp_hooks
            WHERE embedding IS NOT NULL {id_exclusion}
            ''', existing_ids)
            
            semantic_candidates = cursor.fetchall()
            semantic_results = []
            
            for row in semantic_candidates:
                if row[8]:  # If embedding exists
                    similarity = self._compute_similarity(query_embedding, row[8])
                    if similarity > 0.7:  # Threshold for semantic similarity
                        hook = {
                            "id": row[0],
                            "hook_name": row[1],
                            "hook_type": row[2],
                            "description": row[3],
                            "parameters": json.loads(row[4]) if row[4] else {},
                            "source_file": row[5],
                            "example": row[6],
                            "version_added": row[7],
                            "relevance": similarity
                        }
                        semantic_results.append(hook)
            
            # Sort by relevance and add to results
            semantic_results.sort(key=lambda x: x["relevance"], reverse=True)
            results.extend(semantic_results[:limit - len(results)])
        
        return results
    
    async def get_document(self, document_id: int) -> Dict[str, Any]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dict with document data
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT id, title, content, category, tags, source, created_at, updated_at
            FROM documents
            WHERE id = ?
            ''', (document_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"Document with ID {document_id} not found"
                }
            
            document = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "category": row[3],
                "tags": row[4].split(',') if row[4] else [],
                "source": row[5],
                "created_at": row[6],
                "updated_at": row[7]
            }
            
            return {
                "status": "success",
                "document": document
            }
            
        except Exception as e:
            error_msg = f"Error retrieving document: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def get_code_snippet(self, snippet_id: int) -> Dict[str, Any]:
        """
        Get a code snippet by ID.
        
        Args:
            snippet_id: Snippet ID
            
        Returns:
            Dict with snippet data
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT id, title, code, language, description, tags, created_at, updated_at
            FROM code_snippets
            WHERE id = ?
            ''', (snippet_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"Code snippet with ID {snippet_id} not found"
                }
            
            snippet = {
                "id": row[0],
                "title": row[1],
                "code": row[2],
                "language": row[3],
                "description": row[4],
                "tags": row[5].split(',') if row[5] else [],
                "created_at": row[6],
                "updated_at": row[7]
            }
            
            return {
                "status": "success",
                "snippet": snippet
            }
            
        except Exception as e:
            error_msg = f"Error retrieving code snippet: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def get_wp_function(self, function_id: int = None, function_name: str = None) -> Dict[str, Any]:
        """
        Get a WordPress function by ID or name.
        
        Args:
            function_id: Function ID
            function_name: Function name
            
        Returns:
            Dict with function data
        """
        if function_id is None and function_name is None:
            return {
                "status": "error",
                "message": "Either function_id or function_name must be provided"
            }
        
        try:
            cursor = self.conn.cursor()
            
            if function_id is not None:
                cursor.execute('''
                SELECT id, function_name, signature, description, parameters, return_value, 
                       example, version_added, deprecated, source_file, created_at, updated_at
                FROM wp_functions
                WHERE id = ?
                ''', (function_id,))
            else:
                cursor.execute('''
                SELECT id, function_name, signature, description, parameters, return_value, 
                       example, version_added, deprecated, source_file, created_at, updated_at
                FROM wp_functions
                WHERE function_name = ?
                ''', (function_name,))
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"WordPress function not found"
                }
            
            function = {
                "id": row[0],
                "function_name": row[1],
                "signature": row[2],
                "description": row[3],
                "parameters": json.loads(row[4]) if row[4] else {},
                "return_value": row[5],
                "example": row[6],
                "version_added": row[7],
                "deprecated": bool(row[8]),
                "source_file": row[9],
                "created_at": row[10],
                "updated_at": row[11]
            }
            
            return {
                "status": "success",
                "function": function
            }
            
        except Exception as e:
            error_msg = f"Error retrieving WordPress function: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def get_wp_hook(self, hook_id: int = None, hook_name: str = None) -> Dict[str, Any]:
        """
        Get a WordPress hook by ID or name.
        
        Args:
            hook_id: Hook ID
            hook_name: Hook name
            
        Returns:
            Dict with hook data
        """
        if hook_id is None and hook_name is None:
            return {
                "status": "error",
                "message": "Either hook_id or hook_name must be provided"
            }
        
        try:
            cursor = self.conn.cursor()
            
            if hook_id is not None:
                cursor.execute('''
                SELECT id, hook_name, hook_type, description, parameters, source_file, 
                       example, version_added, created_at, updated_at
                FROM wp_hooks
                WHERE id = ?
                ''', (hook_id,))
            else:
                cursor.execute('''
                SELECT id, hook_name, hook_type, description, parameters, source_file, 
                       example, version_added, created_at, updated_at
                FROM wp_hooks
                WHERE hook_name = ?
                ''', (hook_name,))
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"WordPress hook not found"
                }
            
            hook = {
                "id": row[0],
                "hook_name": row[1],
                "hook_type": row[2],
                "description": row[3],
                "parameters": json.loads(row[4]) if row[4] else {},
                "source_file": row[5],
                "example": row[6],
                "version_added": row[7],
                "created_at": row[8],
                "updated_at": row[9]
            }
            
            return {
                "status": "success",
                "hook": hook
            }
            
        except Exception as e:
            error_msg = f"Error retrieving WordPress hook: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def import_wp_documentation(self, docs_path: str) -> Dict[str, Any]:
        """
        Import WordPress documentation from a directory.
        
        Args:
            docs_path: Path to documentation directory
            
        Returns:
            Dict with import status
        """
        try:
            if not os.path.exists(docs_path):
                return {
                "status": "error",
                "message": f"Documentation path {docs_path} does not exist"
            }
            
            # Track import statistics
            stats = {
                "functions_added": 0,
                "hooks_added": 0,
                "documents_added": 0,
                "errors": []
            }
            
            # Process function documentation
            functions_path = os.path.join(docs_path, "functions")
            if os.path.exists(functions_path):
                for file_name in os.listdir(functions_path):
                    if file_name.endswith(".json"):
                        try:
                            with open(os.path.join(functions_path, file_name), 'r', encoding='utf-8') as f:
                                func_data = json.load(f)
                                
                                # Add function to database
                                await self.add_wp_function(
                                    function_name=func_data.get("function_name"),
                                    signature=func_data.get("signature"),
                                    description=func_data.get("description"),
                                    parameters=func_data.get("parameters"),
                                    return_value=func_data.get("return_value"),
                                    example=func_data.get("example"),
                                    version_added=func_data.get("version_added"),
                                    deprecated=func_data.get("deprecated", False),
                                    source_file=func_data.get("source_file")
                                )
                                stats["functions_added"] += 1
                                
                        except Exception as e:
                            error_msg = f"Error importing function from {file_name}: {str(e)}"
                            self.logger.error(error_msg)
                            stats["errors"].append(error_msg)
            
            # Process hook documentation
            hooks_path = os.path.join(docs_path, "hooks")
            if os.path.exists(hooks_path):
                for file_name in os.listdir(hooks_path):
                    if file_name.endswith(".json"):
                        try:
                            with open(os.path.join(hooks_path, file_name), 'r', encoding='utf-8') as f:
                                hook_data = json.load(f)
                                
                                # Add hook to database
                                await self.add_wp_hook(
                                    hook_name=hook_data.get("hook_name"),
                                    hook_type=hook_data.get("hook_type"),
                                    description=hook_data.get("description"),
                                    parameters=hook_data.get("parameters"),
                                    source_file=hook_data.get("source_file"),
                                    example=hook_data.get("example"),
                                    version_added=hook_data.get("version_added")
                                )
                                stats["hooks_added"] += 1
                                
                        except Exception as e:
                            error_msg = f"Error importing hook from {file_name}: {str(e)}"
                            self.logger.error(error_msg)
                            stats["errors"].append(error_msg)
            
            # Process markdown documentation
            docs_content_path = os.path.join(docs_path, "content")
            if os.path.exists(docs_content_path):
                for root, _, files in os.walk(docs_content_path):
                    for file_name in files:
                        if file_name.endswith(".md"):
                            try:
                                file_path = os.path.join(root, file_name)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # Extract title from first heading or use filename
                                title = file_name.replace(".md", "")
                                if content.startswith("# "):
                                    title = content.split("\n")[0].replace("# ", "")
                                
                                # Determine category from directory structure
                                rel_path = os.path.relpath(root, docs_content_path)
                                category = rel_path.replace("\\", "/").split("/")[0] if rel_path != "." else "general"
                                
                                # Add document to database
                                await self.add_document(
                                    title=title,
                                    content=content,
                                    category=category,
                                    source=file_path
                                )
                                stats["documents_added"] += 1
                                
                            except Exception as e:
                                error_msg = f"Error importing document from {file_name}: {str(e)}"
                                self.logger.error(error_msg)
                                stats["errors"].append(error_msg)
            
            # Display import summary
            console.print(f"[bold green]Import completed:[/bold green]")
            console.print(f"- Functions added: {stats['functions_added']}")
            console.print(f"- Hooks added: {stats['hooks_added']}")
            console.print(f"- Documents added: {stats['documents_added']}")
            
            if stats["errors"]:
                console.print(f"[bold yellow]Errors encountered: {len(stats['errors'])}[/bold yellow]")
            
            return {
                "status": "success",
                "message": "Documentation import completed",
                "stats": stats
            }
            
        except Exception as e:
            error_msg = f"Error importing WordPress documentation: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def export_database(self, export_path: str) -> Dict[str, Any]:
        """
        Export the database content to a directory.
        
        Args:
            export_path: Path to export directory
            
        Returns:
            Dict with export status
        """
        try:
            # Create export directory if it doesn't exist
            os.makedirs(export_path, exist_ok=True)
            
            # Create subdirectories
            functions_dir = os.path.join(export_path, "functions")
            hooks_dir = os.path.join(export_path, "hooks")
            documents_dir = os.path.join(export_path, "documents")
            snippets_dir = os.path.join(export_path, "code_snippets")
            
            os.makedirs(functions_dir, exist_ok=True)
            os.makedirs(hooks_dir, exist_ok=True)
            os.makedirs(documents_dir, exist_ok=True)
            os.makedirs(snippets_dir, exist_ok=True)
            
            cursor = self.conn.cursor()
            
            # Export functions
            cursor.execute("SELECT * FROM wp_functions")
            functions = cursor.fetchall()
            
            for func in functions:
                func_data = {
                    "id": func[0],
                    "function_name": func[1],
                    "signature": func[2],
                    "description": func[3],
                    "parameters": json.loads(func[4]) if func[4] else {},
                    "return_value": func[5],
                    "example": func[6],
                    "version_added": func[7],
                    "deprecated": bool(func[8]),
                    "source_file": func[9],
                    "created_at": func[11],
                    "updated_at": func[12]
                }
                
                file_path = os.path.join(functions_dir, f"{func[1]}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(func_data, f, indent=2)
            
            # Export hooks
            cursor.execute("SELECT * FROM wp_hooks")
            hooks = cursor.fetchall()
            
            for hook in hooks:
                hook_data = {
                    "id": hook[0],
                    "hook_name": hook[1],
                    "hook_type": hook[2],
                    "description": hook[3],
                    "parameters": json.loads(hook[4]) if hook[4] else {},
                    "source_file": hook[5],
                    "example": hook[6],
                    "version_added": hook[7],
                    "created_at": hook[9],
                    "updated_at": hook[10]
                }
                
                file_path = os.path.join(hooks_dir, f"{hook[1]}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(hook_data, f, indent=2)
            
            # Export documents
            cursor.execute("SELECT * FROM documents")
            documents = cursor.fetchall()
            
            for doc in documents:
                doc_data = {
                    "id": doc[0],
                    "title": doc[1],
                    "content": doc[2],
                    "category": doc[3],
                    "tags": doc[4].split(',') if doc[4] else [],
                    "source": doc[5],
                    "created_at": doc[7],
                    "updated_at": doc[8]
                }
                
                # Create category subdirectory
                category_dir = os.path.join(documents_dir, doc_data["category"])
                os.makedirs(category_dir, exist_ok=True)
                
                # Save as markdown file
                file_name = f"{doc_data['id']}_{self._sanitize_filename(doc_data['title'])}.md"
                file_path = os.path.join(category_dir, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {doc_data['title']}\n\n")
                    f.write(doc_data['content'])
                
                # Save metadata
                meta_path = os.path.join(category_dir, f"{doc_data['id']}_{self._sanitize_filename(doc_data['title'])}.json")
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(doc_data, f, indent=2)
            
            # Export code snippets
            cursor.execute("SELECT * FROM code_snippets")
            snippets = cursor.fetchall()
            
            for snippet in snippets:
                snippet_data = {
                    "id": snippet[0],
                    "title": snippet[1],
                    "code": snippet[2],
                    "language": snippet[3],
                    "description": snippet[4],
                    "tags": snippet[5].split(',') if snippet[5] else [],
                    "created_at": snippet[7],
                    "updated_at": snippet[8]
                }
                
                # Save as code file with appropriate extension
                ext = self._get_file_extension(snippet_data["language"])
                file_name = f"{snippet_data['id']}_{self._sanitize_filename(snippet_data['title'])}{ext}"
                file_path = os.path.join(snippets_dir, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(snippet_data['code'])
                
                # Save metadata
                meta_path = os.path.join(snippets_dir, f"{snippet_data['id']}_{self._sanitize_filename(snippet_data['title'])}.json")
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(snippet_data, f, indent=2)
            
            # Export database statistics
            stats = await self.get_statistics()
            stats_path = os.path.join(export_path, "database_stats.json")
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            console.print(f"[bold green]Database exported to {export_path}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Database exported to {export_path}",
                "export_path": export_path
            }
            
        except Exception as e:
            error_msg = f"Error exporting database: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be used as a filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:97] + '...'
        
        return filename
    
    def _get_file_extension(self, language: str) -> str:
        """
        Get the file extension for a programming language.
        
        Args:
            language: Programming Language
            
        Returns:
            File extension
        """
        extensions = {
            "php": ".php",
            "javascript": ".js",
            "js": ".js",
            "typescript": ".ts",
            "ts": ".ts",
            "python": ".py",
            "py": ".py",
            "css": ".css",
            "html": ".html",
            "sql": ".sql",
            "bash": ".sh",
            "shell": ".sh",
            "json": ".json",
            "xml": ".xml",
            "yaml": ".yml",
            "yml": ".yml",
            "markdown": ".md",
            "md": ".md"
        }
        
        return extensions.get(language.lower(), ".txt")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dict with database statistics
        """
        try:
            cursor = self.conn.cursor()
            stats = {}
            
            # Count documents
            cursor.execute("SELECT COUNT(*) FROM documents")
            stats["document_count"] = cursor.fetchone()[0]
            
            # Count code snippets
            cursor.execute("SELECT COUNT(*) FROM code_snippets")
            stats["code_snippet_count"] = cursor.fetchone()[0]
            
            # Count WordPress functions
            cursor.execute("SELECT COUNT(*) FROM wp_functions")
            stats["wp_function_count"] = cursor.fetchone()[0]
            
            # Count WordPress hooks
            cursor.execute("SELECT COUNT(*) FROM wp_hooks")
            stats["wp_hook_count"] = cursor.fetchone()[0]
            
            # Count searches
            cursor.execute("SELECT COUNT(*) FROM search_history")
            stats["search_count"] = cursor.fetchone()[0]
            
            # Get document categories
            cursor.execute("SELECT category, COUNT(*) FROM documents GROUP BY category")
            stats["document_categories"] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get code snippet languages
            cursor.execute("SELECT language, COUNT(*) FROM code_snippets GROUP BY language")
            stats["code_snippet_languages"] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get hook types
            cursor.execute("SELECT hook_type, COUNT(*) FROM wp_hooks GROUP BY hook_type")
            stats["hook_types"] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get database size
            stats["database_size_bytes"] = os.path.getsize(self.database_path)
            stats["database_size_mb"] = round(stats["database_size_bytes"] / (1024 * 1024), 2)
            
            # Get most searched queries
            cursor.execute('''
            SELECT query, COUNT(*) as count
            FROM search_history
            GROUP BY query
            ORDER BY count DESC
            LIMIT 10
            ''')
            stats["top_searches"] = [{"query": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # Get recently added items
            cursor.execute('''
            SELECT 'document' as type, title as name, created_at
            FROM documents
            UNION ALL
            SELECT 'code_snippet' as type, title as name, created_at
            FROM code_snippets
            UNION ALL
            SELECT 'wp_function' as type, function_name as name, created_at
            FROM wp_functions
            UNION ALL
            SELECT 'wp_hook' as type, hook_name as name, created_at
            FROM wp_hooks
            ORDER BY created_at DESC
            LIMIT 20
            ''')
            stats["recent_additions"] = [{"type": row[0], "name": row[1], "created_at": row[2]} for row in cursor.fetchall()]
            
            return stats
            
        except Exception as e:
            error_msg = f"Error getting database statistics: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    async def optimize_database(self) -> Dict[str, Any]:
        """
        Optimize the database by rebuilding indexes and vacuuming.
        
        Returns:
            Dict with optimization status
        """
        try:
            start_time = time.time()
            start_size = os.path.getsize(self.database_path)
            
            cursor = self.conn.cursor()
            
            # Analyze tables
            cursor.execute("ANALYZE")
            
            # Vacuum database
            cursor.execute("VACUUM")
            
            # Rebuild indexes
            cursor.execute("REINDEX")
            
            self.conn.commit()
            
            end_time = time.time()
            end_size = os.path.getsize(self.database_path)
            
            size_diff = start_size - end_size
            time_taken = round(end_time - start_time, 2)
            
            console.print(f"[bold green]Database optimized:[/bold green]")
            console.print(f"- Time taken: {time_taken} seconds")
            console.print(f"- Size before: {round(start_size / (1024 * 1024), 2)} MB")
            console.print(f"- Size after: {round(end_size / (1024 * 1024), 2)} MB")
            console.print(f"- Size reduction: {round(size_diff / (1024 * 1024), 2)} MB")
            
            return {
                "status": "success",
                "message": "Database optimized",
                "time_taken": time_taken,
                "size_before_bytes": start_size,
                "size_after_bytes": end_size,
                "size_reduction_bytes": size_diff
            }
            
        except Exception as e:
            error_msg = f"Error optimizing database: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def rebuild_embeddings(self) -> Dict[str, Any]:
        """
        Rebuild all embeddings in the database.
        
        Returns:
            Dict with rebuild status
        """
        if not self.embedding_model:
            return {
                "status": "error",
                "message": "Embedding model not available"
            }
        
        try:
            start_time = time.time()
            stats = {
                "documents_updated": 0,
                "code_snippets_updated": 0,
                "wp_functions_updated": 0,
                "wp_hooks_updated": 0,
                "errors": []
            }
            
            cursor = self.conn.cursor()
            
            # Update document embeddings
            cursor.execute("SELECT id, title, content FROM documents")
            documents = cursor.fetchall()
            
            for doc in documents:
                try:
                    doc_id, title, content = doc
                    embedding_text = f"{title} {content}"
                    embedding = self._generate_embedding(embedding_text)
                    
                    cursor.execute('''
                    UPDATE documents
                    SET embedding = ?
                    WHERE id = ?
                    ''', (embedding, doc_id))
                    
                    stats["documents_updated"] += 1
                    
                except Exception as e:
                    error_msg = f"Error updating embedding for document {doc[0]}: {str(e)}"
                    self.logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Update code snippet embeddings
            cursor.execute("SELECT id, title, code, description FROM code_snippets")
            snippets = cursor.fetchall()
            
            for snippet in snippets:
                try:
                    snippet_id, title, code, description = snippet
                    embedding_text = f"{title} {description or ''} {code}"
                    embedding = self._generate_embedding(embedding_text)
                    
                    cursor.execute('''
                    UPDATE code_snippets
                    SET embedding = ?
                    WHERE id = ?
                    ''', (embedding, snippet_id))
                    
                    stats["code_snippets_updated"] += 1
                    
                except Exception as e:
                    error_msg = f"Error updating embedding for code snippet {snippet[0]}: {str(e)}"
                    self.logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Update WordPress function embeddings
            cursor.execute("SELECT id, function_name, signature, description FROM wp_functions")
            functions = cursor.fetchall()
            
            for func in functions:
                try:
                    func_id, function_name, signature, description = func
                    embedding_text = f"{function_name} {signature or ''} {description or ''}"
                    embedding = self._generate_embedding(embedding_text)
                    
                    cursor.execute('''
                    UPDATE wp_functions
                    SET embedding = ?
                    WHERE id = ?
                    ''', (embedding, func_id))
                    
                    stats["wp_functions_updated"] += 1
                    
                except Exception as e:
                    error_msg = f"Error updating embedding for WordPress function {func[0]}: {str(e)}"
                    self.logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Update WordPress hook embeddings
            cursor.execute("SELECT id, hook_name, hook_type, description FROM wp_hooks")
            hooks = cursor.fetchall()
            
            for hook in hooks:
                try:
                    hook_id, hook_name, hook_type, description = hook
                    embedding_text = f"{hook_name} {hook_type} {description or ''}"
                    embedding = self._generate_embedding(embedding_text)
                    
                    cursor.execute('''
                    UPDATE wp_hooks
                    SET embedding = ?
                    WHERE id = ?
                    ''', (embedding, hook_id))
                    
                    stats["wp_hooks_updated"] += 1
                    
                except Exception as e:
                    error_msg = f"Error updating embedding for WordPress hook {hook[0]}: {str(e)}"
                    self.logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            self.conn.commit()
            
            end_time = time.time()
            time_taken = round(end_time - start_time, 2)
            
            console.print(f"[bold green]Embeddings rebuilt:[/bold green]")
            console.print(f"- Time taken: {time_taken} seconds")
            console.print(f"- Documents updated: {stats['documents_updated']}")
            console.print(f"- Code snippets updated: {stats['code_snippets_updated']}")
            console.print(f"- WordPress functions updated: {stats['wp_functions_updated']}")
            console.print(f"- WordPress hooks updated: {stats['wp_hooks_updated']}")
            
            if stats["errors"]:
                console.print(f"[bold yellow]Errors encountered: {len(stats['errors'])}[/bold yellow]")
            
            return {
                "status": "success",
                "message": "Embeddings rebuilt",
                "time_taken": time_taken,
                "stats": stats
            }
            
        except Exception as e:
            error_msg = f"Error rebuilding embeddings: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def delete_document(self, document_id: int) -> Dict[str, Any]:
        """
        Delete a document from the database.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dict with deletion status
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if document exists
            cursor.execute("SELECT title FROM documents WHERE id = ?", (document_id,))
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"Document with ID {document_id} not found"
                }
            
            document_title = row[0]
            
            # Delete document
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            self.conn.commit()
            
            console.print(f"[bold green]Deleted document: {document_title}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Deleted document: {document_title}",
                "document_id": document_id
            }
            
        except Exception as e:
            error_msg = f"Error deleting document: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def delete_code_snippet(self, snippet_id: int) -> Dict[str, Any]:
        """
        Delete a code snippet from the database.
        
        Args:
            snippet_id: Snippet ID
            
        Returns:
            Dict with deletion status
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if snippet exists
            cursor.execute("SELECT title FROM code_snippets WHERE id = ?", (snippet_id,))
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"Code snippet with ID {snippet_id} not found"
                }
            
            snippet_title = row[0]
            
            # Delete snippet
            cursor.execute("DELETE FROM code_snippets WHERE id = ?", (snippet_id,))
            self.conn.commit()
            
            console.print(f"[bold green]Deleted code snippet: {snippet_title}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Deleted code snippet: {snippet_title}",
                "snippet_id": snippet_id
            }
            
        except Exception as e:
            error_msg = f"Error deleting code snippet: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def delete_wp_function(self, function_id: int) -> Dict[str, Any]:
        """
        Delete a WordPress function from the database.
        
        Args:
            function_id: Function ID
            
        Returns:
            Dict with deletion status
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if function exists
            cursor.execute("SELECT function_name FROM wp_functions WHERE id = ?", (function_id,))
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"WordPress function with ID {function_id} not found"
                }
            
            function_name = row[0]
            
            # Delete function
            cursor.execute("DELETE FROM wp_functions WHERE id = ?", (function_id,))
            self.conn.commit()
            
            console.print(f"[bold green]Deleted WordPress function: {function_name}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Deleted WordPress function: {function_name}",
                "function_id": function_id
            }
            
        except Exception as e:
            error_msg = f"Error deleting WordPress function: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def delete_wp_hook(self, hook_id: int) -> Dict[str, Any]:
        """
        Delete a WordPress hook from the database.
        
        Args:
            hook_id: Hook ID
            
        Returns:
            Dict with deletion status
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if hook exists
            cursor.execute("SELECT hook_name FROM wp_hooks WHERE id = ?", (hook_id,))
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"WordPress hook with ID {hook_id} not found"
                }
            
            hook_name = row[0]
            
            # Delete hook
            cursor.execute("DELETE FROM wp_hooks WHERE id = ?", (hook_id,))
            self.conn.commit()
            
            console.print(f"[bold green]Deleted WordPress hook: {hook_name}[/bold green]")
            
            return {
                "status": "success",
                "message": f"Deleted WordPress hook: {hook_name}",
                "hook_id": hook_id
            }
            
        except Exception as e:
            error_msg = f"Error deleting WordPress hook: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def clear_search_history(self) -> Dict[str, Any]:
        """
        Clear the search history.
        
        Returns:
            Dict with operation status
        """
        try:
            cursor = self.conn.cursor()
            
            # Get count before deletion
            cursor.execute("SELECT COUNT(*) FROM search_history")
            count = cursor.fetchone()[0]
            
            # Delete all search history
            cursor.execute("DELETE FROM search_history")
            self.conn.commit()
            
            console.print(f"[bold green]Cleared search history ({count} entries)[/bold green]")
            
            return {
                                "status": "success",
                "message": f"Cleared search history ({count} entries)",
                "count": count
            }
            
        except Exception as e:
            error_msg = f"Error clearing search history: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def backup_database(self, backup_path: str = None) -> Dict[str, Any]:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path to save the backup file (optional)
            
        Returns:
            Dict with backup status
        """
        try:
            # Generate backup filename with timestamp if not provided
            if not backup_path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(os.path.dirname(self.database_path), "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, f"wp_rag_backup_{timestamp}.db")
            
            # Create backup directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Close connection temporarily
            self.conn.commit()
            self.conn.close()
            
            # Copy database file
            shutil.copy2(self.database_path, backup_path)
            
            # Reopen connection
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row
            
            console.print(f"[bold green]Database backed up to: {backup_path}[/bold green]")
            self.logger.info(f"Database backed up to: {backup_path}")
            
            return {
                "status": "success",
                "message": f"Database backed up to: {backup_path}",
                "backup_path": backup_path
            }
            
        except Exception as e:
            # Make sure connection is reopened even if backup fails
            if not self.conn:
                self.conn = sqlite3.connect(self.database_path)
                self.conn.row_factory = sqlite3.Row
                
            error_msg = f"Error backing up database: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def restore_database(self, backup_path: str) -> Dict[str, Any]:
        """
        Restore database from a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Dict with restore status
        """
        try:
            if not os.path.exists(backup_path):
                return {
                    "status": "error",
                    "message": f"Backup file not found: {backup_path}"
                }
            
            # Close connection
            self.conn.close()
            self.conn = None
            
            # Create a backup of current database before restoring
            current_backup = await self.backup_database()
            
            # Copy backup file to database path
            shutil.copy2(backup_path, self.database_path)
            
            # Reopen connection
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row
            
            console.print(f"[bold green]Database restored from: {backup_path}[/bold green]")
            console.print(f"[bold yellow]Previous database backed up to: {current_backup['backup_path']}[/bold yellow]")
            self.logger.info(f"Database restored from: {backup_path}. Previous database backed up to: {current_backup['backup_path']}")
            
            return {
                "status": "success",
                "message": f"Database restored from: {backup_path}",
                "previous_backup": current_backup['backup_path']
            }
            
        except Exception as e:
            # Make sure connection is reopened even if restore fails
            if not self.conn:
                self.conn = sqlite3.connect(self.database_path)
                self.conn.row_factory = sqlite3.Row
                
            error_msg = f"Error restoring database: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def list_backups(self) -> Dict[str, Any]:
        """
        List available database backups.
        
        Returns:
            Dict with list of backups
        """
        try:
            backup_dir = os.path.join(os.path.dirname(self.database_path), "backups")
            
            if not os.path.exists(backup_dir):
                return {
                    "status": "success",
                    "message": "No backups found",
                    "backups": []
                }
            
            backups = []
            for file in os.listdir(backup_dir):
                if file.startswith("wp_rag_backup_") and file.endswith(".db"):
                    file_path = os.path.join(backup_dir, file)
                    file_size = os.path.getsize(file_path)
                    file_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)) # Use datetime.datetime
                    
                    backups.append({
                        "filename": file,
                        "path": file_path,
                        "size_bytes": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2),
                        "date": file_date.strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # Sort by date (newest first)
            backups.sort(key=lambda x: x["date"], reverse=True)
            self.logger.info(f"Found {len(backups)} backups.")
            
            return {
                "status": "success",
                "message": f"Found {len(backups)} backups",
                "backups": backups
            }
            
        except Exception as e:
            error_msg = f"Error listing backups: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def get_search_history(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get search history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            Dict with search history
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT id, query, timestamp, result_count
            FROM search_history
            ORDER BY timestamp DESC
            LIMIT ?
            ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "id": row[0],
                    "query": row[1],
                    "timestamp": row[2],
                    "result_count": row[3]
                })
            self.logger.info(f"Retrieved {len(history)} search history entries.")
            
            return {
                "status": "success",
                "history": history
            }
            
        except Exception as e:
            error_msg = f"Error retrieving search history: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Database connection closed.")
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()
