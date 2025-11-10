from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image

app = Flask(__name__)

# Carpeta para guardar resultados
RESULTADOS_FOLDER = os.path.join("static", "resultados")
os.makedirs(RESULTADOS_FOLDER, exist_ok=True)

# -----------------------------
# Función auxiliar para nombres
# -----------------------------
def obtener_nombre(nombre_personalizado, archivos, prefijo="resultado"):
    """
    Si el usuario da un nombre, lo usamos.
    Si no, usamos el nombre del primer archivo subido.
    """
    if nombre_personalizado and nombre_personalizado.strip() != "":
        nombre_final = nombre_personalizado.strip()
    else:
        nombre_final = os.path.splitext(archivos[0].filename)[0] if archivos else prefijo
    if not nombre_final.lower().endswith(".pdf"):
        nombre_final += ".pdf"
    return secure_filename(nombre_final)

# -----------------------------
# Rutas principales
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

# -----------------------------
# Convertir imágenes a PDF
# -----------------------------
@app.route("/convertir", methods=["GET", "POST"])
def convertir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        orden = request.form.get("orden", "")
        nombre_pdf = request.form.get("nombre_pdf", "")

        # Reordenar según la lista
        if orden:
            orden_lista = orden.split(",")
            archivos_dict = {f.filename: f for f in archivos}
            archivos = [archivos_dict[n] for n in orden_lista if n in archivos_dict]

        imagenes = []
        for archivo in archivos:
            if archivo and archivo.filename.lower().endswith(("png", "jpg", "jpeg")):
                img = Image.open(archivo).convert("RGB")
                imagenes.append(img)

        if not imagenes:
            return "No se subieron imágenes válidas", 400

        nombre_final = obtener_nombre(nombre_pdf, archivos, "convertido")
        ruta_salida = os.path.join(RESULTADOS_FOLDER, nombre_final)

        imagenes[0].save(ruta_salida, save_all=True, append_images=imagenes[1:])

        return render_template("resultado.html", archivo=nombre_final)

    return render_template("convertir.html")

# -----------------------------
# Unir PDFs
# -----------------------------
@app.route("/unir", methods=["GET", "POST"])
def unir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        orden = request.form.get("orden", "")
        nombre_pdf = request.form.get("nombre_pdf", "")

        # Reordenar según la lista
        if orden:
            orden_lista = orden.split(",")
            archivos_dict = {f.filename: f for f in archivos}
            archivos = [archivos_dict[n] for n in orden_lista if n in archivos_dict]

        if not archivos:
            return "No se subieron PDFs válidos", 400

        nombre_final = obtener_nombre(nombre_pdf, archivos, "unido")
        ruta_salida = os.path.join(RESULTADOS_FOLDER, nombre_final)

        merger = PdfMerger()
        for archivo in archivos:
            merger.append(archivo)
        merger.write(ruta_salida)
        merger.close()

        return render_template("resultado.html", archivo=nombre_final)

    return render_template("unir.html")

# -----------------------------
# Dividir PDF
# -----------------------------
@app.route("/dividir", methods=["GET", "POST"])
def dividir():
    if request.method == "POST":
        archivo = request.files.get("archivo")
        paginas = request.form.get("paginas")
        nombre_pdf = request.form.get("nombre_pdf", "")

        if not archivo or not paginas:
            return "Falta archivo o rango de páginas", 400

        nombre_final = obtener_nombre(nombre_pdf, [archivo], "dividido")
        ruta_salida = os.path.join(RESULTADOS_FOLDER, nombre_final)

        reader = PdfReader(archivo)
        writer = PdfWriter()

        rangos = []
        for parte in paginas.split(","):
            if "-" in parte:
                inicio, fin = map(int, parte.split("-"))
                rangos.extend(range(inicio, fin + 1))
            else:
                rangos.append(int(parte))

        for num in rangos:
            if 1 <= num <= len(reader.pages):
                writer.add_page(reader.pages[num - 1])

        with open(ruta_salida, "wb") as salida:
            writer.write(salida)

        return render_template("resultado.html", archivo=nombre_final)

    return render_template("dividir.html")


if __name__ == "__main__":
    app.run(debug=True)
