const loadingState = {
    count: 0,

    show() {
        this.count += 1;
        document.getElementById('global-loading')?.classList.remove('hidden');
    },

    hide() {
        this.count = Math.max(0, this.count - 1);

        if (this.count === 0) {
            document.getElementById('global-loading')?.classList.add('hidden');
        }
    },

    async run(task) {
        this.show();

        try {
            return await task();
        } finally {
            this.hide();
        }
    }
};

window.loadingState = loadingState;

async function searchRestaurants(keyword) {
    const url = '/api/search/?q=' + encodeURIComponent(keyword);
    const res = await fetch(url);
    if (!res.ok) throw new Error('Search failed: ' + res.status);
    return res.json();
}

function goToRestaurantDetail(id) {
    console.log("Navigating to restaurant detail for id:", id);
    window.location.href = `/restaurants/${id}`;
}