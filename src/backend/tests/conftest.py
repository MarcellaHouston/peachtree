import sys
import os

# Add the project root (parent of this tests/ folder) to sys.path so that
# `import app` and `from sql_db import Database` resolve correctly when
# pytest is run from any working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
