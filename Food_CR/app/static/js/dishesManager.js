(function () {
    const grid = document.getElementById('dish-grid');
    if (!grid) return;

    const addDishBtn = document.getElementById('add-dish-btn');
    const formModal = document.getElementById('dish-form-modal');
    const form = document.getElementById('dish-form');
    const formCancel = document.getElementById('dish-form-cancel');
    const formSubmit = document.getElementById('dish-form-submit');
    const imageInput = document.getElementById('dish-image');
    const imageDrop = document.getElementById('dish-image-drop');
    const imagePreview = document.getElementById('dish-image-preview');
    const imageFilename = document.getElementById('dish-image-filename');

    const deleteMultiBtn = document.getElementById('delete-multi-btn');
    const deleteModal = document.getElementById('dish-delete-modal');
    const deleteMessage = document.getElementById('dish-delete-message');
    const deleteCancel = document.getElementById('dish-delete-cancel');
    const deleteConfirm = document.getElementById('dish-delete-confirm');

    async function refreshDishStats() {
        const totalEl = document.getElementById('stat-total');
        const activeEl = document.getElementById('stat-active');
        const inactiveEl = document.getElementById('stat-inactive');
        if (!totalEl && !activeEl && !inactiveEl) return;

        try {
            const res = await fetch('/api/dishes/stats');
            if (!res.ok) return;
            const stats = await res.json();
            if (totalEl) totalEl.textContent = stats.total ?? 0;
            if (activeEl) activeEl.textContent = stats.active ?? 0;
            if (inactiveEl) inactiveEl.textContent = stats.inactive ?? 0;
        } catch (err) {
            /* bỏ qua lỗi thống kê */
        }
    }

    function openFormModal() {
        formModal.classList.remove('hidden');
        formModal.classList.add('flex');
        setTimeout(() => {
            const input = form && form.querySelector('#dish-name');
            if (input) input.focus();
        }, 50);
    }

    function closeFormModal() {
        formModal.classList.add('hidden');
        formModal.classList.remove('flex');
    }

    function resetForm() {
        if (!form) return;
        form.reset();
        if (imagePreview) imagePreview.classList.add('hidden');
        if (imageFilename) imageFilename.textContent = 'Định dạng PNG, JPG, WebP (Tối đa 5MB)';
    }

    function handleDishImage(file) {
        if (!file) return;
        if (imageFilename) imageFilename.textContent = file.name;
        const reader = new FileReader();
        reader.onload = function (e) {
            imagePreview.src = e.target.result;
            imagePreview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }

    if (imageDrop) {
        imageDrop.addEventListener('click', function () {
            if (imageInput) imageInput.click();
        });

        imageDrop.addEventListener('dragover', function (e) {
            e.preventDefault();
            imageDrop.classList.add('border-primary');
        });

        imageDrop.addEventListener('dragleave', function () {
            imageDrop.classList.remove('border-primary');
        });

        imageDrop.addEventListener('drop', function (e) {
            e.preventDefault();
            imageDrop.classList.remove('border-primary');
            if (e.dataTransfer.files.length > 0) {
                imageInput.files = e.dataTransfer.files;
                handleDishImage(e.dataTransfer.files[0]);
            }
        });
    }

    if (imageInput) {
        imageInput.addEventListener('change', function () {
            const file = this.files && this.files[0];
            if (!file) {
                if (imagePreview) imagePreview.classList.add('hidden');
                if (imageFilename) imageFilename.textContent = 'Định dạng PNG, JPG, WebP (Tối đa 5MB)';
                return;
            }
            handleDishImage(file);
        });
    }

    if (addDishBtn) {
        addDishBtn.addEventListener('click', openFormModal);
    }

    if (formCancel) {
        formCancel.addEventListener('click', function () {
            resetForm();
            closeFormModal();
        });
    }

    if (formModal) {
        formModal.addEventListener('click', function (e) {
            if (e.target === formModal) {
                resetForm();
                closeFormModal();
            }
        });
    }

    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const file = imageInput && imageInput.files && imageInput.files[0];
            if (file && file.size > 5 * 1024 * 1024) {
                showToast('Ảnh tối đa 5MB', 'error');
                return;
            }

            const prevHtml = formSubmit.innerHTML;
            formSubmit.disabled = true;
            formSubmit.innerHTML = '<span class="material-symbols-outlined text-[18px] animate-spin">sync</span> &#272;ang th&#234;m...';

            try {
                const formData = new FormData(form);
                const res = await fetch('/api/dishes/', {
                    method: 'POST',
                    body: formData
                });
                const result = await res.json().catch(() => ({}));
                if (!res.ok) {
                    showToast(result.message || 'Thêm món ăn thất bại', 'error');
                    return;
                }
                showToast('Đã thêm món ăn thành công', 'success');
                resetForm();
                closeFormModal();
                await Promise.all([applyDishFilters(), refreshDishStats()]);
            } catch (err) {
                showToast('Lỗi kết nối đến máy chủ', 'error');
            } finally {
                formSubmit.disabled = false;
                formSubmit.innerHTML = prevHtml;
            }
        });
    }

    function dishIdFromCard(card) {
        const btn = card && card.querySelector('.dish-delete-btn');
        return btn ? btn.dataset.dishId : null;
    }

    async function toggleDish(input) {
        const card = input.closest('.group');
        const dishId = dishIdFromCard(card);
        if (!dishId) return;

        const wantedActive = input.checked;
        card.classList.toggle('dish-disabled', !wantedActive);

        try {
            const res = await fetch('/api/dishes/', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id_dishes: Number(dishId) })
            });
            const result = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(result.message || 'Cập nhật trạng thái thất bại');
            }
            const active = Boolean(result.active);
            input.checked = active;
            card.classList.toggle('dish-disabled', !active);
            showToast(active ? 'Món ăn đã bật' : 'Món ăn đã tắt', 'success');
            refreshDishStats();
        } catch (err) {
            input.checked = wantedActive;
            card.classList.toggle('dish-disabled', !wantedActive);
            showToast(err.message || 'Cập nhật trạng thái thất bại', 'error');
        }
    }

    grid.addEventListener('change', function (e) {
        if (e.target.classList.contains('dish-toggle-input')) {
            toggleDish(e.target);
        }
    });

    function openDeleteModal(message) {
        if (deleteMessage) deleteMessage.textContent = message;
        deleteModal.classList.remove('hidden');
        deleteModal.classList.add('flex');
    }

    function closeDeleteModal() {
        deleteModal.classList.add('hidden');
        deleteModal.classList.remove('flex');
    }

    if (deleteModal) {
        deleteModal.addEventListener('click', function (e) {
            if (e.target === deleteModal) closeDeleteModal();
        });
    }
    if (deleteCancel) {
        deleteCancel.addEventListener('click', closeDeleteModal);
    }

    function exitSelectMode() {
        if (!grid) return;
        grid.classList.remove('select-mode');
        if (deleteMultiBtn) {
            deleteMultiBtn.classList.remove('bg-error-container', 'text-error', 'border-error');
        }
        document.querySelectorAll('.dish-select-input').forEach(function (cb) { cb.checked = false; });
        document.querySelectorAll('.dish-selected').forEach(function (card) { card.classList.remove('dish-selected'); });
    }

    function enterSelectMode() {
        if (!grid) return;
        grid.classList.add('select-mode');
        if (deleteMultiBtn) {
            deleteMultiBtn.classList.add('bg-error-container', 'text-error', 'border-error');
        }
    }

    let pendingDeleteIds = [];

    function setDeleteConfirmLoading(loading) {
        if (!deleteConfirm) return;
        deleteConfirm.disabled = loading;
        deleteConfirm.innerHTML = loading
            ? '<span class="material-symbols-outlined text-[18px] animate-spin">sync</span> &#272;ang x&#243;a...'
            : '<span class="material-symbols-outlined text-[18px]">delete</span> X&#243;a';
    }

    async function deleteOne(id) {
        try {
            const res = await fetch(`/api/dishes/${id}`, { method: 'DELETE' });
            const result = await res.json().catch(() => ({}));
            return { ok: res.ok, message: result.message || 'Không thể xóa món ăn' };
        } catch (err) {
            return { ok: false, message: 'Lỗi kết nối đến máy chủ' };
        }
    }

    async function executePendingDelete() {
        const ids = pendingDeleteIds.slice();
        if (!ids.length) return;

        setDeleteConfirmLoading(true);
        const results = await Promise.all(ids.map(deleteOne));

        const okCount = results.filter(r => r.ok).length;
        const failCount = results.length - okCount;
        const firstFail = results.find(r => !r.ok);

        closeDeleteModal();
        setDeleteConfirmLoading(false);
        pendingDeleteIds = [];

        if (failCount === 0) {
            showToast(ids.length > 1
                ? `Đã xóa ${ids.length} món ăn thành công`
                : 'Đã xóa món ăn thành công', 'success');
        } else if (okCount > 0) {
            showToast(`Đã xóa ${okCount} món, ${failCount} món thất bại`, 'warning');
        } else {
            showToast(firstFail ? firstFail.message : 'Xóa món ăn thất bại', 'error');
        }

        exitSelectMode();
        await Promise.all([applyDishFilters(), refreshDishStats()]);
    }

    if (deleteConfirm) {
        deleteConfirm.addEventListener('click', executePendingDelete);
    }

    grid.addEventListener('click', function (e) {
        const btn = e.target.closest('.dish-delete-btn');
        if (!btn) return;
        pendingDeleteIds = [Number(btn.dataset.dishId)];
        openDeleteModal('Bạn có chắc muốn xóa món ăn này không?');
    });

    if (deleteMultiBtn) {
        deleteMultiBtn.addEventListener('click', function () {
            const isSelectMode = grid.classList.contains('select-mode');

            if (!isSelectMode) {
                enterSelectMode();
                return;
            }

            const selected = Array.from(document.querySelectorAll('.dish-select-input:checked'))
                .map(cb => Number(dishIdFromCard(cb.closest('.group'))))
                .filter(Boolean);

            if (selected.length === 0) {
                exitSelectMode();
                return;
            }

            pendingDeleteIds = selected;
            openDeleteModal(selected.length > 1
                ? `Bạn có chắc muốn xóa ${selected.length} món ăn này không?`
                : 'Bạn có chắc muốn xóa món ăn này không?');
        });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape') return;
        if (formModal && !formModal.classList.contains('hidden')) {
            resetForm();
            closeFormModal();
        }
        if (deleteModal && !deleteModal.classList.contains('hidden')) {
            closeDeleteModal();
        }
    });

    refreshDishStats();
})();
