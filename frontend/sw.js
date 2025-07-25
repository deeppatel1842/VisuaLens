/**
 * VisuaLens Service Worker
 * Provides basic offline functionality and caching
 */

const CACHE_NAME = 'visualens-v1.0.0';
const STATIC_CACHE = 'visualens-static-v1.0.0';

// Files to cache for offline use
const STATIC_FILES = [
    '/',
    '/index.html',
    '/css/reset.css',
    '/css/main.css', 
    '/css/components.css',
    '/css/responsive.css',
    '/js/utils.js',
    '/js/app.js',
    '/assets/favicon.svg'
];

// API endpoints that can work offline (limited functionality)
const API_CACHE = 'visualens-api-v1.0.0';

// Install event - cache static files
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker');
    
    event.waitUntil(
        Promise.all([
            // Cache static files
            caches.open(STATIC_CACHE).then((cache) => {
                console.log('[SW] Caching static files');
                return cache.addAll(STATIC_FILES);
            }),
            
            // Cache API responses
            caches.open(API_CACHE).then((cache) => {
                console.log('[SW] API cache ready');
                return cache;
            })
        ])
    );
    
    // Force activation
    self.skipWaiting();
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    // Take control of all pages
    self.clients.claim();
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Handle static files
    if (STATIC_FILES.includes(url.pathname) || request.destination === 'document') {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                return fetch(request).then((response) => {
                    // Cache successful responses
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(STATIC_CACHE).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                }).catch(() => {
                    // Return offline page for documents
                    if (request.destination === 'document') {
                        return caches.match('/index.html');
                    }
                    
                    // Return empty response for other resources
                    return new Response('', { status: 404 });
                });
            })
        );
        return;
    }
    
    // Handle API requests
    if (url.pathname.startsWith('/api/') || url.origin !== location.origin) {
        event.respondWith(
            fetch(request).then((response) => {
                // Cache successful GET requests
                if (request.method === 'GET' && response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(API_CACHE).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            }).catch(() => {
                // Try to serve from cache
                return caches.match(request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    
                    // Return offline response for API calls
                    return new Response(JSON.stringify({
                        success: false,
                        error: 'Offline',
                        details: 'This feature requires an internet connection'
                    }), {
                        status: 503,
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                });
            })
        );
        return;
    }
    
    // Default fetch for other requests
    event.respondWith(fetch(request));
});

// Background sync for failed requests (when supported)
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync:', event.tag);
    
    if (event.tag === 'retry-failed-requests') {
        event.waitUntil(retryFailedRequests());
    }
});

// Handle push notifications (for future use)
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');
    
    const options = {
        body: event.data ? event.data.text() : 'New update available',
        icon: '/assets/favicon.svg',
        badge: '/assets/favicon.svg',
        vibrate: [200, 100, 200],
        data: {
            url: '/'
        }
    };
    
    event.waitUntil(
        self.registration.showNotification('VisuaLens', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked');
    
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data.url || '/')
    );
});

// Utility functions
async function retryFailedRequests() {
    // Implementation for retrying failed requests
    console.log('[SW] Retrying failed requests...');
    
    // This would typically involve reading from IndexedDB
    // and retrying failed API calls when online
}

// Message handling for communication with main app
self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);
    
    if (event.data && event.data.type) {
        switch (event.data.type) {
            case 'SKIP_WAITING':
                self.skipWaiting();
                break;
                
            case 'GET_VERSION':
                event.ports[0].postMessage({
                    version: CACHE_NAME
                });
                break;
                
            case 'CLEAR_CACHE':
                clearAllCaches().then(() => {
                    event.ports[0].postMessage({
                        success: true
                    });
                });
                break;
                
            default:
                console.log('[SW] Unknown message type:', event.data.type);
        }
    }
});

async function clearAllCaches() {
    const cacheNames = await caches.keys();
    return Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
}

console.log('[SW] Service worker script loaded');
