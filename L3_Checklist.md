# L3 Full-stack — чеклист компетенцій

> Мітки глибини: 🟣 треба добре знати · 🔵 знати · 🟢 поверхнево.  
> Відмічай `[x]`, коли впевнено знаєш пункт. Тільки технічні категорії (по них оцінюють на знаннях).

**Всього: 73 пунктів** — 🟣 31 · 🔵 27 · 🟢 15

---

## Front-End (17)
<sub>🟣 10 · 🔵 5 · 🟢 2</sub>

- [ ] 🔵 Має навики перехоплення запитів (interceptors, transient requests, global error handling).
- [ ] 🟣 Вміє налаштувати з нуля UI-бібліотеки на проєкті (Mantine, Ant, shadcn, etc)
- [ ] 🟣 Вміє вибирати бібліотеки (npm package) для UI-них завдань (e.g.: date-time management, ). Розуміти, як це впливає на розмір bundle, на performance, вміє використовувати bundle analyzer. Опціонально: bundlephobia
- [ ] 🟣 Має розуміння та вміє використовувати state-manager в UI-frameworks (Redux, react-query, React Context, Zustand)
- [ ] 🔵 Має розуміння роботи local storage, session storage, cookies та їхнє можливе використання. Знає їхні обмеження, переваги з точки зору security
- [ ] 🟣 Вміє правильно та ефективно використовувати дебаггінг у браузері (profiling, може ідентифікувати performance issues and bottlnecks за допомогою інструментів браузера)
- [ ] 🟣 Знає та вміє використовувати специфічні інструменти під фреймворки або бібліотеки (напр, debugging plugin for React or Angular)
- [ ] 🔵 Розуміє принцип версіонування packages та застосунків, зокрема semver. Розуміє принципи створення npm package та його публікації. Специфіка створення private package та подальшої роботи з ним (як задати npm_token, що таке .npmrc файл)
- [ ] 🟣 Вміє проєктувати структуру компонентів та їхнє функціональне призначення на рівні кодової архітектури застосунку (page components, feature components, components librabry etc)
- [ ] 🟣 Вміє створювати reusable/shared pieces of UI code (components, hooks, utils). Вміє ідентифікувати необхідність їхнього створення.
- [ ] 🔵 Розуміє види state-ів (component state, global state, server state, browser state). Розуміти методи пропагації даних (top-to-bottom – ReactContext, event injection – Redux)
- [ ] 🟣 Вміє інкапсулювати та структурувати state, напр. feature-based.
- [ ] 🟣 Розуміння clear/generic components, вміти обрати рівень state-у для збереження різних видів даних
- [ ] 🟣 Має розуміння, як оптимізувати великий UI-застосунок (використання lazy-loading, оптимізація bundle (chunks), правильна модуляризація)
- [ ] 🟢 Має базове поняття unit-testing (визначення, що потребує тестування, мати поняття про mocks, fakes; shallow, mount). Має розуміння про pre-conditions та post-conditions.
- [ ] 🔵 Знання принципів написання коду, який має high-testability (чисті та імутабельні функції, які є важливими для бізнес-логіки)
- [ ] 🟢 Має базове поняття e2e (що воно включає, чим відрізняється від unit-testing, хто його проводить, чому воно потрібне)

## Back-end (16)
<sub>🟣 7 · 🔵 3 · 🟢 6</sub>

- [ ] 🟢 Знає, що таке CORS і для чого потрібен.
- [ ] 🟢 Знає, що таке CSP.
- [ ] 🟣 Вміє працювати з TypeScript, знає основні features даної надбудови та ефективно їх застосовувати.
- [ ] 🟣 Вміє дизайнити API операції на REST API (на рівні контроллера або на рівні модуля, або знати коли певні види операцій потребують нового контроллера)
- [ ] 🔵 Розуміє, як працює JWT (які частини має, яку функцію несуть, як вони формуються, які стандартні поля можуть містити)
- [ ] 🟣 Вміє працювати з однією з популярних ORM (TypeORM, Prisma, Knex etc) – додати нове entity, писати запити з relations, aggregations, etc
- [ ] 🟢 Знає, що таке кешуваня, Redis, Memcache (які проблеми вирішує кешування, і які може створювати)
- [ ] 🟢 Знайомий з поняттями різних типів архітектур (мікро-сервісна, модульна, монолітна) (може пояснити на high-level навіщо кожна з них потрібна)
- [ ] 🟣 Вміє виконувати debugging серверного кода, та вирішення базових проблем (ефективне використання VSCode, Jetbrains IDE, etc) (вміє ставити breakpoints, а не console.(x), вміє налаштувати debug-mode в IDE)
- [ ] 🟢 Знає що таке token lifecycle, навіщо потрібні access_token, refresh_token. Знає good practicies по TTL, по їхньому формуванню та валідації.
- [ ] 🟣 Вміє використовувати ефективно інструменти асинхронного програмування – async/await, Promises, callbacks, setTimeout. Bluebird lib: async map. Конструкція: for ... of vs Promise.all.
- [ ] 🟢 Мати поняття про SSR та один з фреймворків для цього (NextJs, NuxtJs або інший). Розуміти, які є переваги SSR, навіщо нам це потрібно, які є обмеження. Вміти пояснити, що таке server pre-rendering (during build-time), data hydration,  file-based routing, fetch data from API. Чим відрізняється runtime NextJS від ReactJs?
- [ ] 🔵 Розуміти request scope (transient, singleton, scoped). Розуміти, як працює req обʼєкт, як перехоплювти та enrich-ати додатковими даними (на прикладі NestJS або іншого фреймворку).
- [ ] 🟣 Вміти реалізувати Global error handling (на прикладі NestJS або іншого фреймворку). Способи логування, та їх подальшого збору в систему моніторингу (stdout, file, json, etc).
- [ ] 🔵 Обмеження кількості запитів на окремі точки доступу (rate limiting on API endpoint). Розуміти основні методи та параметри rate-limit-інгу. Розуміти, які є особливості rate-limiting при використанні більше аніж однієї репліки застосунку.
- [ ] 🟣 Розуміє та вміє застосовувати WebSockets та SSE (server-side events). Розуміти, які є особливості роботи WebSockets та SSE при використанні більше аніж однієї репліки застосунку.

## Databases (11)
<sub>🟣 5 · 🔵 4 · 🟢 2</sub>

- [ ] 🟣 Вміє нормалізувати структури даних (1n 2n 3n).
- [ ] 🔵 Має розуміння транзакційності relational DB, коли і для чого використовувати.
- [ ] 🟣 Являється продвинутим користувачем IDE (DataGrip), вміє проводити аналіз запиту (EXPLAIN, etc), performance analysis (full scan, indexed scan)
- [ ] 🔵 Мати знання, коли потрібно використоувати ORM, а коли raw SQL
- [ ] 🟣 Вміє писати більш складні SQL запити, GROUP BY, nested SELECT, WITH statement, PARTITION  BY (for grouping), ROW NUMBER
- [ ] 🟢 Мати базові знання про DB triggers (e.g. for audit log at DB level)
- [ ] 🟢 Знає, як працюють не-реляційні бази даних: коли їх необхідно вибирати, як структурувати дані, коли варто деструктурувати дані (та які є фізичні обмеження зі сторони БД), як робити запити для отримання цих даних, flattening даних, навігація в даних, як можна (в теорії) масштабувати не-реляційні БД.
- [ ] 🔵 Має розуміння, які види бекапів є (incremental, full-backup), коли є сенс в кожному з них (залежно від розміру БД та сервісу розгортання БД)
- [ ] 🟣 Має розуміння транзакційності relational DB (вміти використовувати транзакції в одній з ORM), мати розуміння, як інший код може впливати на транзакції й чи він потребн всередині транзакції або ні.
- [ ] 🔵 Знати, що таке profiling SQL запитів, проводити аналіз slow query log
- [ ] 🟣 (опціонально) Вміти робити shared queries для команди (використовувати відповідні платформи)

## Code Delivery (10)
<sub>🟣 8 · 🔵 1 · 🟢 1</sub>

- [ ] 🟣 Вміє створювати прості Docker image, тестувати їх та деплоїти у хаб (e.g. Docker hub).
- [ ] 🟣 Вміє працювати на сервері через SSH (принаймні підключитись).
- [ ] 🟣 Налаштувати LLM flow для автоматичної перевірки простих security breaches (наприклад, забуті credentials), перед комітом коду в репозиторій.
- [ ] 🟣 Налаштувати LLM flow для автоматичної перевірки code convention перед комітом коду в репозиторій.
- [ ] 🟣 Вміти створювати serverless function (AWS Lambda або аналоги з інших Cloud providers). Розуміти принципову різницю між VM та serverless function.
- [ ] 🟣 Вміти працювати з Linux server (VPS), вміти зайти на Docker container та провести необхідний debugging. Знати базові команди ls, mkdir, vim, nano, pwd, cd.
- [ ] 🟢 Має базове розуміння необхідності IaC (infrastructure as code), e.g. Terraform, AWS Cloud Formation, etc. (потрібно розуміти принципи, які проблеми вирішує, та які методології infrastructure continuous integration & deployment існують, може навести приклад в якому IaC вирішує проблему мутації інфраструктурних ресурсів).
- [ ] 🟣 Розуміє принци роботи і написання основних видів CI/CD pipelines (писати базовий GitHub Actions, взаємодіяти з поточними, змінювати, вміти працювати з готовими шаблонами, вміти формувати LLM prompt для написання коректного pipeline).
- [ ] 🔵 Знання синтаксису та структуру yaml конфігурації (що таке локальні env, глобальні env, secrets, variables, що таке job, workflow, conditionals, etc, вміння уніфікувати pipeline для різних environments)
- [ ] 🟣 Вміє запускати автоматичне code quality, linting & tests у CI/CD pipeline (на якому етапі pipeline його потрібно робити, який порядок, як оптимізувати формування білдів). Multi-staging pipelines.

## Software Development Methodology (19)
<sub>🟣 1 · 🔵 14 · 🟢 4</sub>

- [ ] 🔵 Розуміє принцип роботи GitFlow, та продвинуті операції Git.
- [ ] 🔵 Розуміє принцип роботи GitFlow та Trunk-based develpoment, різницю між ними, основні переваги та недоліки.
- [ ] 🔵 Розуміти та пояснити різницю між Vibe coding та Agentic development (AI code engineering)
- [ ] 🔵 Що таке spec-driven development (AI-assisted)? Які є його елементи, яка послідовність операцій?
- [ ] 🔵 Мати розуміння, як робити reuse AI prompts для software development (AI agents skills, workflows, commands).
- [ ] 🔵 Розуміти значення принципів: DRY, KISS, YAGNI й як змушувати AI code assistants дотримуватися їх (та розпізнати їх порушення) aka "simplicity is the key"
- [ ] 🔵 Має розуміння SDLC (software-development lifecycle). Знати всі фази, в т.ч. support&maintenance
- [ ] 🟣 Вміє якісно покривати юніт-тестами функціонал за допомогою AI code assistants.
- [ ] 🔵 Мати впевнене розуміння роботи Agile методологій (Scrum, Kanban). Що є не-agile методологія (навести приклад)?
- [ ] 🔵 Знати, які є Agile Scrum церемонії, що вони вирішують, скільки мають тривати, etc.
- [ ] 🟢 Має базові поняття Event-driven architecture – які є переваги та недоліки (logging, tracing, retry strategy). Знати які можливі компоненти (queues, functions, triggers). Time-driven vs User-driven підходи (які є trade-offs, які можливі, та де потрібно оптимізувати виконання, а де не потрібно).
- [ ] 🟢 Знає що таке prototype, PoC, MVP (які між ними різниця, яка у них ціль).
- [ ] 🟢 Знайомий з SDD (spec-driven development), BDD (behaviour-driven development), DDD (domain-driven development)
- [ ] 🔵 Розуміння big О та можливості оптимізувати продуктивність коду.
- [ ] 🟢 Має поняття, що таке PRD (product requirement document) та TDD (technical design document).
- [ ] 🔵 Має знання та розуміння Creational patterns
- [ ] 🔵 Має знання та розуміння Behavioural patterns
- [ ] 🔵 Має знання та розуміння Structural patterns
- [ ] 🔵 Знати способи оцінки US (time, Fibonacci numbers, T-shirt size)
