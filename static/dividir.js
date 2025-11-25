document.addEventListener("DOMContentLoaded", () => {
    const inputPDF = document.getElementById("pdfInput");
    const previewContainer = document.getElementById("previewContainer");
    const paginasSeleccionadas = document.getElementById("paginasSeleccionadas");

    if (!inputPDF) return;

    pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

    inputPDF.addEventListener("change", async function () {
        previewContainer.innerHTML = "";
        paginasSeleccionadas.value = "";

        const archivo = inputPDF.files[0];
        if (!archivo) return;

        const reader = new FileReader();
        reader.onload = async function (e) {
            const typedarray = new Uint8Array(e.target.result);

            const pdf = await pdfjsLib.getDocument(typedarray).promise;

            for (let num = 1; num <= pdf.numPages; num++) {
                const page = await pdf.getPage(num);
                const viewport = page.getViewport({ scale: 0.4 });

                const canvas = document.createElement("canvas");
                const context = canvas.getContext("2d");

                canvas.width = viewport.width;
                canvas.height = viewport.height;

                await page.render({ canvasContext: context, viewport }).promise;

                const thumb = document.createElement("div");
                thumb.classList.add("thumbnail");
                thumb.dataset.page = num;
                thumb.appendChild(canvas);

                thumb.addEventListener("click", () => {
                    thumb.classList.toggle("selected");
                    const seleccionadas = Array.from(document.querySelectorAll(".thumbnail.selected"))
                        .map(t => t.dataset.page);
                    paginasSeleccionadas.value = seleccionadas.join(",");
                });

                previewContainer.appendChild(thumb);
            }
        };

        reader.readAsArrayBuffer(archivo);
    });
});