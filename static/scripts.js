document.addEventListener("DOMContentLoaded", function () {
  const listas = document.querySelectorAll("#listaArchivos");
  listas.forEach((lista) => {
    new Sortable(lista, {
      animation: 150,
      ghostClass: "dragging",
      onEnd: function () {
        const ordenInput = document.getElementById("orden");
        if (ordenInput) {
          const nombres = Array.from(lista.children)
            .map(li => li.querySelector("span")?.textContent || li.textContent.trim());
          ordenInput.value = nombres.join(",");
        }
      }
    });
  });
});
