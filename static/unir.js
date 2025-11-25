document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("fileInputUnir");
  const lista = document.getElementById("listaArchivos");
  const form = document.getElementById("unirForm");
  const nombreInput = document.getElementById("nombre_pdf");

  let archivosActuales = [];

  if (!input || !lista || !form) return;

  input.addEventListener("change", function () {
    const nuevos = Array.from(input.files);
    nuevos.forEach(n => {
      const existe = archivosActuales.some(a => a.name === n.name && a.size === n.size);
      if (!existe) archivosActuales.push(n);
    });
    renderLista();
    input.value = "";
  });

  function renderLista() {
    lista.innerHTML = "";
    archivosActuales.forEach((f, idx) => {
      const li = document.createElement("li");
      li.className = "draggable list-group-item d-flex justify-content-between align-items-center";
      li.dataset.idx = idx;
      li.innerHTML = `<span>${f.name}</span>
                      <button class="btn btn-danger btn-sm eliminar"><i class="bi bi-trash"></i></button>`;
      li.querySelector(".eliminar").addEventListener("click", () => {
        archivosActuales.splice(idx, 1);
        renderLista();
      });
      lista.appendChild(li);
      setTimeout(() => li.classList.add("show"), 50 + idx * 50);
    });
  }

  new Sortable(lista, {
    animation: 150,
    onEnd: function (evt) {
      const moved = archivosActuales.splice(evt.oldIndex, 1)[0];
      archivosActuales.splice(evt.newIndex, 0, moved);
      renderLista();
    }
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (archivosActuales.length === 0) {
      alert("Añade al menos un PDF para unir.");
      return;
    }
    const fd = new FormData();
    archivosActuales.forEach(f => fd.append("archivos", f, f.name));
    fd.append("nombre_pdf", nombreInput.value || "");
    fetch(form.action || window.location.pathname, {
      method: "POST",
      body: fd
    }).then(async resp => {
      if (!resp.ok) {
        const txt = await resp.text();
        alert("Error: " + txt);
        return;
      }
      const blob = await resp.blob();
      const filename = resp.headers.get("content-disposition")?.split("filename=")[1] || (nombreInput.value || "unido.pdf");
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename.replace(/["']/g, "");
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    }).catch(err => {
      console.error(err);
      alert("Ocurrió un error al unir los archivos.");
    });
  });
});