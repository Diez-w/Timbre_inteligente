from flask import Flask, request
DeepFace = None
import os, hashlib, time, threading, cv2
import numpy as np
import mediapipe as mp
import requests

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CALLMEBOT_API = "https://api.callmebot.com/whatsapp.php"
PHONE = "+51902697385"
APIKEY = "2408114"

# Borrar archivo en 5 min
def borrar_archivo(path, delay=300):
    def eliminar():
        if os.path.exists(path):
            os.remove(path)
    threading.Timer(delay, eliminar).start()

# Función para detectar guiño con MediaPipe
def detectar_guiño(imagen_path):
    mp_face_mesh = mp.solutions.face_mesh
    with mp_face_mesh.FaceMesh(static_image_mode=True) as face_mesh:
        image = cv2.imread(imagen_path)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        if not result.multi_face_landmarks:
            return False

        puntos = result.multi_face_landmarks[0].landmark

        # Puntos de ambos ojos
        ojo_izq = [puntos[159], puntos[145]]  # párpado sup/inf izq
        ojo_der = [puntos[386], puntos[374]]  # párpado sup/inf der

        # Distancia vertical en cada ojo
        dist_izq = abs(ojo_izq[0].y - ojo_izq[1].y)
        dist_der = abs(ojo_der[0].y - ojo_der[1].y)

        # Detectar guiño: un ojo cerrado (dist < 0.015), el otro abierto
        if (dist_izq < 0.015 and dist_der > 0.03) or (dist_der < 0.015 and dist_izq > 0.03):
            return True
        return False

@app.route('/recibir', methods=['POST'])
def recibir():
    print ("Archivos recibidos:", request.files)
    if 'imagen' not in request.files:
        return "No se recibió imagen", 400

    file = request.files['imagen']
    timestamp = str(time.time())
    nombre = hashlib.sha256(timestamp.encode()).hexdigest()[:12] + ".jpg"
    filepath = os.path.join(UPLOAD_FOLDER, nombre)
    file.save(filepath)
    borrar_archivo(filepath)

    mensaje = ""

# Reconocimiento facial
    try:
        global DeepFace
        if DeepFace is None:
            from deepface import DeepFace

        resultado = DeepFace.find(img_path=filepath, db_path="base_rostros")
        if len(resultado) > 0:
            persona = resultado[0]['identity'].values[0]
            mensaje += f"Rostro reconocido: {persona}"
        else:
            mensaje += "Rostro desconocido"
    except Exception as e:
        mensaje += f"Error reconocimiento: {str(e)}"

    # Detección de guiño
    try:
        guiño = detectar_guiño(filepath)
        if guiño:
            mensaje += "\nALERTA: Se detectó gesto de guiño (posible situación de emergencia)"
    except:
        mensaje += "\nNo se pudo analizar gesto facial."

    imagen_url = f"https://timbre-inteligente.onrender.com/{filepath}"
    mensaje += f"\nVer imagen: {imagen_url}"

    # Enviar a WhatsApp
    requests.get(CALLMEBOT_API, params={
        "phone": PHONE,
        "text": mensaje,
        "apikey": APIKEY
    })

    return "Procesado"

if __name__ == '_main_':
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)