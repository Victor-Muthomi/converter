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
    const navMerge = document.getElementById("navMerge");
    const navZip = document.getElementById("navZip");
    const navCompress = document.getElementById("navCompress");
    const dropdownItems = document.querySelectorAll(".dropdown-item");

    /* ── State ────────────────────────────────────────────────────────── */
    let selectedFiles = [];
    let selectedFormat = null;
    let pendingSourceFormat = null; // set when user picks a conversion from navbar
    let currentMode = "convert";

    /* ── Source-format filter map ─────────────────────────────────────── */
    const SOURCE_FORMAT_ACCEPT = {
        docx: ".docx",
        pptx: ".pptx",
        pdf: ".pdf",
        html: ".html",
        md: ".md,.markdown",
        txt: ".txt",
    };

    const DEFAULT_ACCEPT = ".docx,.pptx,.pdf,.html,.md,.markdown,.txt";
    const DEFAULT_FORMATS_TEXT = "Supports: DOCX, PPTX, PDF, HTML, MD, TXT — Max 50 MB";

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

    function buildZipOutputName() {
        return "docforge_files.zip";
    }

    function buildCompressedOutputName(originalName) {
        const lastDot = originalName.lastIndexOf(".");
        const stem = lastDot > 0 ? originalName.substring(0, lastDot) : originalName;
        const ext = lastDot > 0 ? originalName.substring(lastDot + 1) : "";
        return ext ? `${stem}_compressed.${ext}` : `${stem}_compressed`;
    }

    function canConvertFileToPdf(file) {
        const ext = getExtension(file.name);
        return ext === "pdf" || (CONVERSIONS[ext] || []).some((option) => option.value === "pdf");
    }

    function canMergeFiles(files) {
        return files.length > 1 && files.every(canConvertFileToPdf);
    }

    function updateActionButtons() {
        const fileCount = selectedFiles.length;
        if (currentMode === "zip") {
            btnConvert.disabled = fileCount === 0;
            btnConvertText.textContent = fileCount > 1 ? `Zip ${fileCount} Files` : "Create ZIP";
        } else {
            btnConvert.disabled = fileCount === 0 || !selectedFormat;
            btnConvertText.textContent = fileCount > 1 ? `Convert ${fileCount} Files` : "Convert Now";
        }

        const mergeAvailable = canMergeFiles(selectedFiles);
        btnMerge.disabled = !mergeAvailable;
        btnMergeText.textContent = mergeAvailable ? `Merge ${fileCount} Files to PDF` : "Merge to PDF";
        mergeHint.classList.toggle("hidden", !mergeAvailable);
    }

    function renderZipModeState() {
        formatOptions.innerHTML = "";

        const message = document.createElement("p");
        message.className = "format-empty-state";
        message.textContent = "ZIP mode bundles your selected files into one archive without converting them.";
        formatOptions.appendChild(message);
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
        if (currentMode !== "zip" && !options.length && !canMergeFiles(files)) {
            showError("These files do not share a common output format. Choose files that can be converted to the same target format.");
            return;
        }

        selectedFiles = files;
        selectedFormat = null;

        renderFilePreview();
        if (currentMode === "zip") {
            renderZipModeState();
        } else {
            renderFormatOptions(options);
        }
        updateActionButtons();
    }

    btnRemove.addEventListener("click", resetUI);

    function resetUI() {
        selectedFiles = [];
        selectedFormat = null;
        pendingSourceFormat = null;
        currentMode = "convert";
        fileInput.value = "";

        // Restore default file filter
        fileInput.accept = DEFAULT_ACCEPT;
        document.querySelector(".dropzone-formats").textContent = DEFAULT_FORMATS_TEXT;

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

        if (!options.length) {
            const message = document.createElement("p");
            message.className = "format-empty-state";
            message.textContent = "These files do not share a direct conversion target, but they can still be merged into one PDF.";
            formatOptions.appendChild(message);
            return;
        }

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

    navMerge.addEventListener("click", (e) => {
        e.preventDefault();
        currentMode = "convert";
        if (selectedFiles.length) {
            renderFormatOptions(getCommonFormatOptions(selectedFiles));
            updateActionButtons();
        }
        showInfo("Merge Mode", "Please upload 2 or more documents. They will be automatically converted and merged into a single PDF.");
        fileInput.click();
    });

    navZip.addEventListener("click", (e) => {
        e.preventDefault();
        currentMode = "zip";
        selectedFormat = null;

        if (selectedFiles.length) {
            renderZipModeState();
            updateActionButtons();
        }

        showInfo("Zip Mode", "Please upload one or more documents. They will be bundled into a ZIP archive without conversion.");
        fileInput.click();
    });

    navCompress.addEventListener("click", (e) => {
        e.preventDefault();
        openCompressModal();
    });

    /* ── Compress Modal Logic ──────────────────────────────────────────── */
    const compressModal       = document.getElementById("compressModal");
    const compressModalClose  = document.getElementById("compressModalClose");
    const compressModalBackdrop = document.getElementById("compressModalBackdrop");
    const compressDropzone    = document.getElementById("compressDropzone");
    const compressFileInput   = document.getElementById("compressFileInput");
    const compressFilePreview = document.getElementById("compressFilePreview");
    const compressFileName    = document.getElementById("compressFileName");
    const compressFileSize    = document.getElementById("compressFileSize");
    const btnCompressGo       = document.getElementById("btnCompressGo");
    const qualityCards        = document.querySelectorAll(".quality-card");
    const qualityRadios       = document.querySelectorAll("input[name='quality']");

    let compressFile = null;
    let selectedQuality = "medium";

    function openCompressModal() {
        compressModal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
    }

    function closeCompressModal() {
        compressModal.classList.add("hidden");
        document.body.style.overflow = "";
        compressFile = null;
        compressFileInput.value = "";
        compressFilePreview.classList.add("hidden");
        btnCompressGo.disabled = true;
    }

    compressModalClose.addEventListener("click", closeCompressModal);
    compressModalBackdrop.addEventListener("click", closeCompressModal);

    // Quality radio selection
    qualityRadios.forEach(radio => {
        radio.addEventListener("change", () => {
            selectedQuality = radio.value;
            qualityCards.forEach(c => c.classList.remove("selected"));
            radio.closest(".quality-option").querySelector(".quality-card").classList.add("selected");
        });
    });

    // Compress dropzone
    compressDropzone.addEventListener("click", () => compressFileInput.click());

    compressFileInput.addEventListener("change", (e) => {
        if (e.target.files[0]) setCompressFile(e.target.files[0]);
    });

    ["dragenter", "dragover"].forEach(evt =>
        compressDropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            compressDropzone.classList.add("drag-over");
        })
    );
    ["dragleave", "drop"].forEach(evt =>
        compressDropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            compressDropzone.classList.remove("drag-over");
        })
    );
    compressDropzone.addEventListener("drop", (e) => {
        const file = e.dataTransfer.files[0];
        if (file) {
            const COMPRESS_ACCEPT = [".docx", ".pptx", ".pdf"];
            const ext = "." + file.name.split(".").pop().toLowerCase();
            if (!COMPRESS_ACCEPT.includes(ext)) {
                alert("Unsupported file type. Please drop a PDF, DOCX, or PPTX file.");
                return;
            }
            setCompressFile(file);
        }
    });

    function setCompressFile(file) {
        compressFile = file;
        compressFileName.textContent = file.name;
        compressFileSize.textContent = formatBytes(file.size);
        compressFilePreview.classList.remove("hidden");
        btnCompressGo.disabled = false;
    }

    btnCompressGo.addEventListener("click", async () => {
        if (!compressFile) return;

        btnCompressGo.disabled = true;
        btnCompressGo.querySelector(".btn-text").textContent = "Compressing…";

        const formData = new FormData();
        formData.append("file", compressFile);
        formData.append("quality", selectedQuality);

        try {
            const response = await fetch("/compress", { method: "POST", body: formData });
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || "Compression failed.");
            }
            const blob = await response.blob();
            const contentDisposition = response.headers.get("Content-Disposition");
            const outputName = extractDownloadName(contentDisposition) || buildCompressedOutputName(compressFile.name);

            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = outputName;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);

            closeCompressModal();
        } catch (err) {
            alert("Compression failed: " + err.message);
        } finally {
            btnCompressGo.disabled = false;
            btnCompressGo.querySelector(".btn-text").textContent = "Compress File";
        }
    });

    dropdownItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const format = item.dataset.format;
            const [from, to] = format.split("-to-");
            currentMode = "convert";

            // Apply source-format filter on the file input
            const accept = SOURCE_FORMAT_ACCEPT[from] || DEFAULT_ACCEPT;
            fileInput.accept = accept;
            pendingSourceFormat = from;

            // Update dropzone hint to reflect the filter
            const formatLabel = from.toUpperCase();
            document.querySelector(".dropzone-formats").textContent =
                `Filtered: ${formatLabel} files only — Max 50 MB`;

            if (selectedFiles.length > 0) {
                // Check if current files match the required source format
                const incompatible = selectedFiles.filter(
                    f => getExtension(f.name) !== from &&
                         !(from === "md" && getExtension(f.name) === "markdown")
                );
                if (incompatible.length === 0) {
                    // Files already compatible — pre-select target format
                    const options = getCommonFormatOptions(selectedFiles);
                    renderFormatOptions(options);
                    const match = options.find(opt => opt.value === to);
                    if (match) {
                        const els = formatOptions.querySelectorAll(".format-option");
                        els.forEach(el => {
                            if (el.querySelector(".format-option-label").textContent === match.label) {
                                selectFormat(el, match.value);
                            }
                        });
                    }
                } else {
                    // Current files are wrong type — reset and prompt for correct ones
                    selectedFiles = [];
                    selectedFormat = null;
                    fileInput.value = "";
                    filePreview.classList.add("hidden");
                    dropzone.style.display = "";
                    formatOptions.innerHTML = "";
                    updateActionButtons();
                    fileInput.click();
                }
            } else {
                fileInput.click();
            }
        });
    });

    function showInfo(title, message) {
        // Reuse error overlay for simple info for now, but with neutral styling if possible
        errorMessage.parentElement.querySelector("h3").textContent = title;
        errorMessage.parentElement.querySelector("h3").style.color = "var(--accent-indigo)";
        errorMessage.textContent = message;
        errorOverlay.classList.remove("hidden");
        // Update retry button text
        btnRetry.querySelector(".btn-text").textContent = "Got it";
    }

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
        if (currentMode === "zip") {
            await startZip();
            return;
        }

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

    async function startZip() {
        if (!selectedFiles.length) {
            return;
        }

        await submitFiles({
            endpoint: "/zip",
            initialText: selectedFiles.length > 1 ? "Uploading files for archive…" : "Uploading file for archive…",
            processingText: selectedFiles.length > 1 ? "Creating ZIP archive…" : "Creating ZIP archive…",
            fallbackName: buildZipOutputName,
            errorMessage: "ZIP creation failed. Please try again.",
        });
    }

    function showError(message) {
        errorOverlay.querySelector("h3").textContent = "Conversion Failed";
        errorOverlay.querySelector("h3").style.color = "var(--accent-red)";
        errorMessage.textContent = message;
        btnRetry.querySelector(".btn-text").textContent = "Try Again";
        errorOverlay.classList.remove("hidden");
    }
})();
