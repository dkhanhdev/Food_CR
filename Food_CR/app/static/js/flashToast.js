(function () {
  var AUTO_DISMISS_MS = 5000;
  var DISMISS_DURATION = 300;

  // Dùng bảng màu Tailwind CHUẨN (emerald/red/amber/blue) — luôn có sẵn qua CDN,
  // không phụ thuộc token tùy biến trong tailwind.config, tránh mất màu như ảnh chụp.
  var TOAST_CONFIG = {
    success: { icon: 'check_circle', title: 'Thành công',     accent: 'bg-emerald-500', iconbg: 'bg-emerald-100', icontext: 'text-emerald-600', border: 'border-emerald-200', bar: 'bg-emerald-500' },
    error:   { icon: 'error',        title: 'Có lỗi xảy ra',  accent: 'bg-red-500',     iconbg: 'bg-red-100',     icontext: 'text-red-600',     border: 'border-red-200',     bar: 'bg-red-500' },
    danger:  { icon: 'error',        title: 'Có lỗi xảy ra',  accent: 'bg-red-500',     iconbg: 'bg-red-100',     icontext: 'text-red-600',     border: 'border-red-200',     bar: 'bg-red-500' },
    warning: { icon: 'warning',      title: 'Cảnh báo',       accent: 'bg-amber-500',   iconbg: 'bg-amber-100',   icontext: 'text-amber-600',   border: 'border-amber-200',   bar: 'bg-amber-500' },
    info:    { icon: 'info',         title: 'Thông báo',      accent: 'bg-blue-500',    iconbg: 'bg-blue-100',    icontext: 'text-blue-600',    border: 'border-blue-200',    bar: 'bg-blue-500' }
  };

  var style = document.createElement('style');
  style.textContent =
    '.toast{' +
      'transition:opacity ' + DISMISS_DURATION + 'ms ease,transform ' + DISMISS_DURATION + 'ms ease,box-shadow 0.2s ease;' +
    '}' +
    '.toast.is-leaving{' +
      'opacity:0;transform:translateX(100%) scale(0.98);' +
    '}' +
    '@keyframes toast-timer{' +
      'from{width:100%}to{width:0}' +
    '}' +
    '.toast__timer{' +
      'animation:toast-timer ' + AUTO_DISMISS_MS + 'ms linear forwards;' +
    '}' +
    '.toast:hover .toast__timer{' +
      'animation-play-state:paused;' +
    '}';
  document.head.appendChild(style);

  function dismiss(toast) {
    if (!toast || toast.classList.contains('is-leaving')) return;
    toast.classList.add('is-leaving');
    setTimeout(function () { toast.remove(); }, DISMISS_DURATION);
  }

  function wireUpToast(toast) {
    var timer = setTimeout(function () { dismiss(toast); }, AUTO_DISMISS_MS);

    toast.addEventListener('mouseenter', function () { clearTimeout(timer); });
    toast.addEventListener('mouseleave', function () {
      timer = setTimeout(function () { dismiss(toast); }, AUTO_DISMISS_MS);
    });

    var closeBtn = toast.querySelector('.toast__close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        clearTimeout(timer);
        dismiss(toast);
      });
    }
  }

  // Cùng cấu trúc/markup với khối Jinja render trong base.html — để toast tạo
  // bằng JS (push notification foreground) và toast từ flash() nhìn giống hệt nhau.
  window.showToast = function (message, category) {
    var container = document.getElementById('toast-container');
    if (!container) return;

    var c = TOAST_CONFIG[category] || TOAST_CONFIG.info;

    var toast = document.createElement('div');
    toast.className = 'toast group relative pointer-events-auto flex overflow-hidden ' +
      'bg-white/95 backdrop-blur-xl border ' + c.border + ' rounded-2xl ' +
      'shadow-[0_12px_40px_rgba(0,0,0,0.12)] transition-all duration-300 ' +
      'hover:-translate-y-0.5 hover:shadow-[0_16px_48px_rgba(0,0,0,0.16)]';

    toast.innerHTML =
      '<div class="absolute left-0 top-0 bottom-0 w-1 ' + c.accent + '"></div>' +
      '<div class="flex items-start gap-3.5 w-full p-4 pl-5 pr-10">' +
        '<div class="shrink-0 flex items-center justify-center w-10 h-10 rounded-xl ' + c.iconbg + '">' +
          '<span class="material-symbols-outlined text-[22px] ' + c.icontext + '">' + c.icon + '</span>' +
        '</div>' +
        '<div class="flex-1 min-w-0 pt-0.5">' +
          '<p class="text-sm font-semibold text-slate-800 leading-5">' + c.title + '</p>' +
          '<p class="toast__message mt-1 text-sm text-slate-600 leading-5 break-words"></p>' +
        '</div>' +
        '<button type="button" aria-label="Đóng thông báo" ' +
          'class="toast__close absolute top-3 right-3 flex items-center justify-center ' +
          'w-7 h-7 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-all duration-200">' +
          '<span class="material-symbols-outlined text-[19px]">close</span>' +
        '</button>' +
      '</div>' +
      '<div class="toast__timer absolute left-0 bottom-0 h-[3px] w-full ' + c.bar + ' opacity-70"></div>';

    // set message bằng textContent để tránh XSS nếu message đến từ nguồn ngoài (payload push)
    toast.querySelector('.toast__message').textContent = message;

    container.appendChild(toast);
    wireUpToast(toast);
  };

  document.addEventListener('DOMContentLoaded', function () {
    var toasts = document.querySelectorAll('#toast-container .toast');
    toasts.forEach(wireUpToast);
  });
})();