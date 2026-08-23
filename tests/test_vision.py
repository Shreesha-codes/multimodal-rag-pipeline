import os
import uuid
import shutil
from backend.services.vision_processor import process_image

def test_vision_pipeline():
    image_path = "test_data/images/architecture_diagram.png"
    if not os.path.exists(image_path):
        return
        
    result = process_image(image_path)
    
    assert "ocr_text" in result
    assert "visual_summary" in result
    assert "entities" in result
    assert "diagram_present" in result
    assert "visual_relationships" in result
    
    result2 = process_image(image_path)
    assert result == result2

if __name__ == "__main__":
    test_vision_pipeline()
