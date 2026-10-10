// firebase-auth-init.js
// Lightweight Firebase Auth init — dùng cho login page.
// Yêu cầu load trước: firebase-app-compat.js, firebase-auth-compat.js, firebase-config.js

firebase.initializeApp(FIREBASE_CONFIG);
const auth = firebase.auth();

async function signInFirebaseFromToken(firebaseToken, uid) {
  try {
    await auth.signInWithCustomToken(firebaseToken);
  } catch (err) {
    console.error("Đăng nhập Firebase thất bại:", err);
  }
}
