import os
import subprocess
import fitz
from PIL import Image, ImageDraw

def build_dataset():
    dirs = [
        "test_data/video",
        "test_data/audio",
        "test_data/images",
        "test_data/documents",
        "test_data/text"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    doc = fitz.open()
    page = doc.new_page()
    text_content = (
        "Distributed Database Sharding Architecture\n\n"
        "Database sharding distributes large databases across multiple machine nodes. "
        "The system uses horizontal partitioning, a Redis caching layer for fast key lookups, "
        "and an API Gateway router."
    )
    page.insert_text((50, 50), text_content, fontsize=12)
    doc.save("test_data/documents/architecture.pdf")
    doc.close()

    img = Image.new('RGB', (800, 600), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    d.text((100, 250), "ARCHITECTURE DIAGRAM: DB SHARDING & REDIS LAYER", fill=(56, 189, 248))
    img.save("test_data/images/architecture_diagram.png")

    with open("test_data/text/meeting_notes.txt", "w", encoding="utf-8") as f:
        f.write("Meeting Notes: Database sharding discussion centered on write scalability and partitioning strategies across distributed database nodes.")

    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-c:a", "libmp3lame", "test_data/audio/architecture_audio.mp3"
    ], capture_output=True)

    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=10:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
        "-pix_fmt", "yuv420p", "test_data/video/architecture_meeting.mp4"
    ], capture_output=True)

if __name__ == "__main__":
    build_dataset()
