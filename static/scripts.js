document.addEventListener("DOMContentLoaded", function () {
  // Inicializa Sortable para cualquier #listaArchivos presente
  const listas = document.querySelectorAll("#listaArchivos");
  listas.forEach((lista) => {
    new Sortable(lista, {
      animation: 150,
      ghostClass: "dragging",
      onEnd: function () {
        // si existe un input #orden sincronizamos
        const ordenInput = document.getElementById("orden");
        if (ordenInput) {
          const nombres = Array.from(lista.children).map(li => li.querySelector("span") ? li.querySelector("span").textContent : li.textContent.trim());
          ordenInput.value = nombres.join(",");
        }
      }
    });
  });
});
