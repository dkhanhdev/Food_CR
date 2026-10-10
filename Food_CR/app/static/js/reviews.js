// ============================================
// REVIEW SYSTEM - Restaurant reviews tab
// Rating summary, review list (load-more), submit/edit/delete
// ============================================

const reviewState = {
    restaurantId: null,
    orderId: null, // order_id requested via URL (?order_id=...), used only as a preselect hint
    userId: null,
    offset: 0,
    pageSize: 10,
    sortBy: 'newest',
    selectedRating: 0,
    selectedImages: [],
    editingReviewId: null,
    hasReviewed: false,
    canReview: false,
    completedOrders: [],
};

function getRestaurantIdFromURL() {
    const match = window.location.pathname.match(/\/restaurants\/(\d+)/);
    return match ? parseInt(match[1], 10) : null;
}

async function initReviews() {
    if (window.reviewsInitialized) return;
    window.reviewsInitialized = true;

    reviewState.restaurantId = getRestaurantIdFromURL();
    const storedUserId = localStorage.getItem('user_id');
    reviewState.userId = storedUserId ? parseInt(storedUserId, 10) : null;
    reviewState.orderId = new URLSearchParams(window.location.search).get('order_id');

    if (!reviewState.restaurantId) return;

    bindEventHandlers();
    await Promise.all([
        loadRatingsSummary(),
        checkEligibility(),
    ]);
    await loadReviews(true);
}

// ====== RATING SUMMARY ======
async function loadRatingsSummary() {
    try {
        const res = await fetch(`/api/reviews/restaurants/${reviewState.restaurantId}/rating-summary`);
        const data = await res.json();
        if (data.success) renderRatingSummary(data.data);
    } catch (error) {
        console.error('Load rating summary failed:', error);
    }
}

function renderRatingSummary(summary) {
    const avg = Number(summary.average_rating) || 0;

    const avgRatingEl = document.getElementById('avg-rating');
    if (avgRatingEl) avgRatingEl.textContent = avg.toFixed(1);

    const reviewCountEl = document.getElementById('review-count');
    if (reviewCountEl) reviewCountEl.textContent = `${summary.total_reviews} nhận xét`;

    const avgStars = document.getElementById('avg-stars');
    if (avgStars) {
        avgStars.innerHTML = '';
        const fullStars = Math.floor(avg);
        const hasHalf = avg % 1 >= 0.25 && avg % 1 < 0.75;
        const roundsUp = avg % 1 >= 0.75;

        for (let i = 1; i <= 5; i++) {
            const span = document.createElement('span');
            span.className = 'material-symbols-outlined';
            const filled = i <= fullStars || (i === fullStars + 1 && roundsUp);
            const half = i === fullStars + 1 && hasHalf;
            span.style.fontVariationSettings = `'FILL' ${filled ? 1 : half ? 0.5 : 0}`;
            span.textContent = 'star';
            avgStars.appendChild(span);
        }
    }

    const distribution = document.getElementById('rating-distribution');
    if (distribution) {
        distribution.innerHTML = '';
        for (let i = 5; i >= 1; i--) {
            const count = (summary.distribution && summary.distribution[i]) || 0;
            const percent = summary.total_reviews > 0 ? Math.round((count / summary.total_reviews) * 100) : 0;

            const row = document.createElement('div');
            row.className = 'flex items-center gap-sm';
            row.innerHTML = `
                <span class="font-label-md text-label-md w-4">${i}</span>
                <div class="flex-1 h-2 bg-surface-container-high rounded-full overflow-hidden">
                    <div class="h-full bg-tertiary rounded-full" style="width: ${percent}%;"></div>
                </div>
            `;
            distribution.appendChild(row);
        }
    }
}

// ====== REVIEW ELIGIBILITY (has COMPLETED order? already reviewed? which orders to pick from?) ======
async function checkEligibility() {
    if (!reviewState.userId) return;

    try {
        const res = await fetch(`/api/reviews/eligibility/restaurants/${reviewState.restaurantId}`);
        const data = await res.json();
        if (data.success) {
            reviewState.hasReviewed = !!data.data.has_reviewed;
            reviewState.canReview = !!data.data.can_review;
            reviewState.completedOrders = data.data.completed_orders || [];
            populateOrderSelect();
            updateWriteReviewVisibility();
        }
    } catch (error) {
        console.error('Check review eligibility failed:', error);
    }
}

// Fill the order picker with the user's COMPLETED orders at this restaurant,
// preselecting the one requested via ?order_id= in the URL when it's valid.
function populateOrderSelect() {
    const wrapper = document.getElementById('order-select-wrapper');
    const select = document.getElementById('order-select');
    if (!wrapper || !select) return;

    select.innerHTML = '';

    if (!reviewState.completedOrders.length) {
        wrapper.classList.add('hidden');
        return;
    }

    reviewState.completedOrders.forEach(order => {
        const option = document.createElement('option');
        option.value = order.id;
        const dateLabel = order.created_at ? new Date(order.created_at).toLocaleDateString('vi-VN') : '';
        option.textContent = `${order.name || ('Đơn #' + order.id)}${dateLabel ? ' - ' + dateLabel : ''}`;
        select.appendChild(option);
    });

    const requested = reviewState.orderId ? String(reviewState.orderId) : null;
    const hasRequested = requested && reviewState.completedOrders.some(o => String(o.id) === requested);
    select.value = hasRequested ? requested : String(reviewState.completedOrders[0].id);

    // Only worth showing the picker when there's an actual choice to make;
    // with a single COMPLETED order it's still selected, just not shown.
    wrapper.classList.toggle('hidden', reviewState.completedOrders.length < 2);
}

function updateWriteReviewVisibility() {
    const form = document.getElementById('write-review');
    const reviewedNotice = document.getElementById('already-reviewed-notice');
    const notEligibleNotice = document.getElementById('not-eligible-notice');
    if (!form || !reviewedNotice || !notEligibleNotice) return;

    if (reviewState.editingReviewId) {
        // Always show the form while editing an existing review
        form.classList.remove('hidden');
        reviewedNotice.classList.add('hidden');
        notEligibleNotice.classList.add('hidden');
        return;
    }

    if (reviewState.hasReviewed) {
        form.classList.add('hidden');
        reviewedNotice.classList.remove('hidden');
        notEligibleNotice.classList.add('hidden');
    } else if (reviewState.canReview) {
        form.classList.remove('hidden');
        reviewedNotice.classList.add('hidden');
        notEligibleNotice.classList.add('hidden');
    } else {
        // Not authenticated handling is done server-side (Jinja if/else);
        // reaching here as an authenticated user means: no COMPLETED order yet
        form.classList.add('hidden');
        reviewedNotice.classList.add('hidden');
        notEligibleNotice.classList.remove('hidden');
    }
}

// ====== REVIEWS LIST (load more) ======
async function loadReviews(reset) {
    if (reset) {
        reviewState.offset = 0;
        const container = document.getElementById('reviews-list');
        if (container) container.innerHTML = '';
    }

    try {
        showLoadingSpinner(true);
        const res = await fetch(
            `/api/reviews/restaurants/${reviewState.restaurantId}?limit=${reviewState.pageSize}&offset=${reviewState.offset}&sort=${reviewState.sortBy}`
        );
        const data = await res.json();
        if (data.success) {
            appendReviews(data.data.reviews);
            reviewState.offset += data.data.reviews.length;
            updateLoadMoreButton(data.data.pagination);
        } else {
            showError(data.message || 'Không thể tải đánh giá');
        }
    } catch (error) {
        console.error('Load reviews failed:', error);
        showError('Không thể tải đánh giá');
    } finally {
        showLoadingSpinner(false);
    }
}

function appendReviews(reviews) {
    const container = document.getElementById('reviews-list');
    if (!container) return;

    if (reviewState.offset === 0 && reviews.length === 0) {
        container.innerHTML = '<p class="text-center py-lg font-body-md text-body-md text-secondary">Chưa có đánh giá nào. Hãy là người đầu tiên chia sẻ trải nghiệm!</p>';
        return;
    }

    reviews.forEach(review => {
        const isOwn = reviewState.userId !== null && review.user_id === reviewState.userId;
        container.appendChild(createReviewCard(review, isOwn));
    });
}

function updateLoadMoreButton(pagination) {
    const btn = document.getElementById('load-more-btn');
    if (!btn) return;
    btn.classList.toggle('hidden', !pagination.has_more);
}

function createReviewCard(review, isOwn) {
    const div = document.createElement('div');
    div.className = 'bg-surface-container-lowest p-md rounded-xl shadow-[0px_4px_20px_rgba(0,0,0,0.05)] flex flex-col md:flex-row gap-md';

    const starsHtml = Array.from({ length: 5 }, (_, i) => `
        <span class="material-symbols-outlined text-[18px]" style="font-variation-settings: 'FILL' ${i < review.rating ? 1 : 0};">star</span>
    `).join('');

    let imagesHtml = '';
    if (review.images && review.images.length > 0) {
        imagesHtml = `<div class="flex gap-xs overflow-x-auto pb-xs custom-scrollbar mb-md">${
            review.images.map(img => `<img src="${img.url}" alt="Ảnh đánh giá" class="w-24 h-24 rounded-lg object-cover shrink-0">`).join('')
        }</div>`;
    }

    let actionsHtml = '';
    if (isOwn) {
        actionsHtml = `
            <div class="mt-md flex items-center gap-md">
                <button type="button" onclick="handleEditReview(${review.id})" class="flex items-center gap-xs font-label-md text-label-md text-secondary hover:text-primary transition-colors">
                    <span class="material-symbols-outlined text-[20px]">edit</span>
                    Chỉnh sửa
                </button>
                <button type="button" onclick="handleDeleteReview(${review.id})" class="flex items-center gap-xs font-label-md text-label-md text-error hover:opacity-80 transition-colors">
                    <span class="material-symbols-outlined text-[20px]">delete</span>
                    Xoá
                </button>
            </div>
        `;
    }

    div.innerHTML = `
        <div class="flex items-start gap-sm md:w-48 shrink-0">
            <div class="w-10 h-10 rounded-full overflow-hidden bg-surface-container shrink-0">
                <img src="${review.user_avatar || ''}" alt="${escapeHtml(review.user_name)}" class="w-full h-full object-cover">
            </div>
            <div>
                <div class="font-label-md text-label-md font-bold">${escapeHtml(review.user_name)}${isOwn ? ' <span class="text-primary">(Bạn)</span>' : ''}</div>
                <div class="font-caption text-caption text-secondary">${formatRelativeTime(review.created_at)}</div>
            </div>
        </div>
        <div class="flex-1">
            <div class="flex text-tertiary-container mb-xs">${starsHtml}</div>
            <p class="font-body-md text-body-md mb-md whitespace-pre-wrap">${escapeHtml(review.comment || '')}</p>
            ${imagesHtml}
            ${actionsHtml}
        </div>
    `;

    return div;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

// ====== STAR RATING SELECTOR ======
function handleStarRating(rating) {
    reviewState.selectedRating = rating;
    updateStarVisuals(rating);
}

function updateStarVisuals(rating) {
    const stars = document.querySelectorAll('#rating-stars span');
    stars.forEach((star, i) => {
        star.style.fontVariationSettings = `'FILL' ${i < rating ? 1 : 0}`;
    });
}

// ====== IMAGE UPLOAD ======
function handleImageSelect(files) {
    if (!validateImages(files)) return;
    reviewState.selectedImages = Array.from(files);
    renderImagePreview();
}

function validateImages(files) {
    const allowed = ['image/jpeg', 'image/png', 'image/webp'];
    const maxSize = 5 * 1024 * 1024;

    if (files.length > 5) {
        showError('Tối đa 5 ảnh');
        return false;
    }
    for (const file of files) {
        if (!allowed.includes(file.type)) {
            showError('Chỉ hỗ trợ ảnh JPG, PNG, WebP');
            return false;
        }
        if (file.size > maxSize) {
            showError(`Ảnh "${file.name}" vượt quá 5MB`);
            return false;
        }
    }
    return true;
}

function renderImagePreview() {
    const gallery = document.getElementById('image-preview');
    if (!gallery) return;
    gallery.innerHTML = '';

    reviewState.selectedImages.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const div = document.createElement('div');
            div.className = 'relative w-24 h-24 rounded-lg overflow-hidden shrink-0';
            div.innerHTML = `
                <img src="${e.target.result}" class="w-full h-full object-cover">
                <button type="button" onclick="removeImage(${index})"
                    class="absolute top-1 right-1 bg-error text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold hover:opacity-80 transition-all">
                    ✕
                </button>
            `;
            gallery.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

function removeImage(index) {
    reviewState.selectedImages.splice(index, 1);
    renderImagePreview();
}

// ====== SUBMIT / UPDATE / DELETE ======
async function handleReviewFormSubmit(e) {
    e.preventDefault();
    if (reviewState.editingReviewId) {
        await handleUpdateReview();
    } else {
        await handleSubmitReview();
    }
}

async function handleSubmitReview() {
    if (!reviewState.userId) {
        showError('Vui lòng đăng nhập để đánh giá');
        return;
    }
    if (reviewState.selectedRating === 0) {
        showError('Vui lòng chọn số sao');
        return;
    }

    const commentField = document.getElementById('comment');
    const comment = commentField ? commentField.value.trim() : '';
    if (comment && (comment.length < 10 || comment.length > 1000)) {
        showError('Nhận xét phải từ 10-1000 ký tự');
        return;
    }

    try {
        showLoadingSpinner(true);

        // The order this review is for comes from the picker (defaults to
        // the most recent COMPLETED order); the server independently
        // re-verifies eligibility regardless of what's sent here.
        const orderSelect = document.getElementById('order-select');
        const selectedOrderId = (orderSelect && orderSelect.value) ? orderSelect.value : reviewState.orderId;

        const formData = new FormData();
        formData.append('restaurant_id', reviewState.restaurantId);
        if (selectedOrderId) formData.append('order_id', selectedOrderId);
        formData.append('rating', reviewState.selectedRating);
        if (comment) formData.append('comment', comment);
        reviewState.selectedImages.forEach(file => formData.append('images', file));

        const res = await fetch('/api/reviews', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.success) {
            showSuccess('Đánh giá đã được gửi thành công!');
            resetForm();
            await checkEligibility();
            await loadReviews(true);
            await loadRatingsSummary();
        } else {
            showError(data.message || 'Gửi đánh giá thất bại');
        }
    } catch (error) {
        showError('Lỗi kết nối: ' + error.message);
    } finally {
        showLoadingSpinner(false);
    }
}

function handleEditReview(reviewId) {
    fetch(`/api/reviews/${reviewId}`)
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                showError(data.message || 'Không thể tải đánh giá để chỉnh sửa');
                return;
            }
            const review = data.data;
            reviewState.editingReviewId = reviewId;
            reviewState.selectedRating = review.rating;

            const commentField = document.getElementById('comment');
            if (commentField) {
                commentField.value = review.comment || '';
                const charCount = document.getElementById('char-count');
                if (charCount) charCount.textContent = commentField.value.length;
            }
            updateStarVisuals(review.rating);

            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) submitBtn.textContent = 'Cập nhật đánh giá';
            const cancelBtn = document.getElementById('cancel-edit-btn');
            if (cancelBtn) cancelBtn.classList.remove('hidden');

            updateWriteReviewVisibility();
            document.getElementById('write-review')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        })
        .catch(() => showError('Không thể tải đánh giá để chỉnh sửa'));
}

async function handleUpdateReview() {
    const reviewId = reviewState.editingReviewId;
    if (reviewState.selectedRating === 0) {
        showError('Vui lòng chọn số sao');
        return;
    }

    const commentField = document.getElementById('comment');
    const comment = commentField ? commentField.value.trim() : '';
    if (comment && (comment.length < 10 || comment.length > 1000)) {
        showError('Nhận xét phải từ 10-1000 ký tự');
        return;
    }

    try {
        showLoadingSpinner(true);
        const res = await fetch(`/api/reviews/${reviewId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rating: reviewState.selectedRating, comment }),
        });
        const data = await res.json();

        if (data.success) {
            showSuccess('Đánh giá đã được cập nhật');
            resetForm();
            await loadReviews(true);
            await loadRatingsSummary();
        } else {
            showError(data.message || 'Cập nhật thất bại');
        }
    } catch (error) {
        showError('Lỗi kết nối: ' + error.message);
    } finally {
        showLoadingSpinner(false);
    }
}

function cancelEdit() {
    resetForm();
}

async function handleDeleteReview(reviewId) {
    if (!confirm('Bạn chắc chắn muốn xoá đánh giá này?')) return;

    try {
        showLoadingSpinner(true);
        const res = await fetch(`/api/reviews/${reviewId}`, { method: 'DELETE' });
        const data = await res.json();

        if (data.success) {
            showSuccess('Đánh giá đã được xoá');
            await checkEligibility();
            await loadReviews(true);
            await loadRatingsSummary();
        } else {
            showError(data.message || 'Xoá thất bại');
        }
    } catch (error) {
        showError('Lỗi kết nối: ' + error.message);
    } finally {
        showLoadingSpinner(false);
    }
}

// ====== FORM HELPERS ======
function resetForm() {
    reviewState.selectedRating = 0;
    reviewState.selectedImages = [];
    reviewState.editingReviewId = null;

    const comment = document.getElementById('comment');
    if (comment) comment.value = '';

    const imagePreview = document.getElementById('image-preview');
    if (imagePreview) imagePreview.innerHTML = '';

    const imageInput = document.getElementById('image-input');
    if (imageInput) imageInput.value = '';

    const charCount = document.getElementById('char-count');
    if (charCount) charCount.textContent = '0';

    updateStarVisuals(0);

    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) submitBtn.textContent = 'Gửi đánh giá ngay';
    const cancelBtn = document.getElementById('cancel-edit-btn');
    if (cancelBtn) cancelBtn.classList.add('hidden');

    updateWriteReviewVisibility();
}

function bindEventHandlers() {
    document.getElementById('review-form')?.addEventListener('submit', handleReviewFormSubmit);
    document.getElementById('cancel-edit-btn')?.addEventListener('click', cancelEdit);

    document.getElementById('sort-dropdown')?.addEventListener('change', (e) => {
        reviewState.sortBy = e.target.value;
        loadReviews(true);
    });

    document.getElementById('image-input')?.addEventListener('change', (e) => {
        handleImageSelect(e.target.files);
    });

    document.getElementById('load-more-btn')?.addEventListener('click', () => loadReviews(false));

    document.getElementById('comment')?.addEventListener('input', (e) => {
        const charCount = document.getElementById('char-count');
        if (charCount) charCount.textContent = e.target.value.length;
    });
}

// ====== UI HELPERS ======
function showLoadingSpinner(show) {
    document.getElementById('loading-spinner')?.classList.toggle('hidden', !show);
}

function showError(msg) {
    if (typeof window.showToast === 'function') {
        window.showToast(msg, 'error');
        return;
    }
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = msg;
        errorDiv.classList.remove('hidden');
        setTimeout(() => errorDiv.classList.add('hidden'), 5000);
    }
}

function showSuccess(msg) {
    if (typeof window.showToast === 'function') {
        window.showToast(msg, 'success');
    }
}

function formatRelativeTime(timestamp) {
    if (!timestamp) return '';
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;
    return date.toLocaleDateString('vi-VN');
}

// ====== ENTRY POINT ======
document.addEventListener('DOMContentLoaded', () => {
    const tabButton = document.querySelector('[data-tab="reviews"]');
    if (tabButton) {
        tabButton.addEventListener('click', initReviews);
    }

    if (new URLSearchParams(window.location.search).get('tab') === 'reviews') {
        tabButton?.click();
    }
});
