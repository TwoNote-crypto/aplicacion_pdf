from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
from io import BytesIO
import shutil
import subprocess
import logging

app = Flask(__name__)
app.secret_key = "cambiala_por_una_segura"

# ---------------------------------------
# LIMITE DE ARCHIVOS (por seguridad)
# 80 MB total por request
# ---------------------------------------
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024

logging.basicConfig(level=logging.INFO)


def obtener_nombre(nombre_usuario, prefijo):
    if nombre_usuario and nombre_usuario.strip() != "":
        nombre_final = secure_filename(nombre_usuario.strip())
    else:
        nombre_final = prefijo

    if not nombre_final.lower().endswith(".pdf"):
        nombre_final += ".pdf"
    return nombre_final


def limpiar_metadata(pdf_bytes: bytes) -> bytes:
    """
    Quita/limpia metadatos como Producer/Creator que pueden traer la marca "Creado por..."
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    # Sobrescribimos metadata con vacíos para evitar Producer/Creator visibles
    writer.add_metadata({
        "/Producer": "",
        "/Creator": "",
    })
    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()


def _find_ghostscript_executable():
    possibles = ["gs", "gswin64c", "gswin32c", "ghostscript"]
    for p in possibles:
        if shutil.which(p):
            return p
    return None


@app.route("/health")
def health():
    """
    Ruta informativa: comprueba si Ghostscript está presente (no forzamos su uso).
    """
    gs = _find_ghostscript_executable()
    ok = bool(gs)
    version = None
    if gs:
        try:
            proc = subprocess.run([gs, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            version = proc.stdout.decode().strip() or proc.stderr.decode().strip()
        except Exception:
            version = None
    return jsonify({"ghostscript_available": ok, "ghostscript_executable": gs, "version": version})


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
        # recibimos archivos con fetch o con form normal; manejar ambos casos
        archivos = request.files.getlist("archivos")
        nombre_pdf = request.form.get("nombre_pdf", "")

        imagenes = []
        for archivo in archivos:
            if archivo and archivo.filename.lower().endswith(("png", "jpg", "jpeg")):
                try:
                    img = Image.open(archivo).convert("RGB")
                    imagenes.append(img)
                except Exception:
                    pass

        if not imagenes:
            flash("No se subieron imágenes válidas")
            return redirect(url_for("convertir"))

        buffer = BytesIO()
        imagenes[0].save(buffer, format="PDF", save_all=True, append_images=imagenes[1:])
        buffer.seek(0)
        pdf_bytes = buffer.read()

        # limpiar metadata por seguridad
        pdf_bytes = limpiar_metadata(pdf_bytes)

        nombre_final = obtener_nombre(nombre_pdf, "convertido.pdf")
        return send_file(BytesIO(pdf_bytes), as_attachment=True, download_name=nombre_final, mimetype="application/pdf")

    return render_template("convertir.html")


# ---------------------------------------
# UNIR PDFs (EN MEMORIA)
# Esta ruta acepta una subida por fetch (FormData) o un form tradicional.
# Espera múltiples entradas 'archivos'
# ---------------------------------------
@app.route("/unir", methods=["GET", "POST"])
def unir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        nombre_pdf = request.form.get("nombre_pdf", "")

        if not archivos:
            flash("No se subieron PDFs")
            return redirect(url_for("unir"))

        merger = PdfMerger()
        for archivo in archivos:
            try:
                merger.append(archivo)
            except Exception as e:
                logging.warning("No se pudo anexar %s: %s", getattr(archivo, "filename", ""), e)

        buffer = BytesIO()
        merger.write(buffer)
        merger.close()
        buffer.seek(0)
        pdf_bytes = buffer.read()

        pdf_bytes = limpiar_metadata(pdf_bytes)

        nombre_final = obtener_nombre(nombre_pdf, "unido.pdf")
        return send_file(BytesIO(pdf_bytes), as_attachment=True, download_name=nombre_final, mimetype="application/pdf")

    # GET -> template con la interfaz (la UI manejará el envío vía JS)
    return render_template("unir.html")


# ---------------------------------------
# DIVIDIR PDF (EN MEMORIA)
# ---------------------------------------
@app.route("/dividir", methods=["GET", "POST"])
def dividir():
    if request.method == "POST":
        archivo = request.files.get("archivo")
        nombre_pdf = request.form.get("nombre_pdf", "")
        paginas = request.form.get("paginas_seleccionadas", "")

        if not archivo or not paginas:
            flash("Falta archivo o selección de páginas")
            return redirect(url_for("dividir"))

        paginas = list(map(int, filter(None, paginas.split(","))))
        reader = PdfReader(archivo)
        writer = PdfWriter()

        for p in paginas:
            if 1 <= p <= len(reader.pages):
                writer.add_page(reader.pages[p - 1])

        buffer = BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        pdf_bytes = buffer.read()

        pdf_bytes = limpiar_metadata(pdf_bytes)

        nombre_final = obtener_nombre(nombre_pdf, "dividido.pdf")
        return send_file(BytesIO(pdf_bytes), as_attachment=True, download_name=nombre_final, mimetype="application/pdf")

    return render_template("dividir.html")


if __name__ == "__main__":
    app.run(debug=True)
