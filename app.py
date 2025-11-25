from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
import shutil
import subprocess
import logging
import os
from PyPDF2 import PdfReader, PdfWriter  # solo para dividir

app = Flask(__name__)
app.secret_key = "cambiala_por_una_segura"

# ---------------------------------------
# Limite de subida
# ---------------------------------------
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024

logging.basicConfig(level=logging.INFO)

# ---------------------------------------
# Buscar Ghostscript
# ---------------------------------------
def find_gs():
    possibles = ["gs", "gswin64c", "gswin32c", "ghostscript"]
    for p in possibles:
        if shutil.which(p):
            return p
    return None

GS = find_gs()

# ---------------------------------------
# Función para ejecutar Ghostscript
# ---------------------------------------
def gs_run(input_files, output_file, extra_args):
    if not GS:
        raise Exception("Ghostscript NO está instalado en el sistema")

    cmd = [GS, "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite"]
    cmd += extra_args
    cmd += ["-sOutputFile=" + output_file] + input_files

    subprocess.run(cmd, check=True)

# ---------------------------------------
# Generar nombre de archivo
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
# Convertir imágenes a PDF
# ---------------------------------------
@app.route("/convertir", methods=["GET", "POST"])
def convertir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        nombre_pdf = request.form.get("nombre_pdf", "")

        imagenes = []
        for archivo in archivos:
            if archivo and archivo.filename.lower().endswith(("png", "jpg", "jpeg")):
                try:
                    img = Image.open(archivo).convert("RGB")
                    imagenes.append(img)
                except:
                    pass

        if not imagenes:
            flash("No se subieron imágenes válidas")
            return redirect(url_for("convertir"))

        buffer = BytesIO()
        imagenes[0].save(buffer, format="PDF", save_all=True, append_images=imagenes[1:])
        buffer.seek(0)

        pdf_bytes = buffer.read()
        return send_file(BytesIO(pdf_bytes),
                         as_attachment=True,
                         download_name=obtener_nombre(nombre_pdf, "convertido.pdf"),
                         mimetype="application/pdf")

    return render_template("convertir.html")

# ---------------------------------------
# UNIR PDFs → Ghostscript
# ---------------------------------------
@app.route("/unir", methods=["GET", "POST"])
def unir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        nombre_pdf = request.form.get("nombre_pdf", "")

        if not archivos:
            flash("No se subieron PDFs")
            return redirect(url_for("unir"))

        tmp_inputs = []
        os.makedirs("/tmp", exist_ok=True)

        for idx, f in enumerate(archivos):
            ruta = f"/tmp/input_{idx}.pdf"
            f.save(ruta)
            tmp_inputs.append(ruta)

        salida = "/tmp/unido.pdf"

        gs_run(tmp_inputs, salida, extra_args=[])

        with open(salida, "rb") as f:
            pdf_bytes = f.read()

        for r in tmp_inputs:
            os.remove(r)
        os.remove(salida)

        return send_file(BytesIO(pdf_bytes),
                         as_attachment=True,
                         download_name=obtener_nombre(nombre_pdf, "unido.pdf"),
                         mimetype="application/pdf")

    return render_template("unir.html")

# ---------------------------------------
# DIVIDIR → PyPDF2 (NO daña firmas)
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

        return send_file(BytesIO(pdf_bytes),
                         as_attachment=True,
                         download_name=obtener_nombre(nombre_pdf, "dividido.pdf"),
                         mimetype="application/pdf")

    return render_template("dividir.html")

# ---------------------------------------
# Health
# ---------------------------------------
@app.route("/health")
def health():
    return jsonify({
        "ghostscript_available": bool(GS),
        "ghostscript_path": GS
    })

if __name__ == "__main__":
    app.run(debug=True)
