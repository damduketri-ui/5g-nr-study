/* 5G NR 통신 이해 — 오프라인 캐시
   ------------------------------------------------------------------
   목적: 인터넷이 될 때 자료를 통째로 받아 두고, 안 될 때도 읽히게 한다.

   경로에 대하여
     GitHub Pages는 이 사이트를 /5g-nr-study/ 아래에 올린다.
     이 파일이 그 폴더에 있으므로 아래의 './...' 는 전부 그 폴더 기준으로 풀린다.
     스코프도 자동으로 /5g-nr-study/ 가 되어 별도 헤더가 필요 없다.

   자료를 고치면 VERSION을 올려야 한다
     캐시 우선으로 내주기 때문에, 버전을 안 올리면 단말에 옛날 것이 남는다.
     새 자료를 추가하면 PAGES에도 넣어야 한다 —
     빠뜨리면 그 자료만 오프라인에서 안 열린다.
     tools/verify-numbers.py 의 check_offline() 이 이 목록을 대조한다. */

const VERSION = '2026-09-05c';
const CACHE = 'nr-study-' + VERSION;

/* 미리 받아 둘 것 — 자료 19개와 목차, 공통 스타일 */
const PAGES = [
  './',
  './index.html',
  './assets/base.css',
  './topics/01-frame-numerology/index.html',
  './topics/02-tdd-pattern/index.html',
  './topics/03-cyclic-prefix/index.html',
  './topics/04-ssb-initial-access/index.html',
  './topics/05-bandwidth-part/index.html',
  './topics/06-harq-timing/index.html',
  './topics/07-beamforming/index.html',
  './topics/08-random-access/index.html',
  './topics/09-precoding-codebook/index.html',
  './topics/10-physical-layer-chain/index.html',
  './topics/11-reference-signals/index.html',
  './topics/12-pdcch-blind-decoding/index.html',
  './topics/13-uplink-physical-layer/index.html',
  './topics/14-oran-fronthaul-split/index.html',
  './topics/15-zadoff-chu-srs/index.html',
  './topics/16-gold-sequence-csi-rs/index.html',
  './topics/17-openairinterface/index.html',
  './topics/18-dmrs-channel-estimation/index.html',
  './topics/19-measurement-handover/index.html',
];

/* 구글 폰트는 다른 출처라 미리 받아 둘 수 없다(응답 내용을 읽지 못한다).
   대신 한 번 불러올 때 그대로 캐시에 넣어 두면 다음부터 오프라인에서도 나온다. */
const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    /* addAll은 하나만 실패해도 전부 실패한다 — 자료 하나가 빠져도
       나머지는 쓸 수 있어야 하므로 하나씩 담는다. */
    await Promise.all(PAGES.map(async (url) => {
      try { await cache.add(new Request(url, { cache: 'reload' })); }
      catch (err) { console.warn('[sw] 못 받음:', url, err); }
    }));
    self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    /* 버전이 바뀌면 옛 캐시를 지운다 — 안 지우면 단말 저장 공간만 먹는다 */
    const keys = await caches.keys();
    await Promise.all(keys
      .filter((k) => k.startsWith('nr-study-') && k !== CACHE)
      .map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;
  const isFont = FONT_HOSTS.includes(url.hostname);
  if (!sameOrigin && !isFont) return;          /* 나머지는 건드리지 않는다 */

  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(req, { ignoreSearch: false });
    if (hit) {
      /* 캐시로 먼저 응답하고, 온라인이면 조용히 새로 받아 둔다.
         읽는 사람을 기다리게 하지 않으면서 다음 방문 때 최신이 된다. */
      e.waitUntil(refresh(cache, req));
      return hit;
    }
    try {
      const res = await fetch(req);
      /* opaque(폰트 등 다른 출처) 응답도 그대로 담아 두면 다시 내줄 수 있다.
         저장은 실패해도 상관없다 — 페이지는 이미 받은 응답으로 그리면 되므로
         put의 실패가 화면까지 번지지 않게 따로 삼킨다. */
      if (res && (res.ok || res.type === 'opaque')) {
        cache.put(req, res.clone()).catch(() => {});
      }
      return res;
    } catch (err) {
      /* 오프라인인데 캐시에도 없는 경우.
         페이지 이동이면 목차라도 띄워 준다 — 빈 화면보다는 낫다. */
      if (req.mode === 'navigate') {
        const home = await cache.match('./index.html');
        if (home) return home;
      }
      throw err;
    }
  })());
});

async function refresh(cache, req) {
  try {
    const res = await fetch(req);
    if (res && (res.ok || res.type === 'opaque')) await cache.put(req, res.clone());
  } catch (err) { /* 오프라인이면 그냥 둔다 */ }
}
