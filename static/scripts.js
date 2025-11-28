document.addEventListener("DOMContentLoaded", () => {
    // Activar el fade-in cuando el DOM ya está cargado
    document.body.classList.add("fade", "fade-in");

    // Logo clicable
    const logo = document.getElementById("logo-nexopdf");
    if (logo) {
        logo.style.cursor = "pointer";

        logo.addEventListener("click", (e) => {
            e.preventDefault();

            // Fade-out ANTES de cambiar de página
            document.body.classList.add("fade-out");

            setTimeout(() => {
                window.location.href = "/";
            }, 350);
        });
    }
});
