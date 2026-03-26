"""プロンプト構築モジュール - 商品画像の完全保持を最優先にしたプロンプトを生成"""

BASE_PROMPT = """You are compositing a product photo onto a background image for an e-commerce landing page.

The FIRST image is the PRODUCT photo. The SECOND image is the BACKGROUND.

CRITICAL RULES - YOU MUST FOLLOW ALL OF THESE:
- Place the product from the first image onto the background from the second image
- The product MUST remain EXACTLY as it appears in the first image
- Do NOT modify ANY detail of the product: shape, color, texture, labels, logos, text on product, reflections, or materials
- Only adjust lighting and shadows AROUND the product to match the background environment
- The product should look naturally placed in the scene
- Do NOT add any text, watermarks, or overlays
- Do NOT crop or cut off any part of the product
- Maintain the product's original proportions

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
