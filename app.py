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
# Función para ejecutar Ghostscript (respeta orden)
# ---------------------------------------
def gs_run(input_files, output_file):
    if not GS:
        raise Exception("Ghostscript NO está instalado en el sistema")

    cmd = [
        GS,
        "-dQUIET",
        "-dNOPAUSE",
        "-dBATCH",
        "-dSAFER",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.7",
        "-dPDFSettings=/prepress",
        "-sOutputFile=" + output_file
    ]

    for f in input_files:
        cmd.append(f)

    subprocess.run(cmd, check=True)

# ---------------------------------------
# Generar nombre
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
# Helper: reordenar archivos según campo 'orden[]'
# Si 'orden[]' falta o es inválido hacemos fallback seguro.
# ---------------------------------------
def reorder_files_from_request():
    archivos = request.files.getlist("archivos")
    orden_raw = request.form.getlist("orden[]")

    # Si no hay archivos, devolver lista vacía
    if not archivos:
        return []

    # Si no se envió orden[] o viene vacío, intentar fallback con lists()
    if not orden_raw:
        # Try lists() (keeps order of form-data)
        try:
            listas = dict(request.files.lists())
            maybe = listas.get("archivos", [])
            if maybe:
                return maybe
        except Exception:
            pass
        # fallback simple: return archivos tal cual llegaron
        return archivos

    # Si orden[] existe, convertir a enteros y reordenar
    try:
        orden = list(map(int, orden_raw))
    except Exception:
        # si falla la conversión, fallback a archivos tal cual
        return archivos

    # defensa: si longitudes no coinciden, fallback
    if len(orden) != len(archivos):
        # intente usar listas() si available
        try:
            listas = dict(request.files.lists())
            maybe = listas.get("archivos", [])
            if maybe and len(maybe) == len(orden):
                archivos = maybe
        except Exception:
            pass
        if len(orden) != len(archivos):
            return archivos

    try:
        archivos_ordenados = [archivos[i] for i in orden]
    except Exception:
        # en caso de indices fuera de rango -> fallback
        return archivos

    return archivos_ordenados

# ---------------------------------------
# Página principal
# ---------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------------------------------
# Convertir imágenes a PDF (orden corregido)
# ---------------------------------------
@app.route("/convertir", methods=["GET", "POST"])
def convertir():
    if request.method == "POST":
        archivos = reorder_files_from_request()
        nombre_pdf = request.form.get("nombre_pdf", "")

        imagenes = []
        for archivo in archivos:
            if archivo and archivo.filename and archivo.filename.lower().endswith(("png", "jpg", "jpeg")):
                try:
                    img = Image.open(archivo).convert("RGB")
                    imagenes.append(img)
                except Exception as e:
                    # saltamos imágenes inválidas
                    logging.warning("Imagen inválida: %s -> %s", archivo.filename, str(e))
                    pass

        if not imagenes:
            flash("No se subieron imágenes válidas")
            return redirect(url_for("convertir"))

        buffer = BytesIO()
        imagenes[0].save(buffer, format="PDF", save_all=True, append_images=imagenes[1:])
        buffer.seek(0)

        return send_file(
            BytesIO(buffer.read()),
            as_attachment=True,
            download_name=obtener_nombre(nombre_pdf, "convertido.pdf"),
            mimetype="application/pdf"
        )

    return render_template("convertir.html")

# ---------------------------------------
# UNIR PDFs — orden corregido
# ---------------------------------------
@app.route("/unir", methods=["GET", "POST"])
def unir():
    if request.method == "POST":
        archivos = reorder_files_from_request()
        nombre_pdf = request.form.get("nombre_pdf", "")

        if not archivos:
            flash("No se subieron PDFs")
            return redirect(url_for("unir"))

        tmp_inputs = []
        os.makedirs("/tmp", exist_ok=True)

        # Debug: mostrar orden recibido
        print("ORDEN RECIBIDO:", [getattr(f, "filename", None) for f in archivos])

        for idx, f in enumerate(archivos):
            ruta = f"/tmp/input_{idx}.pdf"
            f.save(ruta)
            tmp_inputs.append(ruta)

        salida = "/tmp/unido.pdf"

        # Ejecutar Ghostscript respetando orden
        gs_run(tmp_inputs, salida)

        with open(salida, "rb") as fh:
            pdf_bytes = fh.read()

        # Limpiar temporales
        for r in tmp_inputs:
            try:
                os.remove(r)
            except Exception:
                pass
        try:
            os.remove(salida)
        except Exception:
            pass

        return send_file(
            BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=obtener_nombre(nombre_pdf, "unido.pdf"),
            mimetype="application/pdf"
        )

    return render_template("unir.html")

# ---------------------------------------
# DIVIDIR PDFs — PyPDF2
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

        return send_file(
            BytesIO(buffer.read()),
            as_attachment=True,
            download_name=obtener_nombre(nombre_pdf, "dividido.pdf"),
            mimetype="application/pdf"
        )

    return render_template("dividir.html")

# ---------------------------------------
# Health check
# ---------------------------------------
@app.route("/health")
def health():
    return jsonify({
        "ghostscript_available": bool(GS),
        "ghostscript_path": GS
    })

if __name__ == "__main__":
    app.run(debug=True)
