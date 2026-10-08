"""WCAG contrast maths for theme validation."""

_LINEAR_THRESHOLD = 0.03928


def _channel(value: int) -> float:
    scaled = value / 255
    return scaled / 12.92 if scaled <= _LINEAR_THRESHOLD else ((scaled + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    red, green, blue = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    """WCAG 2 contrast ratio between two ``#RRGGBB`` colours (1.0 to 21.0)."""
    lighter, darker = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)
