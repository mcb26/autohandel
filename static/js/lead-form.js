document.addEventListener("DOMContentLoaded", function () {
    var catalogSyncOnSubmit = null;

    function initVehicleCatalog() {
        var configEl = document.getElementById("lead-form-config");
        var brandSelect = document.getElementById("id_brand");
        var modelSelect = document.getElementById("id_model");
        var seriesSelect = document.getElementById("id_series");
        var engineSelect = document.getElementById("id_engine_choice");
        var loadingEl = document.getElementById("catalog-loading");
        var catalogRow = document.querySelector(".vehicle-catalog-row");

        if (!configEl || !brandSelect || !modelSelect || !seriesSelect || !engineSelect) {
            return;
        }

        var config = {};
        try {
            config = JSON.parse(configEl.textContent || "{}");
        } catch (error) {
            return;
        }

        var brandDetailUrl = config.brandDetailUrl || "";
        var catalogCache = {};
        var tomInstances = {};
        var catalogLoading = false;
        var dependentSelects = [modelSelect, seriesSelect, engineSelect];
        var currentEngineEntries = [];
        var fuelSelect = document.getElementById("id_fuel_type");
        var specsPanel = document.getElementById("engine-specs-panel");
        var specDisplacement = document.getElementById("engine-spec-displacement");
        var specHp = document.getElementById("engine-spec-hp");
        var specFuel = document.getElementById("engine-spec-fuel");

        var fuelLabels = {
            benzin: "Benzin",
            diesel: "Diesel",
            elektro: "Elektro",
            hybrid: "Hybrid",
            gas: "Gas (LPG/CNG)",
            other: "Sonstiges",
        };

        function parseDisplacementFromLabel(label) {
            if (!label) {
                return "";
            }
            var match = label.match(/(?:^|[\s(])(\d+(?:\.\d+)?)\s*(?:l|L|Liter)?(?:\s|\(|$|TDI|TSI|CDI|d|i|V\d)/i);
            if (match) {
                return match[1];
            }
            match = label.match(/(\d+\.\d+)\s*(?:TSI|TDI|CDI|HDI|DCI|d|i)/i);
            return match ? match[1] : "";
        }

        function updateEngineSpecsPanel() {
            var label = engineSelect.value;
            if (!label || !specsPanel) {
                if (specsPanel) {
                    specsPanel.classList.add("d-none");
                }
                return;
            }

            var entry = null;
            currentEngineEntries.forEach(function (eng) {
                if (eng.label === label) {
                    entry = eng;
                }
            });

            var displacement = (entry && entry.displacement) || parseDisplacementFromLabel(label);
            var hp = entry && entry.hp;
            var fuelKey = entry && entry.fuel;

            if (specDisplacement) {
                specDisplacement.textContent = displacement ? displacement + " l" : "–";
            }
            if (specHp) {
                specHp.textContent = hp ? hp + " PS" : "–";
            }
            if (specFuel) {
                specFuel.textContent = fuelKey ? fuelLabels[fuelKey] || fuelKey : "–";
            }

            if (fuelSelect && fuelKey && fuelLabels[fuelKey]) {
                fuelSelect.value = fuelKey;
            }

            specsPanel.classList.remove("d-none");
        }

        function setCatalogLoading(active) {
            catalogLoading = active;
            if (loadingEl) {
                loadingEl.classList.toggle("d-none", !active);
            }
            if (catalogRow) {
                catalogRow.classList.toggle("is-catalog-loading", active);
            }
            dependentSelects.forEach(function (select) {
                select.disabled = active;
                var tom = tomInstances[select.id];
                if (tom) {
                    if (active) {
                        tom.disable();
                    } else {
                        tom.enable();
                    }
                }
            });
            if (active && tomInstances[brandSelect.id]) {
                tomInstances[brandSelect.id].disable();
            } else if (!active && tomInstances[brandSelect.id]) {
                tomInstances[brandSelect.id].enable();
            }
        }

        function syncTomSelectToNative(selectEl) {
            if (!selectEl) {
                return;
            }
            selectEl.disabled = false;
            var tom = tomInstances[selectEl.id];
            if (!tom) {
                return;
            }
            var value = tom.getValue();
            if (value === null || value === undefined) {
                value = "";
            }
            if (Array.isArray(value)) {
                value = value[0] || "";
            }
            selectEl.value = value;
            if (tom.isDisabled) {
                tom.enable();
            }
        }

        function syncAllCatalogFields() {
            syncTomSelectToNative(brandSelect);
            syncTomSelectToNative(modelSelect);
            syncTomSelectToNative(seriesSelect);
            syncTomSelectToNative(engineSelect);
        }

        catalogSyncOnSubmit = syncAllCatalogFields;

        function initTomSelect(selectEl) {
            if (!selectEl || typeof TomSelect === "undefined") {
                return;
            }
            if (tomInstances[selectEl.id]) {
                tomInstances[selectEl.id].destroy();
                delete tomInstances[selectEl.id];
            }
            tomInstances[selectEl.id] = new TomSelect(selectEl, {
                create: false,
                allowEmptyOption: true,
                maxOptions: null,
                placeholder: selectEl.options[0] ? selectEl.options[0].text : "",
                onChange: function () {
                    selectEl.value = this.getValue() || "";
                    if (selectEl === engineSelect) {
                        updateEngineSpecsPanel();
                    }
                },
            });
        }

        function setOptions(select, options, placeholder) {
            var tom = tomInstances[select.id];
            if (tom) {
                tom.destroy();
                delete tomInstances[select.id];
            }

            select.innerHTML = "";
            var placeholderOption = document.createElement("option");
            placeholderOption.value = "";
            placeholderOption.textContent = placeholder;
            select.appendChild(placeholderOption);

            options.forEach(function (option) {
                var el = document.createElement("option");
                el.value = option.value;
                el.textContent = option.label;
                select.appendChild(el);
            });

            select.disabled = catalogLoading;
            initTomSelect(select);
            if (catalogLoading && tomInstances[select.id]) {
                tomInstances[select.id].disable();
            }
        }

        var catalogErrorEl = document.getElementById("catalog-error");

        function showCatalogError(message) {
            if (!catalogErrorEl) {
                return;
            }
            catalogErrorEl.textContent = message;
            catalogErrorEl.classList.remove("d-none");
        }

        function hideCatalogError() {
            if (catalogErrorEl) {
                catalogErrorEl.classList.add("d-none");
            }
        }

        function fetchBrandCatalog(brandKey, showLoader) {
            if (!brandKey) {
                return Promise.resolve(null);
            }
            if (catalogCache[brandKey]) {
                hideCatalogError();
                return Promise.resolve(catalogCache[brandKey]);
            }
            var url = brandDetailUrl.replace("__SLUG__", encodeURIComponent(brandKey));
            if (showLoader) {
                setCatalogLoading(true);
            }
            hideCatalogError();
            return fetch(url, { headers: { Accept: "application/json" } })
                .then(function (response) {
                    if (!response.ok) {
                        showCatalogError("Fahrzeugdaten konnten nicht geladen werden. Bitte Seite neu laden.");
                        return null;
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (data) {
                        catalogCache[brandKey] = data;
                        hideCatalogError();
                    } else if (brandKey) {
                        showCatalogError("Für diese Marke sind keine Modelle verfügbar.");
                    }
                    return data;
                })
                .catch(function () {
                    showCatalogError("Verbindungsfehler beim Laden der Fahrzeugdaten. Bitte erneut versuchen.");
                    return null;
                })
                .finally(function () {
                    if (showLoader) {
                        setCatalogLoading(false);
                    }
                });
        }

        function updateModels(catalog, keep) {
            var modelOptions = [];
            if (catalog && catalog.models) {
                Object.keys(catalog.models).forEach(function (modelKey) {
                    modelOptions.push({
                        value: modelKey,
                        label: catalog.models[modelKey].label,
                    });
                });
            }
            setOptions(modelSelect, modelOptions, "Bitte Modellreihe auswählen");
            if (keep && keep.model) {
                modelSelect.value = keep.model;
                if (tomInstances[modelSelect.id]) {
                    tomInstances[modelSelect.id].setValue(keep.model, true);
                }
            } else if (modelSelect.value && tomInstances[modelSelect.id]) {
                tomInstances[modelSelect.id].setValue(modelSelect.value, true);
            }
        }

        function updateSeries(catalog, keep) {
            var brandKey = brandSelect.value;
            var modelKey = modelSelect.value;
            var seriesOptions = [];
            if (catalog && brandKey && modelKey && catalog.models && catalog.models[modelKey]) {
                var seriesMap = catalog.models[modelKey].series || {};
                Object.keys(seriesMap).forEach(function (seriesKey) {
                    seriesOptions.push({
                        value: seriesKey,
                        label: seriesMap[seriesKey].label,
                    });
                });
            }
            setOptions(seriesSelect, seriesOptions, "Bitte Baureihe auswählen");
            if (keep && keep.series) {
                seriesSelect.value = keep.series;
                if (tomInstances[seriesSelect.id]) {
                    tomInstances[seriesSelect.id].setValue(keep.series, true);
                }
            } else if (seriesSelect.value && tomInstances[seriesSelect.id]) {
                tomInstances[seriesSelect.id].setValue(seriesSelect.value, true);
            }
        }

        function updateEngines(catalog, keep) {
            var brandKey = brandSelect.value;
            var modelKey = modelSelect.value;
            var seriesKey = seriesSelect.value;
            var engineOptions = [];
            currentEngineEntries = [];
            if (
                catalog &&
                brandKey &&
                modelKey &&
                seriesKey &&
                catalog.models &&
                catalog.models[modelKey] &&
                catalog.models[modelKey].series &&
                catalog.models[modelKey].series[seriesKey]
            ) {
                currentEngineEntries = catalog.models[modelKey].series[seriesKey].engines || [];
                currentEngineEntries.forEach(function (eng) {
                    engineOptions.push({ value: eng.label, label: eng.label });
                });
            }
            setOptions(engineSelect, engineOptions, "Bitte Ausstattung / Motorisierung auswählen");
            if (keep && keep.engine) {
                engineSelect.value = keep.engine;
                if (tomInstances[engineSelect.id]) {
                    tomInstances[engineSelect.id].setValue(keep.engine, true);
                }
            } else if (engineSelect.value && tomInstances[engineSelect.id]) {
                tomInstances[engineSelect.id].setValue(engineSelect.value, true);
            }
            updateEngineSpecsPanel();
        }

        function resetDependentSelects() {
            currentEngineEntries = [];
            if (specsPanel) {
                specsPanel.classList.add("d-none");
            }
            setOptions(modelSelect, [], "Bitte zuerst Marke auswählen");
            setOptions(seriesSelect, [], "Bitte zuerst Modellreihe auswählen");
            setOptions(engineSelect, [], "Bitte zuerst Baureihe auswählen");
        }

        function onBrandChange() {
            var brandKey = brandSelect.value;
            resetDependentSelects();
            if (!brandKey) {
                return;
            }
            fetchBrandCatalog(brandKey, true).then(function (catalog) {
                updateModels(catalog, null);
                updateSeries(catalog, null);
                updateEngines(catalog, null);
            });
        }

        function onModelChange() {
            var brandKey = brandSelect.value;
            fetchBrandCatalog(brandKey, false).then(function (catalog) {
                updateSeries(catalog, null);
                updateEngines(catalog, null);
            });
        }

        function onSeriesChange() {
            var brandKey = brandSelect.value;
            fetchBrandCatalog(brandKey, false).then(function (catalog) {
                updateEngines(catalog, null);
            });
        }

        engineSelect.addEventListener("change", updateEngineSpecsPanel);
        brandSelect.addEventListener("change", onBrandChange);
        modelSelect.addEventListener("change", onModelChange);
        seriesSelect.addEventListener("change", onSeriesChange);

        initTomSelect(brandSelect);
        initTomSelect(modelSelect);
        initTomSelect(seriesSelect);
        initTomSelect(engineSelect);

        var initial = { model: modelSelect.value, series: seriesSelect.value, engine: engineSelect.value };
        if (brandSelect.value) {
            fetchBrandCatalog(brandSelect.value, true).then(function (catalog) {
                updateModels(catalog, initial);
                updateSeries(catalog, initial);
                updateEngines(catalog, initial);
            });
        }
    }

    function initImageMultiUpload() {
        var fileInput = document.getElementById("id_images");
        var dropzone = document.getElementById("images-dropzone");
        var list = document.getElementById("images-selected-list");
        if (!fileInput || !dropzone || !list) {
            return;
        }

        var selectedFiles = [];
        var previewUrls = new Map();
        var maxFiles = 10;

        function revokePreview(file) {
            var url = previewUrls.get(file);
            if (url) {
                URL.revokeObjectURL(url);
                previewUrls.delete(file);
            }
        }

        function syncInputFiles() {
            var dt = new DataTransfer();
            selectedFiles.forEach(function (file) {
                dt.items.add(file);
            });
            fileInput.files = dt.files;
        }

        function renderList() {
            list.innerHTML = "";
            selectedFiles.forEach(function (file, index) {
                var item = document.createElement("div");
                item.className = "images-selected-item";

                var thumb = document.createElement("img");
                thumb.className = "images-selected-thumb";
                thumb.alt = "";
                var previewUrl = previewUrls.get(file);
                if (!previewUrl) {
                    previewUrl = URL.createObjectURL(file);
                    previewUrls.set(file, previewUrl);
                }
                thumb.src = previewUrl;
                item.appendChild(thumb);

                var name = document.createElement("span");
                name.className = "images-selected-name";
                name.textContent = file.name;
                item.appendChild(name);

                var remove = document.createElement("button");
                remove.type = "button";
                remove.className = "images-selected-remove";
                remove.setAttribute("aria-label", "Bild entfernen: " + file.name);
                remove.textContent = "×";
                remove.addEventListener("click", function () {
                    revokePreview(file);
                    selectedFiles.splice(index, 1);
                    syncInputFiles();
                    renderList();
                });
                item.appendChild(remove);

                list.appendChild(item);
            });
        }

        function addFiles(fileList) {
            Array.from(fileList).forEach(function (file) {
                if (!file || !file.type || !file.type.startsWith("image/")) {
                    return;
                }
                var exists = selectedFiles.some(function (item) {
                    return (
                        item.name === file.name &&
                        item.size === file.size &&
                        item.lastModified === file.lastModified
                    );
                });
                if (selectedFiles.length >= maxFiles) {
                    dropzone.classList.add("is-limit-reached");
                    window.setTimeout(function () {
                        dropzone.classList.remove("is-limit-reached");
                    }, 2500);
                    return;
                }
                if (exists) {
                    return;
                }
                selectedFiles.push(file);
            });
            syncInputFiles();
            renderList();
        }

        fileInput.addEventListener("change", function () {
            addFiles(fileInput.files);
        });

        dropzone.addEventListener("click", function () {
            fileInput.click();
        });
        dropzone.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                fileInput.click();
            }
        });

        ["dragenter", "dragover"].forEach(function (name) {
            dropzone.addEventListener(name, function (event) {
                event.preventDefault();
                dropzone.classList.add("is-dragover");
            });
        });
        ["dragleave", "drop"].forEach(function (name) {
            dropzone.addEventListener(name, function (event) {
                event.preventDefault();
                dropzone.classList.remove("is-dragover");
            });
        });
        dropzone.addEventListener("drop", function (event) {
            if (event.dataTransfer && event.dataTransfer.files) {
                addFiles(event.dataTransfer.files);
            }
        });
    }

    function commitFieldValue(input) {
        if (!input) {
            return;
        }
        var value = input.value;
        if (value !== undefined && value !== null) {
            input.value = value;
            input.setAttribute("value", value);
        }
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function scrollToFirstFormError() {
        var firstError = document.querySelector(".lead-form .is-field-invalid, .lead-form .alert-danger");
        if (firstError) {
            firstError.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }

    function initLeadFormSubmit() {
        var leadForm = document.querySelector(".lead-form");
        if (!leadForm) {
            return;
        }

        var submitBtn = document.getElementById("lead-form-submit-btn");
        var submitLabel = submitBtn && submitBtn.querySelector(".btn-submit-label");
        var contactNames = ["customer_name", "email", "phone", "postal_code"];

        if (leadForm.querySelector(".is-field-invalid, .alert-danger")) {
            scrollToFirstFormError();
        }

        leadForm.addEventListener(
            "submit",
            function () {
                if (typeof catalogSyncOnSubmit === "function") {
                    catalogSyncOnSubmit();
                }

                contactNames.forEach(function (name) {
                    commitFieldValue(leadForm.querySelector('[name="' + name + '"]'));
                });

                var privacy = document.getElementById("id_privacy_accepted");
                if (privacy && privacy.checked) {
                    privacy.checked = true;
                }

                if (submitBtn && !submitBtn.disabled) {
                    submitBtn.disabled = true;
                    submitBtn.classList.add("is-loading");
                    if (submitLabel) {
                        submitLabel.textContent = "Wird gesendet …";
                    }
                }
            },
            true
        );
    }

    function initMonthYearInput() {
        document.querySelectorAll(".lead-month-year-input").forEach(function (input) {
            input.addEventListener("input", function () {
                var digits = input.value.replace(/\D/g, "").slice(0, 4);
                if (digits.length <= 2) {
                    input.value = digits;
                    return;
                }
                input.value = digits.slice(0, 2) + "/" + digits.slice(2);
            });

            input.addEventListener("keydown", function (event) {
                if (event.key === "Backspace" && input.value.endsWith("/")) {
                    input.value = input.value.slice(0, -1);
                }
            });
        });
    }

    function syncChoiceChip(chip) {
        var input = chip.querySelector('input[type="checkbox"]');
        if (!input) {
            return;
        }
        chip.classList.toggle("is-selected", input.checked);
    }

    function initChoiceChips() {
        document.querySelectorAll(".choice-chip").forEach(function (chip) {
            syncChoiceChip(chip);
            var input = chip.querySelector('input[type="checkbox"]');
            if (!input) {
                return;
            }
            input.addEventListener("change", function () {
                syncChoiceChip(chip);
            });
        });
    }

    function initCollapsibleFormSections() {
        document.querySelectorAll("[data-collapsible-section]").forEach(function (section) {
            var toggle = section.querySelector(".form-section-toggle");
            var summary = section.querySelector("[data-section-summary]");
            var labelEl = toggle && toggle.querySelector(".form-section-toggle-label");
            var sectionType = section.getAttribute("data-section-type") || "";

            if (!toggle) {
                return;
            }

            function countSelected() {
                return section.querySelectorAll('input[type="checkbox"]:checked').length;
            }

            function buildSummaryText() {
                var count = countSelected();
                if (sectionType === "features") {
                    if (count === 0) {
                        return "Keine Merkmale ausgewählt";
                    }
                    return count === 1
                        ? "1 Merkmal ausgewählt"
                        : count + " Merkmale ausgewählt";
                }
                if (sectionType === "extras") {
                    if (count === 0) {
                        return "Keine Extras ausgewählt";
                    }
                    return count === 1
                        ? "1 Extra ausgewählt"
                        : count + " Extras ausgewählt";
                }
                return count === 0 ? "Nichts ausgewählt" : count + " ausgewählt";
            }

            function updateSummary() {
                if (!summary) {
                    return;
                }
                summary.textContent = buildSummaryText();
            }

            function setExpanded(expanded) {
                section.classList.toggle("is-expanded", expanded);
                toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
                if (labelEl) {
                    labelEl.textContent = expanded ? "Ausblenden" : "Einblenden";
                }
                if (summary) {
                    summary.hidden = expanded;
                    if (!expanded) {
                        updateSummary();
                    }
                }
            }

            if (section.querySelector(".field-error-message")) {
                setExpanded(true);
            } else {
                setExpanded(false);
            }

            toggle.addEventListener("click", function () {
                setExpanded(!section.classList.contains("is-expanded"));
            });

            section.querySelectorAll('input[type="checkbox"]').forEach(function (input) {
                input.addEventListener("change", function () {
                    if (!section.classList.contains("is-expanded")) {
                        updateSummary();
                    }
                });
            });
        });
    }

    function initVehicleExtrasPicker() {
        var root = document.getElementById("vehicle-extras-field");
        if (!root) {
            return;
        }

        var searchInput = document.getElementById("vehicle-extras-search");
        var countEl = document.getElementById("vehicle-extras-count");
        var clearBtn = document.getElementById("vehicle-extras-clear");
        var emptyEl = document.getElementById("vehicle-extras-empty");
        var chips = root.querySelectorAll(".choice-chip--extra");
        var groups = root.querySelectorAll("[data-extras-group]");

        function updateExtrasCount() {
            if (!countEl) {
                return;
            }
            var selected = root.querySelectorAll('.choice-chip--extra input[type="checkbox"]:checked').length;
            countEl.textContent =
                selected === 1 ? "1 Extra ausgewählt" : selected + " Extras ausgewählt";
        }

        function applyExtrasFilter() {
            var query = (searchInput && searchInput.value ? searchInput.value : "")
                .trim()
                .toLowerCase();
            var visibleTotal = 0;

            groups.forEach(function (group) {
                var groupVisible = 0;
                group.querySelectorAll(".choice-chip--extra").forEach(function (chip) {
                    var label = (chip.getAttribute("data-extra-label") || "").toLowerCase();
                    var show = !query || label.indexOf(query) !== -1;
                    chip.classList.toggle("is-filter-hidden", !show);
                    if (show) {
                        groupVisible += 1;
                        visibleTotal += 1;
                    }
                });
                group.classList.toggle("is-filter-hidden", groupVisible === 0);
            });

            if (emptyEl) {
                emptyEl.classList.toggle("d-none", visibleTotal > 0 || !query);
            }
        }

        chips.forEach(function (chip) {
            var input = chip.querySelector('input[type="checkbox"]');
            if (!input) {
                return;
            }
            input.addEventListener("change", function () {
                syncChoiceChip(chip);
                updateExtrasCount();
            });
        });

        if (searchInput) {
            searchInput.addEventListener("input", applyExtrasFilter);
        }

        if (clearBtn) {
            clearBtn.addEventListener("click", function () {
                chips.forEach(function (chip) {
                    var input = chip.querySelector('input[type="checkbox"]');
                    if (input && input.checked) {
                        input.checked = false;
                        syncChoiceChip(chip);
                    }
                });
                updateExtrasCount();
            });
        }

        updateExtrasCount();
        applyExtrasFilter();
    }

    initVehicleCatalog();
    initImageMultiUpload();
    initMonthYearInput();
    initChoiceChips();
    initCollapsibleFormSections();
    initVehicleExtrasPicker();
    initLeadFormSubmit();
});
