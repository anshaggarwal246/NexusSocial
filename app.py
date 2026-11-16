"""
Social Media Database Project - Main Entry Point
Run with: python app.py
"""
import sys
from server import run_server

if __name__ == '__main__':
    port = 5000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
