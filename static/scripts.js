document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("fileInput");
  const lista = document.getElementById("listaArchivos");
  const ordenInput = document.getElementById("orden");

  if (!fileInput || !lista) return;

  fileInput.addEventListener("change", function () {
    lista.innerHTML = "";

    Array.from(fileInput.files).forEach((archivo, index) => {
      const li = document.createElement("li");
      li.textContent = archivo.name;
      li.classList.add("draggable");
      lista.appendChild(li);

      // Animación de aparición
      setTimeout(() => li.classList.add("show"), 50 + index * 100);
    });

    // Guardar orden inicial
    if (ordenInput) {
      ordenInput.value = Array.from(fileInput.files).map(f => f.name).join(",");
    }
  });

  // Activar Sortable.js
  new Sortable(lista, {
    animation: 150,
    onEnd: function () {
      if (ordenInput) {
        const nombres = Array.from(lista.children).map(li => li.textContent);
        ordenInput.value = nombres.join(",");
      }
    },
    ghostClass: "dragging"
  });
});
