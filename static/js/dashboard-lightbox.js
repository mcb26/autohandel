document.addEventListener("DOMContentLoaded", function () {
    var dataEl = document.getElementById("dashboard-lightbox-images");
    var lightbox = document.getElementById("dashboard-lightbox");
    if (!dataEl || !lightbox) {
        return;
    }

    var images = [];
    try {
        images = JSON.parse(dataEl.textContent || "[]");
    } catch (error) {
        return;
    }
    if (!images.length) {
        return;
    }

    var imgEl = document.getElementById("dashboard-lightbox-img");
    var counterEl = document.getElementById("dashboard-lightbox-counter");
    var closeBtn = lightbox.querySelector(".dashboard-lightbox-close");
    var prevBtn = lightbox.querySelector(".dashboard-lightbox-prev");
    var nextBtn = lightbox.querySelector(".dashboard-lightbox-next");
    var currentIndex = 0;
    var lastFocus = null;

    function showImage(index) {
        if (index < 0) {
            index = images.length - 1;
        }
        if (index >= images.length) {
            index = 0;
        }
        currentIndex = index;
        imgEl.src = images[currentIndex];
        imgEl.alt = "Fahrzeugbild " + (currentIndex + 1);
        if (counterEl) {
            counterEl.textContent = (currentIndex + 1) + " / " + images.length;
        }
    }

    function openLightbox(index) {
        lastFocus = document.activeElement;
        showImage(index);
        lightbox.classList.remove("d-none");
        document.body.classList.add("dashboard-lightbox-open");
        closeBtn.focus();
    }

    function closeLightbox() {
        lightbox.classList.add("d-none");
        document.body.classList.remove("dashboard-lightbox-open");
        imgEl.src = "";
        if (lastFocus && typeof lastFocus.focus === "function") {
            lastFocus.focus();
        }
    }

    function step(delta) {
        showImage(currentIndex + delta);
    }

    document.querySelectorAll(".dashboard-lightbox-open").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var index = parseInt(btn.getAttribute("data-lightbox-index"), 10);
            if (Number.isNaN(index)) {
                index = 0;
            }
            openLightbox(index);
        });
    });

    closeBtn.addEventListener("click", closeLightbox);
    prevBtn.addEventListener("click", function () {
        step(-1);
    });
    nextBtn.addEventListener("click", function () {
        step(1);
    });

    lightbox.addEventListener("click", function (event) {
        if (event.target === lightbox) {
            closeLightbox();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (lightbox.classList.contains("d-none")) {
            return;
        }
        if (event.key === "Escape") {
            closeLightbox();
        } else if (event.key === "ArrowLeft") {
            step(-1);
        } else if (event.key === "ArrowRight") {
            step(1);
        }
    });
});
