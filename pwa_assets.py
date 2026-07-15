#!/usr/bin/env python3
"""PWA-артефакти для build_study.py: маніфест, іконки, service worker.

Іконки растеризуються build-time чистим stdlib (zlib+struct для PNG-кодування,
проста геометрія прямокутників/діагоналей для монограми «KE» з 4x-суперсемплінгом
для згладжених країв) — без Pillow чи інших залежностей, узгоджено з рештою
проєкту («Залежностей, крім python3, не потрібно», див. README.md).

Кеш-версія service worker'а — детермінований SHA-256 від (шлях, вміст) усіх
файлів, уже записаних у dist/ на момент виклику compute_cache_version(). Це
означає: однаковий вміст levels/*.md + study_template.html + pwa_assets.py →
однаковий хеш → та сама версія кеша; будь-яка змістовна зміна → нова версія →
стара стирається на 'activate'. Жодного datetime — версія залежить лише від
контенту, не від часу збірки.
"""
import hashlib
import struct
import zlib

# ---------------------------------------------------------------------------
# Кольори — з палітри темної теми study_template.html (:root, без [data-theme
# ="light"]): --bg:#0d0f14, --accent:#7c6cff. Іконки: суцільне тло кольором
# акценту (без прозорості — обов'язково для apple-touch-icon і для maskable:
# ОС сама накладає власну маску форми поверх повністю непрозорого квадрата).
# Букви — білі: той самий контраст, що й .btn.primary/.tab.active у шаблоні
# (background:var(--accent); color:#fff) — це вже усталена пара в дизайні.
# ---------------------------------------------------------------------------
ACCENT_RGB = (0x7C, 0x6C, 0xFF)  # --accent
GLYPH_RGB = (0xFF, 0xFF, 0xFF)   # білий текст на акцентному тлі

MANIFEST_BG = "#0d0f14"     # --bg (темна тема) — фон сплеш-скріна
MANIFEST_THEME = "#7c6cff"  # --accent (темна тема) — колір хрому ОС/браузера

SUPERSAMPLE = 4  # суперсемплінг для згладжених країв діагоналей монограми

ICON_SIZES = (192, 512)     # розміри іконок маніфеста
APPLE_TOUCH_SIZE = 180      # apple-touch-icon

CACHE_PREFIX = "ke-training-"


# =============================================================================
# Мінімальний PNG-writer (лише те, що потрібно: 8-біт truecolor RGB, без alpha)
# =============================================================================
def _png_chunk(tag, data):
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def encode_png(width, height, rows):
    """rows: `height` bytes-об'єктів по `width*3` байт (RGB, без байта фільтра
    на початку рядка — filter type 0/None додається тут)."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # colorType 2 = RGB
    raw = bytearray()
    for row in rows:
        raw.append(0)  # filter type 0 = None
        raw.extend(row)
    idat = zlib.compress(bytes(raw), 9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


# =============================================================================
# Монограма «KE»: прямокутні штрихи (E) + лінійна інтерполяція по рядку (K).
# Геометрія обчислюється пропорційно до `unit` (розмір канвасу з урахуванням
# суперсемплінгу) — тому не пікселізується на жодному з трьох розмірів іконок.
# =============================================================================
def _row_ranges(y, unit):
    """Зафарбовані діапазони [(x0,x1), ...] по вертикалі y канвасу unit×unit.

    gh=0.44*unit тримає найдальші кути монограми на відстані ~0.37*unit від
    центру — у межах maskable safe-zone (кути мають лишатись у колі радіусом
    0.40*unit від центру, інакше ОС-маска (коло/сквіркл) обріже літери)."""
    gh = unit * 0.44    # висота гліфа
    sw = gh * 0.20      # товщина штриха
    ew = gh * 0.58      # ширина "E"
    kw = gh * 0.62      # ширина "K"
    gap = gh * 0.16     # відстань між літерами
    total_w = ew + gap + kw
    x0 = (unit - total_w) / 2
    y0 = (unit - gh) / 2
    if not (y0 <= y < y0 + gh):
        return []

    ranges = []

    # ---- K (ліворуч): вертикаль + дві діагоналі від середини вертикалі до кутів ----
    kx0 = x0
    ranges.append((kx0, kx0 + sw))
    cx, cy = kx0 + sw / 2, y0 + gh / 2
    half = sw / 2
    if y <= cy:
        t = 0.0 if cy == y0 else (cy - y) / (cy - y0)
        xc = cx + (kx0 + kw - cx) * t
        ranges.append((xc - half, xc + half))
    if y >= cy:
        t = 0.0 if cy == y0 + gh else (y - cy) / (y0 + gh - cy)
        xc = cx + (kx0 + kw - cx) * t
        ranges.append((xc - half, xc + half))

    # ---- E (праворуч): вертикаль + верхня/нижня горизонталі + коротша середня ----
    ex0 = x0 + kw + gap
    ranges.append((ex0, ex0 + sw))
    if y < y0 + sw or y >= y0 + gh - sw:
        ranges.append((ex0, ex0 + ew))
    mid0, mid1 = y0 + gh / 2 - sw / 2, y0 + gh / 2 + sw / 2
    if mid0 <= y < mid1:
        ranges.append((ex0, ex0 + ew * 0.86))

    return ranges


def _mask_row(y, unit):
    """Маска покриття рядка (bytearray довжини unit, 0 або 255)."""
    row = bytearray(unit)
    for rx0, rx1 in _row_ranges(y, unit):
        ix0 = max(0, int(round(rx0)))
        ix1 = min(unit, int(round(rx1)))
        if ix1 > ix0:
            row[ix0:ix1] = b"\xff" * (ix1 - ix0)
    return row


def render_icon(size):
    """PNG size×size: суцільне тло ACCENT_RGB + монограма «KE» кольору
    GLYPH_RGB, з 4x-суперсемплінгом (усереднення блоків) для згладжених країв.
    Без alpha-каналу (повністю непрозоре) — коректно і для maskable (ОС сама
    накладає маску форми), і для apple-touch-icon (iOS не любить прозорість)."""
    ss = SUPERSAMPLE
    big = size * ss
    mask_rows = [_mask_row(y, big) for y in range(big)]

    rows = []
    for by in range(size):
        row = bytearray(size * 3)
        src_rows = mask_rows[by * ss : (by + 1) * ss]
        for bx in range(size):
            total = 0
            bx0, bx1 = bx * ss, (bx + 1) * ss
            for sr in src_rows:
                total += sum(sr[bx0:bx1])
            alpha = total / (255 * ss * ss)  # частка покриття гліфом, 0..1
            off = bx * 3
            for c in range(3):
                v = ACCENT_RGB[c] + (GLYPH_RGB[c] - ACCENT_RGB[c]) * alpha
                row[off + c] = max(0, min(255, round(v)))
        rows.append(bytes(row))
    return encode_png(size, size, rows)


# =============================================================================
# Маніфест
# =============================================================================
def build_manifest():
    """dict для dist/manifest.webmanifest (назва затверджена користувачем)."""
    return {
        "name": "KE Training — тренажер компетенцій",
        "short_name": "KE Training",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "lang": "uk",
        "background_color": MANIFEST_BG,
        "theme_color": MANIFEST_THEME,
        "icons": [
            {
                "src": "/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ],
    }


# =============================================================================
# HTML-фрагменти, спільні для кореневого dist/index.html і шаблону рівня
# (study_template.html через плейсхолдери — див. render_level_html()). Єдине
# джерело правди, щоб дві сторінки не розійшлись текстом тегів.
# =============================================================================
HEAD_TAGS = (
    '<link rel="manifest" href="/manifest.webmanifest">\n'
    '<link rel="apple-touch-icon" href="/icons/apple-touch-icon-180.png">\n'
    '<meta name="theme-color" content="#7c6cff">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    # Chrome вважає apple-* тег застарілим і в консолі радить цей стандартний
    # (виявлено емпірично під час перевірки в реальному браузері) — лишаємо
    # обидва: apple-* потрібен iOS Safari, цей — Chrome/Android.
    '<meta name="mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-status-bar-style" content="black">\n'
)

# Реєстрація SW: feature-detect + реєстрація після 'load', scope '/' явно
# (і так дефолт для sw.js, обслугованого з кореня, але явно — зрозуміліше).
# Не чіпає і не залежить від клієнтського синку /api/state.
SW_REGISTER_SCRIPT = (
    "<script>\n"
    "if ('serviceWorker' in navigator) {\n"
    "  window.addEventListener('load', function () {\n"
    "    navigator.serviceWorker.register('/sw.js', { scope: '/' });\n"
    "  });\n"
    "}\n"
    "</script>\n"
)


# =============================================================================
# Service worker
# =============================================================================
def compute_cache_version(dist_dir):
    """SHA-256(12 hex) по (відносний_шлях, вміст) усіх файлів, уже записаних
    у dist_dir. Викликати ПІСЛЯ запису всіх інших артефактів (index.html,
    рівні, 404, маніфест, іконки), але ДО запису sw.js — інакше sw.js мав би
    хешувати сам себе. Детерміновано й без datetime: сортування за шляхом
    гарантує однаковий результат незалежно від порядку файлової системи."""
    h = hashlib.sha256()
    for path in sorted(dist_dir.rglob("*")):
        if path.is_file():
            h.update(path.relative_to(dist_dir).as_posix().encode("utf-8"))
            h.update(path.read_bytes())
    return h.hexdigest()[:12]


# dist/sw.js. Плейсхолдер __CACHE_VERSION__ підставляється render_sw_js() —
# той самий підхід, що й JSON_DATA_PLACEHOLDER/LEVEL_KEY_PLACEHOLDER у
# build_study.py (просте .replace(), без .format() — щоб не екранувати
# фігурні дужки JS-синтаксису).
SW_JS_TEMPLATE = r"""'use strict';

/* dist/sw.js — згенеровано build_study.py з pwa_assets.py. НЕ редагувати
   вручну: наступна збірка перезапише цей файл. Зміни логіки — у
   pwa_assets.SW_JS_TEMPLATE. */

const CACHE_NAME = 'ke-training-__CACHE_VERSION__';
const CACHE_PREFIX = 'ke-training-';

// Мінімальний precache — решта (майбутні /l2/ тощо) кешується runtime по мірі
// відвідування, у ту саму версійну CACHE_NAME.
const PRECACHE_URLS = [
  '/',
  '/l3/',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon-180.png',
];

const OFFLINE_HTML = `<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Офлайн · KE Training</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;background:#0d0f14;color:#e7e9ef;
display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;padding:24px}
.box{max-width:360px;text-align:center}
h1{font-size:20px;margin:0 0 10px}
p{color:#9aa2b1;font-size:14px;line-height:1.5;margin:0 0 18px}
button{font:inherit;font-weight:600;padding:10px 18px;border-radius:10px;
border:1px solid #7c6cff;background:#7c6cff;color:#fff;cursor:pointer}
</style>
</head>
<body>
<div class="box">
<h1>Немає мережі</h1>
<p>Ця сторінка ще не збережена офлайн. Підключіться до інтернету і спробуйте ще раз.</p>
<button onclick="location.reload()">Спробувати ще раз</button>
</div>
</body>
</html>`;

function isSameOrigin(url) {
  try {
    return new URL(url, self.location.href).origin === self.location.origin;
  } catch (e) {
    return false;
  }
}

// Кешувати ЛИШЕ успішні, не-редіректнуті, same-origin відповіді. Інакше при
// простроченій сесії Cloudflare Access у кеш потрапила б сторінка логіна
// (Access повертає справжній HTTP-редирект на інший хост — те саме
// response.redirected, яким уже керується клієнтський синк у study_template).
function isCacheableResponse(request, response) {
  return !!response && response.ok && !response.redirected && isSameOrigin(request.url);
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names
          .filter((name) => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      ))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request, isNavigation) {
  try {
    const response = await fetch(request);
    if (isCacheableResponse(request, response)) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (isNavigation) {
      const root = await caches.match('/');
      if (root) return root;
      return new Response(OFFLINE_HTML, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=UTF-8' },
      });
    }
    throw err;
  }
}

self.addEventListener('fetch', (event) => {
  const request = event.request;

  // /api/* — повний bypass: синк прогресу цей SW не перехоплює взагалі.
  if (new URL(request.url).pathname.startsWith('/api/')) return;

  // лише GET, лише той самий origin — решту лишаємо браузеру як є.
  if (request.method !== 'GET' || !isSameOrigin(request.url)) return;

  const isNavigation = request.mode === 'navigate' || request.destination === 'document';
  event.respondWith(networkFirst(request, isNavigation));
});
"""


def render_sw_js(version):
    return SW_JS_TEMPLATE.replace("__CACHE_VERSION__", version)
