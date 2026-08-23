import os
import subprocess
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

def generate():
    os.makedirs("test_data", exist_ok=True)
    
    # 1. Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Database Sharding Architecture", ln=True, align='C')
    pdf.multi_cell(0, 10, txt="Database sharding was discussed as a method to split data across multiple machines. It improves write scalability. The architecture uses horizontal partitioning.")
    pdf.output("test_data/test_document.pdf")
    
    # 2. Generate Image
    img = Image.new('RGB', (800, 600), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((100, 250), "ARCHITECTURE DIAGRAM: Database Sharding", fill=(255, 255, 0))
    img.save("test_data/test_diagram.jpg")
    
    # 3. Generate Audio
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=5",
        "-c:a", "libmp3lame", "test_data/test_audio.mp3"
    ], capture_output=True)
    
    # 4. Generate Video (with audio)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=5:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=5",
        "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
        "-pix_fmt", "yuv420p", "test_data/test_video.mp4"
    ], capture_output=True)

if __name__ == "__main__":
    generate()
    print("Test data generated in test_data/")
