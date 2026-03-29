/**
 * DocForge — Client-side application logic.
 *
 * Handles file selection (click + drag-and-drop), dynamic format options,
 * conversion requests via fetch, and UI state transitions (progress,
 * success, error overlays).
 */

(function () {
    "use strict";

    /* ── Format mapping ──────────────────────────────────────────────── */
    const CONVERSIONS = {
        docx: [{ value: "pdf", label: "PDF", icon: "📄", desc: "Portable Document" }],
        pdf: [{ value: "docx", label: "DOCX", icon: "📝", desc: "Word Document" }],
        html: [{ value: "pdf", label: "PDF", icon: "📄", desc: "Portable Document" }],
    };

    /* ── DOM refs ─────────────────────────────────────────────────────── */
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const filePreview = document.getElementById("filePreview");
    const fileIcon = document.getElementById("fileIcon");
    const fileName = document.getElementById("fileName");
    const fileSize = document.getElementById("fileSize");
    const btnRemove = document.getElementById("btnRemove");
    const formatOptions = document.getElementById("formatOptions");
    const btnConvert = document.getElementById("btnConvert");
    const progressOverlay = document.getElementById("progressOverlay");
    const progressText = document.getElementById("progressText");
    const progressBarFill = document.getElementById("progressBarFill");
    const successOverlay = document.getElementById("successOverlay");
    const successFilename = document.getElementById("successFilename");
    const btnNewConversion = document.getElementById("btnNewConversion");
    const errorOverlay = document.getElementById("errorOverlay");
    const errorMessage = document.getElementById("errorMessage");
    const btnRetry = document.getElementById("btnRetry");

    /* ── State ────────────────────────────────────────────────────────── */
    let selectedFile = null;
    let selectedFormat = null;

    /* ── Helpers ──────────────────────────────────────────────────────── */
    function getExtension(name) {
        return name.split(".").pop().toLowerCase();
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    }

    /* ── File selection ────────────────────────────────────────────────── */
    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    // Drag & drop
    ["dragenter", "dragover"].forEach((evt) =>
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropzone.classList.add("drag-over");
        })
    );
    ["dragleave", "drop"].forEach((evt) =>
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropzone.classList.remove("drag-over");
        })
    );
    dropzone.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });

    function handleFile(file) {
        const ext = getExtension(file.name);

        if (!CONVERSIONS[ext]) {
            showError(`Unsupported file type ".${ext}". Please upload a DOCX, PDF, or HTML file.`);
            return;
        }

        selectedFile = file;
        selectedFormat = null;

        // Show preview
        fileName.textContent = file.name;
        fileSize.textContent = formatBytes(file.size);
        fileIcon.className = "file-icon " + ext;
        filePreview.classList.remove("hidden");
        dropzone.style.display = "none";

        // Build format options
        renderFormatOptions(ext);
        btnConvert.disabled = true;
    }

    btnRemove.addEventListener("click", resetUI);

    function resetUI() {
        selectedFile = null;
        selectedFormat = null;
        fileInput.value = "";

        filePreview.classList.add("hidden");
        dropzone.style.display = "";
        formatOptions.innerHTML = "";
        btnConvert.disabled = true;

        progressOverlay.classList.add("hidden");
        successOverlay.classList.add("hidden");
        errorOverlay.classList.add("hidden");
    }

    /* ── Format options ────────────────────────────────────────────────── */
    function renderFormatOptions(inputExt) {
        formatOptions.innerHTML = "";
        const options = CONVERSIONS[inputExt] || [];

        options.forEach((opt, idx) => {
            const el = document.createElement("div");
            el.className = "format-option";
            el.style.animationDelay = `${idx * 0.08}s`;
            el.innerHTML = `
                <span class="format-option-icon">${opt.icon}</span>
                <div>
                    <div class="format-option-label">${opt.label}</div>
                    <div class="format-option-desc">${opt.desc}</div>
                </div>
            `;
            el.addEventListener("click", () => selectFormat(el, opt.value));
            formatOptions.appendChild(el);
        });

        // Auto-select if only one option
        if (options.length === 1) {
            const firstEl = formatOptions.querySelector(".format-option");
            selectFormat(firstEl, options[0].value);
        }
    }

    function selectFormat(el, value) {
        document.querySelectorAll(".format-option").forEach((o) =>
            o.classList.remove("selected")
        );
        el.classList.add("selected");
        selectedFormat = value;
        btnConvert.disabled = false;
    }

    /* ── Conversion ────────────────────────────────────────────────────── */
    btnConvert.addEventListener("click", startConversion);
    btnNewConversion.addEventListener("click", resetUI);
    btnRetry.addEventListener("click", () => {
        errorOverlay.classList.add("hidden");
    });

    async function startConversion() {
        if (!selectedFile || !selectedFormat) return;

        // Show progress
        progressOverlay.classList.remove("hidden");
        progressText.textContent = "Uploading your document…";
        progressBarFill.style.width = "10%";

        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("target_format", selectedFormat);

        try {
            // Simulate upload progress visually
            progressBarFill.style.width = "30%";
            progressText.textContent = "Converting your document…";

            const response = await fetch("/convert", {
                method: "POST",
                body: formData,
            });

            progressBarFill.style.width = "80%";

            if (!response.ok) {
                let errMsg = "Conversion failed. Please try again.";
                try {
                    const errData = await response.json();
                    errMsg = errData.error || errMsg;
                } catch (_) {
                    /* response wasn't JSON */
                }
                throw new Error(errMsg);
            }

            progressBarFill.style.width = "95%";
            progressText.textContent = "Preparing download…";

            // Get the file blob and trigger download
            const blob = await response.blob();
            const outputName = buildOutputName(selectedFile.name, selectedFormat);

            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = outputName;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);

            progressBarFill.style.width = "100%";

            // Show success after brief pause
            setTimeout(() => {
                progressOverlay.classList.add("hidden");
                successFilename.textContent = outputName;
                successOverlay.classList.remove("hidden");
            }, 400);

        } catch (err) {
            progressOverlay.classList.add("hidden");
            showError(err.message);
        }
    }

    function buildOutputName(originalName, targetFormat) {
        const stem = originalName.substring(0, originalName.lastIndexOf(".")) || originalName;
        return `${stem}.${targetFormat}`;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorOverlay.classList.remove("hidden");
    }
})();
