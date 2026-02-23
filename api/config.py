import os
import sys

# Ensure project root is on sys.path so db/ and utils/ are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY: str = os.getenv("PANEL_PASSWORD", "changeme")
ROOT_FOLDER: str = os.getenv("ROOT_FOLDER", ".")
