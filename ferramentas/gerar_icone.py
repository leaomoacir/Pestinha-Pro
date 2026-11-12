"""
Gera o ícone oficial .ico e .png do Pestinha Pro com o rostinho e olhos fofos.
"""
import io
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz))

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter
from PySide6.QtWidgets import QApplication

from pestinha.body.desenho_rosto import draw_face, PADRAO
from pestinha.core.emotion import EYE_SHAPES

def gerar_icone():
    app = QApplication.instance() or QApplication([])

    size = 256
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)

    # Centraliza e escala para preencher confortavelmente o ícone
    p.translate(size / 2, size / 2)
    p.scale(1.85, 1.85)

    # Desenha o rosto observando com olhinhos brilhantes
    draw_face(p, EYE_SHAPES["observando"], gaze=(0.0, -0.05), blink=1.0, emotion="observando", aparencia=PADRAO)
    p.end()

    # Converte QImage para PIL Image
    buffer = img.bits()
    bytes_per_line = img.bytesPerLine()
    raw = bytes(buffer[0:bytes_per_line * size])
    pil_img = Image.frombuffer("RGBA", (size, size), raw, "raw", "BGRA", 0, 1)

    raiz = Path(__file__).resolve().parent.parent
    saida_png = raiz / "assets" / "comum" / "icone.png"
    saida_ico = raiz / "assets" / "comum" / "icone.ico"

    saida_png.parent.mkdir(parents=True, exist_ok=True)
    pil_img.save(str(saida_png), format="PNG")

    # Salva .ico com mipmaps de todos os tamanhos padrões do Windows
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    pil_img.save(str(saida_ico), format="ICO", sizes=sizes)

    print(f"Icone gerado com sucesso em:\n{saida_png}\n{saida_ico}")

if __name__ == "__main__":
    gerar_icone()
