import os
import uuid
import urllib.request
import shutil
from backend.services.vision_processor import process_image

def test_vision_pipeline():
    session_id = f"test_vision_session_{uuid.uuid4().hex[:8]}"
    test_dir = os.path.join("storage", "uploads", session_id)
    os.makedirs(test_dir, exist_ok=True)
    
    # Download a test image that has text and maybe a diagram
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/React-icon.svg/512px-React-icon.svg.png"
    image_path = os.path.join(test_dir, "test_image.png")
    
    print("Downloading test image...")
    urllib.request.urlretrieve(image_url, image_path)
    
    print(f"Processing image: {image_path}")
    result = process_image(image_path)
    
    # Verify the structure has the required keys, even if empty due to no API key
    assert "ocr_text" in result
    assert "visual_summary" in result
    assert "entities" in result
    assert "diagram_present" in result
    assert "visual_relationships" in result
    
    # Test deduplication by calling again on the same image
    result2 = process_image(image_path)
    assert result == result2
    
    print("Vision pipeline test completed successfully.")
    
    shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    test_vision_pipeline()
