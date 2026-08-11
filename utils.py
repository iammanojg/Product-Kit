import io
import base64
from PIL import Image

def encode_image(image: Image.Image) -> str:
    """Resize and base64-encode image for Groq vision."""
    img = image.copy()
    img.thumbnail((800, 800))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
