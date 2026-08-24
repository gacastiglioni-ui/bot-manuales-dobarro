"""
Indexa manuales PDF: extrae texto por página, lo trocea en fragmentos
y guarda un índice de búsqueda (TF-IDF) en disco como JSON + pickle.

Uso:
    python3 indexar.py /ruta/al/manual.pdf
"""
import sys
import json
import pickle
import re
from pathlib import Path

import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer

CHUNK_SIZE_WORDS = 220   # tamaño aprox. de cada fragmento
CHUNK_OVERLAP = 40       # palabras que se repiten entre fragmentos, para no cortar datos a la mitad

INDEX_DIR = Path(__file__).parent / "indice"
INDEX_DIR.mkdir(exist_ok=True)


def extraer_por_pagina(pdf_path: str):
    paginas = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, pagina in enumerate(pdf.pages, start=1):
            texto = pagina.extract_text() or ""
            texto = re.sub(r"\s+", " ", texto).strip()
            if texto:
                paginas.append({"pagina": i, "texto": texto})
    return paginas


def trocear(paginas, manual_nombre: str):
    fragmentos = []
    for p in paginas:
        palabras = p["texto"].split()
        paso = CHUNK_SIZE_WORDS - CHUNK_OVERLAP
        for inicio in range(0, len(palabras), paso):
            trozo = palabras[inicio: inicio + CHUNK_SIZE_WORDS]
            if len(trozo) < 15:
                continue
            fragmentos.append({
                "manual": manual_nombre,
                "pagina": p["pagina"],
                "texto": " ".join(trozo),
            })
    return fragmentos


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 indexar.py /ruta/al/manual.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    manual_nombre = Path(pdf_path).stem

    print(f"Extrayendo texto de: {pdf_path}")
    paginas = extraer_por_pagina(pdf_path)
    print(f"  -> {len(paginas)} páginas con texto")

    fragmentos_nuevos = trocear(paginas, manual_nombre)
    print(f"  -> {len(fragmentos_nuevos)} fragmentos generados")

    # Cargar índice existente (si ya hay otros manuales cargados) y sumar
    fragmentos_path = INDEX_DIR / "fragmentos.json"
    if fragmentos_path.exists():
        fragmentos = json.loads(fragmentos_path.read_text())
        # saco fragmentos viejos de este mismo manual, por si se reindexa
        fragmentos = [f for f in fragmentos if f["manual"] != manual_nombre]
    else:
        fragmentos = []

    fragmentos.extend(fragmentos_nuevos)
    fragmentos_path.write_text(json.dumps(fragmentos, ensure_ascii=False, indent=2))

    # Reconstruyo el índice TF-IDF con TODOS los fragmentos (todos los manuales)
    textos = [f["texto"] for f in fragmentos]
    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
    )
    matriz = vectorizer.fit_transform(textos)

    with open(INDEX_DIR / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    with open(INDEX_DIR / "matriz.pkl", "wb") as f:
        pickle.dump(matriz, f)

    print(f"\nÍndice actualizado. Total fragmentos en la base: {len(fragmentos)}")
    print(f"Manuales indexados: {sorted(set(f['manual'] for f in fragmentos))}")


if __name__ == "__main__":
    main()
