const pathParts = window.location.pathname.split('/');
const restaurantId = window.RESTAURANT_ID || pathParts[pathParts.length - 1];
const isRestaurantMenuPage = Boolean(window.RESTAURANT_ID);

function formatPrice(value) {
    return `${(value || 0).toLocaleString('vi-VN')}đ`;
}

function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderVoucherOffers(vouchers) {
    const wrap = document.getElementById('voucher-offers');
    const list = document.getElementById('voucher-offers-list');
    if (!wrap || !list) return;

    if (!vouchers || vouchers.length === 0) {
        wrap.classList.add('hidden');
        list.innerHTML = '';
        return;
    }

    wrap.classList.remove('hidden');
    list.innerHTML = vouchers.map(v => `
        <div class="bg-gradient-to-br from-primary to-primary-container rounded-2xl p-md text-white relative overflow-hidden group">
            <div class="relative z-10">
                <h4 class="font-headline-md mb-xs text-white">${escapeHtml(v.label)}</h4>
                <p class="text-caption text-white/80 mb-md">${escapeHtml(v.description || v.name || '')}</p>
                <div class="flex items-center gap-xs flex-wrap">
                    <code class="bg-white/20 rounded-lg px-sm py-xs text-caption font-bold tracking-wide text-white">${escapeHtml(v.code)}</code>
                    <button type="button" class="copy-voucher-btn bg-white text-primary px-sm py-xs rounded-lg text-caption font-bold"
                        data-code="${escapeHtml(v.code)}">SAO CHÉP MÃ</button>
                </div>
            </div>
            <span class="material-symbols-outlined absolute -right-4 -bottom-4 text-7xl text-white/20 transform -rotate-12 group-hover:scale-125 transition-transform">local_activity</span>
        </div>
    `).join('');

    list.querySelectorAll('.copy-voucher-btn').forEach(btn => {
        btn.addEventListener('click', () => copyVoucherCode(btn.dataset.code));
    });
}

async function copyVoucherCode(code) {
    try {
        await navigator.clipboard.writeText(code);
        showToast(`Đã sao chép mã ${code}`, 'success');
    } catch (e) {
        showToast(`Không thể sao chép, mã của bạn là: ${code}`, 'error');
    }
}

async function loadVoucherOffers() {
    if (!document.getElementById('voucher-offers')) return;
    try {
        const res = await fetch(`/api/restaurants/${restaurantId}/vouchers`);
        if (!res.ok) return;
        const data = await res.json();
        renderVoucherOffers(data.items || []);
    } catch (e) {
        // Không chặn trang chính nếu tải danh sách voucher thất bại
    }
}

async function fetchCart() {
    const res = await fetch(`/api/cart/${restaurantId}`);
    if (!res.ok) return null;
    return res.json();
}

function renderCart(cart) {
    const container = document.getElementById('cart-items');
    const items = (cart && cart.items) || [];

    container.innerHTML = '';
    items.forEach(item => {
        const row = document.createElement('div');
        row.className = 'flex justify-between items-center py-xs border-b border-outline-variant/10';
        row.innerHTML = `
            <div>
                <p class="font-label-md">${item.dish_name}</p>
                <p class="text-caption text-secondary">${formatPrice(item.price)}</p>
            </div>
            <div class="flex items-center gap-xs">
                <button class="w-6 h-6 rounded-full border border-outline-variant flex items-center justify-center text-secondary hover:bg-primary hover:text-white hover:border-primary active:scale-90 transition-all"
                    onclick="changeCartItemQuantity(${item.id}, ${item.quantity - 1})">
                    <span class="material-symbols-outlined text-sm">remove</span>
                </button>
                <span class="font-label-md w-4 text-center">${item.quantity}</span>
                <button class="w-6 h-6 rounded-full border border-outline-variant flex items-center justify-center text-secondary hover:bg-primary hover:text-white hover:border-primary active:scale-90 transition-all"
                    onclick="changeCartItemQuantity(${item.id}, ${item.quantity + 1})">
                    <span class="material-symbols-outlined text-sm">add</span>
                </button>
            </div>
        `;
        container.appendChild(row);
    });

    const total = cart ? cart.total : 0;
    document.getElementById('cart-subtotal').textContent = formatPrice(total);
    document.getElementById('cart-total').textContent = formatPrice(total);
    document.getElementById('checkout-btn').disabled = items.length === 0;
    document.getElementById('mobile-cart-count').textContent = items.reduce((sum, i) => sum + i.quantity, 0);
    document.getElementById('mobile-cart-total').textContent = formatPrice(total);
}

async function refreshCart() {
    const cart = await fetchCart();
    renderCart(cart);
}

async function fetchRecommendations(dishId) {
    const res = await fetch(`/api/restaurants/${restaurantId}/recommendations?dish_id=${dishId}`);
    if (!res.ok) return null;
    return res.json();
}




function showRecommendationModal(recommendations) {
    const modal = document.getElementById('recommendation-modal');
    const backdrop = document.getElementById('recommendation-backdrop');
    const box = document.getElementById('recommendation-box');
    const container = document.getElementById('recommendation-items');
    if (!modal || !container || !recommendations || recommendations.length === 0) return;

    container.innerHTML = recommendations.map(dish => `
        <div class="group flex items-center justify-between gap-3 p-3 rounded-2xl bg-surface-container-low hover:bg-surface-container-high/70 border border-outline-variant/30 hover:border-primary/40 transition-all duration-200 hover:shadow-sm">
            <div class="flex items-center gap-3 min-w-0 flex-1">
                <div class="relative w-14 h-14 sm:w-16 sm:h-16 rounded-xl overflow-hidden shrink-0 shadow-xs bg-surface-container-highest">
                    <img src="${dish.image || ''}" onerror="this.src='https://png.pngtree.com/png-vector/20210623/ourmid/pngtree-pho-noodle-vietnamese-food-png-png-image_3508276.jpg'" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">
                </div>
                <div class="min-w-0 flex-1">
                    <h4 class="font-label-md font-bold text-on-surface truncate group-hover:text-primary transition-colors text-[14px] sm:text-[15px]">${dish.name}</h4>
                    <p class="font-headline-md text-primary font-bold text-sm mt-0.5">${formatPrice(dish.price)}</p>
                </div>
            </div>
            <button class="shrink-0 py-1.5 px-3 bg-surface-container-highest text-primary rounded-lg text-sm font-semibold hover:bg-primary hover:text-white active:scale-95 transition-all flex items-center gap-1 shadow-xs"
                onclick="addToCart(${dish.id}, this, false)">
                <span class="material-symbols-outlined text-[16px] leading-none">add</span> Thêm
            </button>
        </div>
    `).join('');

    modal.classList.remove('hidden');
    modal.classList.add('flex');

    setTimeout(() => {
        if (backdrop) {
            backdrop.classList.remove('opacity-0');
            backdrop.classList.add('opacity-100');
        }
        if (box) {
            box.classList.remove('translate-y-8', 'sm:scale-95', 'opacity-0');
            box.classList.add('translate-y-0', 'sm:scale-100', 'opacity-100');
        }
    }, 10);
}

function hideRecommendationModal() {
    const modal = document.getElementById('recommendation-modal');
    const backdrop = document.getElementById('recommendation-backdrop');
    const box = document.getElementById('recommendation-box');
    if (!modal) return;

    if (backdrop) {
        backdrop.classList.remove('opacity-100');
        backdrop.classList.add('opacity-0');
    }
    if (box) {
        box.classList.remove('translate-y-0', 'sm:scale-100', 'opacity-100');
        box.classList.add('translate-y-8', 'sm:scale-95', 'opacity-0');
    }

    setTimeout(() => {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }, 300);
}


async function addToCart(dishId, button, triggerRecommendation = true) {
    if (button.disabled) return;

    const originalHtml = button.innerHTML;
    const originalClass = button.className;

    button.disabled = true;
    button.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">progress_activity</span>';

    try {
        const res = await fetch(`/api/cart/${restaurantId}/items`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dish_id: dishId, quantity: 1 })
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            showToast(err.message, 'error');
            button.innerHTML = originalHtml;
            button.className = originalClass;
            button.disabled = false;
            return;
        }

        await refreshCart();

        // Trạng thái đã thêm thành công (V xanh)
        button.className = 'shrink-0 py-1.5 px-3 bg-green-500/20 text-green-600 rounded-xl text-sm font-semibold flex items-center gap-1 transition-all shadow-xs';
        button.innerHTML = '<span class="material-symbols-outlined text-[16px] leading-none">check</span> Đã thêm';

        // Gợi ý món ăn kèm nếu có (chỉ trigger khi thêm từ thực đơn chính)
        if (triggerRecommendation) {
            const recs = await fetchRecommendations(dishId);
            if (recs && recs.data && recs.data.length > 0) {
                showRecommendationModal(recs.data);
            }
        }

        // Giữ trạng thái "Đã thêm" trong 1s rồi trả lại nút ban đầu
        setTimeout(() => {
            button.innerHTML = originalHtml;
            button.className = originalClass;
            button.disabled = false;
        }, 1000);

    } catch (error) {
        showToast(error.message, 'error');
        button.innerHTML = originalHtml;
        button.className = originalClass;
        button.disabled = false;
    }
}



async function changeCartItemQuantity(cartItemId, newQuantity) {
    const res = newQuantity <= 0
        ? await fetch(`/api/cart/${restaurantId}/items/${cartItemId}`, { method: 'DELETE' })
        : await fetch(`/api/cart/${restaurantId}/items/${cartItemId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: newQuantity })
        });

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        showToast(err.message, 'error');
        return;
    }
    await refreshCart();
}

// load data restaurent detail and list dishes

async function fetchRestaurantData(id) {
    const res = await fetch(`/api/restaurants/${id}`);
    if (!res.ok) return null;
    return res.json();
}

async function fetchDishesData(id, page, category, keyword) {
    const params = new URLSearchParams({ page, per_page: 12 });
    if (category && category !== 'all') params.append('category', category);
    if (keyword) params.append('q', keyword);
    const res = await fetch(`/api/restaurants/${id}/dishes?${params}`);
    if (!res.ok) return { data: [], pages: 1 };
    const json = await res.json();
    return { data: json.data || [], pages: json.pages || 1 };
}

function renderRestaurantDetail(data) {
    if (!data) return;

    let el;

    el = document.querySelector('[data-restaurant-name]');
    if (el) el.textContent = data.name;
    el = document.querySelector('[data-restaurant-hero]');
    if (el) el.style.backgroundImage = `url('${data.cover_image || data.avatar}')`;
    el = document.querySelector('[data-restaurant-address]');
    if (el) el.textContent = data.address;
    el = document.querySelector('[data-restaurant-cuisine]');
    if (el) el.textContent = data.cuisine_type;
    el = document.querySelector('[data-restaurant-hours]');
    if (el && data.opening_time) el.textContent = `${data.opening_time} - ${data.closing_time}`;

    el = document.querySelector('[data-restaurant-name-sidebar]');
    if (el) el.textContent = data.name;

    el = document.querySelector('[data-restaurant-info-description]');
    if (el) el.textContent = data.description;
    el = document.querySelector('[data-restaurant-info-address]');
    if (el) el.textContent = data.address;
    el = document.querySelector('[data-restaurant-info-hours]');
    if (el && data.opening_time) el.textContent = `${data.opening_time} - ${data.closing_time}`;
    el = document.querySelector('[data-restaurant-info-phone]');
    if (el) el.textContent = data.phonenumber;
    el = document.querySelector('[data-restaurant-info-email]');
    if (el) el.textContent = data.email;

    el = document.querySelector('[data-restaurant-status]');
    if (el && data.opening_time) {
        const now = new Date();
        const [openH, openM] = data.opening_time.split(':').map(Number);
        const [closeH, closeM] = data.closing_time.split(':').map(Number);
        const open = openH * 60 + openM;
        const close = closeH * 60 + closeM;
        const current = now.getHours() * 60 + now.getMinutes();
        const isOpen = current >= open && current < close;
        el.textContent = isOpen ? 'Đang mở' : 'Đã đóng';
        el.className = `px-sm py-base rounded-full font-label-md text-label-md ${isOpen ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`;
    }

    if (data.distance_km) {
        el = document.querySelector('[data-restaurant-distance]');
        if (el) el.textContent = data.distance_km;
    }
    if (data.delivery_fee) {
        el = document.querySelector('[data-restaurant-fee]');
        if (el) el.textContent = data.delivery_fee;
    }

    document.title = `${data.name} - CraveConnect`;

}

function renderDishes(dishes, emptyMessage = 'Chưa có món ăn nào', showAction = !isRestaurantMenuPage) {
    console.log(dishes)
    const container = document.getElementById('dish-grid');
    if (!container) return;

    if (!dishes || dishes.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-xl text-on-surface-variant">
                <span class="material-symbols-outlined text-5xl mb-sm">restaurant_menu</span>
                <p class="text-body-md">${emptyMessage}</p>
            </div>`;
        return;
    }

    container.innerHTML = dishes.map(d => {
        const hasVoucher = d.voucher_code && d.final_price !== undefined && d.final_price !== null && d.final_price < d.original_price;
        const priceBlock = hasVoucher ? `
            <span class="flex flex-col leading-tight min-w-0">
                <span class="text-caption text-secondary line-through truncate">${(d.original_price || 0).toLocaleString('vi-VN')}đ</span>
                <span class="text-[17px] font-bold text-primary whitespace-nowrap">${(d.final_price || 0).toLocaleString('vi-VN')}đ</span>
            </span>
        ` : `<span class="text-[17px] font-bold text-primary whitespace-nowrap">${(d.price || 0).toLocaleString('vi-VN')}đ</span>`;
        return `
        <div class="bg-surface-container-lowest rounded-2xl shadow-[0px_4px_20px_rgba(0,0,0,0.06)] border border-outline-variant/20 hover:border-primary-fixed hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden group flex flex-col ${d.active ? '' : 'dish-disabled'}">
            <div class="h-40 bg-cover bg-center relative" style="background-image: url('${d.image || ''}')">
                <img src="${d.image || ''}" onerror="this.parentElement.style.backgroundImage='url(https://png.pngtree.com/png-vector/20210623/ourmid/pngtree-pho-noodle-vietnamese-food-png-png-image_3508276.jpg)'" class="hidden">
                ${hasVoucher ? `<span class="absolute top-2 right-2 bg-primary text-white text-caption font-bold px-2 py-0.5 rounded-full z-10 shadow-xs">${escapeHtml(d.voucher_label || '')}</span>` : ''}
                ${showAction ? '' : `
                <label class="dish-select-label absolute top-2 left-2 w-6 h-6 rounded-full bg-white shadow cursor-pointer z-10" title="Chọn để xóa">
                    <input type="checkbox" class="dish-select-input sr-only">
                    <span class="dish-select-check material-symbols-outlined text-sm text-transparent">check</span>
                </label>
                `}
            </div>
            <div class="p-4 flex flex-col flex-1 justify-between">
                <div>
                    <h3 class="font-headline-md text-[16px] font-bold text-on-surface line-clamp-1 group-hover:text-primary transition-colors">${d.name}</h3>
                    <span class="text-caption text-secondary block mt-0.5">${d.category || ''}</span>
                    <p class="text-caption text-secondary/90 italic line-clamp-2 mt-1 mb-3">${d.description || ''}</p>
                </div>
                ${showAction ? `
                <div class="flex items-center justify-between gap-2 pt-2.5 border-t border-outline-variant/15 mt-auto">
                    ${priceBlock}
                    <button class="shrink-0 py-1.5 px-3.5 bg-surface-container-highest text-primary rounded-xl text-sm font-semibold hover:bg-primary hover:text-white active:scale-95 transition-all flex items-center gap-1 shadow-xs"
                        onclick="addToCart(${d.id}, this)">
                        <span class="material-symbols-outlined text-[16px] leading-none">add</span> Thêm
                    </button>
                </div>
                ` : `
                <div class="flex items-center justify-between gap-2 pt-2.5 border-t border-outline-variant/15 mt-auto">
                    ${priceBlock}
                    <div class="flex items-center gap-2 shrink-0">
                        <label class="dish-toggle relative inline-flex items-center cursor-pointer" title="Bật / tắt món ăn">
                            <input type="checkbox" class="dish-toggle-input sr-only" ${d.active ? 'checked' : ''}>
                            <span class="dish-toggle-track w-10 h-5 bg-secondary-fixed rounded-full relative transition-colors">
                                <span class="dish-toggle-dot absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"></span>
                            </span>
                        </label>
                        <button class="dish-delete-btn w-7 h-7 rounded-lg border border-outline-variant flex items-center justify-center text-secondary hover:bg-error-container hover:text-error transition-all" data-dish-id="${d.id}" title="Xóa món ăn">
                            <span class="material-symbols-outlined text-sm">delete</span>
                        </button>
                    </div>
                </div>
                `}
            </div>
        </div>
    `;
    }).join('');
}

let currentCategory = 'all';

async function applyDishFilters() {
    currentPage = 1;
    const dishSearchInput = document.getElementById('dish-search-input');
    const keyword = dishSearchInput ? dishSearchInput.value.trim().toLowerCase() : '';

    const result = await fetchDishesData(restaurantId, 1, currentCategory, keyword);
    renderDishes(result.data, 'Không tìm thấy món ăn phù hợp');
    totalPages = result.pages;
    renderPagination();
}


document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        const tab = this.dataset.tab;

        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.remove('border-primary', 'text-primary');
            b.classList.add('border-transparent', 'text-secondary');
        });
        this.classList.remove('border-transparent', 'text-secondary');
        this.classList.add('border-primary', 'text-primary');

        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.getElementById('tab-' + tab).classList.remove('hidden');
    });
});

async function goToPage(page) {
    if (page < 1 || page > totalPages || page === currentPage) return;
    currentPage = page;
    const dishSearchInput = document.getElementById('dish-search-input');
    const keyword = dishSearchInput ? dishSearchInput.value.trim().toLowerCase() : '';
    const result = await fetchDishesData(restaurantId, currentPage, currentCategory, keyword);
    renderDishes(result.data);
    renderPagination();
}

document.addEventListener('DOMContentLoaded', async function () {
    if (!restaurantId) return;

    await loadingState.run(async () => {
        const [data] = await Promise.all([
            document.querySelector('[data-restaurant-name]') ? fetchRestaurantData(restaurantId) : Promise.resolve(null),
            document.getElementById('cart-items') ? refreshCart() : Promise.resolve()
        ]);

        renderRestaurantDetail(data);

        currentPage = 1;
        await applyDishFilters();
    });

    bindPaginationButtons();

    let searchTimeout;
    const dishSearchInput = document.getElementById('dish-search-input');
    if (dishSearchInput) {
        dishSearchInput.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(applyDishFilters, 300);
        });
    }

    document.querySelectorAll('.dish-category-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            currentCategory = this.dataset.category;

            document.querySelectorAll('.dish-category-btn').forEach(b => {
                b.classList.remove('bg-primary', 'text-white');
                b.classList.add('bg-transparent', 'text-secondary');
            });

            this.classList.remove('bg-transparent', 'text-secondary');
            this.classList.add('bg-primary', 'text-white');

            applyDishFilters();
        });
    });

    document.getElementById('checkout-btn')?.addEventListener('click', () => {
        if (restaurantId) {
            window.location.href = `/order-detail/${restaurantId}`;
        }
    });

    loadVoucherOffers();

    // Event listeners cho Recommendation Modal
    const modal = document.getElementById('recommendation-modal');
    const closeBtn = document.getElementById('close-recommendation-modal');
    const dismissBtn = document.getElementById('dismiss-recommendation-btn');

    if (closeBtn) closeBtn.addEventListener('click', hideRecommendationModal);
    if (dismissBtn) dismissBtn.addEventListener('click', hideRecommendationModal);
    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) hideRecommendationModal();
        });
    }
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') hideRecommendationModal();
    });

    document.getElementById('checkout-btn')?.addEventListener('click', () => {
        if (restaurantId) {
            window.location.href = `/order-detail/${restaurantId}`;
        }
    });
});

