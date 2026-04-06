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
        docx: [
            { value: "html", label: "HTML", icon: "🌐", desc: "Standalone Web Document" },
            { value: "md", label: "Markdown", icon: "✍️", desc: "Plain Text Markdown" },
            { value: "pdf", label: "PDF", icon: "📄", desc: "Portable Document" },
        ],
        pptx: [{ value: "pdf", label: "PDF", icon: "📄", desc: "Portable Document" }],
        pdf: [
            { value: "doc", label: "DOC", icon: "📘", desc: "Legacy Word Document" },
            { value: "docx", label: "DOCX", icon: "📝", desc: "Word Document" },
            { value: "html", label: "HTML", icon: "🌐", desc: "Web Document" },
            { value: "md", label: "Markdown", icon: "✍️", desc: "Plain Text Markdown" },
        ],
        html: [
            { value: "md", label: "Markdown", icon: "✍️", desc: "Plain Text Markdown" },
            { value: "pdf", label: "PDF", icon: "📄", desc: "Portable Document" },
        ],
        md: [{ value: "pdf", label: "PDF", icon: "📄", desc: "Portable Document" }],
        txt: [{ value: "pdf", label: "PDF", icon: "📄", desc: "Portable Document" }],
    };

    /* ── DOM refs ─────────────────────────────────────────────────────── */
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const filePreview = document.getElementById("filePreview");
    const fileSummary = document.getElementById("fileSummary");
    const fileList = document.getElementById("fileList");
    const btnRemove = document.getElementById("btnRemove");
    const formatOptions = document.getElementById("formatOptions");
    const btnConvert = document.getElementById("btnConvert");
    const btnConvertText = document.getElementById("btnConvertText");
    const btnMerge = document.getElementById("btnMerge");
    const btnMergeText = document.getElementById("btnMergeText");
    const mergeHint = document.getElementById("mergeHint");
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
    let selectedFiles = [];
    let selectedFormat = null;

    /* ── Helpers ──────────────────────────────────────────────────────── */
    function normalizeExtension(ext) {
        return ext === "markdown" ? "md" : ext;
    }

    function getExtension(name) {
        return normalizeExtension(name.split(".").pop().toLowerCase());
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    }

    function buildOutputName(originalName, targetFormat) {
        const lastDot = originalName.lastIndexOf(".");
        const stem = lastDot > 0 ? originalName.substring(0, lastDot) : originalName;
        return `${stem}.${targetFormat}`;
    }

    function buildBatchOutputName(targetFormat) {
        return `docforge_batch_${targetFormat}.zip`;
    }

    function buildMergedOutputName() {
        return "docforge_merged.pdf";
    }

    function canMergeFiles(files) {
        return files.length > 1 && getCommonFormatOptions(files).some((option) => option.value === "pdf");
    }

    function updateActionButtons() {
        const fileCount = selectedFiles.length;
        btnConvert.disabled = fileCount === 0 || !selectedFormat;
        btnConvertText.textContent = fileCount > 1 ? `Convert ${fileCount} Files` : "Convert Now";

        const mergeAvailable = canMergeFiles(selectedFiles);
        btnMerge.disabled = !mergeAvailable;
        btnMergeText.textContent = mergeAvailable ? `Merge ${fileCount} Files to PDF` : "Merge to PDF";
        mergeHint.classList.toggle("hidden", !mergeAvailable);
    }

    function getCommonFormatOptions(files) {
        const optionSets = files.map((file) => {
            const ext = getExtension(file.name);
            return CONVERSIONS[ext] || [];
        });

        if (!optionSets.length) {
            return [];
        }

        return optionSets[0].filter((candidate) =>
            optionSets.every((options) =>
                options.some((option) => option.value === candidate.value)
            )
        );
    }

    function extractDownloadName(contentDisposition) {
        if (!contentDisposition) {
            return null;
        }

        const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
        if (utf8Match) {
            return decodeURIComponent(utf8Match[1]);
        }

        const plainMatch = contentDisposition.match(/filename="?([^"]+)"?/i);
        return plainMatch ? plainMatch[1] : null;
    }

    function renderFilePreview() {
        const totalBytes = selectedFiles.reduce((sum, file) => sum + file.size, 0);
        const countLabel = selectedFiles.length === 1 ? "1 file selected" : `${selectedFiles.length} files selected`;

        fileSummary.textContent = `${countLabel} • ${formatBytes(totalBytes)}`;
        fileList.innerHTML = "";

        selectedFiles.forEach((file) => {
            const ext = getExtension(file.name);
            const row = document.createElement("div");
            row.className = "file-row";
            row.innerHTML = `
                <div class="file-icon ${ext}">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor"
                            stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                        <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="1.5" />
                    </svg>
                </div>
                <div class="file-info">
                    <p class="file-name">${file.name}</p>
                    <p class="file-size">${formatBytes(file.size)}</p>
                </div>
            `;
            fileList.appendChild(row);
        });

        filePreview.classList.remove("hidden");
        dropzone.style.display = "none";
    }

    /* ── File selection ────────────────────────────────────────────────── */
    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) handleFiles(e.target.files);
    });

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
        if (e.dataTransfer.files.length) {
            handleFiles(e.dataTransfer.files);
        }
    });

    function handleFiles(fileCollection) {
        const files = Array.from(fileCollection);
        const unsupported = files.filter((file) => !CONVERSIONS[getExtension(file.name)]);

        if (unsupported.length) {
            const invalidNames = unsupported.map((file) => `"${file.name}"`).join(", ");
            showError(`Unsupported file type in ${invalidNames}. Please upload DOCX, PPTX, PDF, HTML, Markdown, or TXT files.`);
            return;
        }

        const options = getCommonFormatOptions(files);
        if (!options.length) {
            showError("These files do not share a common output format. Choose files that can be converted to the same target format.");
            return;
        }

        selectedFiles = files;
        selectedFormat = null;

        renderFilePreview();
        renderFormatOptions(options);
        updateActionButtons();
    }

    btnRemove.addEventListener("click", resetUI);

    function resetUI() {
        selectedFiles = [];
        selectedFormat = null;
        fileInput.value = "";

        filePreview.classList.add("hidden");
        dropzone.style.display = "";
        fileSummary.textContent = "";
        fileList.innerHTML = "";
        formatOptions.innerHTML = "";

        progressBarFill.style.width = "0%";
        progressOverlay.classList.add("hidden");
        successOverlay.classList.add("hidden");
        errorOverlay.classList.add("hidden");

        updateActionButtons();
    }

    /* ── Format options ────────────────────────────────────────────────── */
    function renderFormatOptions(options) {
        formatOptions.innerHTML = "";

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

        if (options.length === 1) {
            const firstEl = formatOptions.querySelector(".format-option");
            selectFormat(firstEl, options[0].value);
        }
    }

    function selectFormat(el, value) {
        document.querySelectorAll(".format-option").forEach((option) =>
            option.classList.remove("selected")
        );
        el.classList.add("selected");
        selectedFormat = value;
        updateActionButtons();
    }

    /* ── Conversion ────────────────────────────────────────────────────── */
    btnConvert.addEventListener("click", startConversion);
    btnMerge.addEventListener("click", startMerge);
    btnNewConversion.addEventListener("click", resetUI);
    btnRetry.addEventListener("click", () => {
        errorOverlay.classList.add("hidden");
    });

    async function submitFiles({
        endpoint,
        initialText,
        processingText,
        fallbackName,
        errorMessage,
        includeTargetFormat = false,
    }) {
        progressOverlay.classList.remove("hidden");
        progressText.textContent = initialText;
        progressBarFill.style.width = "10%";

        const formData = new FormData();
        selectedFiles.forEach((file) => formData.append("file", file));

        try {
            progressBarFill.style.width = "30%";
            progressText.textContent = processingText;

            if (includeTargetFormat && selectedFormat) {
                formData.append("target_format", selectedFormat);
            }

            const response = await fetch(endpoint, {
                method: "POST",
                body: formData,
            });

            progressBarFill.style.width = "80%";

            if (!response.ok) {
                let errMsg = errorMessage;
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

            const blob = await response.blob();
            const contentDisposition = response.headers.get("Content-Disposition");
            const outputName = extractDownloadName(contentDisposition) || fallbackName();

            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = outputName;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);

            progressBarFill.style.width = "100%";

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

    async function startConversion() {
        if (!selectedFiles.length || !selectedFormat) {
            return;
        }

        const isBatch = selectedFiles.length > 1;
        await submitFiles({
            endpoint: "/convert",
            initialText: isBatch ? "Uploading your files…" : "Uploading your document…",
            processingText: isBatch ? "Converting your files…" : "Converting your document…",
            fallbackName: () => (
                isBatch
                    ? buildBatchOutputName(selectedFormat)
                    : buildOutputName(selectedFiles[0].name, selectedFormat)
            ),
            errorMessage: "Conversion failed. Please try again.",
            includeTargetFormat: true,
        });
    }

    async function startMerge() {
        if (!canMergeFiles(selectedFiles)) {
            return;
        }

        await submitFiles({
            endpoint: "/merge",
            initialText: "Uploading documents for merge…",
            processingText: "Merging documents into one PDF…",
            fallbackName: buildMergedOutputName,
            errorMessage: "Merge failed. Please try again.",
        });
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorOverlay.classList.remove("hidden");
    }
})();
