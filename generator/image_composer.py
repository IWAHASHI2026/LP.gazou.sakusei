"""画像合成モジュール - Nano Banana 2 (Gemini API) を使用した商品×背景の合成"""

import io
import time
from PIL import Image as PILImage
from google import genai
from google.genai import types

from config import MODEL_ID, OUTPUT_QUALITY
from generator.prompt_builder import build_variation_prompts


def _create_client(api_key):
    return genai.Client(api_key=api_key)


def compose_single(client, product_bytes, background_bytes, prompt, aspect_ratio):
    """1枚の合成画像を生成する

    Args:
        client: genai.Client
        product_bytes: 商品画像のバイトデータ
        background_bytes: 背景画像のバイトデータ
        prompt: 合成指示プロンプト
        aspect_ratio: アスペクト比 (例: "16:9")

    Returns:
        生成画像のバイトデータ (JPEG) or None
    """
    product_img = PILImage.open(io.BytesIO(product_bytes))
    background_img = PILImage.open(io.BytesIO(background_bytes))

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            prompt,
            product_img,
            background_img,
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
            ),
        ),
    )

    # レスポンスから画像データを抽出し、JPEG に変換
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                return _convert_to_jpeg(part.inline_data.data)
    return None


def _convert_to_jpeg(image_data):
    """画像データをJPEGに変換"""
    img = PILImage.open(io.BytesIO(image_data))
    if img.mode == "RGBA":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=OUTPUT_QUALITY)
    return buf.getvalue()


def generate_variations(api_key, product_bytes, background_bytes, aspect_ratio,
                        count=1, user_instructions="", text_space="none",
                        progress_callback=None):
    """複数バリエーションの合成画像を生成する

    Args:
        api_key: Google API Key
        product_bytes: 商品画像のバイトデータ
        background_bytes: 背景画像のバイトデータ
        aspect_ratio: アスペクト比
        count: 生成枚数 (1-4)
        user_instructions: ユーザーの追加指示
        progress_callback: 進捗コールバック fn(completed, total)

    Returns:
        list[bytes]: 生成画像のバイトデータリスト
    """
    client = _create_client(api_key)
    prompts = build_variation_prompts(user_instructions, count, text_space)
    results = []

    for i, prompt in enumerate(prompts):
        image_data = _call_with_retry(client, product_bytes, background_bytes, prompt, aspect_ratio)
        if image_data:
            results.append(image_data)
        if progress_callback:
            progress_callback(i + 1, count)

    return results


def _call_with_retry(client, product_bytes, background_bytes, prompt, aspect_ratio, max_retries=3):
    """リトライ付きAPI呼び出し（429エラー対応）"""
    for attempt in range(max_retries):
        try:
            return compose_single(client, product_bytes, background_bytes, prompt, aspect_ratio)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
                continue
            raise
    return None
