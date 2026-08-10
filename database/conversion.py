def gradient_tuple_to_hex(rgba_tuple: tuple) -> str:
    """Converts an (R, G, B, A) tuple into a hex color string ('#RRGGBB').

    (Note: The alpha channel is ignored in standard hex representation).
    """
    r, g, b, *alpha = rgba_tuple

    # Format integers as 2-character uppercase hex strings
    return f"#{r:02X}{g:02X}{b:02X}"

def hex_to_gradient_tuple(hex_color: str, alpha: int = 230) -> tuple:
    # Remove the hash symbol if present
    hex_color = hex_color.lstrip("#")

    # Handle 3-digit shorthand hex (e.g., '#F0A' -> '#FF00AA')
    if len(hex_color) == 3:
        hex_color = "".join([char * 2 for char in hex_color])

    if len(hex_color) != 6:
        raise ValueError(
            f"Invalid hex color: '{hex_color}'. Must be 3 or 6 characters."
        )

    # Convert hex pairs to integer values for Red, Green, and Blue
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b, alpha)