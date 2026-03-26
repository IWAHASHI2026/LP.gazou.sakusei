// ===== ドラッグ&ドロップ + プレビュー =====
document.addEventListener("DOMContentLoaded", () => {
    setupDropZone("product-zone", "product-input", "product-preview", "product-placeholder");
    setupDropZone("background-zone", "background-input", "background-preview", "background-placeholder");
    setupAspectRatio();
    setupCountSlider();
    setupForm();
    setupModal();
});

function setupDropZone(zoneId, inputId, previewId, placeholderId) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const placeholder = document.getElementById(placeholderId);

    if (!zone || !input) return;

    ["dragenter", "dragover"].forEach(evt => {
        zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.add("dragover"); });
    });
    ["dragleave", "drop"].forEach(evt => {
        zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.remove("dragover"); });
    });

    zone.addEventListener("drop", e => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            showPreview(files[0], preview, placeholder);
        }
    });

    input.addEventListener("change", () => {
        if (input.files.length > 0) {
            showPreview(input.files[0], preview, placeholder);
        }
    });
}

function showPreview(file, previewEl, placeholderEl) {
    const reader = new FileReader();
    reader.onload = e => {
        previewEl.src = e.target.result;
        previewEl.style.display = "block";
        placeholderEl.style.display = "none";
    };
    reader.readAsDataURL(file);
}

// ===== アスペクト比カスタム表示切替 =====
function setupAspectRatio() {
    const select = document.getElementById("aspect-ratio");
    const custom = document.getElementById("custom-ratio");
    if (!select || !custom) return;

    select.addEventListener("change", () => {
        custom.style.display = select.value === "custom" ? "block" : "none";
    });
}

// ===== スライダーのラベル更新 =====
function setupCountSlider() {
    const slider = document.getElementById("count");
    const label = document.getElementById("count-label");
    if (!slider || !label) return;

    slider.addEventListener("input", () => { label.textContent = slider.value; });
}

// ===== フォーム送信 & 複数バッチ管理 =====
let batchCounter = 0;

function setupForm() {
    const form = document.getElementById("generate-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const btn = document.getElementById("generate-btn");
        const formData = new FormData(form);

        // 保存済み画像で再生成する場合、空のファイルinputを送らない
        const productInput = document.getElementById("product-input");
        const backgroundInput = document.getElementById("background-input");
        if (!productInput.files.length) {
            formData.delete("product_image");
        }
        if (!backgroundInput.files.length) {
            formData.delete("background_image");
        }

        // ボタンを一時的に無効化（連打防止）
        btn.disabled = true;
        btn.textContent = "生成中...（数秒かかります）";

        try {
            const res = await fetch("/generate", { method: "POST", body: formData });

            // レスポンスがJSONでない場合のハンドリング
            const contentType = res.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) {
                const text = await res.text();
                showError("サーバーエラー: " + (text.substring(0, 200) || `HTTP ${res.status}`));
                btn.disabled = false;
                btn.textContent = "画像を生成";
                return;
            }

            const data = await res.json();

            if (!res.ok) {
                showError(data.error || "エラーが発生しました。");
                btn.disabled = false;
                btn.textContent = "画像を生成";
                return;
            }

            // session_idを更新（初回生成時にサーバーが発行）
            if (data.session_id) {
                document.getElementById("session-id").value = data.session_id;
            }

            // バッチをリストに追加してポーリング開始
            batchCounter++;
            addBatchItem(data.batch_id, data.session_id, batchCounter);
            pollBatch(data.batch_id, batchCounter);

            btn.disabled = false;
            btn.textContent = "画像を生成";

        } catch (err) {
            showError("通信エラーが発生しました: " + err.message);
            btn.disabled = false;
            btn.textContent = "画像を生成";
        }
    });
}

function addBatchItem(batchId, sessionId, num) {
    const listSection = document.getElementById("batch-list");
    const container = document.getElementById("batch-items");
    listSection.style.display = "block";

    const item = document.createElement("div");
    item.className = "batch-item";
    item.id = `batch-${batchId}`;
    item.innerHTML = `
        <div class="batch-info">
            <span class="batch-label">バッチ ${num}</span>
            <span class="batch-status" id="batch-status-${batchId}">
                <span class="spinner-small"></span> 生成開始中...
            </span>
        </div>
        <div class="batch-action" id="batch-action-${batchId}"></div>
    `;
    container.prepend(item);
}

async function pollBatch(batchId, num) {
    const statusEl = document.getElementById(`batch-status-${batchId}`);
    const actionEl = document.getElementById(`batch-action-${batchId}`);
    const sessionId = document.getElementById("session-id").value;

    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/status/${batchId}`);
            const data = await res.json();

            if (data.done && data.error) {
                clearInterval(interval);
                statusEl.innerHTML = `<span class="batch-error">エラー</span>`;
                actionEl.textContent = data.error;
                return;
            }

            statusEl.innerHTML = `<span class="spinner-small"></span> 生成中... (${data.completed}/${data.total})`;

            if (data.done) {
                clearInterval(interval);
                statusEl.innerHTML = `<span class="batch-complete">完了</span>`;
                const previewUrl = `/preview/${batchId}?session_id=${sessionId}`;
                actionEl.innerHTML = `<a href="${previewUrl}" target="_blank" class="btn-small">プレビュー</a>`;
            }
        } catch {
            // ネットワークエラーは無視して再試行
        }
    }, 1500);
}

function showError(message) {
    const toast = document.getElementById("error-toast");
    if (!toast) return;
    toast.textContent = message;
    toast.style.display = "block";
    setTimeout(() => { toast.style.display = "none"; }, 5000);
}

// ===== プレビューページのモーダル =====
function setupModal() {
    const cards = document.querySelectorAll(".image-card a:not(.btn-download)");
    const modal = document.getElementById("modal");
    const modalImg = document.getElementById("modal-img");

    if (!modal || !modalImg) return;

    cards.forEach(card => {
        card.addEventListener("click", e => {
            e.preventDefault();
            modalImg.src = card.href;
            modal.style.display = "flex";
        });
    });
}
