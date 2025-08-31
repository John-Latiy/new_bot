import os
from PIL import Image

def prepare_for_instagram(input_path: str, output_path: str = "data/ig_cover.jpg", variant: str = "portrait") -> str:
    """
    Приводит изображение к допустимому соотношению для IG:
      - portrait: 1080x1350 (4:5) — рекомендую
      - square:   1080x1080 (1:1)
      - landscape:1080x566  (~1.91:1)
    Сохраняет JPEG (кач-во 90). Возвращает путь к файлу.
    """
    targets = {
        "portrait":  (1080, 1350),
        "square":    (1080, 1080),
        "landscape": (1080, 566),
    }
    if variant not in targets:
        raise ValueError("variant must be one of: portrait, square, landscape")

    tw, th = targets[variant]
    im = Image.open(input_path).convert("RGB")
    # Вписываем в целевой прямоугольник
    im.thumbnail((tw, th), Image.LANCZOS)

    # Центруем на холсте (чёрный фон — можно поменять на белый (255,255,255))
    canvas = Image.new("RGB", (tw, th), (0, 0, 0))
    x = (tw - im.width) // 2
    y = (th - im.height) // 2
    canvas.paste(im, (x, y))
    # Сохраняем как JPEG
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, "JPEG", quality=90, optimize=True, progressive=True)
    return output_path
