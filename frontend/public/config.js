window.APP_CONFIG = Object.freeze({
  API_BASE: ["localhost", "127.0.0.1"].includes(window.location.hostname)
    ? "http://localhost:8080"
    : "https://uth-cloudbot.onrender.com"
});
