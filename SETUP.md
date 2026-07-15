# SETUP.md — ручні кроки деплою (Cloudflare + GitHub)

Код і збірка вже готові (`python3 build_study.py` → `dist/`, Pages Function `/api/state`, workflow `claude.yml`). Лишилось кілька кліків у дашбордах — разом ≈ 30–40 хв. Виконувати по порядку: 1 → 2 → 3 → 4, потім 5 — наскрізна перевірка. Позначайте `- [x]` по ходу.

---

## 1. Cloudflare Pages — підключити репозиторій (~10 хв)

Документація: [Git integration · Cloudflare Pages](https://developers.cloudflare.com/pages/get-started/git-integration/), [GitHub integration](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/)

> Дашборд Cloudflare може відкрити майстер **Worker** замість Pages. Ознаки: заголовок «Configure your Worker project», поле **Deploy command** = `npx wrangler deploy`, немає поля **Build output directory**.
>
> Поверніться назад, оберіть вкладку **Pages** (**Import an existing Git repository**) — там є поле **Build output directory** = `dist`. Без цього `/api/state` не запрацює: `functions/api/state.js` — це Pages Function, не Worker.

- [ ] Акаунт Cloudflare — створити на cloudflare.com, якщо ще немає.
- [ ] У дашборді: **Workers & Pages** → **Create application** → вкладка **Pages** → **Connect to Git**.
- [ ] Авторизувати GitHub-застосунок Cloudflare (кнопка додавання акаунта, потім Install/Authorize) → доступ дати **Only select repositories** → обрати `KE-training`.
- [ ] Обрати репозиторій `Sensation02/KE-training`, заповнити форму збірки:
  - **Project name** — можна лишити згенероване; саме воно стане частиною `<project>.pages.dev` — **запишіть цей URL**, знадобиться в кроці 3.
  - **Production branch** — `main`
  - **Framework preset** — `None` (без фреймворку)
  - **Build command** — `python3 build_study.py`
  - **Build output directory** — `dist`
- [ ] **Save and Deploy** — перший білд піде автоматично.
- Якщо білд падає з «Error: Output directory "..." not found» / «build output directory not found» — у полі **Build output directory** стоїть не `dist` (типова помилка — вписати туди назву гілки, напр. `main`): виправити в **Settings** → **Builds & deployments** → **Build configuration**, поставити `dist`, натиснути **Retry deployment**.
- [ ] Після завершення білда відкрити `<project>.pages.dev` — перевірити і з ноутбука, і з телефона.

## 2. KV namespace + binding `STUDY_STATE` (~5 хв)

Документація: [Workers KV · Get started](https://developers.cloudflare.com/kv/get-started/), [Bindings · Cloudflare Pages](https://developers.cloudflare.com/pages/functions/bindings/)

- [ ] Створити namespace: в дашборді відкрити **Workers KV** → **Create instance** → назва, наприклад `study-state` → **Create**.
- [ ] У Pages-проєкті: **Settings** → **Bindings** → **Add** → **KV namespace**.
- [ ] **Variable name** — увести рівно **`STUDY_STATE`** (великими, без варіацій — саме це ім'я читає `env.STUDY_STATE` у `functions/api/state.js`).
- [ ] **KV namespace** — обрати щойно створений namespace → зберегти.
- [ ] Передеплоїти проєкт, щоб binding підхопився (найпростіше — порожній push у `main`, або повторний деплой останнього білда з вкладки Deployments).
- [ ] Перевірка (робити ПІСЛЯ кроку 3): відкрити `<project>.pages.dev/api/state?level=l3` без входу — має спрацювати логін-екран Access, а не голий JSON.

## 3. Cloudflare Access (~10 хв)

Документація: [Zero Trust onboarding](https://developers.cloudflare.com/cloudflare-one/setup/), [Self-hosted public app](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/), [One-time PIN login](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/), [Policies: Allow за email](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/common-policies/), [Application paths (wildcards, пріоритет специфічнішого шляху)](https://developers.cloudflare.com/cloudflare-one/policies/access/app-paths/), [Preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/), [Branch build controls](https://developers.cloudflare.com/pages/configuration/branch-build-controls/)

- [ ] Перший вхід у **Zero Trust** відкриває онбординг організації: обрати **team name** — з нього складається адреса сторінки логіна Access `<team>.cloudflareaccess.com` — **запишіть її**.
- [ ] Обрати план **Free** (до 50 користувачів, $0). Платіжний метод онбординг просить навіть для Free — кошти не списуються, це верифікація.
- [ ] Увімкнути One-time PIN (з 2026 не додається автоматично новим Zero Trust акаунтам): **Zero Trust** → **Integrations** → **Identity providers** → **Add new identity provider** → **One-time PIN**.
- [ ] Створити застосунок: **Zero Trust** → **Access controls** → **Applications** → **Create new application** → **Self-hosted and private** → **Add public hostname**.
- [ ] **Domain** — `<project>.pages.dev` з кроку 1. **Path** — лишити **порожнім**, НЕ вписувати `api`: порожній Path покриває весь домен, тож сторінка і `/api/*` — в одному контурі автентифікації (будь-яке значення в Path захистить лише частину сайту).
- [ ] Рекомендовано: тут же **+ Add public hostname** → **Subdomain** — `*`, **Domain** — той самий `<project>.pages.dev`: та сама політика накриє і прев'ю-деплеї `*.<project>.pages.dev` (зокрема майбутні PR-прев'ю від `@claude` з кроку 4).
- [ ] Політика: **Add a policy** → назва (напр. `KE Training users`) → **Action: Allow** → в **Include** → селектор **Emails** → вписати свою пошту. (Додати колегу пізніше = дописати ще один email у це саме правило.)
- [ ] **Session Duration** — обрати найближче до 30 днів значення зі списку.
- [ ] Зберегти застосунок.
- [ ] **Bypass для PWA-файлів** (без цього застосунок не встановлюється на телефон: браузер тягне manifest, а iOS — іконку, окремими запитами без куків сесії; самі файли генеруються з публічного репозиторію і конфіденційності не мають). Створити **другий** застосунок: **Create new application** → **Self-hosted and private** → трьома **Add public hostname** додати записи на тому самому домені `<project>.pages.dev` з **Path** відповідно: `manifest.webmanifest`, `icons/*`, `sw.js`.
- [ ] Політика цього другого застосунку: **Add a policy** → назва (напр. `PWA assets bypass`) → **Action: Bypass** → в **Include** → селектор **Everyone** → зберегти. За правилами Access специфічніший шлях має пріоритет, тож лише ці три шляхи виходять з-під логіна — `/`, `/l3/` і `/api/*` лишаються під Access основного застосунку.
- [ ] Якщо wildcard-hostname `*` вище **не** додавали: прев'ю-деплеї Pages (`*.<project>.pages.dev` для гілок/PR, зокрема від `@claude` з кроку 4) застосунок з одним hostname **не покриває** — окремий піддомен. Тоді обрати один варіант:
  - (а) простіше: Pages-проєкт → **Settings** → **General** → **Enable access policy** — вбудований перемикач Cloudflare Pages, захищає прев'ю-посилання через Access;
  - (б) або вимкнути прев'ю зовсім: Pages-проєкт → **Settings** → **Builds & deployments** → **Preview deployments** → **None**.
- [ ] Перевірка: відкрити `<project>.pages.dev` в інкогніто-вікні — має показати екран логіна Access (форма email), а не сайт одразу.

## 4. Claude GitHub App + секрет (~5 хв)

Документація: [Claude Code GitHub Actions](https://code.claude.com/docs/en/github-actions), [Authentication — setup-token](https://code.claude.com/docs/en/authentication), [Secrets у GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)

> `.github/workflows/claude.yml` в репо вже є і навмисно запінений на конкретний commit SHA (див. коментар у файлі) — тому НЕ запускайте `/install-github-app` у Claude Code (може запропонувати інший/новий workflow-файл). Потрібен лише ручний варіант нижче: App + секрет.
>
> Приклад у документації за посиланнями вище показує секрет `ANTHROPIC_API_KEY` — у цьому репозиторії використовується саме `CLAUDE_CODE_OAUTH_TOKEN` (OAuth-токен від підписки Claude), як і описано нижче в чеклисті.

- [ ] Встановити GitHub App: [github.com/apps/claude](https://github.com/apps/claude) → Install → обрати акаунт → **Only select repositories** → `KE-training` → підтвердити.
- [ ] Локально в терміналі: `claude setup-token` (потрібна підписка Pro, Max, Team або Enterprise) → відкриється браузер для авторизації → після підтвердження токен виводиться прямо в термінал (ніде не зберігається — копіювати одразу).
- [ ] GitHub: репозиторій `KE-training` → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
- [ ] **Name** — рівно **`CLAUDE_CODE_OAUTH_TOKEN`** (саме цю назву читає `.github/workflows/claude.yml`), **Secret** — вставити скопійований токен → **Add secret**.
- [ ] Перевірка: створити Issue з текстом `@claude привіт` — за хвилину-дві Claude має відповісти коментарем (якщо ні — дивитись вкладку **Actions** репозиторію на помилку).

## 5. Наскрізна перевірка (~10 хв)

- [ ] Чекбокс на ноутбуці → оновити сторінку на телефоні (той самий email в Access) — з'явився і там, і навпаки.
- [ ] Правка будь-якого `.md` у `levels/L3/` → commit + push у `main` → сайт оновився за ~1–2 хв (прогрес білда видно у вкладці Deployments Pages-проєкту).
- [ ] Індикатор синку показує **«✓ збережено»** після зміни (не «офлайн» і не «⚠ помилка синку»).
- [ ] Сесійний банер: DevTools → **Application** → **Cookies** → видалити кукі `CF_Authorization` → зробити будь-яку зміну в чеклисті. Очікування — банер **«Сесію завершено — увійдіть знову.»** внизу екрана. Якщо замість банера індикатор показує «офлайн» — занотуйте і повідомте: це відома невизначеність (залежить, чи `fetch` бачить редирект Access як `redirected`, чи браузер трактує це як мережеву помилку).
- [ ] PWA-встановлення: на телефоні відкрити `<project>.pages.dev/l3/`, у меню браузера обрати **«Додати на головний екран»** (Add to Home Screen) — іконка «KE Training» з'являється на екрані, відкривається без адресного рядка (standalone).
- [ ] Офлайн: увімкнути режим польоту → відкрити встановлений застосунок — тренажер відкривається з кеша, чекбокси й статуси питань перемикаються як завжди; вимкнути режим польоту — індикатор синку за кілька секунд сам переходить у **«✓ збережено»** (наздогнав сервер без ручних дій).
- [ ] Прострочена сесія Access офлайн: якщо на момент відкриття сесія вже неактивна, офлайн-версія все одно відкривається з кеша (service worker до Access не звертається) — але індикатор синку покаже **«потрібен вхід»**, поки не увійдете знову. Це очікувано, не баг.
