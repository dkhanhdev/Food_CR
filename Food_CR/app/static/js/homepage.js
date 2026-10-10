const hero_datas = {
    'morning': {
        'section_bg': "linear-gradient(135deg, #f97316 0%, #f59e0b 40%, #fde68a 100%)",
        'chip_bg': "rgba(255,255,255,0.25)", 'chip_text': "#ffffff",
        'title_color': "#ffffff", 'desc_color': "rgba(255,255,255,0.9)",
        'btn_primary_bg': "#ffffff", 'btn_primary_text': "#ea580c",
        'btn_secondary_border': "#ffffff", 'btn_secondary_text': "#ffffff",
        'icon': "wb_sunny", 'greeting': "Chào buổi sáng tươi đẹp!",
        'title': "Bữa sáng ngon miệng cho bạn",
        'desc': "Hôm nay AI của chúng tôi gợi ý bạn một bữa sáng cân bằng dinh dưỡng. Đặt ngay để nhận ưu đãi miễn phí vận chuyển!",
        'img': "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=600&q=80",
        'img_alt': "Healthy breakfast spread"
    },
    'afternoon': {
        'section_bg': "#d34000",
        'chip_bg': "rgba(255,251,255,0.2)", 'chip_text': "#fffbff",
        'title_color': "#fffbff", 'desc_color': "rgba(255,251,255,0.9)",
        'btn_primary_bg': "#fffbff", 'btn_primary_text': "#d34000",
        'btn_secondary_border': "#fffbff", 'btn_secondary_text': "#fffbff",
        'icon': "wb_sunny", 'greeting': "Chào buổi trưa rực rỡ!",
        'title': "Bữa trưa ngon miệng cho bạn",
        'desc': "Hôm nay AI của chúng tôi gợi ý bạn một bữa trưa cân bằng dinh dưỡng. Đặt ngay để nhận ưu đãi miễn phí vận chuyển!",
        'img': "https://lh3.googleusercontent.com/aida-public/AB6AXuCF0DccTUJBz9XzaTXhWQvnpdqJ_9tgEajJ9-vzn1Hzj9WlttbRR6jg_YzQh_XJC7D5hN5ZGv4k5HhbBIRjolLA2PEcPEtL8AbVEe2tVSxcxiM6QzLTm5H6Vd0FiixYDGe2kpSDk19ayt_2WFW-8rOLH6lB8U9Xy4FbzXqiQxCBl9zG28RlxUpQhsQmtNo3kpKWtBNWQm5nEYBKzGSx__mibsEWwtmx5sM3NdlnWTNqwdc6QqZk6ooYt7MrxDUEfG3Sd7x_SxjC904",
        'img_alt': "Healthy poke bowl"
    },
    'evening': {
        'section_bg': "#000099",
        'chip_bg': "rgba(255,255,255,0.2)", 'chip_text': "white",
        'title_color': "white", 'desc_color': "rgba(255,255,255,0.8)",
        'btn_primary_bg': "white", 'btn_primary_text': "#000099",
        'btn_secondary_border': "white", 'btn_secondary_text': "white",
        'icon': "mode_night", 'greeting': "Chào buổi tối ấm áp!",
        'title': "Bữa tối nhẹ nhàng cho bạn",
        'desc': "Kết thúc ngày dài với bữa tối nhẹ nhàng, đầy đủ dinh dưỡng từ những nhà hàng yêu thích.",
        'img': "https://images.unsplash.com/photo-1559847844-5315695dadae?w=600&q=80",
        'img_alt': "Warm dinner meal"
    }
}

const DEFAULT_HERO_DATA = hero_datas['morning'];

function getTimePeriod() {
    const h = new Date().getHours();
    if (h < 12) return 'morning';
    if (h < 16) return 'afternoon';
    return 'evening';
}

const restaurantList = [
    { 'name': 'Pizza Lab - Artisan Pizza', 'cuisine': 'Pizza Ý, Đồ Âu, Salad', 'rating': '4.8', 'time': '20-30 phút', 'fee': 'Miễn phí', 'dist': '1.2km', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuCemJHkWhaP2n1luejRMNSoyv6vijXwjtLjg4NpEaIR_Vju-kusc86HbMg8KDgGIrmY_Avq7hp-JKjWA30xiGvv0vd77z-XQ8rsgYg5QC5TG_JYM0PwfB9IdJvljPj7hqm1KmepOSdbddIKW2_7PPTuIdKKUOsjD1EbSOK3S_KQTsCmc-r8uue0MRms-kMSl7Z7h0GIxB5CpEo6CvcMyWCGAAF63lBr96sl1PB86CtcGad0stEXeARB2TmM-YEMfkNTpJcAsj_vDas', 'alt': 'Modern facade of a trendy artisan pizza restaurant' },
    { 'name': 'Ichiran Ramen - Authentic', 'cuisine': 'Mì Ramen, Sashimi, Donburi', 'rating': '4.9', 'time': '15-25 phút', 'fee': '15k', 'dist': '0.8km', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuBYzJ0anHstS8aVXFgVZlmZWQWtaobKcYphzqlYAkIeTExSyobDO2C5DpJD99PfPhOuxvKn1EyzBEpGWiw3jrf4xiFRhQkjMFShOmzxk39sKXUG6UUEsSgLs1tmngwxBXYN8kCypJrApIHrl8M8eftVHUmt9SRK_Kk2beEKFDCNuWXw0jXiZeZG2jPJXPYnyv_ooPeFk54lEtxxGf7uYfDSpD78kPpJncagjxQqB_Ett2M1B6lLoXg23O_XVK0HD1r6HOLjlmn33L8', 'alt': 'Interior of a traditional Japanese ramen shop' },
    { 'name': 'TocoToco Bubble Tea', 'cuisine': 'Trà sữa, Trà trái cây, Snack', 'rating': '4.7', 'time': '10-20 phút', 'fee': '10k', 'dist': '0.5km', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuC5IwZC0GS9I4CV4rhhgyXdorBW2NBcACy0hOut3gmLWxlGv7biALu3hKn0CRpI63CTC_AoeS6h4sGVdZDBqPiRyDXgMziOEXFqkloyO2t-FzEK29Be3iR_RK509aYbcqTExcc5RGC7-4lVzsfYUV9h3YYWo4rCvNFDKnwDrAPyQRHhRrI3-fH1AnDJYYuTpNtk1qcGK6p3i9xOVCEGCqsUWR3VcvIxNOtwc_7a7J5zNJBC-F23h0JuypzjKBuulb9yjVxn2c0XC1w', 'alt': 'A colorful milk tea shop interior' },
    { 'name': 'Phở Hà Nội - Authentic Vietnamese', 'cuisine': 'Phở, Bún, Nem rán', 'rating': '4.6', 'time': '20-35 phút', 'fee': '20k', 'dist': '1.5km', 'img': 'https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=600&q=80', 'alt': 'Street food market stall with steaming pho' },
    { 'name': 'Sushi Master - Nhật Bản', 'cuisine': 'Sushi, Sashimi, Tempura', 'rating': '4.5', 'time': '25-40 phút', 'fee': '30k', 'dist': '2.1km', 'img': 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=600&q=80', 'alt': 'Assorted sushi platter on wooden board' },
    { 'name': 'Burger King - Premium Beef', 'cuisine': 'Burger, Khoai tây, Gà rán', 'rating': '4.3', 'time': '15-20 phút', 'fee': '15k', 'dist': '0.9km', 'img': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&q=80', 'alt': 'Juicy burger with fries' },
    { 'name': 'Tiệm Bánh Mì Phố Cổ', 'cuisine': 'Bánh mì, Xôi, Cháo', 'rating': '4.4', 'time': '10-15 phút', 'fee': '8k', 'dist': '0.3km', 'img': 'https://images.unsplash.com/photo-1553909489-cd47e0907980?w=600&q=80', 'alt': 'Vietnamese banh mi sandwich' },
    { 'name': 'Cơm Niêu Cô Ba', 'cuisine': 'Cơm niêu, Món Việt, Canh', 'rating': '4.2', 'time': '30-45 phút', 'fee': '12k', 'dist': '1.8km', 'img': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&q=80', 'alt': 'Traditional Vietnamese clay pot rice' },
]

const categories = [{ 'icon': 'bia', 'label': 'Pizza' },
{ 'icon': 'ramen_dining', 'label': 'Bún/Phở' },
{ 'icon': 'local_cafe', 'label': 'Trà sữa' },
{ 'icon': 'bakery_dining', 'label': 'Bánh mì' },
{ 'icon': 'lunch_dining', 'label': 'Burger' },
{ 'icon': 'icecream', 'label': 'Tráng miệng' },
{ 'icon': 'restaurant', 'label': 'Cơm văn phòng' },
{ 'icon': 'fastfood', 'label': 'Đồ ăn nhanh' },]

const suggestions = [
    { 'tag': 'Dựa trên lịch sử', 'name': 'Sushi Sake Roll', 'price': '145,000đ', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuCtyNLmRFjdYwSUL-kYk3jCXI2fAgbR9bo5QYrr9caXBmgJf7cdQ2qhnuimRFgFa0IGnXxsqQZg41KTR1jXykmCnVjOvouJ9Q9xmoV9HF0monUtRxVUdJRhs_vqIqcDOcDYYYZmdD2ejgQqZlnD8LlHHyz7JEdSvoAbdnsA8Wa3d7nDWpc_C0UkoekfNurGjWkGnvKoe40agHf7NnKtX7ktwjcQgU5wRe64MQdytJwNUvR3ju1RW8FddGtss-IiU_7sLcqcgdwN5KU', 'alt': 'Overhead shot of spicy salmon roll sushi' },
    { 'tag': 'Ưa thích của bạn', 'name': 'Tagliatelle Basilico', 'price': '120,000đ', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuDM4KVnMi3C5hdKa1l_BTCmhz1ofKq8X-xj1q6PTrcufAyZ6p8P8wFS75TBX-yPYNmU97Rdke-JVW5aqGGaKL-CR9vuGuKGiEbWgBfcgI4-ag3ZiLW46cQ5ui36cZbNjHM3QHi-la2w2SwHjpvyQ6RclGHaetEcdy-Ua8ks5L1jRYNZifH76SeclHDu_i19wz9LZ7RCG4vTtN_4-8kh_POTaCxDnQKlntG4JRmGRucZT9PT6q2CkXf4yb39Smhzs9OXbSRhqKgIfw8', 'alt': 'Close-up of Italian pasta dish' },
    { 'tag': 'Món trưa bán chạy nhất', 'name': 'Combo Cơm Tấm Sườn Bì Chả Đặc Biệt', 'price': '85,000đ', 'old_price': '115,000đ', 'badge': 'HOT DEAL', 'colspan': 'lg:col-span-2', 'big': true, 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuB114Mr47cqdjzVUCzxUD2gMDUqnN4p9K0FdQBwQRn519qUEFmkZGkGwQ-U57aTFxzm0kA8XDgTHcjbTgjTdvWZ8l0JDoP1twJosILRmCvkZQwXvedYgBPvYSm2yz93NItR7gosiL-b2wwvOhXp1UD08Mi_DUBuliPLSZhkJnKIn_vZ83aiFrLhPhHpqL3zBWQXovRboyjOPK_OdhC0P0biwQJIpa2SF4WS4VxZchxhgD0SSfYyRtTS4scy78_20gaPl1knFz1_j80', 'alt': 'Vietnamese broken rice combo' },
]

async function loadTopRecommendations() {
    const res = await fetch('/api/dishes/top-recommendations');
    if (!res.ok) return [];
    const data = await res.json();
    return data.data || [];
}

async function loadRestaurants(){
    const res = await fetch('/api/restaurants/');
    if (!res.ok) {
        throw new Error(`Không thể tải danh sách nhà hàng: ${res.status}`);
    }
    const data = await res.json();
    return data.data;
}

function renderCategoryChips(containerId,data) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    data.forEach(c => {
        const btn = document.createElement('button');
        btn.className = 'flex flex-col items-center gap-3 shrink-0 group';
        btn.innerHTML = `
            <div class="w-16 h-16 rounded-2xl bg-surface-container-high flex items-center justify-center group-hover:bg-primary-container transition-all group-hover:scale-110">
                <span class="material-symbols-outlined text-primary group-hover:text-on-primary-container text-[32px]">${c.icon}</span>
            </div>
            <span class="font-label-md text-label-md">${c.label}</span>`;
        container.appendChild(btn);
    });
}

function renderHeroSection(period) {
    const d = hero_datas[period];
    const container = document.getElementById('hero-section');
    if (!container || !d) return;
    container.innerHTML = `
    <section class="relative overflow-hidden rounded-xl p-lg md:p-xl flex flex-col md:flex-row items-center gap-md" style="background:${d.section_bg}">
    <div class="absolute inset-0 opacity-10 pointer-events-none">
        <div class="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,_rgba(255,255,255,0.2)_0%,_transparent_70%)]"></div>
    </div>
    <div class="z-10 text-center md:text-left flex-1 space-y-4">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full font-label-md text-label-md" style="background-color:${d.chip_bg};color:${d.chip_text}">
            <span class="material-symbols-outlined text-[18px]">${d.icon}</span>
            <span>${d.greeting}</span>
        </div>
        <h1 class="font-display-lg text-headline-lg-mobile md:text-display-lg" style="color:${d.title_color}">${d.title}</h1>
        <p class="font-body-lg text-body-lg max-w-xl" style="color:${d.desc_color}">${d.desc}</p>
        <div class="flex flex-wrap gap-4 pt-4 justify-center md:justify-start">
            <button onclick="document.getElementById('restaurant-scroll')?.scrollIntoView({behavior: 'smooth'})" class="px-8 py-4 rounded-full font-label-md text-label-md font-bold shadow-lg hover:scale-105 transition-all" style="background-color:${d.btn_primary_bg};color:${d.btn_primary_text}">Khám phá ngay</button>
            <button onclick="document.getElementById('suggestions-section')?.scrollIntoView({behavior: 'smooth'})" class="border px-8 py-4 rounded-full font-label-md text-label-md hover:opacity-80 transition-all" style="border-color:${d.btn_secondary_border};color:${d.btn_secondary_text}">Xem menu gợi ý</button>
        </div>
    </div>
    <div class="flex-1 w-full max-w-md">
        <div class="aspect-[4/3] rounded-2xl overflow-hidden shadow-2xl rotate-3 hover:rotate-0 transition-transform duration-500">
            <img class="w-full h-full object-cover" src="${d.img}" alt="${d.img_alt}">
        </div>
    </div>
</section>
    `;

}


function renderSuggestions(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container || !data || data.length === 0) return;
    container.innerHTML = '';
    data.forEach(s => {
        const div = document.createElement('div');
        div.className = 'min-w-[240px] md:min-w-[260px] snap-start shrink-0 cursor-pointer group relative overflow-hidden rounded-2xl bg-white shadow-[0px_4px_20px_rgba(0,0,0,0.05)] hover:shadow-xl hover:-translate-y-2 transition-all duration-300 h-64';
        div.onclick = () => {

            if (s.restaurant_id) {
                window.location.href = `/restaurants/${s.restaurant_id}`;
            }
        };
        div.innerHTML = `
            <img class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
                 src="${s.image || ''}" 
                 onerror="this.src='https://png.pngtree.com/png-vector/20210623/ourmid/pngtree-pho-noodle-vietnamese-food-png-png-image_3508276.jpg'" 
                 alt="${s.name}">
            <div class="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent flex flex-col justify-end p-4 text-white">
                <h3 class="font-headline-md text-headline-md leading-tight line-clamp-1 group-hover:text-primary-fixed transition-colors">${s.name}</h3>
                <div class="mt-2">
                    <span class="font-bold text-primary-fixed text-lg">${Number(s.price || 0).toLocaleString('vi-VN')}đ</span>
                </div>
            </div>`;


        container.appendChild(div);
    });
}


let restaurantCardTemplate = null;

async function loadRestaurantCardTemplate() {
    if (restaurantCardTemplate) return restaurantCardTemplate;
    const res = await fetch('/templates/restaurantCard.html');
    restaurantCardTemplate = await res.text();
    return restaurantCardTemplate;
}

async function renderRestaurantList(containerId, data, layout = 'grid') {
    const container = document.getElementById(containerId);
    if (!container) return;

    const template = await loadRestaurantCardTemplate();
    container.innerHTML = '';

    const wrapperClass = layout === 'carousel'
        ? 'min-w-[350px] md:min-w-[380px] snap-start group bg-white rounded-2xl overflow-hidden shadow-[0px_4px_20px_rgba(0,0,0,0.05)] hover:-translate-y-2 transition-all duration-300 restaurant-card'
        : 'w-full group bg-white rounded-2xl overflow-hidden shadow-[0px_4px_20px_rgba(0,0,0,0.05)] hover:-translate-y-2 transition-all duration-300 restaurant-card';

    data.forEach(r => {
        const innerHtml = template
            .replace(/\{\{id\}\}/g, r.id || '')
            .replace(/\{\{cover_image\}\}/g, r.cover_image || '')
            .replace(/\{\{name\}\}/g, r.name || '')
            .replace(/\{\{cuisine_type\}\}/g, r.cuisine_type || '')
            .replace(/\{\{address\}\}/g, r.address || '')
            .replace(/\{\{opening_time\}\}/g, r.opening_time || '')
            .replace(/\{\{closing_time\}\}/g, r.closing_time || '');

        const wrapper = document.createElement('div');
        wrapper.className = wrapperClass;
        wrapper.innerHTML = innerHtml;
        container.appendChild(wrapper);
    });
}