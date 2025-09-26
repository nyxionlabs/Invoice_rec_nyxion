import sys, os

# Add app folder to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import Flask app
from app import app as application

if __name__ == "__main__":
    application.run()