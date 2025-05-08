from flask import Flask, request
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/recibir', methods=['POST'])
def recibir():
    if 'imagen' not in request.files:
        return "No se recibió imagen", 400

    file = request.files['imagen']
    if file.filename == '':
        return "Nombre de archivo vacío", 400

    nombre = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, nombre)
    file.save(filepath)

    return f"Imagen recibida y guardada como {nombre}", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)