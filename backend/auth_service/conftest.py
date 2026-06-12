import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))
