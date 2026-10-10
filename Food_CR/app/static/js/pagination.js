var currentPage = 1;
var totalPages = 1;

function renderPagination() {
    var pagination = document.getElementById('dish-pagination');
    var prevBtn = document.getElementById('page-prev');
    var nextBtn = document.getElementById('page-next');
    var numbers = document.getElementById('page-numbers');
    if (!pagination || !numbers) return;

    if (totalPages <= 1) {
        pagination.classList.add('hidden');
        return;
    }
    pagination.classList.remove('hidden');

    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;

    numbers.innerHTML = '';
    var start = Math.max(1, currentPage - 2);
    var end = Math.min(totalPages, currentPage + 2);

    if (start > 1) {
        numbers.appendChild(createPageBtn(1));
        if (start > 2) numbers.appendChild(createEllipsis());
    }
    for (var i = start; i <= end; i++) {
        numbers.appendChild(createPageBtn(i));
    }
    if (end < totalPages) {
        if (end < totalPages - 1) numbers.appendChild(createEllipsis());
        numbers.appendChild(createPageBtn(totalPages));
    }
}

function createPageBtn(page) {
    var btn = document.createElement('button');
    btn.textContent = page;
    btn.className = 'w-8 h-8 rounded-lg text-sm font-label-md transition-all ' +
        (page === currentPage
            ? 'bg-primary text-white'
            : 'text-secondary hover:bg-surface-container-highest');
    btn.addEventListener('click', function () { goToPage(page); });
    return btn;
}

function createEllipsis() {
    var span = document.createElement('span');
    span.textContent = '...';
    span.className = 'px-1 text-secondary text-sm';
    return span;
}

function bindPaginationButtons() {
    document.getElementById('page-prev').addEventListener('click', function () {
        goToPage(currentPage - 1);
    });
    document.getElementById('page-next').addEventListener('click', function () {
        goToPage(currentPage + 1);
    });
}
