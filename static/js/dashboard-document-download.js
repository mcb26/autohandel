document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-document-download]").forEach(function (link) {
        link.addEventListener("click", function (event) {
            event.preventDefault();

            var url = link.getAttribute("href");
            if (!url) {
                return;
            }

            var labelDefault = link.getAttribute("data-label-default") || link.textContent.trim();
            var labelLoading = link.getAttribute("data-label-loading") || "Wird erstellt …";
            var downloadUrl = url.indexOf("?") === -1 ? url + "?dl=1" : url + "&dl=1";

            link.classList.add("is-loading");
            link.setAttribute("aria-busy", "true");
            link.textContent = labelLoading;

            var iframe = document.createElement("iframe");
            iframe.className = "dashboard-document-download-frame";
            iframe.setAttribute("aria-hidden", "true");
            iframe.src = downloadUrl;
            document.body.appendChild(iframe);

            window.setTimeout(function () {
                iframe.remove();
                link.classList.remove("is-loading");
                link.removeAttribute("aria-busy");
                link.textContent = labelDefault;
            }, 6000);

            window.setTimeout(function () {
                link.textContent = "Download gestartet – prüfen Sie Ihren Download-Ordner";
                window.setTimeout(function () {
                    link.textContent = labelDefault;
                }, 3500);
            }, 1200);
        });
    });
});
