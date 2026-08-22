import os
import json
import hashlib
from typing import Dict, Any, Optional
import pytesseract
from PIL import Image
import google.generativeai as genai
from backend.config import settings

_PROCESSED_HASHES = {}

def get_image_hash(image: Image.Image) -> str:
    return hashlib.md5(image.tobytes()).hexdigest()

def extract_ocr(image: Image.Image) -> str:
    try:
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception:
        return ""

def extract_vision_metadata(image: Image.Image) -> Dict[str, Any]:
    if not settings.google_api_key:
        return {}
        
    try:
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        
        prompt = (
            "Analyze this image and return a strict JSON object with these exact keys: "
            "'visual_summary' (string), "
            "'entities' (list of strings), "
            "'diagram_present' (boolean), "
            "'important_text' (string), "
            "'visual_relationships' (string). "
            "Do not include any formatting, markdown, or other text outside the JSON."
        )
        
        response = model.generate_content([prompt, image])
        
        if not response or not response.text:
            return {}
            
        json_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_text)
        
        return {
            "visual_summary": data.get("visual_summary"),
            "entities": data.get("entities", []),
            "diagram_present": data.get("diagram_present", False),
            "important_text": data.get("important_text"),
            "visual_relationships": data.get("visual_relationships")
        }
    except Exception:
        return {}

def process_image(image_path: str) -> Dict[str, Any]:
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            
            img_hash = get_image_hash(img)
            
            if img_hash in _PROCESSED_HASHES:
                return _PROCESSED_HASHES[img_hash]
                
            ocr_text = extract_ocr(img)
            
            vision_data = extract_vision_metadata(img)
            
            result = {
                "ocr_text": ocr_text,
                "visual_summary": vision_data.get("visual_summary"),
                "entities": vision_data.get("entities"),
                "diagram_present": vision_data.get("diagram_present"),
                "visual_relationships": vision_data.get("visual_relationships")
            }
            
            _PROCESSED_HASHES[img_hash] = result
            
            return result
    except Exception:
        return {}
