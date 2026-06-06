document.addEventListener("DOMContentLoaded", function () {
    var storageKey = "cookie_consent_v1";
    var banner = document.getElementById("cookie-banner");
    var acceptBtn = document.getElementById("cookie-accept");
    var declineBtn = document.getElementById("cookie-decline");

    if (!banner || !acceptBtn || !declineBtn) {
        return;
    }

    function setBannerVisible(visible) {
        banner.classList.toggle("d-none", !visible);
        document.body.classList.toggle("cookie-banner-visible", visible);
    }

    var consentRaw = localStorage.getItem(storageKey);
    if (consentRaw) {
        setBannerVisible(false);
        return;
    }

    setBannerVisible(true);

    function storeConsent(marketingAllowed) {
        var payload = {
            necessary: true,
            marketing: Boolean(marketingAllowed),
            statistics: Boolean(marketingAllowed),
            ts: new Date().toISOString(),
        };
        localStorage.setItem(storageKey, JSON.stringify(payload));
        setBannerVisible(false);
    }

    acceptBtn.addEventListener("click", function () {
        storeConsent(true);
    });

    declineBtn.addEventListener("click", function () {
        storeConsent(false);
    });
});
