#!/usr/bin/env python3
"""PWA-артефакти для build_study.py: маніфест, іконки, service worker.

Іконки растеризуються build-time чистим stdlib (zlib+struct для PNG-кодування,
проста геометрія прямокутників/діагоналей/шевронів з 4x-суперсемплінгом для
згладжених країв) — без Pillow чи інших залежностей, узгоджено з рештою
проєкту («Залежностей, крім python3, не потрібно», див. README.md).

Дизайн іконки «Комета» (затверджений 2026-07-21, див.
docs/superpowers/specs/2026-07-21-app-icon-comet-design.md): темне тло,
білі літери «KE» в нижній половині, акцентний шеврон-стрілка, крила якого
сідають на верхні кути літер, і два шеврони-«сліди» вище — кожен на 20%
менший і темніший за попередній (геометрична прогресія ×0.8).

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
# ="light"]). УВАГА: значення ЗАХАРДКОЖЕНІ, з CSS не читаються — вони мають
# збігатися з --accent (study_template.html:14) і --bg (study_template.html:11);
# при зміні палітри шаблону оновити вручну і тут (наступна збірка перегенерує
# іконки/маніфест/theme-color, але лише з цих констант).
# Іконка dark-first: суцільне темне тло --bg (без прозорості — обов'язково для
# apple-touch-icon і для maskable: ОС сама накладає власну маску форми поверх
# повністю непрозорого квадрата). Літери — білі (контраст як у .btn.primary),
# основний шеврон — акцент; сліди — той самий відтінок, пригашений до тла
# двома кроками (кольори передобчислені, бо рендерер без альфа-каналу).
# ---------------------------------------------------------------------------
ICON_BG_RGB = (0x0D, 0x0F, 0x14)        # = --bg темної теми (#0d0f14)
LETTER_RGB = (0xFF, 0xFF, 0xFF)         # білі літери «KE»
CHEVRON_MAIN_RGB = (0x7C, 0x6C, 0xFF)   # = --accent (#7c6cff)
CHEVRON_ECHO1_RGB = (0x5B, 0x4F, 0xC0)  # слід 1: акцент, пригашений до тла
CHEVRON_ECHO2_RGB = (0x3E, 0x35, 0x84)  # слід 2: ще один крок до тла

MANIFEST_BG = "#0d0f14"     # = --bg (темна тема) — фон сплеш-скріна
MANIFEST_THEME = "#7c6cff"  # = --accent — колір хрому ОС/браузера і theme-color

SUPERSAMPLE = 4  # суперсемплінг для згладжених країв діагоналей монограми

ICON_SIZES = (192, 512)     # розміри іконок маніфеста
APPLE_TOUCH_SIZE = 180      # apple-touch-icon

# Єдине джерело префікса імені кеша SW: підставляється в SW_JS_TEMPLATE
# (плейсхолдер __CACHE_PREFIX__) через render_sw_js() — у JS-шаблоні літерала немає.
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
# Знак «Комета»: монограма «KE» (прямокутні штрихи E + діагоналі K лінійною
# інтерполяцією по рядку) під трьома шевронами. Геометрія обчислюється
# пропорційно до `unit` (розмір канвасу з урахуванням суперсемплінгу) — тому
# не пікселізується на жодному з розмірів іконок. _metrics()/_chevrons() —
# єдине джерело цієї геометрії: і растрові *_ranges() (PNG-іконки), і
# векторний render_icon_svg() (SVG-фавікон) рахують від тих самих чисел,
# тому растр і вектор завжди лишаються одним і тим самим знаком.
# =============================================================================
def _metrics(unit):
    """Метрики літер «KE». gh=0.28·unit і y0=0.50·unit тримають нижні кути
    монограми на відстані ~0.34·unit від центру, а апекс найдальшого сліду
    (див. _chevrons) — на 0.38·unit: усе в межах maskable safe-zone (коло
    радіусом 0.40·unit від центру, інакше ОС-маска обріже знак).

    «K» без тонких діагоналей: горизонтальна півширина діагоналі hw=0.66·sw
    компенсує кут нахилу ~50° (перпендикулярна товщина ≈ sw, як у вертикалей);
    діагоналі сходяться на правому краї вертикалі (jx), а не в центрі штриха;
    нижня нога винесена назовні на kick для оптичного балансу."""
    gh = unit * 0.28    # висота гліфа
    sw = gh * 0.20      # товщина штриха
    ew = gh * 0.58      # ширина "E"
    kw = gh * 0.62      # ширина "K"
    gap = gh * 0.16     # відстань між літерами
    x0 = (unit - (ew + gap + kw)) / 2
    y0 = unit * 0.50
    kx0 = x0
    ex0 = x0 + kw + gap
    return {
        "gh": gh, "sw": sw, "ew": ew, "kw": kw,
        "x0": x0, "y0": y0, "kx0": kx0, "ex0": ex0,
        "jx": kx0 + sw,          # стик діагоналей: правий край вертикалі K
        "jy": y0 + gh / 2,
        "ktx": kx0 + kw,         # x верхнього кута K
        "hw": sw * 0.66,         # горизонтальна півширина діагоналей K
        "kick": gh * 0.03,       # винос нижньої ноги K назовні
    }


def _chevrons(unit):
    """Шеврони знизу вгору: (RGB, ay, hs, d, th) — y апекса, піврозмах,
    вертикальний спад крила, вертикальна товщина. Кожен наступний слід —
    ×0.8 за всіма трьома вимірами (геометрична прогресія «віддалення»).
    Кінці крил основного шеврона (cx±hs, ay+d+th) = (0.30, 0.50) і
    (0.70, 0.50)·unit — точно на верхній лінії літер (стик «одного знака»)."""
    u = unit / 100.0
    return [
        (CHEVRON_MAIN_RGB, 31.0 * u, 20.0 * u, 13.0 * u, 6.0 * u),
        (CHEVRON_ECHO1_RGB, 21.0 * u, 16.0 * u, 10.4 * u, 4.8 * u),
        (CHEVRON_ECHO2_RGB, 12.0 * u, 12.8 * u, 8.32 * u, 3.84 * u),
    ]


def _letter_ranges(y, unit):
    """Зафарбовані діапазони [(x0,x1), ...] літер «KE» по вертикалі y."""
    m = _metrics(unit)
    gh, sw, ew = m["gh"], m["sw"], m["ew"]
    y0, kx0, ex0 = m["y0"], m["kx0"], m["ex0"]
    jx, jy, ktx, hw, kick = m["jx"], m["jy"], m["ktx"], m["hw"], m["kick"]
    if not (y0 <= y < y0 + gh):
        return []

    ranges = []

    # ---- K (ліворуч): вертикаль + дві діагоналі від краю вертикалі до кутів ----
    ranges.append((kx0, kx0 + sw))
    if y <= jy:
        t = 0.0 if jy == y0 else (jy - y) / (jy - y0)
        xc = jx + (ktx - jx) * t
        ranges.append((xc - hw, xc + hw))
    if y >= jy:
        t = 0.0 if jy == y0 + gh else (y - jy) / (y0 + gh - jy)
        xc = jx + (ktx + kick - jx) * t
        ranges.append((xc - hw, xc + hw))

    # ---- E (праворуч): вертикаль + верхня/нижня горизонталі + коротша середня ----
    ranges.append((ex0, ex0 + sw))
    if y < y0 + sw or y >= y0 + gh - sw:
        ranges.append((ex0, ex0 + ew))
    mid0, mid1 = y0 + gh / 2 - sw / 2, y0 + gh / 2 + sw / 2
    if mid0 <= y < mid1:
        ranges.append((ex0, ex0 + ew * 0.86))

    return ranges


def _chevron_ranges(y, unit, ay, hs, d, th):
    """Діапазони одного шеврона по вертикалі y: зовнішня межа крила — лінія
    від апекса (cx, ay) до (cx±hs, ay+d), внутрішня — та сама лінія, зсунута
    вниз на th; біля апекса внутрішня ще не почалась і крила зливаються."""
    if not (ay <= y < ay + d + th):
        return []
    cx = unit / 2.0
    hi = min(hs, hs * (y - ay) / d)
    lo = max(0.0, hs * (y - ay - th) / d) if y >= ay + th else 0.0
    if hi <= lo:
        return []
    if lo <= 0:
        return [(cx - hi, cx + hi)]
    return [(cx - hi, cx - lo), (cx + lo, cx + hi)]


def _glyph_layers(unit):
    """Шари знака: (RGB, функція y → діапазони). Шари не перетинаються, тож
    порядок важливий лише на стиках (літери малюються останніми)."""
    layers = [
        (rgb, (lambda yy, a=ay, h=hs, dd=d, t=th:
               _chevron_ranges(yy, unit, a, h, dd, t)))
        for rgb, ay, hs, d, th in _chevrons(unit)
    ]
    layers.append((LETTER_RGB, lambda yy: _letter_ranges(yy, unit)))
    return layers


def _index_row(y, unit, layers):
    """Карта шарів рядка (bytearray довжини unit: 0 = тло, i = layers[i-1])."""
    row = bytearray(unit)
    for i, (_rgb, ranges_fn) in enumerate(layers, start=1):
        fill = bytes([i])
        for rx0, rx1 in ranges_fn(y):
            ix0 = max(0, int(round(rx0)))
            ix1 = min(unit, int(round(rx1)))
            if ix1 > ix0:
                row[ix0:ix1] = fill * (ix1 - ix0)
    return row


def render_icon(size):
    """PNG size×size: суцільне тло ICON_BG_RGB + багатоколірний знак
    (три шеврони + білі літери), з 4x-суперсемплінгом (усереднення RGB
    блоків 4×4) для згладжених країв. Без alpha-каналу (повністю
    непрозоре) — коректно і для maskable (ОС сама накладає маску форми),
    і для apple-touch-icon (iOS не любить прозорість)."""
    ss = SUPERSAMPLE
    big = size * ss
    layers = _glyph_layers(big)
    palette = [ICON_BG_RGB] + [rgb for rgb, _fn in layers]
    index_rows = [_index_row(y, big, layers) for y in range(big)]

    n = ss * ss
    rows = []
    for by in range(size):
        row = bytearray(size * 3)
        src_rows = index_rows[by * ss : (by + 1) * ss]
        for bx in range(size):
            r = g = b = 0
            bx0, bx1 = bx * ss, (bx + 1) * ss
            for sr in src_rows:
                for idx in sr[bx0:bx1]:
                    pr, pg, pb = palette[idx]
                    r += pr
                    g += pg
                    b += pb
            off = bx * 3
            row[off] = round(r / n)
            row[off + 1] = round(g / n)
            row[off + 2] = round(b / n)
        rows.append(bytes(row))
    return encode_png(size, size, rows)


def render_icon_svg():
    """Векторна (SVG) версія того самого знака «Комета», що й render_icon() —
    для favicon вкладки браузера: різкий на будь-якому масштабі й розмірі
    (на відміну від растрового favicon.ico), і той самий силует, що й
    растрові PWA-іконки, тож вкладка і встановлений застосунок виглядають
    як один і той самий значок. Геометрія — з _metrics()/_chevrons(), а не
    окремі числа, тому не може розійтися з растровими icon-192/512."""
    unit = 100
    m = _metrics(unit)
    gh, sw, ew = m["gh"], m["sw"], m["ew"]
    y0, kx0, ex0 = m["y0"], m["kx0"], m["ex0"]
    jx, jy, ktx, hw, kick = m["jx"], m["jy"], m["ktx"], m["hw"], m["kick"]
    cx = unit / 2.0
    bg = "#%02x%02x%02x" % ICON_BG_RGB
    letter = "#%02x%02x%02x" % LETTER_RGB

    def rect(x, y, w, h, fill):
        return f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{fill}"/>'

    def poly(fill, *points):
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
        return f'<polygon points="{pts}" fill="{fill}"/>'

    shapes = []
    # Шеврони (сліди спершу — далі від глядача, хоча фігури й не перетинаються)
    for rgb, ay, hs, d, th in reversed(_chevrons(unit)):
        fill = "#%02x%02x%02x" % rgb
        shapes.append(poly(
            fill,
            (cx, ay), (cx + hs, ay + d), (cx + hs, ay + d + th),
            (cx, ay + th), (cx - hs, ay + d + th), (cx - hs, ay + d),
        ))
    shapes += [
        rect(kx0, y0, sw, gh, letter),  # K: вертикаль
        # K: верхня діагональ — від верхнього кута до краю вертикалі
        poly(letter, (ktx - hw, y0), (ktx + hw, y0), (jx + hw, jy), (jx - hw, jy)),
        # K: нижня діагональ — від краю вертикалі до винесеного нижнього кута
        poly(letter, (jx - hw, jy), (jx + hw, jy),
             (ktx + kick + hw, y0 + gh), (ktx + kick - hw, y0 + gh)),
        rect(ex0, y0, sw, gh, letter),               # E: вертикаль
        rect(ex0, y0, ew, sw, letter),               # E: верхня горизонталь
        rect(ex0, y0 + gh - sw, ew, sw, letter),     # E: нижня горизонталь
        rect(ex0, y0 + gh / 2 - sw / 2, ew * 0.86, sw, letter),  # E: середня
    ]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {unit} {unit}">'
        f'<rect width="{unit}" height="{unit}" fill="{bg}"/>'
        + "".join(shapes)
        + "</svg>"
    )


# =============================================================================
# Маніфест
# =============================================================================
def build_manifest():
    """dict для dist/manifest.webmanifest (назва затверджена користувачем)."""
    return {
        "name": "KE Training",
        "short_name": "KE Training",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "lang": "uk",
        "background_color": MANIFEST_BG,
        "theme_color": MANIFEST_THEME,
        "icons": [
            {
                "src": "/icons/icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any",
            },
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
    # SVG-фавікон вкладки браузера — та сама монограма «KE», що й PWA-іконки
    # (render_icon_svg() рахує геометрію з тих самих _metrics(), що й
    # render_icon()), тож вкладка й встановлений застосунок більше не
    # розходяться виглядом. PNG-фолбек — для Safari/старих браузерів, які
    # SVG-favicon не підтримують.
    '<link rel="icon" type="image/svg+xml" href="/icons/icon.svg">\n'
    '<link rel="alternate icon" href="/icons/icon-192.png">\n'
    # crossorigin="use-credentials" обов'язковий: за специфікацією фетч
    # маніфеста дефолтно йде БЕЗ куків (credentials mode "omit", навіть
    # same-origin) — за Cloudflare Access такий запит упирається в 302 на
    # логін, і встановлюваність на проді не працює.
    '<link rel="manifest" href="/manifest.webmanifest" crossorigin="use-credentials">\n'
    '<link rel="apple-touch-icon" href="/icons/apple-touch-icon-180.png">\n'
    f'<meta name="theme-color" content="{MANIFEST_THEME}">\n'
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


# dist/sw.js. Плейсхолдери __CACHE_PREFIX__/__CACHE_VERSION__ підставляються
# render_sw_js() — той самий підхід, що й JSON_DATA_PLACEHOLDER/
# LEVEL_KEY_PLACEHOLDER у build_study.py (просте .replace(), без .format() —
# щоб не екранувати фігурні дужки JS-синтаксису).
SW_JS_TEMPLATE = r"""'use strict';

/* dist/sw.js — згенеровано build_study.py з pwa_assets.py. НЕ редагувати
   вручну: наступна збірка перезапише цей файл. Зміни логіки — у
   pwa_assets.SW_JS_TEMPLATE. */

const CACHE_PREFIX = '__CACHE_PREFIX__';
const CACHE_NAME = CACHE_PREFIX + '__CACHE_VERSION__';

// Мінімальний precache — решта (майбутні /l2/ тощо) кешується runtime по мірі
// відвідування, у ту саму версійну CACHE_NAME.
const PRECACHE_URLS = [
  '/',
  '/l3/',
  '/manifest.webmanifest',
  '/icons/icon.svg',
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
function isCacheableResponse(url, response) {
  return !!response && response.ok && !response.redirected && isSameOrigin(url);
}

// Precache стійкий до часткових збоїв: НЕ cache.addAll (він все-або-ніщо —
// один редирект простроченої сесії Access завалив би весь install). Кожен URL
// фетчиться окремо і кладеться в кеш лише якщо відповідь проходить ті самі
// перевірки, що й runtime-кеш; що не вдалося — докешується runtime по мірі
// відвідування.
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => Promise.all(PRECACHE_URLS.map(async (url) => {
        try {
          const response = await fetch(url, { credentials: 'same-origin' });
          if (isCacheableResponse(url, response)) await cache.put(url, response);
        } catch (e) { /* офлайн/збій мережі — пропускаємо цей URL */ }
      })))
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
    if (isCacheableResponse(request.url, response)) {
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
    return SW_JS_TEMPLATE.replace("__CACHE_PREFIX__", CACHE_PREFIX).replace(
        "__CACHE_VERSION__", version
    )
