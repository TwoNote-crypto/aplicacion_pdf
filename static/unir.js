// static/unir.js
document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("fileInputUnir");
  const lista = document.getElementById("listaArchivos");
  const btn = document.getElementById("btnUnir");
  const nombreInput = document.getElementById("nombre_pdf");

  let archivosActuales = []; // [{id, file}]

  if (!input || !lista || !btn) return;

  input.addEventListener("change", function () {
    const nuevos = Array.from(input.files);
    nuevos.forEach(n => {
      archivosActuales.push({
        id: crypto.randomUUID(),
        file: n
      });
    });
    renderLista();
    input.value = "";
  });

  function renderLista() {
    lista.innerHTML = "";

    archivosActuales.forEach(obj => {
      const li = document.createElement("li");
      li.className =
  "list-group-item d-flex justify-content-between align-items-center draggable show";
      li.dataset.id = obj.id;

      li.innerHTML = `
        <span>${obj.file.name}</span>
        <button class="btn btn-danger btn-sm eliminar"><i class="bi bi-trash"></i></button>
      `;

      li.querySelector(".eliminar").addEventListener("click", () => {
        archivosActuales = archivosActuales.filter(x => x.id !== obj.id);
        renderLista();
        activarSortable(); // reactivar para mantener consistencia
      });

      lista.appendChild(li);
    });
  }

  function activarSortable() {
    // destrucción/creación no necesaria con Sortable moderno, pero para evitar duplicados
    if (lista._sortable) {
      try { lista._sortable.destroy(); } catch(e){/*ignore*/ }
      lista._sortable = null;
    }

    lista._sortable = new Sortable(lista, {
      animation: 150,
      ghostClass: "dragging",
      onEnd() {
        const nuevo = [];
        lista.querySelectorAll("li").forEach(li => {
          const id = li.dataset.id;
          const obj = archivosActuales.find(a => a.id === id);
          if (obj) nuevo.push(obj);
        });
        archivosActuales = nuevo;
      }
    });
  }

  activarSortable();

  btn.addEventListener("click", function () {
    if (archivosActuales.length === 0) {
      alert("Añade al menos un PDF.");
      return;
    }

    const fd = new FormData();
    archivosActuales.forEach((obj, idx) => {
      fd.append("archivos", obj.file);
      fd.append("orden[]", idx); // enviamos orden explícito
    });
    fd.append("nombre_pdf", nombreInput.value);

    fetch("/unir", {
      method: "POST",
      body: fd
    })
    .then(async resp => {
      const blob = await resp.blob();
      const filename =
        resp.headers.get("content-disposition")?.split("filename=")[1] || "unido.pdf";

      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename.replace(/["']/g, "");
      a.click();
    });
  });
});
