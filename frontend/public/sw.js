/**
 * RAHAT Progressive Web App (PWA) Service Worker.
 * Caches static application assets, UI shells, stylesheets, and fonts for offline operation.
 * NOTE: Strictly bypasses and NEVER caches raw API responses (/api/*) to guarantee data privacy.
 */

const CACHE_NAME = "rahat-static-v1";

const STATIC_ASSETS = [
  "/",
  "/favicon.ico",
  "/manifest.json",
];

// Install Event: Pre-cache core static shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate Event: Clean old cache versions
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch Event: Network-first for navigation, Cache-first for static assets, Bypass for API
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // 1. Strictly bypass API endpoints and health checks (handled by IndexedDB/Dexie)
  if (url.pathname.startsWith("/api") || url.pathname.startsWith("/health")) {
    return;
  }

  // 2. Navigation requests: Network first with static cache fallback
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match("/") || caches.match(event.request);
      })
    );
    return;
  }

  // 3. Static assets (_next/static, fonts, icons): Stale-while-revalidate / Cache-first
  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.endsWith(".css") ||
    url.pathname.endsWith(".js") ||
    url.pathname.endsWith(".ico") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".svg")
  ) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          // Revalidate in background
          fetch(event.request)
            .then((networkResponse) => {
              if (networkResponse && networkResponse.status === 200) {
                caches.open(CACHE_NAME).then((cache) => {
                  cache.put(event.request, networkResponse);
                });
              }
            })
            .catch(() => {});
          return cachedResponse;
        }

        return fetch(event.request).then((networkResponse) => {
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== "basic") {
            return networkResponse;
          }
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
          return networkResponse;
        });
      })
    );
  }
});
