"""Genera docs/Manual_Usuario.pdf a partir de docs/MANUAL_USUARIO.md.

Convierte el Markdown a HTML con un estilo para impresión y lo imprime con Microsoft Edge (o Chrome)
sin interfaz. Uso:  python docs/generar_manual_pdf.py
Requiere el paquete `markdown` (está en requirements-dev.txt).
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

DOCS = Path(__file__).resolve().parent
ORIGEN = DOCS / "MANUAL_USUARIO.md"
DESTINO = DOCS / "Manual_Usuario.pdf"

ESTILO = """
@page { size: Letter; margin: 1.4cm 1.6cm; }
body { font-family: "Segoe UI", Calibri, Arial, sans-serif; font-size: 10pt; line-height: 1.38; color: #1d1d1f; }
h1 { font-size: 17pt; margin: 0 0 4px; color: #8b1a1a; }
h2 { font-size: 12.5pt; margin: 12px 0 4px; color: #8b1a1a; border-bottom: 1px solid #ddd; padding-bottom: 2px;
     break-after: avoid; }
p, li { margin: 3px 0; }
ul, ol { margin: 3px 0; padding-left: 20px; }
img { display: block; max-width: 100%; max-height: 6.6cm; margin: 5px auto 8px; border: 1px solid #ccc;
      border-radius: 4px; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 3px 6px; text-align: left; vertical-align: top; }
th { background: #f3f3f3; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #f3f3f3; padding: 0 3px; border-radius: 3px; }
a { color: #1f5fa8; }
"""


def navegador():
    for c in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              shutil.which("msedge"), shutil.which("google-chrome"), shutil.which("chromium")):
        if c and Path(c).exists():
            return c
    sys.exit("No se encontró Microsoft Edge ni Chrome para imprimir el PDF.")


def main():
    cuerpo = markdown.markdown(ORIGEN.read_text(encoding="utf-8"), extensions=["tables"])
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Manual de usuario</title>'
            f"<style>{ESTILO}</style></head><body>{cuerpo}</body></html>")
    # el HTML se escribe junto al manual para que las rutas img/... funcionen
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=DOCS, delete=False, encoding="utf-8") as f:
        f.write(html)
        temporal = Path(f.name)
    try:
        subprocess.run([navegador(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={DESTINO}", temporal.as_uri()], check=True, timeout=120,
                       capture_output=True)
    finally:
        temporal.unlink(missing_ok=True)
    paginas = len(re.findall(rb"/Type\s*/Page[^s]", DESTINO.read_bytes()))
    print(f"{DESTINO.name}: {paginas} página(s)")
    if paginas > 5:
        sys.exit("El manual supera las 5 páginas que permite el enunciado.")


if __name__ == "__main__":
    main()
