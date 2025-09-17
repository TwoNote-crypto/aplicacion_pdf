from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image

# ----------------------------
# CONFIGURACIÓN
# ----------------------------
app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
RESULTADOS_FOLDER = "static/resultados"
LOGO_PATH = "static/logo.png"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTADOS_FOLDER, exist_ok=True)

# ----------------------------
# RUTA PRINCIPAL
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------
# CONVERTIR IMAGEN A PDF
# ----------------------------
@app.route("/convertir", methods=["GET", "POST"])
def convertir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        orden = request.form.get("orden").split(",") if request.form.get("orden") else []

        if archivos:
            # Crear PDF desde las imágenes en el orden definido
            archivos_dict = {archivo.filename: archivo for archivo in archivos}
            nombre_pdf = "convertido.pdf"
            ruta_pdf = os.path.join(RESULTADOS_FOLDER, nombre_pdf)

            # Abrir imágenes en orden
            imagenes = [Image.open(archivos_dict[nombre]) for nombre in orden if nombre in archivos_dict]
            if imagenes:
                imagenes[0].convert("RGB").save(
                    ruta_pdf, save_all=True, append_images=imagenes[1:]
                )

                # Agregar marca de agua
                ruta_final = agregar_marca_agua(ruta_pdf, "convertido_final.pdf")
                return render_template("preview.html", archivo=os.path.basename(ruta_final))
    return render_template("convertir.html")

# ----------------------------
# UNIR PDFs
# ----------------------------
@app.route("/unir", methods=["GET", "POST"])
def unir():
    if request.method == "POST":
        archivos = request.files.getlist("archivos")
        orden = request.form.get("orden").split(",") if request.form.get("orden") else []

        if archivos:
            merger = PdfMerger()
            archivos_dict = {archivo.filename: archivo for archivo in archivos}
            for nombre in orden:
                if nombre in archivos_dict:
                    merger.append(archivos_dict[nombre])

            nombre_pdf = "unido.pdf"
            ruta_pdf = os.path.join(RESULTADOS_FOLDER, nombre_pdf)
            merger.write(ruta_pdf)
            merger.close()

            ruta_final = agregar_marca_agua(ruta_pdf, "unido_final.pdf")
            return render_template("preview.html", archivo=os.path.basename(ruta_final))
    return render_template("unir.html")

# ----------------------------
# DIVIDIR PDF
# ----------------------------
@app.route("/dividir", methods=["GET", "POST"])
def dividir():
    if request.method == "POST":
        archivo = request.files["archivo"]
        paginas = request.form.get("paginas")

        if archivo and archivo.filename.endswith(".pdf"):
            nombre = secure_filename(archivo.filename)
            ruta_pdf = os.path.join(UPLOAD_FOLDER, nombre)
            archivo.save(ruta_pdf)

            reader = PdfReader(ruta_pdf)
            writer = PdfWriter()

            paginas_seleccionadas = []
            for parte in paginas.split(","):
                if "-" in parte:
                    inicio, fin = parte.split("-")
                    paginas_seleccionadas.extend(range(int(inicio)-1, int(fin)))
                else:
                    paginas_seleccionadas.append(int(parte)-1)

            for num in paginas_seleccionadas:
                if 0 <= num < len(reader.pages):
                    writer.add_page(reader.pages[num])

            nombre_pdf = "dividido.pdf"
            ruta_pdf = os.path.join(RESULTADOS_FOLDER, nombre_pdf)
            with open(ruta_pdf, "wb") as salida:
                writer.write(salida)

            ruta_final = agregar_marca_agua(ruta_pdf, "dividido_final.pdf")
            return render_template("preview.html", archivo=os.path.basename(ruta_final))
    return render_template("dividir.html")

# ----------------------------
# FUNCIÓN MARCA DE AGUA
# ----------------------------
def agregar_marca_agua(ruta_pdf, nombre_salida):
    ruta_temp = os.path.join(RESULTADOS_FOLDER, "temp.pdf")
    c = canvas.Canvas(ruta_temp, pagesize=A4)
    ancho, alto = A4
    c.setFont("Helvetica", 10)
    c.drawString(200, 20, "Creado por Gestión Documental")
    c.save()

    reader = PdfReader(ruta_pdf)
    marca = PdfReader(ruta_temp)
    writer = PdfWriter()

    for pagina in reader.pages:
        pagina.merge_page(marca.pages[0])
        writer.add_page(pagina)

    ruta_final = os.path.join(RESULTADOS_FOLDER, nombre_salida)
    with open(ruta_final, "wb") as salida:
        writer.write(salida)

    return ruta_final

# ----------------------------
# EJECUCIÓN
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
