(function () {
    const API_ORDERS = "/api/orders_customer/";

    const STATUS_META = {
        "Pending Payment": { label: "Chờ thanh toán", badge: "bg-amber-50 text-amber-700" },
        "Payment Failed": { label: "Thanh toán thất bại", badge: "bg-red-50 text-red-700" },
        "Paid": { label: "Đã thanh toán", badge: "bg-emerald-50 text-emerald-700" },
        "Confirmed": { label: "Đã xác nhận", badge: "bg-blue-50 text-blue-700" },
        "Preparing": { label: "Đang chuẩn bị", badge: "bg-amber-50 text-amber-700" },
        "Delivering": { label: "Đang giao", badge: "bg-blue-50 text-blue-700" },
        "Completed": { label: "Hoàn tất", badge: "bg-emerald-50 text-emerald-700" },
        "Cancelled": { label: "Đã huỷ", badge: "bg-red-50 text-red-700" }
    };

    const FILTER_STATUS_MAP = {
        "pending_payment": "PENDING_PAYMENT",
        "payment_failed": "PAYMENT_FAILED",
        "paid": "PAID",
        "confirmed": "CONFIRMED",
        "preparing": "PREPARING",
        "delivering": "DELIVERING",
        "completed": "COMPLETED",
        "cancelled": "CANCELLED"
    };

    const ACTIVE_BTN_CLASSES = "bg-primary text-on-primary shadow-sm";
    const INACTIVE_BTN_CLASSES = "bg-white text-secondary border border-outline-variant hover:border-primary hover:text-primary";

    const MAX_ITEMS_SHOWN = 3;

    let currentFilter = "all";
    let searchKeyword = "";
    let debounceTimer = null;

    function money(n) {
        return Math.round(n).toLocaleString("vi-VN") + " đ";
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

    function renderOrders(orders) {
        const list = document.getElementById("order-list");
        const template = document.getElementById("order-card-template");
        const itemRowTemplate = document.getElementById("order-item-row-template");
        if (!list || !template) return;

        list.innerHTML = "";

        if (!orders || orders.length === 0) {
            list.innerHTML = '<p class="col-span-full text-center text-secondary py-8">Không có đơn hàng nào.</p>';
            return;
        }

        orders.forEach(function (o) {
            var meta = STATUS_META[o.status] || { label: o.status, badge: "bg-gray-100 text-gray-700" };
            var node = template.content.cloneNode(true);

            var card = node.querySelector(".order-card");
            card.addEventListener("click", function () {
                window.location.href = "/order_customer/" + o.id;
            });

            node.querySelector(".restaurant-img").src = o.restaurant ? o.restaurant.cover_image || "" : "";
            node.querySelector(".restaurant-img").alt = o.restaurant ? o.restaurant.name || "" : "";
            node.querySelector(".restaurant-name").textContent = o.restaurant ? o.restaurant.name || "" : "";
            node.querySelector(".order-code").textContent = "#" + String(o.id).padStart(5, "0");

            var badge = node.querySelector(".status-badge");
            badge.textContent = meta.label;
            badge.className = "status-badge text-xs font-medium px-2.5 py-1 rounded-md whitespace-nowrap " + meta.badge;

            if (o.items && o.items.length > 0) {
                var itemsWrap = node.querySelector(".order-items");
                var itemsToShow = o.items.slice(0, MAX_ITEMS_SHOWN);

                itemsToShow.forEach(function (item) {
                    var itemNode = itemRowTemplate.content.cloneNode(true);
                    var img = itemNode.querySelector(".item-img");
                    if (item.dish_image) {
                        img.src = item.dish_image;
                        img.alt = item.dish_name || "";
                    } else {
                        img.remove();
                    }
                    itemNode.querySelector(".item-name").textContent = item.dish_name || "";
                    itemNode.querySelector(".item-qty").textContent = "x" + item.quantity;
                    itemsWrap.appendChild(itemNode);
                });

                var remaining = o.items.length - itemsToShow.length;
                if (remaining > 0) {
                    var moreEl = document.createElement("p");
                    moreEl.className = "text-xs text-gray-400 pl-9";
                    moreEl.textContent = "+" + remaining + " món khác";
                    itemsWrap.appendChild(moreEl);
                }
            }

            if (o.note) {
                var noteEl = node.querySelector(".order-note");
                noteEl.classList.remove("hidden");
                noteEl.querySelector(".order-note-text").textContent = o.note;
            }

            if (o.rejection_reason) {
                var rejEl = node.querySelector(".order-rejection");
                rejEl.classList.remove("hidden");
                rejEl.querySelector(".order-rejection-text").textContent = o.rejection_reason;
            }

            node.querySelector(".shipping-fee").textContent = money(o.shipping_fee);
            node.querySelector(".total-amount").textContent = money(o.total_amount);

            list.appendChild(node);
        });
    }

    function buildUrl() {
        var url = new URL(API_ORDERS, window.location.origin);
        if (currentFilter !== "all") {
            var statusParam = FILTER_STATUS_MAP[currentFilter];
            if (statusParam) {
                url.searchParams.set("status", statusParam);
            }
        }
        if (searchKeyword) {
            url.searchParams.set("keyword", searchKeyword);
        }
        return url.toString();
    }

    async function loadOrders() {
        try {
            await loadingState.run(async function () {
                var res = await fetch(buildUrl());
                if (!res.ok) throw new Error("Failed to load orders: " + res.status);

                var json = await res.json();
                if (!json.success || !json.data) {
                    throw new Error(json.message || "Failed to load orders");
                }

                renderOrders(json.data);
            });
        } catch (e) {
            console.error("Failed to load orders:", e);
        }
    }

    function setActiveButton(filter) {
        currentFilter = filter;
        var tabs = document.querySelectorAll("#order-filter-tabs button");
        tabs.forEach(function (btn) {
            if (btn.dataset.filter === filter) {
                btn.classList.add(...ACTIVE_BTN_CLASSES.split(" "));
                btn.classList.remove(...INACTIVE_BTN_CLASSES.split(" "));
            } else {
                btn.classList.remove(...ACTIVE_BTN_CLASSES.split(" "));
                btn.classList.add(...INACTIVE_BTN_CLASSES.split(" "));
            }
        });
    }

    function initFilterButtons() {
        var tabs = document.querySelectorAll("#order-filter-tabs button");
        tabs.forEach(function (btn) {
            btn.addEventListener("click", function () {
                setActiveButton(btn.dataset.filter);
                loadOrders();
            });
        });
    }

    function initSearch() {
        var searchInput = document.getElementById("order-search-input");
        if (!searchInput) return;

        searchInput.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                searchKeyword = searchInput.value.trim();
                loadOrders();
            }, 350);
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        initFilterButtons();
        initSearch();
        loadOrders();
    });
})();
