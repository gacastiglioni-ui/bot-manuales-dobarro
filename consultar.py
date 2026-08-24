"""
Busca en el índice los fragmentos más relevantes para una pregunta
y arma la respuesta con Claude, citando manual y página.
 
Requiere la variable de entorno ANTHROPIC_API_KEY para la parte de Claude.
La búsqueda (retrieval) funciona sin esa key, para poder probarla sola.
"""
import json
import os
import pickle
from pathlib import Path
 
from sklearn.metrics.pairwise import cosine_similarity
 
INDEX_DIR = Path(__file__).parent / "indice"
 
_fragmentos = json.loads((INDEX_DIR / "fragmentos.json").read_text())
with open(INDEX_DIR / "vectorizer.pkl", "rb") as f:
    _vectorizer = pickle.load(f)
with open(INDEX_DIR / "matriz.pkl", "rb") as f:
    _matriz = pickle.load(f)
 
 
import re
 
_PATRON_MODELO = re.compile(r"[A-Z0-9]{2,6}-[A-Z0-9]{2,8}(?:[-/][A-Z0-9]{2,8})*", re.IGNORECASE)
_PATRON_CODIGO_CORTO = re.compile(r"\b[A-Za-z]{1,2}\d{1,3}\b")  # códigos tipo C31, E1, P0, H9
_PATRON_CODIGO_LETRAS = re.compile(r"\b[A-Z]{2,3}\b")  # códigos solo con letras tipo PA, EF, HC (deben venir en MAYÚSCULA en la pregunta)
 
 
def buscar(pregunta: str, top_k: int = 4):
    """Devuelve los top_k fragmentos más relevantes para la pregunta.
 
    Combina TF-IDF (similitud por palabras) con:
    - un bonus fuerte cuando el fragmento contiene literalmente el código de
      modelo mencionado en la pregunta (ej. "MC-SU60-RN8L")
    - un bonus fuerte cuando contiene un código de falla corto (ej. "C31", "E1")
    - coincidencia de palabras clave normales de la pregunta
 
    Los manuales técnicos tienen tablas con poco texto narrativo alrededor,
    así que el TF-IDF solo no alcanza para encontrar datos puntuales.
    """
    vec_pregunta = _vectorizer.transform([pregunta])
    similitudes = cosine_similarity(vec_pregunta, _matriz)[0]
 
    modelos_en_pregunta = [m.upper() for m in _PATRON_MODELO.findall(pregunta)]
    codigos_en_pregunta = [c.upper() for c in _PATRON_CODIGO_CORTO.findall(pregunta)]
    # códigos solo-letras: se buscan tal cual fueron escritos (en mayúscula) para no
    # confundir con palabras comunes en minúscula ("la", "el", "de", etc.)
    codigos_letras_en_pregunta = _PATRON_CODIGO_LETRAS.findall(pregunta)
    palabras_clave = [w.lower() for w in re.findall(r"\w+", pregunta) if len(w) > 3]
 
    puntajes = []
    for i, score_tfidf in enumerate(similitudes):
        texto_frag_upper = _fragmentos[i]["texto"].upper()
        texto_frag_lower = _fragmentos[i]["texto"].lower()
 
        bonus_modelo = 0.0
        for modelo in modelos_en_pregunta:
            if modelo in texto_frag_upper:
                bonus_modelo += 2.5
 
        bonus_codigo = 0.0
        for codigo in codigos_en_pregunta:
            # \b para no matchear "C31" dentro de "C310" por ejemplo
            if re.search(r"\b" + re.escape(codigo) + r"\b", texto_frag_upper):
                bonus_codigo += 3.0
        for codigo in codigos_letras_en_pregunta:
            if re.search(r"\b" + re.escape(codigo) + r"\b", texto_frag_upper):
                bonus_codigo += 3.0
 
        coincidencias_literales = sum(1 for w in palabras_clave if w in texto_frag_lower)
 
        puntajes.append(float(score_tfidf) + bonus_modelo + bonus_codigo + 0.4 * coincidencias_literales)
 
    indices_ordenados = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)[:top_k]
    resultados = []
    for i in indices_ordenados:
        if puntajes[i] <= 0:
            continue
        resultados.append({
            **_fragmentos[i],
            "score": round(puntajes[i], 3),
        })
    return resultados
 
 
PROMPT_SISTEMA = """Sos un asistente técnico para instaladores de HVAC de Dobarro & Pichel.
Respondé la pregunta del técnico usando SOLO la información de los fragmentos de manual
que te paso a continuación. No inventes ni completes con conocimiento general.
Si el dato no está en los fragmentos, decí claramente que no lo encontraste en el manual indexado.
Si encontrás valores distintos para el mismo dato en distintos fragmentos, señalá la discrepancia
en vez de elegir uno solo.
Siempre indicá al final de tu respuesta el manual y la página de donde sacaste el dato,
en el formato: (Manual: <nombre>, pág. <n>).
Respondé corto y directo, como lo necesitaría un técnico parado al lado del equipo."""
 
 
def responder(pregunta: str, top_k: int = 4) -> str:
    fragmentos = buscar(pregunta, top_k=top_k)
    if not fragmentos:
        return "No encontré nada relacionado en los manuales indexados."
 
    contexto = "\n\n".join(
        f"[Manual: {f['manual']} | Página {f['pagina']}]\n{f['texto']}"
        for f in fragmentos
    )
 
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Modo de prueba sin API key: mostramos qué se hubiera mandado a Claude
        return (
            "[MODO PRUEBA - sin ANTHROPIC_API_KEY configurada]\n\n"
            f"Pregunta: {pregunta}\n\n"
            f"Fragmentos recuperados (los que se le mandarían a Claude):\n\n{contexto}"
        )
 
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    mensaje = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=PROMPT_SISTEMA,
        messages=[{
            "role": "user",
            "content": f"Fragmentos del manual:\n\n{contexto}\n\nPregunta del técnico: {pregunta}",
        }],
    )
    return mensaje.content[0].text
 
 
if __name__ == "__main__":
    import sys
    pregunta = " ".join(sys.argv[1:]) or "¿Cuántos kilos de refrigerante lleva el MC-SU60-RN8L?"
    print(f"PREGUNTA: {pregunta}\n")
    print(responder(pregunta))
 


