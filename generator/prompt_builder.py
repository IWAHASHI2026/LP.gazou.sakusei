"""プロンプト構築モジュール - 商品画像のディテール保持と背景への自然な馴染みを両立するプロンプトを生成"""

BASE_PROMPT = """You are a professional photo compositor. Seamlessly composite the product from the FIRST image into the background scene from the SECOND image, creating a result that looks like a single photograph taken in that environment.

PRODUCT IDENTITY - PRESERVE THESE EXACTLY:
- Shape, silhouette, and proportions of the product
- All logos, brand names, labels, and text printed on the product
- Surface texture and material appearance (metal, glass, fabric, etc.)
- Do NOT crop or cut off any part of the product

NATURAL INTEGRATION - YOU MUST DO ALL OF THESE to make the product belong in the scene:
- Match the lighting direction and intensity of the background onto the product (highlights, shading)
- Apply the background's color temperature and ambient color cast to the product naturally
- Add realistic cast shadows and contact shadows that match the scene's light source
- If the background has warm/cool tones, let those subtly influence the product's appearance
- Add subtle reflections or bounce light from nearby surfaces where physically appropriate
- Ensure the product's edges blend naturally with the background (no hard cutout look)
- Match the depth of field and focus level of the background

The final image must look like a real photograph, not a cut-and-paste collage.
Do NOT add any text, watermarks, or overlays.

{placement}
{text_space}
{user_instructions}"""

PLACEMENT_VARIATIONS = [
    "Place the product in the center of the composition, as the clear focal point.",
    "Place the product slightly to the left of center, leaving space on the right for potential text placement.",
    "Place the product slightly to the right of center, leaving space on the left for potential text placement.",
    "Place the product in the lower-center area of the composition, with more background visible above.",
]

TEXT_SPACE_INSTRUCTIONS = {
    "none": "",
    "top-right": "IMPORTANT: Leave a large clean open space in the TOP-RIGHT area of the image for text overlay. Position the product toward the bottom-left to ensure the top-right area remains clear and uncluttered.",
    "right": "IMPORTANT: Leave a large clean open space on the RIGHT SIDE of the image for text overlay. Position the product toward the left side to ensure the right area remains clear and uncluttered.",
    "bottom-right": "IMPORTANT: Leave a large clean open space in the BOTTOM-RIGHT area of the image for text overlay. Position the product toward the top-left to ensure the bottom-right area remains clear and uncluttered.",
    "top-left": "IMPORTANT: Leave a large clean open space in the TOP-LEFT area of the image for text overlay. Position the product toward the bottom-right to ensure the top-left area remains clear and uncluttered.",
    "left": "IMPORTANT: Leave a large clean open space on the LEFT SIDE of the image for text overlay. Position the product toward the right side to ensure the left area remains clear and uncluttered.",
    "bottom-left": "IMPORTANT: Leave a large clean open space in the BOTTOM-LEFT area of the image for text overlay. Position the product toward the top-right to ensure the bottom-left area remains clear and uncluttered.",
    "top": "IMPORTANT: Leave a large clean open space in the TOP area of the image for text overlay. Position the product toward the bottom to ensure the top area remains clear and uncluttered.",
    "bottom": "IMPORTANT: Leave a large clean open space in the BOTTOM area of the image for text overlay. Position the product toward the top to ensure the bottom area remains clear and uncluttered.",
}


def build_prompt(user_instructions="", placement_index=0, text_space="none"):
    """商品保持を最優先にしたプロンプトを構築する"""
    placement = PLACEMENT_VARIATIONS[placement_index % len(PLACEMENT_VARIATIONS)]
    text_space_line = TEXT_SPACE_INSTRUCTIONS.get(text_space, "")
    instructions_line = f"Additional instructions: {user_instructions}" if user_instructions else ""
    return BASE_PROMPT.format(
        placement=placement,
        text_space=text_space_line,
        user_instructions=instructions_line,
    ).strip()


def build_variation_prompts(user_instructions="", count=1, text_space="none"):
    """複数バリエーション用のプロンプトリストを生成"""
    return [build_prompt(user_instructions, i, text_space) for i in range(count)]
