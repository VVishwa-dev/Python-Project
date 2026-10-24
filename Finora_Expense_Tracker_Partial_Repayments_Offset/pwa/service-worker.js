// Starter service worker for a future PWA frontend.
// Do not register this from a Streamlit component iframe: the worker must be
// served from the app origin/root by a frontend or reverse proxy.
self.addEventListener("install", event => self.skipWaiting());
self.addEventListener("activate", event => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", event => {
  // Financial pages are intentionally network-only; never cache private financial data.
  if (event.request.method !== "GET") return;
  event.respondWith(fetch(event.request));
});
