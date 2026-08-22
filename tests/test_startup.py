from backend.config import check_system_dependencies, create_required_directories, settings
import os
import sys

def test_system_dependencies_check_runs():
    deps = check_system_dependencies()
    assert isinstance(deps, dict)
    assert "ffmpeg" in deps
    assert "tesseract" in deps
    assert "google_api_key" in deps
    print("test_system_dependencies_check_runs: PASSED")

def test_directory_creation():
    create_required_directories()
    assert os.path.exists("storage/uploads")
    assert os.path.exists("storage/processed")
    assert os.path.exists("chroma_db")
    assert os.path.exists("graph")
    print("test_directory_creation: PASSED")

def test_config_loads_env_var():
    assert hasattr(settings, "google_api_key")
    print("test_config_loads_env_var: PASSED")

if __name__ == "__main__":
    # Simulate pytest
    try:
        test_system_dependencies_check_runs()
        test_directory_creation()
        test_config_loads_env_var()
        print("ALL TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
