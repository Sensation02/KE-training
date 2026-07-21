# Вихід з акаунта + owner guard — план реалізації

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Кнопка виходу з Cloudflare Access + захист від змішування прогресу двох користувачів на одному пристрої.

**Architecture:** Вихід — навігація на вбудований ендпоінт Access `/cdn-cgi/access/logout` з попереднім дотисканням синку та очищенням localStorage. Захист — «owner guard»: сервер віддає email власника заголовком `X-Study-User`, клієнт при синку помічає зміну користувача і скидає чужий локальний стан до злиття. Service worker отримує bypass для `/cdn-cgi/*`.

**Tech Stack:** Vanilla JS у `study_template.html`, Cloudflare Pages Function (`functions/api/state.js`), Python-генератор (`build_study.py`, `pwa_assets.py`).

## Global Constraints

- Мова UI-текстів і коментарів у коді — українська (як у всьому репозиторії).
- Автотестів у репозиторії немає; цикл перевірки кожної задачі: `python3 build_study.py` (збірка з валідацією) + grep по `dist/` + ручна перевірка в браузері наприкінці.
- Ключ власника в localStorage: рівно `study_owner_v1`. Ключі прогресу рівнів: `<level>_study_v1` та `<level>_study_v1_synced` (наявна схема — не змінювати).
- Заголовок відповіді: рівно `X-Study-User`, значення — `encodeURIComponent(email)`.
- Коміт після кожної задачі; повідомлення закінчувати рядком `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: Заголовок X-Study-User у відповіді GET /api/state

**Files:**
- Modify: `functions/api/state.js:29-37` (функція `onRequestGet`)

**Interfaces:**
- Consumes: заголовок запиту `Cf-Access-Authenticated-User-Email` (його наявність уже гарантує `authorize()` — інакше 401).
- Produces: заголовок відповіді `X-Study-User: encodeURIComponent(email)` на успішному GET. Його читає Task 2.

- [ ] **Step 1: Додати заголовок у відповідь onRequestGet**

Замінити функцію `onRequestGet` цілком:

```js
export async function onRequestGet({ request, env }) {
  const ctx = authorize(request, env);
  if (ctx.error) return ctx.error;
  const stored = await env.STUDY_STATE.get(ctx.key);
  // X-Study-User — для owner guard на клієнті: браузер дізнається, чий це
  // прогрес, і скидає локальний стан при зміні акаунта на спільному пристрої.
  // encodeURIComponent — значення HTTP-заголовків мають бути ASCII.
  const email = request.headers.get("Cf-Access-Authenticated-User-Email");
  return new Response(stored || "{}", {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
      "X-Study-User": encodeURIComponent(email),
    },
  });
}
```

- [ ] **Step 2: Перевірити синтаксис**

Run: `node --check functions/api/state.js`
Expected: без виводу, код завершення 0.

- [ ] **Step 3: Commit**

```bash
git add functions/api/state.js
git commit -m "API: заголовок X-Study-User у GET — власник стану для owner guard

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Owner guard у syncOnLoad (study_template.html)

**Files:**
- Modify: `study_template.html:345-363` (блок «Стан / localStorage» — додати хелпери)
- Modify: `study_template.html:450-461` (`syncOnLoad()` — вставка guard після перевірок статусу)

**Interfaces:**
- Consumes: заголовок `X-Study-User` з Task 1; наявні `renderReader`, `renderCheck`, `refreshProgress`, `rebuildDeck` (усі вже визначені в шаблоні, function declarations — доступні до виконання `syncOnLoad`).
- Produces: `const OWNER_KEY = 'study_owner_v1'` і `function clearLocalProgress()` — їх використовує Task 3.

- [ ] **Step 1: Додати OWNER_KEY і clearLocalProgress**

Після рядка `const LS_KEY = window.__LEVEL__ + '_study_v1';` (рядок 338) додати:

```js
const OWNER_KEY = 'study_owner_v1';
// Прибирає прогрес УСІХ рівнів: localStorage спільний на origin, тож зміна
// акаунта стосується l2/l3/... одразу, а не лише відкритого рівня.
function clearLocalProgress(){
  Object.keys(localStorage)
    .filter(k => k.endsWith('_study_v1') || k.endsWith('_study_v1_synced'))
    .forEach(k => localStorage.removeItem(k));
}
```

- [ ] **Step 2: Вставити guard у syncOnLoad**

У `syncOnLoad()`, одразу після рядка `if(!res.ok){ setBadge('error'); syncArmed = true; return; }` і ПЕРЕД `let remote = {};` вставити:

```js
  // Owner guard: якщо локальний стан належить іншому користувачу (акаунт на
  // цьому пристрої змінився — кнопкою виходу чи після протермінування сесії),
  // скидаємо чужий прогрес ДО union/LWW — інакше він злився б у серверний
  // стан нового користувача або перезаписав його.
  const owner = decodeURIComponent(res.headers.get('X-Study-User') || '');
  const prevOwner = localStorage.getItem(OWNER_KEY);
  if(owner && prevOwner && owner !== prevOwner){
    clearLocalProgress(); // знімає і прапорець _synced → нижче спрацює гілка "перший синк"
    state = {theme:state.theme, tab:'reader', q:{}, chk:{}, updatedAt:0}; // тема — косметика пристрою, лишається
    renderReader(); renderCheck(); refreshProgress(); rebuildDeck();
  }
  if(owner) localStorage.setItem(OWNER_KEY, owner);
```

- [ ] **Step 3: Зібрати і перевірити**

Run: `python3 build_study.py && grep -c "study_owner_v1" dist/l3/index.html`
Expected: збірка `OK -> ...`, grep виводить число ≥ 2 (оголошення + використання).

- [ ] **Step 4: Commit**

```bash
git add study_template.html
git commit -m "Owner guard: скидання чужого локального прогресу при зміні акаунта

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Кнопка «Вийти» у топбарі (study_template.html)

**Files:**
- Modify: `study_template.html:274` (топбар — кнопка після `#themeBtn`)
- Modify: `study_template.html:1035` (в `init()` — обробник після `$('#themeBtn').onclick`)

**Interfaces:**
- Consumes: `clearLocalProgress()` і `OWNER_KEY` з Task 2; наявні `pushNow()` (повертає `Promise<boolean>`), `syncArmed`, `syncTimer`.
- Produces: кнопка `#logoutBtn` (нових залежностей для інших задач немає).

- [ ] **Step 1: Додати кнопку в топбар**

Після рядка `<button class="icon-btn" id="themeBtn" ...>◐</button>` додати:

```html
    <button class="icon-btn" id="logoutBtn" title="Вийти з акаунта" aria-label="Вийти з акаунта">⎋</button>
```

- [ ] **Step 2: Додати обробник в init()**

Після рядка `$('#themeBtn').onclick = ...;` додати:

```js
  $('#logoutBtn').onclick = async ()=>{
    // Дотиснути незбережені зміни перед виходом; якщо не вдалося
    // (офлайн / сесія вже мертва) — вирішує людина.
    let pushed = true;
    if(syncArmed){ clearTimeout(syncTimer); pushed = await pushNow(); }
    if(!pushed && !confirm('Останні зміни не збережено на сервері. Вийти все одно?')) return;
    clearLocalProgress();
    localStorage.removeItem(OWNER_KEY);
    // Вбудований logout Cloudflare Access: стирає кукі сесії,
    // наступний візит показує форму входу.
    location.href = '/cdn-cgi/access/logout';
  };
```

- [ ] **Step 3: Зібрати і перевірити**

Run: `python3 build_study.py && grep -c "logoutBtn" dist/l3/index.html`
Expected: збірка `OK -> ...`, grep виводить `3` (кнопка + обробник + текст селектора) або ≥ 2.

- [ ] **Step 4: Commit**

```bash
git add study_template.html
git commit -m "Кнопка «Вийти» у топбарі: синк → очищення localStorage → logout Access

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Посилання «вийти з акаунта» на кореневій сторінці (build_study.py)

**Files:**
- Modify: `build_study.py:430` (`render_root_index` — рядок футера)

**Interfaces:**
- Consumes: нічого з попередніх задач (owner guard страхує цей шлях: тут localStorage не чиститься).
- Produces: посилання у футері `dist/index.html`.

- [ ] **Step 1: Замінити рядок футера**

Було:

```python
        '  <div class="footer">згенеровано з навчальних .md</div>\n'
```

Стало:

```python
        '  <div class="footer">згенеровано з навчальних .md'
        ' · <a href="/cdn-cgi/access/logout" style="color:var(--mute)">вийти з акаунта</a></div>\n'
```

(Стиль лінка — як у «скинути прогрес» у футері сторінки рівня: `color:var(--mute)`.)

- [ ] **Step 2: Зібрати і перевірити**

Run: `python3 build_study.py && grep -c "cdn-cgi/access/logout" dist/index.html`
Expected: збірка `OK -> ...`, grep виводить `1`.

- [ ] **Step 3: Commit**

```bash
git add build_study.py
git commit -m "Коренева сторінка: посилання «вийти з акаунта» у футері

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Bypass /cdn-cgi/* у service worker (pwa_assets.py)

**Files:**
- Modify: `pwa_assets.py:514-525` (fetch-обробник у `SW_JS_TEMPLATE`)

**Interfaces:**
- Consumes: нічого.
- Produces: SW не перехоплює `/cdn-cgi/*` — навігація на logout завжди йде в мережу.

- [ ] **Step 1: Об'єднати bypass /api/ і /cdn-cgi/**

Було (усередині `self.addEventListener('fetch', ...)`):

```js
  // /api/* — повний bypass: синк прогресу цей SW не перехоплює взагалі.
  if (new URL(request.url).pathname.startsWith('/api/')) return;
```

Стало:

```js
  // /api/* — повний bypass: синк прогресу цей SW не перехоплює взагалі.
  // /cdn-cgi/* — інфраструктура Cloudflare (logout Access тощо): теж bypass,
  // інакше офлайн-фолбек підмінив би сторінку виходу кешованим застосунком.
  const pathname = new URL(request.url).pathname;
  if (pathname.startsWith('/api/') || pathname.startsWith('/cdn-cgi/')) return;
```

- [ ] **Step 2: Зібрати і перевірити**

Run: `python3 build_study.py && grep -c "cdn-cgi" dist/sw.js`
Expected: збірка `OK -> ...`, grep виводить ≥ 1.

- [ ] **Step 3: Commit**

```bash
git add pwa_assets.py
git commit -m "SW: bypass /cdn-cgi/* — logout Access не перехоплюється кешем

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Наскрізна перевірка в браузері

**Files:**
- (без змін коду; за потреби фікси — окремими комітами)

**Interfaces:**
- Consumes: результати Task 1–5, зібраний `dist/`.

- [ ] **Step 1: Локальний прев'ю зібраного dist**

Відкрити `dist/l3/index.html` через локальний статичний сервер (Browser pane / preview). Перевірити:
- кнопка ⎋ видна в топбарі поруч із ◐, має tooltip «Вийти з акаунта»;
- на мобільній ширині (375px) топбар не ламається.

- [ ] **Step 2: Перевірка футера кореневої сторінки**

Відкрити `dist/index.html` — у футері є лінк «вийти з акаунта» кольору `--mute`.

- [ ] **Step 3: Клік по ⎋ локально**

Локально `/api/state` і `/cdn-cgi/*` не існують — очікувано: після кліку (синк упаде → confirm → «ОК») ключі `l3_study_v1`, `l3_study_v1_synced`, `study_owner_v1` зникають із localStorage (DevTools → Application), браузер переходить на `/cdn-cgi/access/logout` (локально — 404, це нормально).

- [ ] **Step 4: Зафіксувати прод-перевірки**

Ці кроки виконуються на проді після деплою (руками, поза сесією):
1. Клік ⎋ → сторінка logout Access → повторний візит просить email.
2. Увійти під другим email у тому самому браузері → відкрити `/l3/` → прогрес першого користувача не видно і він не з'являється в акаунті другого.
3. Regression: один користувач — «✓ збережено», офлайн-PWA працює як раніше.

- [ ] **Step 5: Commit (лише якщо були фікси після перевірки)**

```bash
git add -A && git commit -m "Фікси за результатами перевірки logout-флоу

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
