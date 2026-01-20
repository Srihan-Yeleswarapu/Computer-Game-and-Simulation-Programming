WIDTH, HEIGHT = 960, 600
BG = "#0f1326"
TEXT = "#f5f6f7"

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
