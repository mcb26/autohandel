document.addEventListener("DOMContentLoaded", function () {
    var docxType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

    document.querySelectorAll("[data-document-download]").forEach(function (link) {
        link.addEventListener("click", function (event) {
            event.preventDefault();

            var url = link.getAttribute("href");
            if (!url) {
                return;
            }

            var labelDefault = link.getAttribute("data-label-default") || link.textContent.trim();
            var labelLoading = link.getAttribute("data-label-loading") || "Wird erstellt …";

            link.classList.add("is-loading");
            link.setAttribute("aria-busy", "true");
            link.textContent = labelLoading;

            fetch(url, { credentials: "same-origin", redirect: "follow" })
                .then(function (response) {
                    var contentType = response.headers.get("Content-Type") || "";
                    if (!response.ok || contentType.indexOf(docxType) === -1) {
                        throw new Error("invalid_response");
                    }
                    var disposition = response.headers.get("Content-Disposition") || "";
                    var filename = "Dokument.docx";
                    var match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
                    if (match) {
                        filename = decodeURIComponent(match[1]);
                    }
                    return response.blob().then(function (blob) {
                        return { blob: blob, filename: filename };
                    });
                })
                .then(function (result) {
                    var objectUrl = URL.createObjectURL(result.blob);
                    var anchor = document.createElement("a");
                    anchor.href = objectUrl;
                    anchor.download = result.filename;
                    anchor.style.display = "none";
                    document.body.appendChild(anchor);
                    anchor.click();
                    anchor.remove();
                    URL.revokeObjectURL(objectUrl);
                    link.classList.add("is-download-done");
                    link.textContent = "Download gestartet";
                    window.setTimeout(function () {
                        link.textContent = labelDefault;
                        link.classList.remove("is-download-done");
                    }, 2500);
                })
                .catch(function () {
                    window.alert(
                        "Das Dokument konnte nicht erstellt werden. " +
                            "Bitte prüfen Sie, ob Sie eingeloggt sind, und versuchen Sie es erneut."
                    );
                    link.textContent = labelDefault;
                })
                .finally(function () {
                    link.classList.remove("is-loading");
                    link.removeAttribute("aria-busy");
                });
        });
    });
});
