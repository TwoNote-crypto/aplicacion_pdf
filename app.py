from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# ---------------------------------------
# LIMITE DE ARCHIVOS (por seguridad)
# 80 MB total por request
# ---------------------------------------
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024  


# ---------------------------------------
# Función: nombre final del PDF
# (solo aseguramos que tenga .pdf)
# ---------------------------------------
def obtener_nombre(nombre_usuario, prefijo):
    if nombre_usuario and nombre_usuario.strip() != "":
        nombre_final = secure_filename(nombre_usuario.strip())
    else:
        nombre_final = prefijo

    if not nombre_final.lower().endswith(".pdf"):
        nombre_final += ".pdf"
    return nombre_final


# ---------------------------------------
# Página principal
# ---------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------
# Convertir IMÁGENES a PDF (EN MEMORIA)
# ---------------------------------------
@app.route("/convertir", methods=["GET", "POST"])
def convertir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        orden = request.form.get("orden", "")
        nombre_pdf = request.form.get("nombre_pdf", "")

        # Reordenar
        if orden:
            orden_lista = orden.split(",")
            archivos_dict = {f.filename: f for f in archivos}
            archivos = [archivos_dict[n] for n in orden_lista if n in archivos_dict]

        imagenes = []
        for archivo in archivos:
            if archivo.filename.lower().endswith(("png", "jpg", "jpeg")):
                img = Image.open(archivo).convert("RGB")
                imagenes.append(img)

        if not imagenes:
            return "No se subieron imágenes válidas", 400

        # Crear buffer en memoria
        buffer = BytesIO()

        # Guardar todas las imágenes en 1 PDF
        imagenes[0].save(buffer, format="PDF", save_all=True, append_images=imagenes[1:])
        buffer.seek(0)

        nombre_final = obtener_nombre(nombre_pdf, "convertido.pdf")

        return send_file(
            buffer,
            as_attachment=True,
            download_name=nombre_final,
            mimetype="application/pdf"
        )

    return render_template("convertir.html")


# ---------------------------------------
# UNIR PDFs (EN MEMORIA)
# ---------------------------------------
@app.route("/unir", methods=["GET", "POST"])
def unir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        orden = request.form.get("orden", "")
        nombre_pdf = request.form.get("nombre_pdf", "")

        # Reordenar
        if orden:
            orden_lista = orden.split(",")
            archivos_dict = {f.filename: f for f in archivos}
            archivos = [archivos_dict[n] for n in orden_lista if n in archivos_dict]

        merger = PdfMerger()

        for archivo in archivos:
            merger.append(archivo)

        buffer = BytesIO()
        merger.write(buffer)
        merger.close()
        buffer.seek(0)

        nombre_final = obtener_nombre(nombre_pdf, "unido.pdf")

        return send_file(
            buffer,
            as_attachment=True,
            download_name=nombre_final,
            mimetype="application/pdf"
        )

    return render_template("unir.html")


# ---------------------------------------
# DIVIDIR PDF (EN MEMORIA)
# ---------------------------------------
@app.route("/dividir", methods=["GET", "POST"])
def dividir():
    if request.method == "POST":
        archivo = request.files.get("archivo")
        nombre_pdf = request.form.get("nombre_pdf", "")
        paginas = request.form.get("paginas_seleccionadas")

        if not archivo or not paginas:
            return "Falta archivo o selección de páginas", 400

        paginas = list(map(int, paginas.split(",")))

        reader = PdfReader(archivo)
        writer = PdfWriter()

        for p in paginas:
            if 1 <= p <= len(reader.pages):
                writer.add_page(reader.pages[p - 1])

        buffer = BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        nombre_final = obtener_nombre(nombre_pdf, "dividido.pdf")

        return send_file(
            buffer,
            as_attachment=True,
            download_name=nombre_final,
            mimetype="application/pdf"
        )

    return render_template("dividir.html")


if __name__ == "__main__":
    app.run(debug=True)
