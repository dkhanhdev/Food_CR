(function () {
    const API_URL = "/api/promotions";
    const DISHES_API_URL = `${API_URL}/dishes`;

    const state = {
        vouchers: [],
        filtered: [],
        dishes: [],
    };

    const els = {
        loading: document.getElementById("voucher-loading"),
        error: document.getElementById("voucher-error"),
        empty: document.getElementById("voucher-empty"),
        list: document.getElementById("voucher-list"),
        search: document.getElementById("voucher-search-input"),
        total: document.getElementById("voucher-stat-total"),
        active: document.getElementById("voucher-stat-active"),
        expiring: document.getElementById("voucher-stat-expiring"),
        refreshBtn: document.getElementById("refresh-vouchers-btn"),
        openCreateBtn: document.getElementById("open-create-modal-btn"),
        modal: document.getElementById("voucher-modal"),
        backdrop: document.getElementById("voucher-modal-backdrop"),
        closeModalBtn: document.getElementById("close-voucher-modal-btn"),
        cancelBtn: document.getElementById("cancel-voucher-btn"),
        modalTitle: document.getElementById("voucher-modal-title"),
        form: document.getElementById("voucher-form"),
        submitBtn: document.getElementById("voucher-submit-btn"),
        formError: document.getElementById("voucher-form-error"),
        id: document.getElementById("voucher-id"),
        name: document.getElementById("voucher-name"),
        code: document.getElementById("voucher-code"),
        discountValue: document.getElementById("voucher-discount-value"),
        maxDiscount: document.getElementById("voucher-max-discount"),
        usageLimit: document.getElementById("voucher-usage-limit"),
        startDate: document.getElementById("voucher-start-date"),
        endDate: document.getElementById("voucher-end-date"),
        dishLoading: document.getElementById("voucher-dish-loading"),
        dishList: document.getElementById("voucher-dish-list"),
        dishEmpty: document.getElementById("voucher-dish-empty"),
        dishSection: document.getElementById("voucher-dish-section"),
        selectedDishesCount: document.getElementById("voucher-selected-dishes-count"),
        scopeDish: document.getElementById("voucher-scope-dish"),
        scopeOrder: document.getElementById("voucher-scope-order"),
    };

    function getSelectedScope() {
        return els.scopeOrder.checked ? "ORDER" : "DISH";
    }

    function setScope(scope) {
        els.scopeDish.checked = scope !== "ORDER";
        els.scopeOrder.checked = scope === "ORDER";
        els.dishSection.classList.toggle("hidden", scope === "ORDER");
    }

    function escapeHtml(value) {
        if (value === null || value === undefined) return "";
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatCurrency(value) {
        if (value === null || value === undefined || value === "") return "-";
        return new Intl.NumberFormat("vi-VN").format(Number(value)) + " đ";
    }

    function formatDateTime(value) {
        if (!value) return "-";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return "-";

        const pad = (number) => String(number).padStart(2, "0");
        return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
    }

    function toDatetimeLocalValue(value) {
        if (!value) return "";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return "";
        const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
        return local.toISOString().slice(0, 16);
    }

    function showLoading(isLoading) {
        els.loading.classList.toggle("hidden", !isLoading);
    }

    function showError(message) {
        els.error.textContent = message || "";
        els.error.classList.toggle("hidden", !message);
    }

    function showEmpty(isEmpty) {
        els.empty.classList.toggle("hidden", !isEmpty);
    }

    function clearFormErrors() {
        els.formError.textContent = "";
        els.formError.classList.add("hidden");

        document.querySelectorAll("[data-error-for]").forEach((node) => {
            node.textContent = "";
            node.classList.add("hidden");
        });
    }

    function setFormError(message) {
        els.formError.textContent = message;
        els.formError.classList.remove("hidden");
    }

    function getApiErrorMessage(data, fallbackMessage) {
        const messages = [];
        if (data?.message) messages.push(data.message);

        const dishErrors = data?.errors?.dish_ids;
        if (Array.isArray(dishErrors)) {
            dishErrors.forEach((error) => {
                const details = [error.dish_name, error.voucher_code]
                    .filter(Boolean)
                    .join(" - ");
                messages.push(details ? `${error.dish_id}: ${details}` : String(error));
            });
        } else if (dishErrors) {
            messages.push(String(dishErrors));
        }

        return messages.join("\n") || fallbackMessage;
    }

    function setFieldError(fieldId, message) {
        const node = document.querySelector(`[data-error-for="${fieldId}"]`);
        if (!node) return;
        node.textContent = message;
        node.classList.remove("hidden");
    }

    function getSelectedDishIds() {
        return Array.from(els.dishList.querySelectorAll("input[name='dish_ids']:checked"))
            .map((input) => Number(input.value));
    }

    function getDishVoucher(dishId, editingVoucherId = null) {
        return state.vouchers.find((voucher) => {
            return voucher.id !== editingVoucherId
                && voucher.is_valid
                && Array.isArray(voucher.dish_ids)
                && voucher.dish_ids.includes(dishId);
        });
    }

    function updateSelectedDishesCount() {
        const count = getSelectedDishIds().length;
        els.selectedDishesCount.textContent = `${count} món đã chọn`;
    }

    function renderDishList(selectedDishIds = []) {
        const selectedIds = new Set(selectedDishIds.map(Number));
        const editingVoucherId = els.id.value ? Number(els.id.value) : null;

        els.dishList.innerHTML = state.dishes.map((dish) => {
            const currentVoucher = getDishVoucher(dish.id, editingVoucherId);
            const statusLabel = dish.active === false ? "Ngừng bán" : "Đang bán";
            const statusClass = dish.active === false
                ? "text-error bg-error-container"
                : "text-green-700 bg-green-100";
            const voucherLabel = currentVoucher
                ? `Đang dùng: ${escapeHtml(currentVoucher.code)}`
                : "Chưa gán voucher";

            return `
                <label class="flex cursor-pointer items-start gap-3 rounded-lg border border-outline-variant/60 p-3 transition-colors hover:bg-surface-container-low">
                    <input type="checkbox" name="dish_ids" value="${dish.id}"
                        class="mt-1 h-4 w-4 accent-primary"
                        ${selectedIds.has(dish.id) ? "checked" : ""}>
                    <span class="min-w-0 flex-1">
                        <span class="flex flex-wrap items-center justify-between gap-2">
                            <span class="truncate text-body-md font-bold text-on-surface">${escapeHtml(dish.name)}</span>
                            <span class="whitespace-nowrap text-label-md font-bold text-primary">${escapeHtml(formatCurrency(dish.price))}</span>
                        </span>
                        <span class="mt-1 flex flex-wrap items-center gap-2 text-caption text-secondary">
                            <span class="rounded-full px-2 py-1 ${statusClass}">${statusLabel}</span>
                            <span>${escapeHtml(voucherLabel)}</span>
                        </span>
                    </span>
                </label>
            `;
        }).join("");

        els.dishList.querySelectorAll("input[name='dish_ids']").forEach((input) => {
            input.addEventListener("change", updateSelectedDishesCount);
        });

        els.dishList.classList.toggle("hidden", !state.dishes.length);
        els.dishEmpty.classList.toggle("hidden", Boolean(state.dishes.length));
        updateSelectedDishesCount();
    }

    async function loadDishes() {
        els.dishLoading.classList.remove("hidden");
        els.dishList.classList.add("hidden");
        els.dishEmpty.classList.add("hidden");

        try {
            const res = await fetch(DISHES_API_URL);
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.message || "Tải danh sách món thất bại");
            }

            state.dishes = data.items || [];
            renderDishList();
        } catch (err) {
            state.dishes = [];
            els.dishList.innerHTML = "";
            els.dishEmpty.textContent = err.message || "Không thể tải danh sách món.";
            els.dishEmpty.classList.remove("hidden");
        } finally {
            els.dishLoading.classList.add("hidden");
        }
    }

    function getVoucherStatus(voucher) {
        const now = new Date();
        const start = voucher.start_date ? new Date(voucher.start_date) : null;
        const end = voucher.end_date ? new Date(voucher.end_date) : null;

        if (start && now < start) return "Sắp áp dụng";
        if (end && now > end) return "Hết hạn";
        if (end) {
            const diffDays = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
            if (diffDays <= 3) return "Sắp hết hạn";
        }
        return "Đang hoạt động";
    }

    function getStatusBadgeClass(label) {
        if (label === "Đang hoạt động") return "bg-green-500/10 text-green-600";
        if (label === "Sắp hết hạn") return "bg-tertiary-fixed text-on-tertiary-fixed-variant";
        if (label === "Sắp áp dụng") return "bg-primary-fixed text-on-primary-fixed-variant";
        return "bg-secondary-container text-on-secondary-container";
    }

    function renderStats(allItems) {
        const now = new Date();
        const activeCount = allItems.filter((voucher) => {
            const start = voucher.start_date ? new Date(voucher.start_date) : null;
            const end = voucher.end_date ? new Date(voucher.end_date) : null;
            return (!start || now >= start) && (!end || now <= end);
        }).length;

        const expiringSoonCount = allItems.filter((voucher) => {
            if (!voucher.end_date) return false;
            const end = new Date(voucher.end_date);
            const diffDays = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
            return diffDays >= 0 && diffDays <= 3;
        }).length;

        els.total.textContent = allItems.length;
        els.active.textContent = activeCount;
        els.expiring.textContent = expiringSoonCount;
    }

    function renderRows(items) {
        renderStats(state.vouchers);

        if (!items.length) {
            els.list.innerHTML = "";
            showEmpty(true);
            return;
        }

        showEmpty(false);
        els.list.innerHTML = items.map((voucher) => {
            const statusLabel = getVoucherStatus(voucher);
            const discountLabel = `${voucher.discount_value}%`;
            const maxDiscountLabel = voucher.max_discount ? formatCurrency(voucher.max_discount) : "Không giới hạn";

            return `
                <article class="rounded-2xl border border-outline-variant bg-surface-bright p-5 shadow-sm">
                    <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                        <div class="space-y-3 flex-1">
                            <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                                <div>
                                    <div class="flex flex-wrap items-center gap-3">
                                        <h4 class="font-headline-md text-headline-md text-on-surface">${escapeHtml(voucher.name)}</h4>
                                        <span class="px-3 py-1 rounded-full text-caption font-bold ${getStatusBadgeClass(statusLabel)}">${escapeHtml(statusLabel)}</span>
                                        <span class="px-3 py-1 rounded-full text-caption font-bold bg-secondary-container text-on-secondary-container">${voucher.scope === "ORDER" ? "Cả đơn hàng" : "Theo món"}</span>
                                    </div>
                                    <p class="text-label-md text-primary font-bold mt-1">${escapeHtml(voucher.code)}</p>
                                </div>
                                <div class="flex items-center gap-2">
                                    <button type="button" data-action="edit" data-id="${voucher.id}" class="px-3 py-2 rounded-lg bg-surface-container-low text-secondary hover:bg-surface-container transition-colors font-bold">Sửa</button>
                                    <button type="button" data-action="delete" data-id="${voucher.id}" class="px-3 py-2 rounded-lg bg-error-container text-error hover:bg-error hover:text-white transition-colors font-bold">Xóa</button>
                                </div>
                            </div>

                            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                                <div class="rounded-xl bg-surface-container-lowest p-4">
                                    <p class="text-caption text-secondary uppercase tracking-wide">Giảm giá</p>
                                    <p class="text-body-md font-bold text-on-surface mt-2">${escapeHtml(discountLabel)}</p>
                                </div>
                                <div class="rounded-xl bg-surface-container-lowest p-4">
                                    <p class="text-caption text-secondary uppercase tracking-wide">Giảm tối đa</p>
                                    <p class="text-body-md font-bold text-on-surface mt-2">${escapeHtml(maxDiscountLabel)}</p>
                                </div>
                                <div class="rounded-xl bg-surface-container-lowest p-4">
                                    <p class="text-caption text-secondary uppercase tracking-wide">Lượt dùng</p>
                                    <p class="text-body-md font-bold text-on-surface mt-2">${voucher.used_count}/${voucher.usage_limit}</p>
                                </div>
                            </div>
                        </div>

                        <div class="xl:w-72 rounded-2xl bg-surface-container-lowest p-4">
                            <p class="text-caption text-secondary uppercase tracking-wide">Thời gian áp dụng</p>
                            <p class="text-body-md font-bold text-on-surface mt-2">${escapeHtml(formatDateTime(voucher.start_date))}</p>
                            <p class="text-body-md text-secondary mt-1">đến ${escapeHtml(formatDateTime(voucher.end_date))}</p>
                        </div>
                    </div>
                </article>
            `;
        }).join("");
    }

    function applyFilter() {
        const keyword = (els.search?.value || "").trim().toLowerCase();
        state.filtered = !keyword
            ? [...state.vouchers]
            : state.vouchers.filter((voucher) => {
                return [voucher.code, voucher.name]
                    .filter(Boolean)
                    .some((value) => String(value).toLowerCase().includes(keyword));
            });

        els.empty.textContent = keyword
            ? "Không tìm thấy voucher phù hợp."
            : "Chưa có voucher nào. Hãy tạo voucher đầu tiên.";
        renderRows(state.filtered);
    }

    async function loadVouchers() {
        showLoading(true);
        showError("");

        try {
            const res = await fetch(API_URL);
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.message || "Tải danh sách voucher thất bại");
            }

            state.vouchers = data.items || [];
            applyFilter();
            renderDishList(getSelectedDishIds());
        } catch (err) {
            state.vouchers = [];
            renderRows([]);
            showError(err.message || "Lỗi kết nối máy chủ");
        } finally {
            showLoading(false);
        }
    }

    function openModal() {
        els.modal.classList.remove("hidden");
        document.body.classList.add("overflow-hidden");
    }

    function closeModal() {
        els.modal.classList.add("hidden");
        document.body.classList.remove("overflow-hidden");
        els.form.reset();
        els.id.value = "";
        clearFormErrors();
        setScope("DISH");
        renderDishList();
    }

    function openCreateModal() {
        clearFormErrors();
        els.form.reset();
        els.id.value = "";
        els.modalTitle.textContent = "Tạo voucher";
        els.submitBtn.textContent = "Tạo voucher";
        setScope("DISH");
        renderDishList();
        openModal();
    }

    function openEditModal(voucher) {
        clearFormErrors();
        els.form.reset();
        els.id.value = voucher.id;
        els.modalTitle.textContent = "Cập nhật voucher";
        els.submitBtn.textContent = "Lưu thay đổi";
        els.name.value = voucher.name || "";
        els.code.value = voucher.code || "";
        els.discountValue.value = voucher.discount_value ?? "";
        els.maxDiscount.value = voucher.max_discount ?? "";
        els.usageLimit.value = voucher.usage_limit ?? 1;
        els.startDate.value = toDatetimeLocalValue(voucher.start_date);
        els.endDate.value = toDatetimeLocalValue(voucher.end_date);
        setScope(voucher.scope || (voucher.dish_ids?.length ? "DISH" : "ORDER"));
        renderDishList(voucher.dish_ids || []);
        openModal();
    }

    function collectPayload() {
        const scope = getSelectedScope();
        return {
            name: els.name.value.trim(),
            code: els.code.value.trim(),
            discount_type: "PERCENTAGE",
            discount_value: Number(els.discountValue.value),
            minimum_order: 0,
            max_discount: els.maxDiscount.value ? Number(els.maxDiscount.value) : null,
            usage_limit: Number(els.usageLimit.value || 0),
            start_date: els.startDate.value ? new Date(els.startDate.value).toISOString() : "",
            end_date: els.endDate.value ? new Date(els.endDate.value).toISOString() : "",
            dish_ids: scope === "ORDER" ? [] : getSelectedDishIds(),
        };
    }

    function validateForm(payload) {
        clearFormErrors();
        let valid = true;

        if (!payload.name) {
            setFieldError("voucher-name", "Tên voucher không được để trống");
            valid = false;
        }
        if (!payload.code) {
            setFieldError("voucher-code", "Mã voucher không được để trống");
            valid = false;
        }
        if (!(payload.discount_value > 0)) {
            setFieldError("voucher-discount-value", "Phần trăm giảm phải lớn hơn 0");
            valid = false;
        }
        if (!(payload.usage_limit >= 1)) {
            setFieldError("voucher-usage-limit", "Giới hạn lượt dùng phải lớn hơn hoặc bằng 1");
            valid = false;
        }
        if (getSelectedScope() === "DISH" && !payload.dish_ids.length) {
            setFieldError("voucher-dish-list", "Voucher phải áp dụng ít nhất một món");
            valid = false;
        }
        if (!payload.start_date) {
            setFieldError("voucher-start-date", "Ngày bắt đầu là bắt buộc");
            valid = false;
        }
        if (!payload.end_date) {
            setFieldError("voucher-end-date", "Ngày kết thúc là bắt buộc");
            valid = false;
        }

        const startDate = payload.start_date ? new Date(payload.start_date) : null;
        const endDate = payload.end_date ? new Date(payload.end_date) : null;
        if (startDate && endDate && startDate >= endDate) {
            setFieldError("voucher-end-date", "Ngày kết thúc phải lớn hơn ngày bắt đầu");
            valid = false;
        }

        if (payload.discount_value > 100) {
            setFieldError("voucher-discount-value", "Phần trăm giảm không được vượt quá 100");
            valid = false;
        }

        return valid;
    }

    async function submitForm(event) {
        event.preventDefault();

        const voucherId = els.id.value.trim();
        const payload = collectPayload();
        if (!validateForm(payload)) {
            setFormError("Vui lòng kiểm tra lại các trường dữ liệu.");
            return;
        }

        const originalText = els.submitBtn.textContent;
        els.submitBtn.disabled = true;
        els.submitBtn.textContent = "Đang lưu...";

        try {
            const res = await fetch(voucherId ? `${API_URL}/${voucherId}` : API_URL, {
                method: voucherId ? "PUT" : "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(getApiErrorMessage(data, "Lưu voucher thất bại"));
            }
            showToast("Tạo voucher thành công", "success");
            closeModal();
            await loadVouchers();
        } catch (err) {
            showToast("Lỗi không xác định", "error");
        } finally {
            els.submitBtn.disabled = false;
            els.submitBtn.textContent = originalText;
        }
    }

    async function deleteVoucher(voucherId) {
        if (!confirm("Xác nhận xóa voucher này?")) return;

        try {
            const res = await fetch(`${API_URL}/${voucherId}`, {
                method: "DELETE",
            });
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.message);
            }

            await loadVouchers();
        } catch (err) {
            showToast(err.message, "error");
        }
    }

    document.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) return;

        const action = button.dataset.action;
        const voucherId = Number(button.dataset.id);
        const voucher = state.vouchers.find((item) => item.id === voucherId);

        if (action === "edit" && voucher) {
            openEditModal(voucher);
        }

        if (action === "delete") {
            deleteVoucher(voucherId);
        }
    });

    els.scopeDish?.addEventListener("change", () => setScope(getSelectedScope()));
    els.scopeOrder?.addEventListener("change", () => setScope(getSelectedScope()));
    els.openCreateBtn?.addEventListener("click", openCreateModal);
    els.refreshBtn?.addEventListener("click", loadVouchers);
    els.closeModalBtn?.addEventListener("click", closeModal);
    els.cancelBtn?.addEventListener("click", closeModal);
    els.backdrop?.addEventListener("click", closeModal);
    els.form?.addEventListener("submit", submitForm);
    els.search?.addEventListener("input", applyFilter);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !els.modal.classList.contains("hidden")) {
            closeModal();
        }
    });

    loadVouchers();
    loadDishes();
})();
