// Input focus highlight
document.querySelectorAll('input, textarea, select').forEach(input => {
    input.addEventListener('focus', () => {
        input.parentElement.querySelector('label')?.classList.add('text-primary');
    });
    input.addEventListener('blur', () => {
        input.parentElement.querySelector('label')?.classList.remove('text-primary');
    });
});

// Validation helpers
const requiredFields = [
    { id: 'restaurant-name', label: 'Tên nhà hàng' },
    { id: 'restaurant-phone', label: 'Số điện thoại' },
    { id: 'restaurant-email', label: 'Email kinh doanh' },
    { id: 'restaurant-address', label: 'Địa chỉ' },
];

function clearErrors() {
    document.querySelectorAll('.field-error').forEach(e => e.remove());
    document.querySelectorAll('.input-error').forEach(e => e.classList.remove('input-error'));
}

function showError(id, message) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add('input-error');
    const error = document.createElement('p');
    error.className = 'field-error text-error text-caption mt-1';
    error.textContent = message;
    el.parentElement.appendChild(error);
}

function validate() {
    clearErrors();
    let valid = true;

    requiredFields.forEach(f => {
        const el = document.getElementById(f.id);
        const val = el?.value?.trim();
        if (!val) {
            showError(f.id, `${f.label} không được để trống`);
            valid = false;
        }
    });

    // Email format
    const email = document.getElementById('restaurant-email');
    if (email?.value?.trim()) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!re.test(email.value.trim())) {
            showError('restaurant-email', 'Email không đúng định dạng');
            valid = false;
        }
    }

    // Phone format
    const phone = document.getElementById('restaurant-phone');
    if (phone?.value?.trim()) {
        const re = /^(0|\+84)[0-9]{8,9}$/;
        if (!re.test(phone.value.replace(/\s/g, ''))) {
            showError('restaurant-phone', 'Số điện thoại không hợp lệ (0xxxxxxxxx)');
            valid = false;
        }
    }

    return valid;
}

// Clear error on input — restaurant
requiredFields.forEach(f => {
    const el = document.getElementById(f.id);
    if (el) {
        el.addEventListener('input', () => {
            const error = el.parentElement.querySelector('.field-error');
            if (error) error.remove();
            el.classList.remove('input-error');
        });
    }
});
// Clear error on input — restaurant max cart items
const maxCartInput = document.getElementById('restaurant-max-cart-items');
if (maxCartInput) {
    maxCartInput.addEventListener('input', () => {
        const error = maxCartInput.parentElement.querySelector('.field-error');
        if (error) error.remove();
        maxCartInput.classList.remove('input-error');
    });
}

// Clear error on input — customer
['customer-name', 'customer-email', 'customer-phone', 'customer-address'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('input', () => {
            const error = el.parentElement.querySelector('.field-error');
            if (error) error.remove();
            el.classList.remove('input-error');
        });
    }
});

function validateCustomer() {
    clearErrors();
    let valid = true;

    const name = document.getElementById('customer-name');
    if (!name?.value?.trim()) {
        showError('customer-name', 'Tên không được để trống');
        valid = false;
    }

    const email = document.getElementById('customer-email');
    if (email?.value?.trim()) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!re.test(email.value.trim())) {
            showError('customer-email', 'Email không đúng định dạng');
            valid = false;
        }
    }

    const phone = document.getElementById('customer-phone');
    if (phone?.value?.trim()) {
        const re = /^(0|\+84)[0-9]{8,9}$/;
        if (!re.test(phone.value.replace(/\s/g, ''))) {
            showError('customer-phone', 'Số điện thoại không hợp lệ');
            valid = false;
        }
    }

    const address = document.getElementById('customer-address');
    if (!address?.value?.trim()) {
        showError('customer-address', 'Địa chỉ không được để trống');
        valid = false;
    }

    return valid;
}

// Save button — Restaurant profile
const saveBtn = document.getElementById('save-btn');
if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
        if (!validate()) return;

        const data = {
            name: document.getElementById('restaurant-name')?.value?.trim(),
            cuisine_type: document.getElementById('restaurant-cuisine')?.value,
            description: document.getElementById('restaurant-description')?.value?.trim(),
            phonenumber: document.getElementById('restaurant-phone')?.value?.trim(),
            email: document.getElementById('restaurant-email')?.value?.trim(),
            address: document.getElementById('restaurant-address')?.value?.trim(),
            opening_time: document.getElementById('restaurant-opening-time')?.value,
            closing_time: document.getElementById('restaurant-closing-time')?.value,
        };
        const coverImg = document.querySelector('.h-48 img');
        if (coverImg) data.cover_image = coverImg.src;

        // Giới hạn giỏ hàng riêng của nhà hàng (number input)
        const maxCartInput = document.getElementById('restaurant-max-cart-items');
        if (maxCartInput) {
            const val = Number(maxCartInput.value);
            const cap = Number(maxCartInput.max) || 0;
            if (!Number.isInteger(val) || val < 1 || val > cap) {
                maxCartInput.classList.add('input-error');
                showError('restaurant-max-cart-items', `Giới hạn phải là số nguyên từ 1 đến ${cap}`);
                return;
            }
            data.max_cart_items = val;
        }

        const originalContent = saveBtn.innerHTML;
        saveBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">sync</span> Đang lưu...';
        saveBtn.disabled = true;

        try {
            const res = await fetch('/api/auth/update-profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();
            if (res.ok) {
                showToast(result.message, 'success');
                saveBtn.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Đã lưu thành công';
                saveBtn.classList.add('bg-green-600');
                saveBtn.classList.remove('bg-primary');
                setTimeout(() => {
                    saveBtn.innerHTML = originalContent;
                    saveBtn.classList.remove('bg-green-600');
                    saveBtn.classList.add('bg-primary');
                    saveBtn.disabled = false;
                }, 2000);
            } else {
                showToast(result.message, 'error');
                saveBtn.innerHTML = originalContent;
                saveBtn.disabled = false;
            }
        } catch (err) {
            showToast('Lỗi kết nối đến máy chủ', 'error');
            saveBtn.innerHTML = originalContent;
            saveBtn.disabled = false;
        }
    });
}

// Save button — Customer profile
const customerSaveBtn = document.getElementById('customer-save-btn');
if (customerSaveBtn) {
    customerSaveBtn.addEventListener('click', async () => {
        if (!validateCustomer()) return;
        const data = {
            name: document.getElementById('customer-name')?.value?.trim(),
            email: document.getElementById('customer-email')?.value?.trim(),
            phonenumber: document.getElementById('customer-phone')?.value?.trim(),
            address: document.getElementById('customer-address')?.value?.trim(),
        };

        const originalContent = customerSaveBtn.innerHTML;
        customerSaveBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">sync</span> Đang lưu...';
        customerSaveBtn.disabled = true;

        try {
            const res = await fetch('/api/auth/update-profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();
            if (res.ok) {
                showToast(result.message, 'success');
                customerSaveBtn.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Đã lưu thành công';
                customerSaveBtn.classList.add('bg-green-600');
                customerSaveBtn.classList.remove('bg-primary');
                setTimeout(() => {
                    customerSaveBtn.innerHTML = originalContent;
                    customerSaveBtn.classList.remove('bg-green-600');
                    customerSaveBtn.classList.add('bg-primary');
                    customerSaveBtn.disabled = false;
                }, 2000);
            } else {
                showToast(result.message, 'error');
                customerSaveBtn.innerHTML = originalContent;
                customerSaveBtn.disabled = false;
            }
        } catch (err) {
            showToast('Lỗi kết nối đến máy chủ', 'error');
            customerSaveBtn.innerHTML = originalContent;
            customerSaveBtn.disabled = false;
        }
    });
}
