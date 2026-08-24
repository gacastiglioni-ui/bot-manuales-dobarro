"""
Webhook para conectar el bot de consulta de manuales a WhatsApp vía Twilio.

Deploy sugerido: Railway, Render o un VPS chico (Vercel no corre bien Flask
persistente; si querés Vercel, hay que adaptarlo a función serverless).

Configuración en Twilio:
  1. En la consola de Twilio, activar el WhatsApp Sandbox (gratis para probar).
  2. En "When a message comes in", poner la URL pública de este servidor + /whatsapp
     (ej: https://tu-app.up.railway.app/whatsapp)
  3. Guardar. Escribir por WhatsApp al número del sandbox y probar.

Variables de entorno necesarias:
  ANTHROPIC_API_KEY   -> tu API key de Anthropic (console.anthropic.com)
"""
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from consultar import responder

app = Flask(__name__)


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    pregunta = request.form.get("Body", "").strip()
    numero_de = request.form.get("From", "desconocido")

    print(f"[{numero_de}] Pregunta: {pregunta}")

    if not pregunta:
        texto_respuesta = "Escribime una pregunta sobre algún manual (ej: 'kg de refrigerante del MC-SU60-RN8L')."
    else:
        try:
            texto_respuesta = responder(pregunta)
        except Exception as e:
            texto_respuesta = f"Hubo un error consultando el manual: {e}"

    resp = MessagingResponse()
    resp.message(texto_respuesta)
    return str(resp)


@app.route("/", methods=["GET"])
def healthcheck():
    return "Bot de manuales activo."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
