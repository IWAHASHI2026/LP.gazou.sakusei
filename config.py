import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL_ID = "gemini-3.1-flash-image-preview"

IS_VERCEL = os.getenv("VERCEL", "") == "1"

if IS_VERCEL:
    UPLOAD_FOLDER = "/tmp/uploads"
    OUTPUT_FOLDER = "/tmp/output"
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "output")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

ASPECT_RATIOS = {
    "1:1 (正方形)": "1:1",
    "3:2 (横長)": "3:2",
    "2:3 (縦長)": "2:3",
    "4:3 (横長)": "4:3",
    "3:4 (縦長)": "3:4",
    "16:9 (ワイド)": "16:9",
    "9:16 (縦ワイド)": "9:16",
    "21:9 (超ワイド)": "21:9",
    "4:1 (バナー横)": "4:1",
    "1:4 (バナー縦)": "1:4",
}

MAX_PATTERNS = 4
OUTPUT_QUALITY = 95
