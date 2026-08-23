import sys
import os

def test_imports():
    try:
        import fastapi
        import streamlit
        import dotenv
        import pydantic
        
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        import backend.main
        import frontend.app
        print("Foundation imports successful!")
    except Exception as e:
        print(f"Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_imports()
