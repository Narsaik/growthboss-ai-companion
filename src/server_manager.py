"""
Server Manager - Controls the Flask web server process
"""
import os
import sys
import subprocess
import signal
import time
import requests
from pathlib import Path
import psutil

class ServerManager:
    def __init__(self, port=5000):
        self.port = port
        self.process = None
        self.project_root = Path(__file__).parent.parent
        self.server_script = self.project_root / 'scripts' / 'start_web_app.py'
        
    def is_running(self):
        """Check if server is running on the port"""
        try:
            response = requests.get(f'http://localhost:{self.port}/api/health', timeout=2)
            return response.status_code == 200
        except:
            # Check if port is in use
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'start_web_app.py' in cmdline or f':{self.port}' in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return False
    
    def start(self):
        """Start the Flask server"""
        if self.is_running():
            return True, "Server is already running"
        
        try:
            # Start server in background
            if sys.platform == 'win32':
                # Windows
                self.process = subprocess.Popen(
                    [sys.executable, str(self.server_script)],
                    cwd=str(self.project_root),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                # Unix/Linux/Mac
                self.process = subprocess.Popen(
                    [sys.executable, str(self.server_script)],
                    cwd=str(self.project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
            
            # Wait a bit and check if it started
            time.sleep(3)
            if self.is_running():
                return True, "Server started successfully"
            else:
                return False, "Server failed to start"
        except Exception as e:
            return False, f"Error starting server: {str(e)}"
    
    def stop(self):
        """Stop the Flask server"""
        try:
            # Try to find and kill the process
            killed = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'start_web_app.py' in cmdline:
                            proc.kill()
                            killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Also try to kill by port
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc.kill()
                        killed = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            if self.process:
                try:
                    if sys.platform == 'win32':
                        self.process.terminate()
                    else:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except:
                    pass
                self.process = None
            
            time.sleep(1)
            return True, "Server stopped" if killed or self.process else "Server was not running"
        except Exception as e:
            return False, f"Error stopping server: {str(e)}"
    
    def get_url(self):
        """Get the server URL"""
        return f"http://localhost:{self.port}"





