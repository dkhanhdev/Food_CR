// ============ 1. Config ============
const firebaseConfig = {
  apiKey: "AIzaSyD-PLWV-35PFcqzF7wyD9F655rtPpwxj68",
  authDomain: "foodie-ef6b6.firebaseapp.com",
  projectId: "foodie-ef6b6",
  storageBucket: "foodie-ef6b6.firebasestorage.app",
  messagingSenderId: "113694762167",
  appId: "1:113694762167:web:3fb9f2989bd3b3ec795932",
  measurementId: "G-7R1ZFKDE6W"
};

const VAPID_KEY = window.FIREBASE_VAPID_KEY;
const SAVE_TOKEN_ENDPOINT = "/api/fcm/save-token";

// ============ 2. Khởi tạo ============
const messaging = firebase.messaging();

// ============ 3. Đăng ký Service Worker ============
async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    console.warn("Trình duyệt không hỗ trợ Service Worker.");
    return null;
  }
  return await navigator.serviceWorker.register("/firebase-messaging-sw.js");
}

// ============ 4. Xin quyền + lấy token ============
async function requestPermissionAndGetToken() {
  try {
    const permission = await Notification.requestPermission();

    if (permission !== "granted") {
      console.log("Người dùng chưa cho phép nhận thông báo.");
      return;
    }

    const registration = await registerServiceWorker();

    const token = await messaging.getToken({
      vapidKey: VAPID_KEY,
      serviceWorkerRegistration: registration,
    });

    if (!token) {
      console.warn("Không lấy được FCM token.");
      return;
    }

    const userId = localStorage.getItem("user_id") || "guest";
    const cached = localStorage.getItem("fcm_token");
    if (cached === token && localStorage.getItem("fcm_user_id") === userId) {
      return;
    }

    console.log("Đã lấy FCM token:", token);
    await sendTokenToBackend(token);

    localStorage.setItem("fcm_token", token);
    localStorage.setItem("fcm_user_id", userId);

  } catch (err) {
    console.error("Lỗi khi lấy FCM token:", err);
  }
}

// ============ 5. Gửi token lên backend ============
function getOrCreateDeviceId() {
  let deviceId = localStorage.getItem("device_id");
  if (!deviceId) {
    deviceId = "web-" + crypto.randomUUID();
    localStorage.setItem("device_id", deviceId);
  }
  return deviceId;
}

async function sendTokenToBackend(token) {
  const deviceId = getOrCreateDeviceId();
  const userId = localStorage.getItem("user_id") || "guest";

  const res = await fetch(SAVE_TOKEN_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ token, device_id: deviceId, platform: "web", user_id: userId }),
  });

  if (!res.ok) {
    console.error("Gửi token lên backend thất bại:", res.status);
    return;
  }
  console.log("Đã gửi token lên backend thành công.");
}

// ============ 6. Cập nhật badge số chưa đọc ============
async function updateUnreadBadge() {
  const userId = localStorage.getItem("user_id");
  const badge = document.getElementById("notif-badge");
  if (!userId || !badge) return;

  try {
    const res = await fetch("/api/fcm/unread-count?user_id=" + userId);
    const data = await res.json();
    const count = data.unread_count || 0;
    if (count > 0) {
      badge.textContent = count;
      badge.classList.remove("hidden");
    } else {
      badge.classList.add("hidden");
    }
  } catch (err) {
    console.error("Lỗi cập nhật badge:", err);
  }
}

// ============ 7. Nhận thông báo khi tab đang mở ============
messaging.onMessage((payload) => {
  const { title, body, category } = payload.data || {};
  console.log(title)
  if (title) {
    new Notification(title, { body });
    if (typeof window.showToast === "function") {
      window.showToast(body || title, category || "info");
    }
  }
  updateUnreadBadge();
});

// ============ 8. TỰ ĐỘNG CHẠY khi trang load ============
document.addEventListener("DOMContentLoaded", () => {
  requestPermissionAndGetToken();
  updateUnreadBadge();
});