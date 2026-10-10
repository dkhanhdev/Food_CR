// firebase-chat-core.js
// Load SAU firebase-config.js và SAU 3 script SDK sau trong <head> hoặc
// cuối <body>:
//   <script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js"></script>
//   <script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js"></script>
//   <script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore-compat.js"></script>
//   <script src="/static/js/firebase-config.js"></script>
//   <script src="/static/js/firebase-chat-core.js"></script>

firebase.initializeApp(FIREBASE_CONFIG);

const auth = firebase.auth();
const db = firebase.firestore();

let currentUid = null;
let firebaseReady = false;

// ---------------------------------------------------------------------
// KẾT NỐI FIREBASE — 2 CÁCH GỌI
// ---------------------------------------------------------------------

/**
 * Cách 1 (khuyến nghị, nhanh nhất): gọi ngay khi trang login trả về
 * response có kèm firebase_token (đã gộp vào route /login backend).
 *
 * Dùng khi: ngay sau khi submit form login thành công bằng AJAX.
 */
async function signInFirebaseFromToken(firebaseToken, uid) {
    try {
        await auth.signInWithCustomToken(firebaseToken);
        currentUid = String(uid);
        firebaseReady = true;
        document.dispatchEvent(
            new CustomEvent("firebase-ready", { detail: { uid: currentUid } })
        );
    } catch (err) {
        console.error("Đăng nhập Firebase thất bại:", err);
    }
}

/**
 * Sign-in Firebase từ token nhúng trong HTML (context processor).
 * Không cần API call — token được inject trực tiếp khi render template.
 */
function signInFromEmbeddedToken() {
    if (firebaseReady) return;
    const token = window.__FIREBASE_TOKEN__;
    const uidMeta = document.querySelector('meta[name="user-id"]');
    if (token && uidMeta) {
        signInFirebaseFromToken(token, uidMeta.content);
    }
}

// Tự động sign-in khi trang load — dùng token nhúng trong HTML
document.addEventListener("DOMContentLoaded", signInFromEmbeddedToken);

// ---------------------------------------------------------------------
// ĐĂNG XUẤT — đồng bộ Firebase + Flask
// ---------------------------------------------------------------------

async function logoutFirebaseAndFlask() {
    // Dừng mọi listener chat đang mở trước, tránh lỗi permission-denied
    // bắn ra console sau khi signOut
    if (typeof unsubscribeMessages === "function") unsubscribeMessages();

    try {
        await fetch("/api/chats/logout", { method: "POST" });
    } catch (err) {
        console.error("Lỗi gọi API logout:", err);
    }

    await auth.signOut();
    window.location.href = "/login";
}

// ---------------------------------------------------------------------
// TẠO / MỞ CHAT 1-1
// ---------------------------------------------------------------------

async function startDirectChat(otherUserId) {
    if (!firebaseReady) {
        console.warn("Firebase chưa sẵn sàng, thử lại sau.");
        return;
    }

    const res = await fetch("/api/chats/direct", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ other_user_id: otherUserId }),
    });
    const data = await res.json();
    if (!res.ok) {
        showToast(data.error, "error");
        return;
    }
    openChat(data.chatId);
}

// ---------------------------------------------------------------------
// DANH SÁCH CHAT CỦA TÔI
// ---------------------------------------------------------------------

async function loadMyChats() {
    // Placeholder — chatPage.html sẽ override trong firebase-ready
}

// ---------------------------------------------------------------------
// MỞ 1 PHÒNG CHAT + LẮNG NGHE TIN NHẮN REAL-TIME
// ---------------------------------------------------------------------

let currentChatId = null;
let unsubscribeMessages = null;

function openChat(chatId) {
    currentChatId = chatId;

    console.log(currentChatId)

    const header = document.getElementById("chat-header");
    if (header) header.textContent = "Đang chat: " + chatId;

    const msgInput = document.getElementById("msg-input");
    const sendBtn = document.getElementById("send-btn");
    if (msgInput) msgInput.disabled = false;
    if (sendBtn) sendBtn.disabled = false;

    document.querySelectorAll(".chat-item").forEach((el) => {
        el.classList.toggle("active", el.dataset.chatId === chatId);
    });

    if (unsubscribeMessages) unsubscribeMessages();

    const messagesEl = document.getElementById("messages");
    if (messagesEl) messagesEl.innerHTML = "";

    unsubscribeMessages = db
        .collection("chats")
        .doc(chatId)
        .collection("messages")
        .orderBy("createdAt", "asc")
        .onSnapshot(
            (snapshot) => {
                snapshot.docChanges().forEach((change) => {
                    if (change.type === "added") renderMessage(change.doc.data());
                });
                if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
            },
            (err) => {
                console.error("Lỗi lắng nghe tin nhắn:", err);
            }
        );

}

function renderMessage(msg) {
    const messagesEl = document.getElementById("messages");
    if (!messagesEl) return;

    const div = document.createElement("div");
    div.className = "msg" + (msg.senderId === currentUid ? " mine" : "");
    div.innerHTML = `<div class="sender">User #${escapeHtml(
        msg.senderId
    )}</div>${escapeHtml(msg.text)}`;
    messagesEl.appendChild(div);
}

function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
}

// ---------------------------------------------------------------------
// GỬI TIN NHẮN — ghi thẳng vào Firestore (Security Rules kiểm soát quyền)
// ---------------------------------------------------------------------

async function sendMessage() {
    const msgInput = document.getElementById("msg-input");
    if (!msgInput) return;

    const text = msgInput.value.trim();
    if (!text || !currentChatId) return;

    try {
        await db.collection("chats").doc(currentChatId).collection("messages").add({
            senderId: currentUid,
            text: text,
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
        });
        msgInput.value = "";
    } catch (err) {
        console.error("Gửi tin nhắn thất bại:", err);
        showToast("Không gửi được tin nhắn, thử lại sau.", "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const sendBtn = document.getElementById("send-btn");
    const msgInput = document.getElementById("msg-input");

    if (sendBtn) sendBtn.addEventListener("click", sendMessage);
    if (msgInput) {
        msgInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }
});