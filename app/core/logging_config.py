# app/core/logging_config.py
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/psychsync/app.log')
        ]
    )

# Create a logger for use throughout the application
logger = logging.getLogger(__name__)

