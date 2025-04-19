import os
import logging
from pathlib import Path

def initialize_directories():
    """Create required directories if they don't exist."""
    directories = [
        "chroma_db",
        "data",
        "logs",  
        "frontend/static",
        "frontend/templates"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logging.info(f"Directory created/verified: {directory}")
        except Exception as e:
            logging.error(f"Error creating directory {directory}: {e}")

def setup_logging():
    """Configure basic logging for the application."""
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

setup_logging()
initialize_directories() 