// File này BẮT BUỘC đặt ở thư mục gốc (root) của web, không đặt trong thư mục con
// vì scope mặc định của Service Worker là nơi file này được đặt.

importScripts("https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.14.1/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyD-PLWV-35PFcqzF7wyD9F655rtPpwxj68",
  authDomain: "foodie-ef6b6.firebaseapp.com",
  projectId: "foodie-ef6b6",
  storageBucket: "foodie-ef6b6.firebasestorage.app",
  messagingSenderId: "113694762167",
  appId: "1:113694762167:web:3fb9f2989bd3b3ec795932",
  measurementId: "G-7R1ZFKDE6W"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const notificationTitle = payload.data?.title || "Thông báo mới";
  const notificationOptions = {
    body: payload.data?.body || "",
    icon: "/icon.png",
  };
  self.registration.showNotification(notificationTitle, notificationOptions);
});