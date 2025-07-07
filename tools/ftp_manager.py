import os
import ftplib
import asyncio
import logging
import datetime
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

# Configure logging for the FTPManager
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console = Console()

class FTPManager:
    """FTP Manager for WordPress installations and file management."""
    
    def __init__(self):
        self.connections = {}
        self.current_connection = None
        self.logger = logging.getLogger("FTPManager")
    
    async def connect(self, host: str, username: str, password: str, port: int = 21, 
                     connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to an FTP server.
        
        Args:
            host: FTP server hostname
            username: FTP username
            password: FTP password
            port: FTP port (default: 21)
            connection_name: Optional name for this connection
            
        Returns:
            Dict with connection status and details
        """
        if not connection_name:
            connection_name = f"{username}@{host}"
        
        self.logger.info(f"Attempting to connect to {host}:{port} as {username} (Connection: {connection_name})")

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Connecting to FTP server..."),
            console=console
        ) as progress:
            progress.add_task("connect", total=None)
            
            try:
                # Create FTP connection
                ftp = ftplib.FTP()
                ftp.connect(host, port, timeout=10) # Add timeout for connection
                ftp.login(username, password)
                
                # Store connection
                self.connections[connection_name] = {
                    "ftp": ftp,
                    "host": host,
                    "username": username,
                    "port": port,
                    "current_dir": ftp.pwd()
                }
                
                self.current_connection = connection_name
                
                # Get welcome message
                welcome = ftp.getwelcome()
                
                console.print(f"[bold green]Connected to {host}[/bold green]")
                console.print(Panel(welcome, title="Server Welcome", border_style="green"))
                self.logger.info(f"Successfully connected to {host} as {username}. Welcome message: {welcome}")
                
                return {
                    "status": "success",
                    "message": f"Connected to {host}",
                    "connection_name": connection_name,
                    "welcome": welcome,
                    "current_dir": ftp.pwd()
                }
            except ftplib.all_errors as e: # Catch all ftplib-specific errors
                error_msg = f"FTP connection failed to {host}: {str(e)}"
                self.logger.error(error_msg, exc_info=True) # Log exception details
                console.print(f"[bold red]Error:[/bold red] {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg
                }
            except ConnectionRefusedError as e:
                error_msg = f"Connection refused by {host}:{port}. Check host and port, and ensure FTP server is running: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                console.print(f"[bold red]Error:[/bold red] {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg
                }
            except TimeoutError as e:
                error_msg = f"Connection to {host}:{port} timed out. Check network connectivity or server availability: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                console.print(f"[bold red]Error:[/bold red] {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg
                }
            except Exception as e: # Catch any other unexpected errors
                error_msg = f"An unexpected error occurred while connecting to {host}: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                console.print(f"[bold red]Error:[/bold red] {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg
                }
    
    async def disconnect(self, connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Disconnect from an FTP server.
        
        Args:
            connection_name: Name of the connection to disconnect
            
        Returns:
            Dict with disconnection status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": f"No active connection named '{connection_name}'"
            }
        
        try:
            ftp = self.connections[connection_name]["ftp"]
            ftp.quit()
            del self.connections[connection_name]
            
            if self.current_connection == connection_name:
                self.current_connection = None if not self.connections else list(self.connections.keys())[0]
            
            console.print(f"[bold green]Disconnected from {connection_name}[/bold green]")
            self.logger.info(f"Successfully disconnected from {connection_name}")
            
            return {
                "status": "success",
                "message": f"Disconnected from {connection_name}"
            }
            
        except ftplib.all_errors as e:
            error_msg = f"FTP disconnection failed for {connection_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while disconnecting from {connection_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def list_files(self, remote_path: Optional[str] = None, 
                        connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        List files in the specified remote directory.
        
        Args:
            remote_path: Remote directory path (default: current directory)
            connection_name: Name of the connection to use
            
        Returns:
            Dict with file listing
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            if remote_path:
                ftp.cwd(remote_path)
                conn["current_dir"] = ftp.pwd()
            
            current_dir = conn["current_dir"]
            
            # Get file listing
            files = []
            directories = []
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Fetching file listing..."),
                console=console
            ) as progress:
                task = progress.add_task("list", total=None)
                
                def process_line(line):
                    parts = line.split()
                    if len(parts) >= 9:
                        # Check if it's a directory (starts with 'd')
                        is_dir = parts[0].startswith('d')
                        name = ' '.join(parts[8:])
                        size = parts[4]
                        date = ' '.join(parts[5:8])
                        
                        if is_dir:
                            directories.append({"name": name, "date": date})
                        else:
                            files.append({"name": name, "size": size, "date": date})
                
                ftp.retrlines('LIST', process_line)
            
            # Display results in a table
            table = Table(title=f"Contents of {current_dir}")
            table.add_column("Type", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Size", style="magenta")
            table.add_column("Date", style="yellow")
            
            for d in directories:
                table.add_row("DIR", d["name"], "", d["date"])
            
            for f in files:
                table.add_row("FILE", f["name"], f["size"], f["date"])
            
            console.print(table)
            
            console.print(f"[bold green]Listed contents of {current_dir}[/bold green]")
            self.logger.info(f"Successfully listed contents of {current_dir}. Found {len(directories)} directories and {len(files)} files.")
            
            return {
                "status": "success",
                "current_dir": current_dir,
                "directories": directories,
                "files": files
            }
            
        except ftplib.all_errors as e:
            error_msg = f"FTP error listing files in {remote_path or 'current directory'}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while listing files: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def upload_file(self, local_path: str, remote_path: Optional[str] = None,
                         connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to the FTP server.
        
        Args:
            local_path: Path to the local file
            remote_path: Remote path (default: current directory with same filename)
            connection_name: Name of the connection to use
            
        Returns:
            Dict with upload status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            if not os.path.exists(local_path):
                return {
                    "status": "error",
                    "message": f"Local file not found: {local_path}"
                }
            
            filename = os.path.basename(local_path)
            
            if not remote_path:
                remote_path = filename
            elif remote_path.endswith('/'):
                remote_path = remote_path + filename
            
            # Get file size for progress tracking
            file_size = os.path.getsize(local_path)
            
            with Progress(
                TextColumn("[bold blue]Uploading..."),
                BarColumn(),
                TextColumn("[bold green]{task.percentage:.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("upload", total=file_size)
                
                # Custom callback to update progress
                uploaded = 0
                
                def callback(data):
                    nonlocal uploaded
                    uploaded += len(data)
                    progress.update(task, completed=uploaded)
                
                with open(local_path, 'rb') as file:
                    ftp.storbinary(f'STOR {remote_path}', file, 8192, callback)
            
            console.print(f"[bold green]Successfully uploaded {local_path} to {remote_path}[/bold green]")
            
            self.logger.info(f"Successfully uploaded {local_path} to {remote_path}")
            
            return {
                "status": "success",
                "message": f"Uploaded {local_path} to {remote_path}",
                "local_path": local_path,
                "remote_path": remote_path
            }
            
        except FileNotFoundError:
            error_msg = f"Local file not found: {local_path}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
        except ftplib.all_errors as e:
            error_msg = f"FTP error uploading {local_path} to {remote_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while uploading file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def download_file(self, remote_path: str, local_path: Optional[str] = None,
                           connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a file from the FTP server.
        
        Args:
            remote_path: Path to the remote file
            local_path: Local path (default: current directory with same filename)
            connection_name: Name of the connection to use
            
        Returns:
            Dict with download status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            filename = os.path.basename(remote_path)
            
            if not local_path:
                local_path = filename
            elif os.path.isdir(local_path):
                local_path = os.path.join(local_path, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            
            # Get file size for progress tracking (if possible)
            try:
                file_size = ftp.size(remote_path)
            except:
                file_size = 0  # Unknown size
            
            with Progress(
                TextColumn("[bold blue]Downloading..."),
                BarColumn(),
                TextColumn("[bold green]{task.percentage:.0f}%" if file_size else ""),
                console=console
            ) as progress:
                task = progress.add_task("download", total=file_size if file_size else None)
                
                # Custom callback to update progress
                downloaded = 0
                
                def callback(data):
                    nonlocal downloaded
                    downloaded += len(data)
                    if file_size:
                        progress.update(task, completed=downloaded)
                
                with open(local_path, 'wb') as file:
                    ftp.retrbinary(f'RETR {remote_path}', lambda data: (file.write(data), callback(data)))
            
            console.print(f"[bold green]Successfully downloaded {remote_path} to {local_path}[/bold green]")
            
            self.logger.info(f"Successfully downloaded {remote_path} to {local_path}")
            
            return {
                "status": "success",
                "message": f"Downloaded {remote_path} to {local_path}",
                "remote_path": remote_path,
                "local_path": local_path
            }
            
        except ftplib.all_errors as e:
            error_msg = f"FTP error downloading {remote_path} to {local_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while downloading file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def create_directory(self, remote_path: str, connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a directory on the FTP server.
        
        Args:
            remote_path: Path of the directory to create
            connection_name: Name of the connection to use
            
        Returns:
            Dict with creation status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            ftp.mkd(remote_path)
            console.print(f"[bold green]Created directory: {remote_path}[/bold green]")
            
            self.logger.info(f"Successfully created directory: {remote_path}")
            
            return {
                "status": "success",
                "message": f"Created directory: {remote_path}"
            }
            
        except ftplib.all_errors as e:
            error_msg = f"FTP error creating directory {remote_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while creating directory: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def delete_file(self, remote_path: str, connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a file from the FTP server.
        
        Args:
            remote_path: Path to the remote file
            connection_name: Name of the connection to use
            
        Returns:
            Dict with deletion status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            # Confirm deletion
            if Confirm.ask(f"Are you sure you want to delete {remote_path}?"):
                ftp.delete(remote_path)
                console.print(f"[bold green]Deleted file: {remote_path}[/bold green]")
                self.logger.info(f"Successfully deleted file: {remote_path}")
                
                return {
                    "status": "success",
                    "message": f"Deleted file: {remote_path}" 
                }
            else:
                console.print("[bold yellow]Deletion canceled[/bold yellow]")
                self.logger.info(f"Deletion of {remote_path} canceled by user.")
                return {
                    "status": "canceled",
                    "message": "Deletion canceled"
                }
        except ftplib.all_errors as e:
            error_msg = f"FTP error deleting file {remote_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while deleting file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def delete_directory(self, remote_path: str, connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a directory from the FTP server.
        
        Args:
            remote_path: Path to the remote directory
            connection_name: Name of the connection to use
            
        Returns:
            Dict with deletion status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            # Confirm deletion
            if Confirm.ask(f"Are you sure you want to delete directory {remote_path}?"):
                # First, we need to delete all files in the directory
                ftp.cwd(remote_path)
                files = []
                
                def process_line(line):
                    parts = line.split()
                    if len(parts) >= 9:
                        # Skip . and ..
                        name = ' '.join(parts[8:])
                        if name not in ['.', '..']:
                            # Check if it's a directory (starts with 'd')
                            is_dir = parts[0].startswith('d')
                            files.append({"name": name, "is_dir": is_dir})
                
                ftp.retrlines('LIST', process_line)
                
                # Delete all files first
                for file in files:
                    if not file["is_dir"]:
                        ftp.delete(file["name"])
                    else:
                        # Recursively delete subdirectories
                        # Call asynchronously if possible, otherwise directly
                        await self.delete_directory(f"{remote_path}/{file['name']}", connection_name)
                
                # Go back to parent directory
                ftp.cwd('..')
                
                # Delete the directory
                ftp.rmd(remote_path)
                
                console.print(f"[bold green]Deleted directory: {remote_path}[/bold green]")
                self.logger.info(f"Successfully deleted directory: {remote_path}")
                
                return {
                    "status": "success",
                    "message": f"Deleted directory: {remote_path}"
                }
            else:
                console.print("[bold yellow]Directory deletion canceled[/bold yellow]")
                self.logger.info(f"Deletion of directory {remote_path} canceled by user.")
                return {
                    "status": "cancelled",
                    "message": "Directory deletion cancelled"
                }
            
        except ftplib.all_errors as e:
            error_msg = f"FTP error deleting directory {remote_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while deleting directory: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }    
    async def rename_file(self, remote_path: str, new_name: str, connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Rename a file on the FTP server.
        
        Args:
            remote_path: Path to the remote file
            new_name: New name for the file
            connection_name: Name of the connection to use
            
        Returns:
            Dict with rename status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            # Get the directory and filename
            directory = os.path.dirname(remote_path)
            if not directory:
                directory = ftp.pwd()
            
            new_path = os.path.join(directory, new_name)
            
            # Rename the file
            ftp.rename(remote_path, new_path)
            
            console.print(f"[bold green]Renamed {remote_path} to {new_path}[/bold green]")
            
            self.logger.info(f"Successfully renamed {remote_path} to {new_path}")
            
            return {
                "status": "success",
                "message": f"Renamed {remote_path} to {new_path}",
                "old_path": remote_path,
                "new_path": new_path
            }
            
        except ftplib.all_errors as e:
            error_msg = f"FTP error renaming {remote_path} to {new_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while renaming file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def change_directory(self, remote_path: str, connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Change the current directory on the FTP server.
        
        Args:
            remote_path: Path to change to
            connection_name: Name of the connection to use
            
        Returns:
            Dict with change directory status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            ftp.cwd(remote_path)
            current_dir = ftp.pwd()
            conn["current_dir"] = current_dir
            
            console.print(f"[bold green]Changed directory to: {current_dir}[/bold green]")
            
            self.logger.info(f"Successfully changed directory to: {current_dir}")
            
            return {
                "status": "success",
                "message": f"Changed directory to: {current_dir}",
                "current_dir": current_dir
            }
            
        except ftplib.all_errors as e:
            error_msg = f"FTP error changing directory to {remote_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while changing directory: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def list_connections(self) -> Dict[str, Any]:
        """
        List all active FTP connections.
        
        Returns:
            Dict with connection information
        """
        if not self.connections:
            console.print("[yellow]No active FTP connections[/yellow]")
            return {
                "status": "success",
                "message": "No active FTP connections",
                "connections": []
            }
        
        connections_info = []
        
        for name, conn in self.connections.items():
            connections_info.append({
                "name": name,
                "host": conn["host"],
                "username": conn["username"],
                "current_dir": conn["current_dir"],
                "is_current": name == self.current_connection
            })
        
        # Display connections in a table
        table = Table(title="Active FTP Connections")
        table.add_column("Name", style="cyan")
        table.add_column("Host", style="green")
        table.add_column("Username", style="yellow")
        table.add_column("Current Directory", style="magenta")
        table.add_column("Current", style="bold")
        
        for conn in connections_info:
            table.add_row(
                conn["name"],
                conn["host"],
                conn["username"],
                conn["current_dir"],
                "✓" if conn["is_current"] else ""
            )
        
        console.print(table)
        
        return {
            "status": "success",
            "message": f"{len(connections_info)} active connection(s)",
            "connections": connections_info
        }
    
    async def switch_connection(self, connection_name: str) -> Dict[str, Any]:
        """
        Switch to a different FTP connection.
        
        Args:
            connection_name: Name of the connection to switch to
            
        Returns:
            Dict with switch status
        """
        if connection_name not in self.connections:
            return {
                "status": "error",
                "message": f"No connection named '{connection_name}'"
            }
        
        self.current_connection = connection_name
        conn = self.connections[connection_name]
        
        console.print(f"[bold green]Switched to connection: {connection_name}[/bold green]")
        console.print(f"Current directory: {conn['current_dir']}")
        
        return {
            "status": "success",
            "message": f"Switched to connection: {connection_name}",
            "current_dir": conn["current_dir"]
        }
    
    async def upload_wordpress_theme(self, theme_path: str, remote_path: Optional[str] = None,
                                   connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a WordPress theme to the FTP server.
        
        Args:
            theme_path: Path to the local theme directory
            remote_path: Remote path (default: wp-content/themes/)
            connection_name: Name of the connection to use
            
        Returns:
            Dict with upload status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        if not os.path.isdir(theme_path):
            return {
                "status": "error",
                "message": f"Theme directory not found: {theme_path}"
            }
        
        # Default remote path for WordPress themes
        if not remote_path:
            remote_path = "wp-content/themes"
        
        # Get theme name from directory
        theme_name = os.path.basename(os.path.normpath(theme_path))
        theme_remote_path = f"{remote_path}/{theme_name}"
        
        try:
            conn = self.connections[connection_name]
            ftp = conn["ftp"]
            
            # Create theme directory on server
            try:
                ftp.mkd(theme_remote_path)
            except:
                # Directory might already exist
                pass
            
            # Upload all theme files
            uploaded_files = 0
            failed_files = 0
            
            with Progress(
                TextColumn("[bold blue]Uploading theme..."),
                BarColumn(),
                TextColumn("[bold green]{task.completed}/{task.total} files"),
                console=console
            ) as progress:
                # Count total files
                total_files = 0
                for root, _, files in os.walk(theme_path):
                    total_files += len(files)
                
                task = progress.add_task("upload", total=total_files)
                
                for root, dirs, files in os.walk(theme_path):
                    # Create remote directories
                    for dir_name in dirs:
                        local_dir = os.path.join(root, dir_name)
                        rel_path = os.path.relpath(local_dir, theme_path)
                        remote_dir = f"{theme_remote_path}/{rel_path.replace(os.sep, '/')}"
                        
                        try:
                            ftp.mkd(remote_dir)
                        except:
                            # Directory might already exist
                            pass
                    
                    # Upload files
                    for file_name in files:
                        local_file = os.path.join(root, file_name)
                        rel_path = os.path.relpath(local_file, theme_path)
                        remote_file = f"{theme_remote_path}/{rel_path.replace(os.sep, '/')}"
                        
                        try:
                            with open(local_file, 'rb') as file:
                                ftp.storbinary(f'STOR {remote_file}', file)
                            uploaded_files += 1
                        except Exception as e:
                            self.logger.error(f"Error uploading {local_file}: {str(e)}")
                            failed_files += 1
                        
                        progress.update(task, advance=1)
            
            result_message = f"Theme upload complete: {uploaded_files} files uploaded"
            if failed_files > 0:
                result_message += f", {failed_files} files failed"
            
            console.print(f"[bold green]{result_message}[/bold green]")
            
            return {
                "status": "success",
                "message": result_message,
                "theme_name": theme_name,
                "remote_path": theme_remote_path,
                "uploaded_files": uploaded_files,
                "failed_files": failed_files
            }
            
        except Exception as e:
            error_msg = f"Error uploading theme: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def upload_wordpress_plugin(self, plugin_path: str, remote_path: Optional[str] = None,
                                    connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a WordPress plugin to the FTP server.
        
        Args:
            plugin_path: Path to the local plugin directory
            remote_path: Remote path (default: wp-content/plugins/)
            connection_name: Name of the connection to use
            
        Returns:
            Dict with upload status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        if not os.path.isdir(plugin_path):
            return {
                "status": "error",
                "message": f"Plugin directory not found: {plugin_path}"
            }
        
        # Default remote path for WordPress plugins
        if not remote_path:
            remote_path = "wp-content/plugins"
        
        # Get plugin name from directory
        plugin_name = os.path.basename(os.path.normpath(plugin_path))
        plugin_remote_path = f"{remote_path}/{plugin_name}"
        
        try:
            conn = self.connections[connection_name]
            ftp = conn["ftp"]
            
            # Create plugin directory on server
            try:
                ftp.mkd(plugin_remote_path)
            except:
                # Directory might already exist
                pass
            
            # Upload all plugin files
            uploaded_files = 0
            failed_files = 0
            
            with Progress(
                TextColumn("[bold blue]Uploading plugin..."),
                BarColumn(),
                TextColumn("[bold green]{task.completed}/{task.total} files"),
                console=console
            ) as progress:
                # Count total files
                total_files = 0
                for root, _, files in os.walk(plugin_path):
                    total_files += len(files)
                
                task = progress.add_task("upload", total=total_files)
                
                for root, dirs, files in os.walk(plugin_path):
                    # Create remote directories
                    for dir_name in dirs:
                        local_dir = os.path.join(root, dir_name)
                        rel_path = os.path.relpath(local_dir, plugin_path)
                        remote_dir = f"{plugin_remote_path}/{rel_path.replace(os.sep, '/')}"
                        
                        try:
                            ftp.mkd(remote_dir)
                        except:
                            # Directory might already exist
                            pass
                    
                    # Upload files # Upload files
                    for file_name in files:
                        local_file = os.path.join(root, file_name)
                        rel_path = os.path.relpath(local_file, plugin_path)
                        remote_file = f"{plugin_remote_path}/{rel_path.replace(os.sep, '/')}"
                        
                        try:
                            with open(local_file, 'rb') as file:
                                ftp.storbinary(f'STOR {remote_file}', file)
                            uploaded_files += 1
                        except Exception as e:
                            self.logger.error(f"Error uploading {local_file}: {str(e)}")
                            failed_files += 1
                        
                        progress.update(task, advance=1)
            
            result_message = f"Plugin upload complete: {uploaded_files} files uploaded"
            if failed_files > 0:
                result_message += f", {failed_files} files failed"
            
            console.print(f"[bold green]{result_message}[/bold green]")
            
            return {
                "status": "success",
                "message": result_message,
                "plugin_name": plugin_name,
                "remote_path": plugin_remote_path,
                "uploaded_files": uploaded_files,
                "failed_files": failed_files
            }
            
        except Exception as e:
            error_msg = f"Error uploading plugin: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def backup_wordpress_site(self, backup_dir: str, remote_path: str = "/", 
                                  connection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Backup a WordPress site from the FTP server.
        
        Args:
            backup_dir: Local directory to store the backup
            remote_path: Remote path to backup (default: root directory)
            connection_name: Name of the connection to use
            
        Returns:
            Dict with backup status
        """
        if not connection_name:
            connection_name = self.current_connection
        
        if not connection_name or connection_name not in self.connections:
            return {
                "status": "error",
                "message": "No active FTP connection"
            }
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        conn = self.connections[connection_name]
        ftp = conn["ftp"]
        
        try:
            # Save current directory
            original_dir = conn["current_dir"]
            
            # Change to the specified remote directory
            ftp.cwd(remote_path)
            
            # Get timestamp for backup folder
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"wp_backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            # Start backup process
            console.print(f"[bold blue]Starting WordPress backup to {backup_path}[/bold blue]")
            
            # Track statistics
            downloaded_files = 0
            failed_files = 0
            
            # Recursive function to download directory contents
            async def download_directory(remote_dir, local_dir, progress_task=None):
                nonlocal downloaded_files, failed_files
                
                # Create local directory
                os.makedirs(local_dir, exist_ok=True)
                
                # Change to remote directory
                ftp.cwd(remote_dir)
                
                # Get file listing
                files = []
                directories = []
                
                def process_line(line):
                    parts = line.split()
                    if len(parts) >= 9:
                        # Skip . and ..
                        name = ' '.join(parts[8:])
                        if name not in ['.', '..']:
                            is_dir = parts[0].startswith('d')
                            if is_dir:
                                directories.append(name)
                            else:
                                files.append(name)
                
                ftp.retrlines('LIST', process_line)
                
                # Download files
                for file_name in files:
                    remote_file = f"{remote_dir}/{file_name}"
                    local_file = os.path.join(local_dir, file_name)
                    
                    try:
                        with open(local_file, 'wb') as file:
                            ftp.retrbinary(f'RETR {file_name}', file.write)
                        downloaded_files += 1
                        if progress_task:
                            progress.update(progress_task, advance=1)
                    except Exception as e:
                        self.logger.error(f"Error downloading {remote_file}: {str(e)}")
                        failed_files += 1
                
                # Process subdirectories
                for dir_name in directories:
                    next_remote_dir = f"{remote_dir}/{dir_name}"
                    next_local_dir = os.path.join(local_dir, dir_name)
                    await download_directory(next_remote_dir, next_local_dir, progress_task)
                
                # Go back to parent directory
                ftp.cwd('..')
            
            # Count total files for progress tracking
            total_files = 0
            
            def count_files(dir_path):
                nonlocal total_files
                
                ftp.cwd(dir_path)
                
                files = []
                directories = []
                
                def process_line(line):
                    parts = line.split()
                    if len(parts) >= 9:
                        name = ' '.join(parts[8:])
                        if name not in ['.', '..']:
                            is_dir = parts[0].startswith('d')
                            if is_dir:
                                directories.append(name)
                            else:
                                files.append(name)
                                total_files += 1
                
                ftp.retrlines('LIST', process_line)
                
                for dir_name in directories:
                    count_files(f"{dir_path}/{dir_name}")
                
                ftp.cwd('..')
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Counting files..."),
                console=console
            ) as progress:
                progress.add_task("count", total=None)
                count_files(remote_path)
            
            # Start download with progress tracking
            with Progress(
                TextColumn("[bold blue]Backing up WordPress site..."),
                BarColumn(),
                TextColumn("[bold green]{task.completed}/{task.total} files"),
                console=console
            ) as progress:
                task = progress.add_task("backup", total=total_files)
                await download_directory(remote_path, backup_path, task)
            
            # Restore original directory
            ftp.cwd(original_dir)
            
            result_message = f"Backup complete: {downloaded_files} files downloaded to {backup_path}"
            if failed_files > 0:
                result_message += f", {failed_files} files failed"
            
            console.print(f"[bold green]{result_message}[/bold green]")
            
            return {
                "status": "success",
                "message": result_message,
                "backup_path": backup_path,
                "downloaded_files": downloaded_files,
                "failed_files": failed_files
            }
            
        except Exception as e:
            error_msg = f"Error backing up WordPress site: {str(e)}"
            self.logger.error(error_msg)
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            return {
                "status": "error",
                "message": error_msg
            }

    async def interactive_mode(self) -> None:
        """
        Start an interactive FTP session with a visual terminal interface.
        """
        # Define command completions
        commands = [
            "connect", "disconnect", "list", "upload", "download", "mkdir", 
            "rmdir", "delete", "rename", "cd", "pwd", "connections", "switch",
            "upload-theme", "upload-plugin", "backup", "help", "exit"
        ]
        
        command_completer = WordCompleter(commands)
        
        # Define prompt style
        style = Style.from_dict({
            'prompt': 'bold cyan',
        })
        
        # Create session
        session = PromptSession(completer=command_completer, style=style)
        
        console.print(Panel.fit(
            "[bold green]WordPress FTP Manager Interactive Mode[/bold green]\n"
            "Type [bold]help[/bold] for a list of commands or [bold]exit[/bold] to quit.",
            title="FTP Manager",
            border_style="blue"
        ))
        
        while True:
            try:
                # Show current connection in prompt
                prompt = f"[FTP:{self.current_connection or 'Not connected'}] > "
                
                # Get command
                command = await session.prompt_async(prompt)
                command = command.strip()
                
                if not command:
                    continue
                
                # Parse command and arguments
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                # Process commands
                if cmd == "exit":
                    # Disconnect all connections before exiting
                    for conn_name in list(self.connections.keys()):
                        await self.disconnect(conn_name)
                    
                    console.print("[bold green]Exiting FTP Manager[/bold green]")
                    break
                
                elif cmd == "help":
                    self._show_help()
                
                elif cmd == "connect":
                    # Interactive connection
                    host = Prompt.ask("Host")
                    username = Prompt.ask("Username")
                    # Log username but not password for security
                    self.logger.info(f"Interactive connect prompt: Host={host}, User={username}")
                    password = Prompt.ask("Password", password=True) 
                    port = Prompt.ask("Port", default="21")
                    name = Prompt.ask("Connection name (optional)", default="")
            
                    await self.connect(
                        host=host,
                        username=username,
                        password=password,
                        port=int(port),
                        connection_name=name if name else None
                    )
                
                elif cmd == "disconnect":
                    if len(args) > 0:
                        await self.disconnect(args[0])
                    else:
                        await self.disconnect()
                
                elif cmd == "list":
                    if len(args) > 0:
                        await self.list_files(args[0])
                    else:
                        await self.list_files()
                
                elif cmd == "upload":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing local file path[/bold red]")
                        continue
                    
                    local_path = args[0]
                    remote_path = args[1] if len(args) > 1 else None
                    
                    await self.upload_file(local_path, remote_path)
                
                elif cmd == "download":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing remote file path[/bold red]")
                        continue
                    
                    remote_path = args[0]
                    local_path = args[1] if len(args) > 1 else None
                    
                    await self.download_file(remote_path, local_path)
                
                elif cmd == "mkdir" or cmd == "md":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing directory name[/bold red]")
                        continue
                    
                    await self.create_directory(args[0])
                
                elif cmd == "rmdir" or cmd == "rd":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing directory name[/bold red]")
                        continue
                    
                    await self.delete_directory(args[0])
                
                elif cmd == "delete" or cmd == "del" or cmd == "rm":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing file name[/bold red]")
                        continue
                    
                    await self.delete_file(args[0])
                
                elif cmd == "rename" or cmd == "ren":
                    if len(args) < 2:
                        console.print("[bold red]Error: Missing file name or new name[/bold red]")
                        continue
                    
                    await self.rename_file(args[0], args[1])
                
                elif cmd == "cd":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing directory path[/bold red]")
                        continue
                    
                    await self.change_directory(args[0])
                
                elif cmd == "pwd":
                    if not self.current_connection:
                        console.print("[bold red]Error: Not connected[/bold red]")
                        continue
                    
                    conn = self.connections[self.current_connection]
                    console.print(f"Current directory: [bold green]{conn['current_dir']}[/bold green]")
                
                elif cmd == "connections":
                    await self.list_connections()
                
                elif cmd == "switch":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing connection name[/bold red]")
                        continue
                    
                    await self.switch_connection(args[0])
                
                elif cmd == "upload-theme":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing theme directory path[/bold red]")
                        continue
                    
                    theme_path = args[0]
                    remote_path = args[1] if len(args) > 1 else None
                    
                    await self.upload_wordpress_theme(theme_path, remote_path)
                
                elif cmd == "upload-plugin":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing plugin directory path[/bold red]")
                        continue
                    
                    plugin_path = args[0]
                    remote_path = args[1] if len(args) > 1 else None
                    
                    await self.upload_wordpress_plugin(plugin_path, remote_path)
                
                elif cmd == "backup":
                    if len(args) < 1:
                        console.print("[bold red]Error: Missing backup directory path[/bold red]")
                        continue
                    
                    backup_dir = args[0]
                    remote_path = args[1] if len(args) > 1 else "/"
                    
                    await self.backup_wordpress_site(backup_dir, remote_path)
                
                else:
                    console.print(f"[bold red]Unknown command: {cmd}[/bold red]")
                    console.print("Type [bold]help[/bold] for a list of commands")
            
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Operation cancelled[/bold yellow]")
            except Exception as e:
                console.print(f"[bold red]Error: {str(e)}[/bold red]")
    
    def _show_help(self) -> None:
        """Display help information for interactive mode."""
        help_text = """
[bold]Available Commands:[/bold]

[bold cyan]Connection Management:[/bold cyan]
  [bold]connect[/bold]      - Connect to an FTP server
  [bold]disconnect[/bold]   - Disconnect from the current FTP server
  [bold]connections[/bold]  - List all active connections
  [bold]switch[/bold]       - Switch to a different connection

[bold cyan]Navigation:[/bold cyan]
  [bold]list[/bold]         - List files in the current directory
  [bold]cd[/bold]           - Change directory
  [bold]pwd[/bold]          - Show current directory

[bold cyan]File Operations:[/bold cyan]
  [bold]upload[/bold]       - Upload a file to the server
  [bold]download[/bold]     - Download a file from the server
  [bold]mkdir[/bold]        - Create a directory
  [bold]rmdir[/bold]        - Delete a directory
  [bold]delete[/bold]       - Delete a file
  [bold]rename[/bold]       - Rename a file

[bold cyan]WordPress Operations:[/bold cyan]
  [bold]upload-theme[/bold] - Upload a WordPress theme
  [bold]upload-plugin[/bold] - Upload a WordPress plugin
  [bold]backup[/bold]       - Backup a WordPress site

[bold cyan]Other:[/bold cyan]
  [bold]help[/bold]         - Show this help message
  [bold]exit[/bold]         - Exit the FTP manager
"""
        console.print(Panel(help_text, title="FTP Manager Help", border_style="green"))
