# Bot de consulta de manuales (prueba de concepto)

Prototipo funcional: indexa manuales PDF y responde preguntas técnicas citando
manual y página, listo para conectar a WhatsApp por Twilio.

## Ya probado en esta sesión
- Se indexó el manual `Midea_MC-SU90RN8L-B_...pdf` (56 páginas → 158 fragmentos).
- La búsqueda ya encuentra correctamente datos de tabla (ej: kg de refrigerante
  por modelo) usando un buscador híbrido (TF-IDF + coincidencia exacta de
  código de modelo), no solo búsqueda por palabras sueltas.
- **Importante**: el buscador simple por palabras clave (sin el ajuste que
  hicimos) NO encontraba los datos de tabla — se corrigió durante esta prueba.
  Es la razón por la que un prototipo real, antes de mostrárselo a Fernando,
  necesita probarse con preguntas reales, no asumir que "búsqueda + IA" ya
  funciona bien de entrada.

## Cómo seguir probando localmente (ya funciona, sin gastar nada)

```bash
# ver qué fragmentos encuentra para una pregunta (no llama a la API)
python3 consultar.py "cuantos kilos de refrigerante lleva el MC-SU90-RN8L-B"
```

## Para que responda con Claude (no solo mostrar los fragmentos)

1. Conseguí una API key en https://console.anthropic.com
2. `export ANTHROPIC_API_KEY="tu-key-acá"`
3. `python3 consultar.py "tu pregunta"`

## Para indexar más manuales

```bash
python3 indexar.py /ruta/al/otro_manual.pdf
```
Se suman al mismo índice — las preguntas después buscan entre todos los
manuales cargados a la vez.

## Para conectarlo a WhatsApp (Twilio)

1. Creá cuenta gratis en https://www.twilio.com (el sandbox de WhatsApp es gratis para probar).
2. En la consola de Twilio: Messaging → Try it out → Send a WhatsApp message.
   Ahí te dan un número y un código para "activar" tu WhatsApp personal contra el sandbox.
3. Deployá este proyecto (`app.py`) en un servicio que lo mantenga corriendo:
   - Railway.app o Render.com son los más simples para Flask (con Vercel hay que adaptarlo a función serverless, no es tan directo).
4. En Twilio, en "WHEN A MESSAGE COMES IN", poné la URL pública + `/whatsapp`
   (ej: `https://tu-proyecto.up.railway.app/whatsapp`).
5. Configurá la variable de entorno `ANTHROPIC_API_KEY` en el servicio de deploy.
6. Escribile por WhatsApp al número del sandbox y probá con una pregunta real.

## Limitaciones de este prototipo (a mejorar antes de producción)

- La búsqueda es TF-IDF + coincidencia de modelo, no embeddings semánticos
  reales — funciona bien para preguntas con el código de modelo explícito,
  pero puede fallar con preguntas más ambiguas o mal escritas.
- No hay memoria de conversación (cada pregunta es independiente).
- No hay control de quién puede escribirle al bot (cualquiera con el número
  del sandbox podría probarlo mientras esté en modo prueba).
- El sandbox de Twilio es solo para pruebas: para producción con el equipo
  hace falta un número de WhatsApp Business verificado (tiene costo y proceso
  de aprobación de Meta).
