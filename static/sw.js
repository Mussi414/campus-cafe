// Campus Café service worker: gør appen installerbar og viser en offline-besked.
const CACHE = "campus-cafe-v2";
const SHELL = ["/static/style.css", "/static/app.js", "/static/icon.svg", "/static/images/iba-aften.jpg"];

self.addEventListener("install", (e) => {
    e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
    e.waitUntil(
        caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (e) => {
    if (e.request.method !== "GET") return;
    // Netværk først, så cache: nye versioner af CSS/JS kommer altid igennem,
    // og cachen bruges kun, når man er offline.
    e.respondWith(
        fetch(e.request)
            .then((res) => {
                const kopi = res.clone();
                caches.open(CACHE).then((c) => c.put(e.request, kopi));
                return res;
            })
            .catch(() => caches.match(e.request).then((hit) => hit || new Response(
                "<h1 style='font-family:sans-serif;text-align:center;margin-top:40vh'>Du er offline</h1>",
                { headers: { "Content-Type": "text/html; charset=utf-8" } }
            )))
    );
});
