import os
import sys
import subprocess
import threading
import time
import socket
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Default Streamlit port
STREAMLIT_PORT = 8501

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=8501, max_attempts=10):
    """Find an available port starting from start_port"""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    raise Exception(f"Could not find an available port after {max_attempts} attempts")

def update_frontend_config(streamlit_port):
    """Update the frontend configuration to point to the correct Streamlit port"""
    # Update setupProxy.js
    proxy_path = os.path.join('frontend', 'src', 'setupProxy.js')
    with open(proxy_path, 'r') as f:
        content = f.read()
    
    # Replace the port in the proxy configuration
    updated_content = content.replace(
        "target: 'http://localhost:8501'",
        f"target: 'http://localhost:{streamlit_port}'"
    )
    
    with open(proxy_path, 'w') as f:
        f.write(updated_content)
    
    # Update Index.tsx
    index_path = os.path.join('frontend', 'src', 'pages', 'Index.tsx')
    with open(index_path, 'r') as f:
        content = f.read()
    
    # Replace the port in the handleDemoClick function
    updated_content = content.replace(
        "window.location.href = 'http://localhost:8501/dashboard'",
        f"window.location.href = 'http://localhost:{streamlit_port}/dashboard'"
    )
    
    with open(index_path, 'w') as f:
        f.write(updated_content)
    
    print(f"Frontend configuration updated to use Streamlit port {streamlit_port}")

def run_streamlit(port):
    """Run the Streamlit dashboard with the correct base URL path and port"""
    print(f"Starting Streamlit dashboard on port {port}...")
    os.system(f"streamlit run src/dashboard/app.py --server.port={port} --server.baseUrlPath=dashboard")

def run_react():
    """Run the React frontend"""
    print("Starting React frontend...")
    os.chdir("frontend")
    os.system("npm start")

if __name__ == "__main__":
    # Find an available port for Streamlit
    port = find_available_port(STREAMLIT_PORT)
    print(f"Using port {port} for Streamlit")
    
    # Update frontend configuration to use the selected port
    update_frontend_config(port)
    
    # Start Streamlit in a separate thread
    streamlit_thread = threading.Thread(target=run_streamlit, args=(port,))
    streamlit_thread.daemon = True
    streamlit_thread.start()
    
    # Give Streamlit a moment to start
    time.sleep(3)
    
    # Start React in the main thread
    run_react()
