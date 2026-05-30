document.addEventListener("DOMContentLoaded", function () {
    var storageKey = "cookie_consent_v1";
    var banner = document.getElementById("cookie-banner");
    var acceptBtn = document.getElementById("cookie-accept");
    var declineBtn = document.getElementById("cookie-decline");

    if (!banner || !acceptBtn || !declineBtn) {
        return;
    }

    var consentRaw = localStorage.getItem(storageKey);
    if (consentRaw) {
        banner.classList.add("d-none");
        return;
    }

    banner.classList.remove("d-none");

    function storeConsent(marketingAllowed) {
        var payload = {
            necessary: true,
            marketing: Boolean(marketingAllowed),
            statistics: Boolean(marketingAllowed),
            ts: new Date().toISOString(),
        };
        localStorage.setItem(storageKey, JSON.stringify(payload));
        banner.classList.add("d-none");
    }

    acceptBtn.addEventListener("click", function () {
        storeConsent(true);
    });

    declineBtn.addEventListener("click", function () {
        storeConsent(false);
    });
});
