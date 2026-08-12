from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
import requests, io
import content.config as config
from bidi.algorithm import get_display


def prepare_text_for_rendering(text, script):
    """Convert logical Arabic text into the visual glyph order Pillow expects."""
    if script == "arabic":
        return get_display(arabic_reshaper.reshape(text))
    return text

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        #calculate width
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def create_post(news_item, settings):
    gradient_start = settings["gradient_color"]
    text_color = settings["text_color"]

    script = config.detect_script(news_item["title"])
    font_path = config.FONT_PATHS[script]

    #extract the image
    if not news_item["thumbnail"]:
        raise ValueError("news_item has contain no thumbnail URL")

    try:
        response = requests.get(news_item["thumbnail"], timeout=10)
        response.raise_for_status()
        bg_image = Image.open(io.BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"problem fetching data {e}")
        return None
    
    #crop and resize the background image
    bg_w, bg_h = bg_image.size
    scale = max(config.POST_WIDTH / bg_w, config.POST_HEIGHT / bg_h)
    new_w = int(bg_w * scale)
    new_h = int(bg_h * scale)
    bg_image = bg_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    #center the image
    left = (new_w - config.IMAGE_WIDTH) / 2
    top = (new_h - config.IMAGE_HEIGHT) / 2
    right = (new_w + config.IMAGE_WIDTH) / 2
    buttom = (new_h + config.IMAGE_HEIGHT) / 2
    canvas = bg_image.crop((left, top, right, buttom))

    #create and apply the gradient
      #create the overlay for the fradient
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(overlay)

    gradient_start_y = int(config.POST_HEIGHT * (1 - config.GRADIENT_HEIGHT_PCT))

    for y in range(gradient_start_y, config.POST_HEIGHT):
        # Calculate interpolation factor (0.0 at top of gradient, 1.0 at bottom)
        relation = (y - gradient_start_y) / (config.POST_HEIGHT - gradient_start_y)
        
        # Linearly interpolate RGBA values
        r = int(config.GRADIENT_END[0] + (gradient_start[0] - config.GRADIENT_END[0]) * relation)
        g = int(config.GRADIENT_END[1] + (gradient_start[1] - config.GRADIENT_END[1]) * relation)
        b = int(config.GRADIENT_END[2] + (gradient_start[2] - config.GRADIENT_END[2]) * relation)
        a = int(config.GRADIENT_END[3] + (gradient_start[3] - config.GRADIENT_END[3]) * relation)
        
        gradient_draw.line([(0, y), (config.POST_WIDTH, y)], fill=(r, g, b, a))

    # Alpha composite the gradient over the background image
    canvas = Image.alpha_composite(canvas, overlay)

    # 4. Draw the Text
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(font_path, config.FONT_SIZE)
    except IOError:
        print(f"Font file not found at {font_path}. Falling back to default system font.")
        font = ImageFont.load_default()
    
    # Wrap the title to fit within margins
    max_text_width = config.POST_WIDTH - (config.PADDING_X * 2)
    # Wrap the logical text first, then reshape every Arabic line for Pillow.
    # Pillow does not perform Arabic shaping or bidirectional text processing.
    wrapped_lines = wrap_text(news_item["title"], font, max_text_width)
    rendered_lines = [prepare_text_for_rendering(line, script) for line in wrapped_lines]

    # Calculate text rendering start position (Working from the bottom up)
    total_text_height = 0
    line_heights = []
    
    for line in rendered_lines:
        bbox = font.getbbox(line)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_text_height += h + config.LINE_SPACING
    total_text_height -= config.LINE_SPACING

    # Y coordinate where the first line of text should start
    current_y = config.POST_HEIGHT - config.PADDING_BOTTOM - total_text_height

    # Draw each line of text
    for i, line in enumerate(rendered_lines):
        if script == "arabic":
            # Arabic is right-to-left, so position each line against the right margin.
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            x = config.POST_WIDTH - config.PADDING_X - line_width
        else:
            x = config.PADDING_X
        draw.text((x, current_y), line, fill=text_color, font=font)
        current_y += line_heights[i] + config.LINE_SPACING

    # Convert back to RGB to save as JPEG if desired, or keep as PNG
    final_post = canvas.convert("RGB")
    return final_post
