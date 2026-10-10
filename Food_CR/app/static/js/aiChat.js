/**
 * aiChat.js — Foodie AI Assistant Widget
 * Floating chat bubble tích hợp Gemini AI tư vấn món ăn cho CraveConnect.
 */

(function () {
    'use strict';

    // ──────────────────────────────────────────────────────────────
    //  State
    // ──────────────────────────────────────────────────────────────
    let conversationHistory = [];
    let isOpen = false;
    let isTyping = false;
    let quickPromptsLoaded = false;

    // ──────────────────────────────────────────────────────────────
    //  DOM References (populated after inject)
    // ──────────────────────────────────────────────────────────────
    let widgetEl, messagesEl, inputEl, sendBtn, fabBtn, badgeEl, typingEl;

    // ──────────────────────────────────────────────────────────────
    //  Widget HTML Template
    // ──────────────────────────────────────────────────────────────
    function createWidgetHTML() {
        return `
        <!-- AI Chat FAB -->
        <button id="ai-chat-fab" aria-label="Mở trợ lý AI"
            class="fixed bottom-24 right-5 md:bottom-8 md:right-8 z-[90] w-14 h-14 rounded-full
                   bg-gradient-to-br from-orange-500 to-red-600 text-white shadow-[0_8px_32px_rgba(169,49,0,0.4)]
                   flex items-center justify-center transition-all duration-300
                   hover:scale-110 hover:shadow-[0_12px_40px_rgba(169,49,0,0.55)]
                   active:scale-95 group">
            <span id="ai-fab-icon" class="material-symbols-outlined text-2xl transition-transform duration-300 group-hover:rotate-12">auto_awesome</span>
            <span id="ai-fab-close-icon" class="material-symbols-outlined text-2xl hidden">close</span>
            <span id="ai-chat-badge"
                class="absolute -top-1 -right-1 w-5 h-5 bg-amber-400 text-on-surface text-[10px] font-black
                       rounded-full flex items-center justify-center shadow-md hidden animate-bounce">AI</span>
        </button>

        <!-- AI Chat Widget Panel -->
        <div id="ai-chat-widget"
            class="fixed bottom-44 right-5 md:bottom-28 md:right-8 z-[89]
                   w-[calc(100vw-40px)] max-w-sm
                   bg-white rounded-3xl shadow-[0_20px_60px_rgba(0,0,0,0.18)]
                   border border-outline-variant/40
                   flex flex-col overflow-hidden
                   transition-all duration-400 ease-[cubic-bezier(.34,1.56,.64,1)]
                   opacity-0 scale-90 origin-bottom-right pointer-events-none"
            style="height: 480px; max-height: calc(100dvh - 180px);">

            <!-- Header -->
            <div class="flex items-center gap-3 px-4 py-3.5
                        bg-gradient-to-r from-orange-600 via-red-600 to-rose-600 text-white shrink-0">
                <div class="w-9 h-9 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center shrink-0">
                    <span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1">auto_awesome</span>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="font-bold text-sm leading-tight">Foodie AI</p>
                    <p class="text-white/70 text-[11px] leading-tight">Trợ lý ẩm thực thông minh</p>
                </div>
                <button id="ai-chat-clear" aria-label="Xóa lịch sử hội thoại"
                    title="Xóa hội thoại"
                    class="w-8 h-8 rounded-full hover:bg-white/20 transition-colors flex items-center justify-center">
                    <span class="material-symbols-outlined text-[18px]">restart_alt</span>
                </button>
            </div>

            <!-- Messages area -->
            <div id="ai-messages"
                class="flex-1 overflow-y-auto px-3 py-3 space-y-3 scroll-smooth"
                style="scrollbar-width: thin; scrollbar-color: #e6beb2 transparent;">
                <!-- Welcome message injected by JS -->
            </div>

            <!-- Typing indicator -->
            <div id="ai-typing-indicator"
                class="hidden px-4 pb-2 flex items-center gap-2 text-on-surface-variant text-xs shrink-0">
                <div class="flex gap-1 items-center">
                    <span class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style="animation-delay:0ms"></span>
                    <span class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style="animation-delay:150ms"></span>
                    <span class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style="animation-delay:300ms"></span>
                </div>
                <span>Foodie AI đang tư vấn...</span>
            </div>

            <!-- Quick prompts -->
            <div id="ai-quick-prompts" class="px-3 pb-2 flex gap-2 overflow-x-auto no-scrollbar shrink-0"></div>

            <!-- Input area -->
            <div class="px-3 pb-3 pt-1 border-t border-outline-variant/30 shrink-0">
                <div class="flex gap-2 items-end bg-surface-container rounded-2xl px-3 py-2">
                    <textarea id="ai-input"
                        rows="1"
                        placeholder="Hỏi Foodie AI về món ăn..."
                        class="flex-1 bg-transparent border-none outline-none resize-none text-sm text-on-surface
                               placeholder:text-on-surface-variant leading-5 max-h-24 overflow-y-auto"
                        style="scrollbar-width: thin;"
                        aria-label="Nhập câu hỏi cho Foodie AI"></textarea>
                    <button id="ai-send-btn" aria-label="Gửi"
                        class="w-8 h-8 rounded-full bg-primary text-on-primary flex items-center justify-center
                               transition-all duration-200 hover:bg-primary-container hover:scale-110
                               active:scale-90 disabled:opacity-40 disabled:cursor-not-allowed shrink-0 mb-0.5">
                        <span class="material-symbols-outlined text-[18px]">send</span>
                    </button>
                </div>
                <p class="text-center text-[10px] text-on-surface-variant/60 mt-1.5">
                    Powered by Gemini AI · Dữ liệu thời gian thực
                </p>
            </div>
        </div>
        `;
    }

    // ──────────────────────────────────────────────────────────────
    //  Message Renderers
    // ──────────────────────────────────────────────────────────────
    function renderMessage(role, text) {
        const isUser = role === 'user';
        const wrapper = document.createElement('div');
        wrapper.className = `flex gap-2 ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in-up`;

        // Format markdown-like bold (**text**), italic (*text*), lists
        const formatted = formatMarkdown(text);

        if (isUser) {
            wrapper.innerHTML = `
                <div class="max-w-[80%] bg-primary text-on-primary rounded-2xl rounded-br-sm px-3.5 py-2.5 text-sm leading-relaxed shadow-sm">
                    ${escapeHTML(text)}
                </div>`;
        } else {
            wrapper.innerHTML = `
                <div class="w-7 h-7 rounded-full bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center shrink-0 mt-0.5">
                    <span class="material-symbols-outlined text-white text-[14px]" style="font-variation-settings: 'FILL' 1">auto_awesome</span>
                </div>
                <div class="max-w-[82%] bg-surface-container rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm leading-relaxed shadow-sm text-on-surface">
                    ${formatted}
                </div>`;
        }

        messagesEl.appendChild(wrapper);
        scrollToBottom();
        return wrapper;
    }

    function renderWelcomeMessage() {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex gap-2 justify-start';
        wrapper.innerHTML = `
            <div class="w-7 h-7 rounded-full bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center shrink-0 mt-0.5">
                <span class="material-symbols-outlined text-white text-[14px]" style="font-variation-settings: 'FILL' 1">auto_awesome</span>
            </div>
            <div class="max-w-[85%] space-y-1.5">
                <div class="bg-surface-container rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm leading-relaxed shadow-sm text-on-surface">
                    👋 Xin chào! Tôi là <strong>Foodie AI</strong> — trợ lý ẩm thực của CraveConnect.<br><br>
                    Tôi có thể giúp bạn tìm món ăn ngon, gợi ý nhà hàng phù hợp theo tâm trạng, ngân sách hoặc khẩu vị. 🍜
                </div>
            </div>`;
        messagesEl.appendChild(wrapper);
    }

    function formatMarkdown(text) {
        return escapeHTML(text)
            // Bold: **text**
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic: *text*
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Inline code: `text`
            .replace(/`([^`]+)`/g, '<code class="bg-outline-variant/30 px-1 rounded text-xs font-mono">$1</code>')
            // Headings: ### text
            .replace(/^### (.+)$/gm, '<p class="font-bold text-primary mt-2 mb-0.5">$1</p>')
            // Unordered list items: - text
            .replace(/^[-•] (.+)$/gm, '<li class="ml-3 list-disc">$1</li>')
            // Newlines to <br>
            .replace(/\n/g, '<br>');
    }

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function scrollToBottom() {
        setTimeout(() => {
            if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
        }, 50);
    }

    // ──────────────────────────────────────────────────────────────
    //  Quick Prompts
    // ──────────────────────────────────────────────────────────────
    async function loadQuickPrompts() {
        if (quickPromptsLoaded) return;
        const container = document.getElementById('ai-quick-prompts');
        if (!container) return;

        try {
            const res = await fetch('/api/ai/quick-prompts');
            const json = await res.json();
            if (!json.success) return;

            json.prompts.forEach(p => {
                const btn = document.createElement('button');
                btn.className = `shrink-0 text-[11px] px-2.5 py-1.5 rounded-full border border-outline-variant
                                  bg-surface-container hover:bg-primary-container hover:border-primary
                                  hover:text-on-primary-container text-on-surface-variant
                                  transition-all duration-200 whitespace-nowrap`;
                btn.textContent = `${p.icon} ${p.text}`;
                btn.addEventListener('click', () => {
                    if (inputEl) {
                        inputEl.value = p.text;
                        autoResize(inputEl);
                        inputEl.focus();
                        // hide quick prompts after selection
                        container.classList.add('hidden');
                    }
                });
                container.appendChild(btn);
            });
            quickPromptsLoaded = true;
        } catch (e) {
            console.warn('[AiChat] Không tải được quick prompts:', e);
        }
    }

    // ──────────────────────────────────────────────────────────────
    //  Send message
    // ──────────────────────────────────────────────────────────────
    async function sendMessage() {
        if (isTyping) return;
        const text = (inputEl.value || '').trim();
        if (!text) return;

        // Clear input
        inputEl.value = '';
        autoResize(inputEl);

        // Hide quick prompts after first user message
        const qp = document.getElementById('ai-quick-prompts');
        if (qp) qp.classList.add('hidden');

        // Render user bubble
        renderMessage('user', text);

        // Add to history
        conversationHistory.push({ role: 'user', parts: [text] });

        // Show typing indicator
        isTyping = true;
        sendBtn.disabled = true;
        typingEl.classList.remove('hidden');
        scrollToBottom();

        try {
            const res = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    // send previous history (excluding last user message we just added)
                    history: conversationHistory.slice(0, -1),
                }),
            });

            let json = {};
            try {
                json = await res.json();
            } catch (parseErr) {
                console.warn('[AiChat] Phản hồi không phải JSON:', parseErr);
            }

            typingEl.classList.add('hidden');
            isTyping = false;
            sendBtn.disabled = false;

            if (res.ok && json.success) {
                renderMessage('model', json.reply);
                conversationHistory.push({ role: 'model', parts: [json.reply] });
            } else if (res.status === 401) {
                renderMessage('model', '🔐 Bạn cần đăng nhập để sử dụng Foodie AI nhé!');
            } else {
                renderMessage('model', `⚠️ ${json.message || 'Có lỗi xảy ra, vui lòng thử lại sau.'}`);
            }
        } catch (e) {
            typingEl.classList.add('hidden');
            isTyping = false;
            sendBtn.disabled = false;
            renderMessage('model', '⚠️ Mất kết nối, vui lòng thử lại.');
            console.error('[AiChat] Lỗi fetch:', e);
        }
    }

    // ──────────────────────────────────────────────────────────────
    //  Toggle open/close
    // ──────────────────────────────────────────────────────────────
    function openWidget() {
        isOpen = true;
        widgetEl.classList.remove('opacity-0', 'scale-90', 'pointer-events-none');
        widgetEl.classList.add('opacity-100', 'scale-100');
        fabBtn.querySelector('#ai-fab-icon').classList.add('hidden');
        fabBtn.querySelector('#ai-fab-close-icon').classList.remove('hidden');
        badgeEl.classList.add('hidden');
        loadQuickPrompts();
        setTimeout(() => inputEl && inputEl.focus(), 300);
        scrollToBottom();
    }

    function closeWidget() {
        isOpen = false;
        widgetEl.classList.add('opacity-0', 'scale-90', 'pointer-events-none');
        widgetEl.classList.remove('opacity-100', 'scale-100');
        fabBtn.querySelector('#ai-fab-icon').classList.remove('hidden');
        fabBtn.querySelector('#ai-fab-close-icon').classList.add('hidden');
    }

    function toggleWidget() {
        if (isOpen) closeWidget();
        else openWidget();
    }

    // ──────────────────────────────────────────────────────────────
    //  Auto-resize textarea
    // ──────────────────────────────────────────────────────────────
    function autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 96) + 'px';
    }

    // ──────────────────────────────────────────────────────────────
    //  Clear conversation
    // ──────────────────────────────────────────────────────────────
    function clearConversation() {
        conversationHistory = [];
        messagesEl.innerHTML = '';
        renderWelcomeMessage();
        const qp = document.getElementById('ai-quick-prompts');
        if (qp) {
            qp.classList.remove('hidden');
        }
    }

    // ──────────────────────────────────────────────────────────────
    //  Inject & Init
    // ──────────────────────────────────────────────────────────────
    function init() {
        // Inject HTML
        const container = document.createElement('div');
        container.id = 'ai-chat-root';
        container.innerHTML = createWidgetHTML();
        document.body.appendChild(container);

        // Grab DOM refs
        widgetEl = document.getElementById('ai-chat-widget');
        messagesEl = document.getElementById('ai-messages');
        inputEl = document.getElementById('ai-input');
        sendBtn = document.getElementById('ai-send-btn');
        fabBtn = document.getElementById('ai-chat-fab');
        badgeEl = document.getElementById('ai-chat-badge');
        typingEl = document.getElementById('ai-typing-indicator');

        // Initial welcome
        renderWelcomeMessage();

        // Show badge after 2s to attract attention (only first time)
        setTimeout(() => {
            if (!isOpen && badgeEl) badgeEl.classList.remove('hidden');
        }, 2000);

        // Event listeners
        fabBtn.addEventListener('click', toggleWidget);

        document.getElementById('ai-chat-clear').addEventListener('click', clearConversation);

        sendBtn.addEventListener('click', sendMessage);

        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        inputEl.addEventListener('input', () => autoResize(inputEl));

        // Close on ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) closeWidget();
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (isOpen &&
                !widgetEl.contains(e.target) &&
                !fabBtn.contains(e.target)) {
                closeWidget();
            }
        });

        // Inject animation CSS
        if (!document.getElementById('ai-chat-styles')) {
            const style = document.createElement('style');
            style.id = 'ai-chat-styles';
            style.textContent = `
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(8px); }
                    to   { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in-up {
                    animation: fadeInUp 0.25s ease forwards;
                }
                #ai-messages::-webkit-scrollbar { width: 4px; }
                #ai-messages::-webkit-scrollbar-track { background: transparent; }
                #ai-messages::-webkit-scrollbar-thumb { background: #e6beb2; border-radius: 4px; }
                #ai-chat-widget { transition: opacity 0.25s ease, transform 0.35s cubic-bezier(.34,1.56,.64,1); }
            `;
            document.head.appendChild(style);
        }
    }

    // Boot when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
