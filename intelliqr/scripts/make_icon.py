
import sys
from pathlib import Path
from PIL import Image

def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python make_icon.py ruta\\a\\LOGO.jpeg")
        return 1
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"No se encontró: {src}")
        return 1
    dst = src.with_suffix(".ico")
    img = Image.open(src).convert("RGBA")
    # Windows espera un .ico con varios tamaños embebidos.
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(dst, format="ICO", sizes=sizes)
    print(f"Listo: {dst}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
