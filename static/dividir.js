document.addEventListener("DOMContentLoaded", () => {
  const pdfInput = document.getElementById("pdfInput");
  const preview = document.getElementById("preview-container");
  const extractBtn = document.getElementById("extract-btn");

  pdfInput.addEventListener("change", async () => {
    const formData = new FormData();
    formData.append("archivo", pdfInput.files[0]);

    preview.innerHTML = "<p class='text-muted'>Generando miniaturas...</p>";

    const response = await fetch("/dividir_preview", {
      method: "POST",
      body: formData
    });

    const pages = await response.json();
    preview.innerHTML = "";

    pages.forEach((url, i) => {
      const card = document.createElement("div");
      card.classList.add("page-card");
      card.innerHTML = `
        <img src="${url}" alt="Página ${i + 1}">
        <div class="page-number">Página ${i + 1}</div>
      `;
      card.addEventListener("click", () => {
        card.classList.toggle("selected");
      });
      preview.appendChild(card);
    });

    extractBtn.classList.remove("d-none");
  });

  extractBtn.addEventListener("click", async () => {
    const selected = [...document.querySelectorAll(".page-card.selected")];
    if (selected.length === 0) {
      alert("Selecciona al menos una página");
      return;
    }

    const pages = selected.map((c, i) => i + 1);
    const body = JSON.stringify({ paginas: pages });

    const response = await fetch("/dividir_extraer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body
    });

    if (response.ok) {
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pdf_dividido.pdf";
      a.click();
    }
  });
});
