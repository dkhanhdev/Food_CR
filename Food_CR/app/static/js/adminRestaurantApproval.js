// Admin: duyệt nhà hàng
(function () {
    const API_LIST = "/api/admin/restaurants?status=";
    const API_APPROVE = (id) => `/api/admin/restaurants/${id}/approve`;
    const API_REJECT = (id) => `/api/admin/restaurants/${id}/reject`;

    const FILTERS = [
        { key: "approved", label: "Đã duyệt" },
        { key: "pending", label: "Chờ duyệt" },
        { key: "rejected", label: "Từ chối" },
    ];

    const APPROVE_BUTTON_CLASSES = "w-9 h-9 flex items-center justify-center rounded-lg bg-[#dbeafe] text-[#2563eb] hover:bg-[#2563eb] hover:text-white transition-all active:scale-90";
    const APPROVE_MODAL_ACCENT_CLASSES = "rounded-xl bg-[#dbeafe]/80 p-4 border border-[#bfdbfe]";
    const APPROVE_MODAL_CONFIRM_CLASSES = "px-4 py-2 rounded-xl bg-[#2563eb] text-white font-bold hover:bg-[#1d4ed8] transition-colors";

    const tbody = document.getElementById("pending-tbody");
    const paginationEl = document.getElementById("pagination");
    const rangeEl = document.getElementById("pagination-range");
    const totalEl = document.getElementById("pagination-total");
    const filterBar = document.getElementById("approval-filters");

    let currentPage = 1;
    let currentStatus = "pending";

    function formatDate(iso) {
        if (!iso) return "-";
        const d = new Date(iso);
        const pad = (n) => String(n).padStart(2, "0");
        return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }

    function escapeHtml(s) {
        if (s == null) return "";
        return String(s)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function normalizeStatus(status) {
        return String(status || "").trim().toLowerCase();
    }

    function isApproved(status) {
        const value = normalizeStatus(status);
        return value === "đã duyệt" || value === "approved";
    }

    function isRejected(status) {
        const value = normalizeStatus(status);
        return value === "bị từ chối" || value === "rejected";
    }

    function renderStatusBadge(status) {
        const value = normalizeStatus(status);
        if (value === "đã duyệt" || value === "approved") {
            return `
                <span class="px-3 py-1 bg-[#dcfce7] text-[#166534] rounded-full text-caption font-bold flex items-center w-fit gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-[#22c55e]"></span>
                    Đã duyệt
                </span>
            `;
        }
        if (value === "bị từ chối" || value === "rejected") {
            return `
                <span class="px-3 py-1 bg-error-container text-error rounded-full text-caption font-bold flex items-center w-fit gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-error"></span>
                    Từ chối
                </span>
            `;
        }
        return `
            <span class="px-3 py-1 bg-tertiary-fixed text-on-tertiary-fixed-variant rounded-full text-caption font-bold flex items-center w-fit gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
                Chờ duyệt
            </span>
        `;
    }

    function renderRow(r) {
        const owner = r.owner || {};
        const cover = r.cover_image || owner.avatar || "https://via.placeholder.com/40";
        const approved = isApproved(r.approval_status);
        const rejected = isRejected(r.approval_status);
        const approveDisabled = approved;
        const rejectDisabled = rejected;
        const approveBtnClasses = [
            APPROVE_BUTTON_CLASSES,
            approveDisabled ? "opacity-40 cursor-not-allowed pointer-events-none grayscale" : ""
        ].filter(Boolean).join(" ");
        const rejectBtnClasses = [
            "w-9 h-9 flex items-center justify-center rounded-lg bg-error-container text-error hover:bg-error hover:text-white transition-all active:scale-90",
            rejectDisabled ? "opacity-40 cursor-not-allowed pointer-events-none grayscale" : ""
        ].filter(Boolean).join(" ");
        const actionButtons = approved
            ? `
                <button data-action="view" data-id="${r.id}" class="w-9 h-9 flex items-center justify-center rounded-lg bg-surface-container-low text-secondary hover:bg-secondary-container hover:text-on-secondary-container transition-all active:scale-90" title="Xem chi tiết">
                    <span class="material-symbols-outlined text-[20px]">visibility</span>
                </button>
            `
            : `
                <button data-action="view" data-id="${r.id}" class="w-9 h-9 flex items-center justify-center rounded-lg bg-surface-container-low text-secondary hover:bg-secondary-container hover:text-on-secondary-container transition-all active:scale-90" title="Xem chi tiết">
                    <span class="material-symbols-outlined text-[20px]">visibility</span>
                </button>
                <button data-action="approve" data-id="${r.id}" class="${approveBtnClasses}" title="${approveDisabled ? 'Đã duyệt' : 'Duyệt'}" ${approveDisabled ? "disabled aria-disabled=\"true\"" : ""}>
                    <span class="material-symbols-outlined text-[20px]">check</span>
                </button>
                <button data-action="reject" data-id="${r.id}" class="${rejectBtnClasses}" title="${rejectDisabled ? 'Đã từ chối' : 'Từ chối'}" ${rejectDisabled ? "disabled aria-disabled=\"true\"" : ""}>
                    <span class="material-symbols-outlined text-[20px]">close</span>
                </button>
            `;
        return `
        <tr class="hover:bg-surface-container-lowest transition-colors group" data-row-id="${r.id}">
            <td class="px-md py-4">
                <div class="flex items-center gap-sm">
                    <div class="w-10 h-10 rounded-lg overflow-hidden bg-surface-container">
                        <img class="w-full h-full object-cover" src="${escapeHtml(cover)}" alt="${escapeHtml(r.name)}"/>
                    </div>
                    <div>
                        <p class="font-headline-md text-on-surface text-[15px]">${escapeHtml(r.name)}</p>
                        <p class="text-caption text-secondary">${escapeHtml(owner.address || "-")}</p>
                    </div>
                </div>
            </td>
            <td class="px-md py-4 font-body-md text-on-surface">${escapeHtml(owner.name || "-")}</td>
            <td class="px-md py-4 font-body-md text-secondary">${formatDate(r.created_at)}</td>
            <td class="px-md py-4">
                ${renderStatusBadge(r.approval_status)}
            </td>
            <td class="px-md py-4">
                <div class="flex items-center justify-end gap-2">
                    ${actionButtons}
                </div>
            </td>
        </tr>
        `;
    }

    function renderEmpty() {
        return `<tr><td colspan="5" class="px-md py-8 text-center text-secondary">Không có nhà hàng nào.</td></tr>`;
    }

    function setActiveFilter(status) {
        if (!filterBar) return;
        filterBar.querySelectorAll("[data-filter]").forEach((btn) => {
            const active = btn.dataset.filter === status;
            btn.classList.toggle("bg-primary", active);
            btn.classList.toggle("text-white", active);
            btn.classList.toggle("border-primary", active);
            btn.classList.toggle("bg-white", !active);
            btn.classList.toggle("text-secondary", !active);
            btn.classList.toggle("border-outline-variant", !active);
        });
    }

    function initFilters() {
        if (!filterBar) return;
        filterBar.innerHTML = "";
        FILTERS.forEach((filter) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.dataset.filter = filter.key;
            btn.className = "px-4 py-2 rounded-xl border text-sm font-bold transition-colors";
            btn.textContent = filter.label;
            btn.addEventListener("click", () => {
                if (currentStatus === filter.key) return;
                currentStatus = filter.key;
                currentPage = 1;
                setActiveFilter(currentStatus);
                loadPage(1);
            });
            filterBar.appendChild(btn);
        });
        setActiveFilter(currentStatus);
    }

    function renderPagination(data) {
        const { page, pages, total, per_page } = data;
        if (rangeEl) {
            const start = total === 0 ? 0 : (page - 1) * per_page + 1;
            const end = Math.min(page * per_page, total);
            rangeEl.textContent = `${start}-${end}`;
        }
        if (totalEl) totalEl.textContent = total;

        if (!paginationEl) return;
        paginationEl.innerHTML = "";

        const prevDisabled = page <= 1;
        const nextDisabled = page >= pages;

        const prev = document.createElement("button");
        prev.className = "p-2 rounded-lg border border-outline-variant bg-white text-secondary hover:bg-surface-container transition-colors disabled:opacity-50";
        prev.disabled = prevDisabled;
        prev.innerHTML = `<span class="material-symbols-outlined">chevron_left</span>`;
        prev.onclick = () => loadPage(page - 1);
        paginationEl.appendChild(prev);

        const totalPages = Math.max(pages, 1);
        for (let i = 1; i <= totalPages; i++) {
            const btn = document.createElement("button");
            if (i === page) {
                btn.className = "w-8 h-8 rounded-lg bg-primary text-white font-bold text-caption";
            } else {
                btn.className = "w-8 h-8 rounded-lg text-secondary font-bold text-caption hover:bg-surface-container transition-colors";
            }
            btn.textContent = i;
            btn.onclick = () => loadPage(i);
            paginationEl.appendChild(btn);
        }

        const next = document.createElement("button");
        next.className = "p-2 rounded-lg border border-outline-variant bg-white text-secondary hover:bg-surface-container transition-colors disabled:opacity-50";
        next.disabled = nextDisabled;
        next.innerHTML = `<span class="material-symbols-outlined">chevron_right</span>`;
        next.onclick = () => loadPage(page + 1);
        paginationEl.appendChild(next);
    }

    async function loadPage(page) {
        if (page < 1) return;
        currentPage = page;
        try {
            const res = await fetch(`${API_LIST}${encodeURIComponent(currentStatus)}&page=${page}`);
            const data = await res.json();
            if (!tbody) return;

            if (!data.items || data.items.length === 0) {
                if (window.__pendingRestaurants) {
                    window.__pendingRestaurants.clear();
                }
                tbody.innerHTML = renderEmpty();
            } else {
                if (window.__pendingRestaurants) {
                    window.__pendingRestaurants.clear();
                    data.items.forEach((item) => {
                        window.__pendingRestaurants.set(String(item.id), item);
                    });
                }
                tbody.innerHTML = data.items.map(renderRow).join("");
            }
            renderPagination(data);
        } catch (err) {
            console.error("Load pending restaurants failed:", err);
            if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="px-md py-8 text-center text-error">Lỗi tải dữ liệu.</td></tr>`;
        }
    }

    async function patchAction(id, kind, payload = {}) {
        try{
            const url = kind === "approve" ? API_APPROVE(id) : API_REJECT(id);
        const init = { method: "PATCH", headers: { "Content-Type": "application/json" } };
        if (Object.keys(payload).length > 0) {
            init.body = JSON.stringify(payload);
        }
        const res = await fetch(url, init);
         if(res.ok)
            if(kind =="approve")
                showToast("Duyệt nhà hàng thành công", "success")
            else
                showToast("Từ chối nhà hàng thành công", "success")
            return res.json();
        }
        catch(e)
        {
            showToast(e.message,"error")
        }
        
    }

    function getModalRoot() {
        return document.getElementById("modal-root");
    }

    function closeApprovalModal() {
        if (typeof window.closeModal === "function") {
            window.closeModal();
        }
    }

    function renderDetailItem(label, value) {
        return `
            <div class="rounded-xl border border-outline-variant bg-surface-container-lowest p-4">
                <p class="text-caption uppercase tracking-wider text-secondary font-bold">${escapeHtml(label)}</p>
                <p class="text-body-md text-on-surface mt-1">${escapeHtml(value || "-")}</p>
            </div>
        `;
    }

    async function openDetailModal(r) {
        const owner = r.owner || {};
        window.openModal({
            size: "lg",
            icon: "restaurant_menu",
            iconClass: "text-[#2563eb]",
            title: "Chi tiết nhà hàng đăng ký",
            body: `
                <div class="space-y-5 text-on-surface">
                    <div class="rounded-2xl overflow-hidden border border-outline-variant bg-surface-container-lowest">
                        <div class="h-44 bg-surface-container">
                            <img src="${escapeHtml(r.cover_image || owner.avatar || "https://via.placeholder.com/800x400")}" alt="${escapeHtml(r.name)}" class="w-full h-full object-cover">
                        </div>
                        <div class="p-4">
                            <p class="text-caption uppercase tracking-wider text-[#2563eb] font-bold">Nhà hàng</p>
                            <h3 class="font-headline-lg text-headline-lg mt-1">${escapeHtml(r.name)}</h3>
                            <p class="text-body-md text-secondary mt-1">${escapeHtml(r.description || "Chưa có mô tả")}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        ${renderDetailItem("Chủ sở hữu", owner.name)}
                        ${renderDetailItem("Tên đăng nhập", owner.username)}
                        ${renderDetailItem("Email", owner.email)}
                        ${renderDetailItem("Số điện thoại", owner.phonenumber)}
                        ${renderDetailItem("Địa chỉ", owner.address)}
                        ${renderDetailItem("Mã số thuế", r.tax_code)}
                        ${renderDetailItem("Loại ẩm thực", r.cuisine_type)}
                    </div>

                    <div class="grid grid-cols-1 gap-3">
                        ${r.rejection_reason ? renderDetailItem("Lý do từ chối", r.rejection_reason) : ""}
                    </div>
                </div>
            `,
            footer: `
                <button type="button" data-modal-cancel class="px-4 py-2 rounded-xl border border-outline-variant text-secondary font-bold hover:bg-surface-container transition-colors">
                    Đóng
                </button>
            `
        });

        const root = getModalRoot();
        const closeBtn = root?.querySelector("[data-modal-cancel]");
        if (closeBtn) closeBtn.addEventListener("click", closeApprovalModal, { once: true });
    }

    async function openApproveModal(r) {
        if (typeof window.openModal !== "function") {
            if (!confirm(`Xác nhận duyệt nhà hàng #${r.id}?`)) return;
            try {
                const data = await patchAction(r.id, "approve");
                if (data.success) {
                    loadPage(currentPage);
                } else {
                    showToast(data.message || "Thao tác thất bại.", "error");
                }
            } catch (err) {
                console.error(err);
                showToast("Lỗi mạng.", "error");
            }
            return;
        }

        const owner = r.owner || {};
        window.openModal({
            size: "md",
            icon: "check_circle",
            iconClass: "text-[#2563eb]",
            title: "Xác nhận duyệt nhà hàng",
            body: `
                <div class="space-y-4 text-on-surface">
                    <div class="${APPROVE_MODAL_ACCENT_CLASSES}">
                        <p class="text-caption uppercase tracking-wider text-[#2563eb] font-bold">Nhà hàng</p>
                        <p class="font-headline-md text-headline-md">${escapeHtml(r.name)}</p>
                        <p class="text-body-md text-secondary mt-1">${escapeHtml(owner.name || "-")}</p>
                    </div>
                    <p class="text-body-md text-on-surface-variant">
                        Duyệt nhà hàng này sẽ kích hoạt tài khoản chủ nhà hàng
                    </p>
                </div>
            `,
            footer: `
                <button type="button" data-modal-cancel class="px-4 py-2 rounded-xl border border-outline-variant text-secondary font-bold hover:bg-surface-container transition-colors">
                    Hủy
                </button>
                <button type="button" data-modal-confirm class="${APPROVE_MODAL_CONFIRM_CLASSES}">
                    Duyệt nhà hàng
                </button>
            `
        });

        const root = getModalRoot();
        const cancelBtn = root?.querySelector("[data-modal-cancel]");
        const confirmBtn = root?.querySelector("[data-modal-confirm]");
        if (cancelBtn) cancelBtn.addEventListener("click", closeApprovalModal, { once: true });
        if (confirmBtn) {
            confirmBtn.addEventListener("click", async () => {
                if (confirmBtn.disabled) return;
                confirmBtn.disabled = true;
                confirmBtn.classList.add("opacity-50", "cursor-not-allowed");
                confirmBtn.textContent = "Đang xử lý...";
                try {
                    const data = await patchAction(r.id, "approve");
                    if (data.success) {
                        closeApprovalModal();
                        loadPage(currentPage);
                    } else {
                        showToast(data.message || "Thao tác thất bại.", "error");
                        confirmBtn.disabled = false;
                        confirmBtn.classList.remove("opacity-50", "cursor-not-allowed");
                        confirmBtn.textContent = "Duyệt nhà hàng";
                    }
                } catch (err) {
                    console.error(err);
                    showToast("Lỗi mạng.", "error");
                    confirmBtn.disabled = false;
                    confirmBtn.classList.remove("opacity-50", "cursor-not-allowed");
                    confirmBtn.textContent = "Duyệt nhà hàng";
                }
            }, { once: true });
        }
    }

    async function openRejectModal(r) {
        if (typeof window.openModal !== "function") {
            const reason = prompt(`Nhập lý do từ chối nhà hàng #${r.id}:`);
            if (reason === null) return null;
            const cleaned = reason.trim();
            if (!cleaned) return null;
            try {
                const data = await patchAction(r.id, "reject", { reason: cleaned });
                if (data.success) {
                    loadPage(currentPage);
                } else {
                    showToast(data.message || "Thao tác thất bại.", "error");
                }
            } catch (err) {
                console.error(err);
                showToast("Lỗi mạng.", "error");
            }
            return;
        }

        const owner = r.owner || {};
        window.openModal({
            size: "md",
            icon: "cancel",
            title: "Xác nhận từ chối nhà hàng",
            body: `
                <div class="space-y-4 text-on-surface">
                    <div class="rounded-xl bg-error-container/60 p-4 border border-error-container">
                        <p class="text-caption uppercase tracking-wider text-error font-bold">Nhà hàng</p>
                        <p class="font-headline-md text-headline-md">${escapeHtml(r.name)}</p>
                        <p class="text-body-md text-secondary mt-1">${escapeHtml(owner.name || "-")}</p>
                    </div>
                    <p class="text-body-md text-on-surface-variant">
                        Từ chối sẽ khóa tài khoản nhà hàng và lưu lý do để đối tác có thể kiểm tra lại sau.
                    </p>
                    <div class="space-y-2">
                        <label for="reject-reason" class="font-label-md text-label-md font-bold text-on-surface">
                            Lý do từ chối
                        </label>
                        <textarea
                            id="reject-reason"
                            rows="4"
                            class="w-full rounded-xl border border-outline-variant bg-surface-container-lowest px-4 py-3 text-body-md outline-none focus:border-primary"
                            placeholder="Ví dụ: Thiếu giấy phép kinh doanh, ảnh bìa chưa đúng chuẩn..."
                        ></textarea>
                        <p id="reject-reason-error" class="text-error text-caption hidden">Vui lòng nhập lý do từ chối.</p>
                    </div>
                </div>
            `,
            footer: `
                <button type="button" data-modal-cancel class="px-4 py-2 rounded-xl border border-outline-variant text-secondary font-bold hover:bg-surface-container transition-colors">
                    Hủy
                </button>
                <button type="button" data-modal-confirm class="px-4 py-2 rounded-xl bg-error text-white font-bold hover:bg-red-700 transition-colors">
                    Từ chối nhà hàng
                </button>
            `
        });

        const root = getModalRoot();
        const cancelBtn = root?.querySelector("[data-modal-cancel]");
        const confirmBtn = root?.querySelector("[data-modal-confirm]");
        const reasonEl = root?.querySelector("#reject-reason");
        const errorEl = root?.querySelector("#reject-reason-error");

        if (cancelBtn) cancelBtn.addEventListener("click", closeApprovalModal, { once: true });
        if (reasonEl) {
            reasonEl.addEventListener("input", () => {
                if (!errorEl) return;
                errorEl.classList.add("hidden");
            }, { once: true });
        }
        if (confirmBtn) {
            confirmBtn.addEventListener("click", async () => {
                const reason = (reasonEl?.value || "").trim();
                if (!reason) {
                    if (errorEl) errorEl.classList.remove("hidden");
                    reasonEl?.focus();
                    return;
                }

                if (confirmBtn.disabled) return;
                confirmBtn.disabled = true;
                confirmBtn.classList.add("opacity-50", "cursor-not-allowed");
                confirmBtn.textContent = "Đang xử lý...";
                try {
                    const data = await patchAction(r.id, "reject", { reason });
                    if (data.success) {
                        closeApprovalModal();
                        loadPage(currentPage);
                    } else {
                        showToast(data.message || "Thao tác thất bại.", "error");
                        confirmBtn.disabled = false;
                        confirmBtn.classList.remove("opacity-50", "cursor-not-allowed");
                        confirmBtn.textContent = "Từ chối nhà hàng";
                    }
                } catch (err) {
                    console.error(err);
                    showToast("Lỗi mạng.", "error");
                    confirmBtn.disabled = false;
                    confirmBtn.classList.remove("opacity-50", "cursor-not-allowed");
                    confirmBtn.textContent = "Từ chối nhà hàng";
                }
            });
        }
    }

    document.addEventListener("click", async (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        const id = btn.dataset.id;
        const action = btn.dataset.action;
        const rowData = window.__pendingRestaurants?.get?.(String(id));
        if (!rowData) return;

        if (btn.disabled || btn.getAttribute("aria-disabled") === "true") {
            return;
        }

        if (action === "view") {
            await openDetailModal(rowData);
            return;
        }

        if (action === "approve") {
            await openApproveModal(rowData);
            return;
        }

        if (action === "reject") {
            await openRejectModal(rowData);
        }
    });

    document.addEventListener("DOMContentLoaded", () => {
        window.__pendingRestaurants = new Map();
        initFilters();
        loadPage(1);
    });
})();
