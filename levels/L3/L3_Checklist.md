# L3 Full-stack — чеклист компетенцій

> Мітки глибини: 🟣 треба добре знати · 🔵 знати · 🟢 поверхнево.  
> Відмічай `[x]`, коли впевнено знаєш пункт. Тільки технічні категорії (по них оцінюють на знаннях).

**Всього: 73 пунктів** — 🟣 31 · 🔵 27 · 🟢 15

---

## Front-End (17)
<sub>🟣 10 · 🔵 5 · 🟢 2</sub>

- [ ] 🔵 Має навики перехоплення запитів (interceptors, transient requests, global error handling). <!-- q:front-end/Q1 -->
- [ ] 🟣 Вміє налаштувати з нуля UI-бібліотеки на проєкті (Mantine, Ant, shadcn, etc) <!-- q:front-end/Q2 -->
- [ ] 🟣 Вміє вибирати бібліотеки (npm package) для UI-них завдань (e.g.: date-time management, ). Розуміти, як це впливає на розмір bundle, на performance, вміє використовувати bundle analyzer. Опціонально: bundlephobia <!-- q:front-end/Q3 -->
- [ ] 🟣 Має розуміння та вміє використовувати state-manager в UI-frameworks (Redux, react-query, React Context, Zustand) <!-- q:front-end/Q4 -->
- [ ] 🔵 Має розуміння роботи local storage, session storage, cookies та їхнє можливе використання. Знає їхні обмеження, переваги з точки зору security <!-- q:front-end/Q5 -->
- [ ] 🟣 Вміє правильно та ефективно використовувати дебаггінг у браузері (profiling, може ідентифікувати performance issues and bottlnecks за допомогою інструментів браузера) <!-- q:front-end/Q6 -->
- [ ] 🟣 Знає та вміє використовувати специфічні інструменти під фреймворки або бібліотеки (напр, debugging plugin for React or Angular) <!-- q:front-end/Q7 -->
- [ ] 🔵 Розуміє принцип версіонування packages та застосунків, зокрема semver. Розуміє принципи створення npm package та його публікації. Специфіка створення private package та подальшої роботи з ним (як задати npm_token, що таке .npmrc файл) <!-- q:front-end/Q8 -->
- [ ] 🟣 Вміє проєктувати структуру компонентів та їхнє функціональне призначення на рівні кодової архітектури застосунку (page components, feature components, components librabry etc) <!-- q:front-end/Q9 -->
- [ ] 🟣 Вміє створювати reusable/shared pieces of UI code (components, hooks, utils). Вміє ідентифікувати необхідність їхнього створення. <!-- q:front-end/Q10 -->
- [ ] 🔵 Розуміє види state-ів (component state, global state, server state, browser state). Розуміти методи пропагації даних (top-to-bottom – ReactContext, event injection – Redux) <!-- q:front-end/Q11 -->
- [ ] 🟣 Вміє інкапсулювати та структурувати state, напр. feature-based. <!-- q:front-end/Q12 -->
- [ ] 🟣 Розуміння clear/generic components, вміти обрати рівень state-у для збереження різних видів даних <!-- q:front-end/Q13 -->
- [ ] 🟣 Має розуміння, як оптимізувати великий UI-застосунок (використання lazy-loading, оптимізація bundle (chunks), правильна модуляризація) <!-- q:front-end/Q14 -->
- [ ] 🟢 Має базове поняття unit-testing (визначення, що потребує тестування, мати поняття про mocks, fakes; shallow, mount). Має розуміння про pre-conditions та post-conditions. <!-- q:front-end/Q15 -->
- [ ] 🔵 Знання принципів написання коду, який має high-testability (чисті та імутабельні функції, які є важливими для бізнес-логіки) <!-- q:front-end/Q16 -->
- [ ] 🟢 Має базове поняття e2e (що воно включає, чим відрізняється від unit-testing, хто його проводить, чому воно потрібне) <!-- q:front-end/Q17 -->

## Back-end (16)
<sub>🟣 7 · 🔵 3 · 🟢 6</sub>

- [ ] 🟢 Знає, що таке CORS і для чого потрібен. <!-- q:back-end/Q1 -->
- [ ] 🟢 Знає, що таке CSP. <!-- q:back-end/Q2 -->
- [ ] 🟣 Вміє працювати з TypeScript, знає основні features даної надбудови та ефективно їх застосовувати. <!-- q:back-end/Q3 -->
- [ ] 🟣 Вміє дизайнити API операції на REST API (на рівні контроллера або на рівні модуля, або знати коли певні види операцій потребують нового контроллера) <!-- q:back-end/Q4 -->
- [ ] 🔵 Розуміє, як працює JWT (які частини має, яку функцію несуть, як вони формуються, які стандартні поля можуть містити) <!-- q:back-end/Q5 -->
- [ ] 🟣 Вміє працювати з однією з популярних ORM (TypeORM, Prisma, Knex etc) – додати нове entity, писати запити з relations, aggregations, etc <!-- q:back-end/Q6 -->
- [ ] 🟢 Знає, що таке кешуваня, Redis, Memcache (які проблеми вирішує кешування, і які може створювати) <!-- q:back-end/Q7 -->
- [ ] 🟢 Знайомий з поняттями різних типів архітектур (мікро-сервісна, модульна, монолітна) (може пояснити на high-level навіщо кожна з них потрібна) <!-- q:back-end/Q8 -->
- [ ] 🟣 Вміє виконувати debugging серверного кода, та вирішення базових проблем (ефективне використання VSCode, Jetbrains IDE, etc) (вміє ставити breakpoints, а не console.(x), вміє налаштувати debug-mode в IDE) <!-- q:back-end/Q9 -->
- [ ] 🟢 Знає що таке token lifecycle, навіщо потрібні access_token, refresh_token. Знає good practicies по TTL, по їхньому формуванню та валідації. <!-- q:back-end/Q10 -->
- [ ] 🟣 Вміє використовувати ефективно інструменти асинхронного програмування – async/await, Promises, callbacks, setTimeout. Bluebird lib: async map. Конструкція: for ... of vs Promise.all. <!-- q:back-end/Q11 -->
- [ ] 🟢 Мати поняття про SSR та один з фреймворків для цього (NextJs, NuxtJs або інший). Розуміти, які є переваги SSR, навіщо нам це потрібно, які є обмеження. Вміти пояснити, що таке server pre-rendering (during build-time), data hydration,  file-based routing, fetch data from API. Чим відрізняється runtime NextJS від ReactJs? <!-- q:back-end/Q12 -->
- [ ] 🔵 Розуміти request scope (transient, singleton, scoped). Розуміти, як працює req обʼєкт, як перехоплювти та enrich-ати додатковими даними (на прикладі NestJS або іншого фреймворку). <!-- q:back-end/Q13 -->
- [ ] 🟣 Вміти реалізувати Global error handling (на прикладі NestJS або іншого фреймворку). Способи логування, та їх подальшого збору в систему моніторингу (stdout, file, json, etc). <!-- q:back-end/Q14 -->
- [ ] 🔵 Обмеження кількості запитів на окремі точки доступу (rate limiting on API endpoint). Розуміти основні методи та параметри rate-limit-інгу. Розуміти, які є особливості rate-limiting при використанні більше аніж однієї репліки застосунку. <!-- q:back-end/Q15 -->
- [ ] 🟣 Розуміє та вміє застосовувати WebSockets та SSE (server-side events). Розуміти, які є особливості роботи WebSockets та SSE при використанні більше аніж однієї репліки застосунку. <!-- q:back-end/Q16 -->

## Databases (11)
<sub>🟣 5 · 🔵 4 · 🟢 2</sub>

- [ ] 🟣 Вміє нормалізувати структури даних (1n 2n 3n). <!-- q:databases/Q1 -->
- [ ] 🔵 Має розуміння транзакційності relational DB, коли і для чого використовувати. <!-- q:databases/Q2 -->
- [ ] 🟣 Являється продвинутим користувачем IDE (DataGrip), вміє проводити аналіз запиту (EXPLAIN, etc), performance analysis (full scan, indexed scan) <!-- q:databases/Q3 -->
- [ ] 🔵 Мати знання, коли потрібно використоувати ORM, а коли raw SQL <!-- q:databases/Q4 -->
- [ ] 🟣 Вміє писати більш складні SQL запити, GROUP BY, nested SELECT, WITH statement, PARTITION  BY (for grouping), ROW NUMBER <!-- q:databases/Q5 -->
- [ ] 🟢 Мати базові знання про DB triggers (e.g. for audit log at DB level) <!-- q:databases/Q6 -->
- [ ] 🟢 Знає, як працюють не-реляційні бази даних: коли їх необхідно вибирати, як структурувати дані, коли варто деструктурувати дані (та які є фізичні обмеження зі сторони БД), як робити запити для отримання цих даних, flattening даних, навігація в даних, як можна (в теорії) масштабувати не-реляційні БД. <!-- q:databases/Q7 -->
- [ ] 🔵 Має розуміння, які види бекапів є (incremental, full-backup), коли є сенс в кожному з них (залежно від розміру БД та сервісу розгортання БД) <!-- q:databases/Q8 -->
- [ ] 🟣 Має розуміння транзакційності relational DB (вміти використовувати транзакції в одній з ORM), мати розуміння, як інший код може впливати на транзакції й чи він потребн всередині транзакції або ні. <!-- q:databases/Q9 -->
- [ ] 🔵 Знати, що таке profiling SQL запитів, проводити аналіз slow query log <!-- q:databases/Q10 -->
- [ ] 🟣 (опціонально) Вміти робити shared queries для команди (використовувати відповідні платформи) <!-- q:databases/Q11 -->

## Code Delivery (10)
<sub>🟣 8 · 🔵 1 · 🟢 1</sub>

- [ ] 🟣 Вміє створювати прості Docker image, тестувати їх та деплоїти у хаб (e.g. Docker hub). <!-- q:code-delivery/Q1 -->
- [ ] 🟣 Вміє працювати на сервері через SSH (принаймні підключитись). <!-- q:code-delivery/Q2 -->
- [ ] 🟣 Налаштувати LLM flow для автоматичної перевірки простих security breaches (наприклад, забуті credentials), перед комітом коду в репозиторій. <!-- q:code-delivery/Q3 -->
- [ ] 🟣 Налаштувати LLM flow для автоматичної перевірки code convention перед комітом коду в репозиторій. <!-- q:code-delivery/Q4 -->
- [ ] 🟣 Вміти створювати serverless function (AWS Lambda або аналоги з інших Cloud providers). Розуміти принципову різницю між VM та serverless function. <!-- q:code-delivery/Q5 -->
- [ ] 🟣 Вміти працювати з Linux server (VPS), вміти зайти на Docker container та провести необхідний debugging. Знати базові команди ls, mkdir, vim, nano, pwd, cd. <!-- q:code-delivery/Q6 -->
- [ ] 🟢 Має базове розуміння необхідності IaC (infrastructure as code), e.g. Terraform, AWS Cloud Formation, etc. (потрібно розуміти принципи, які проблеми вирішує, та які методології infrastructure continuous integration & deployment існують, може навести приклад в якому IaC вирішує проблему мутації інфраструктурних ресурсів). <!-- q:code-delivery/Q7 -->
- [ ] 🟣 Розуміє принци роботи і написання основних видів CI/CD pipelines (писати базовий GitHub Actions, взаємодіяти з поточними, змінювати, вміти працювати з готовими шаблонами, вміти формувати LLM prompt для написання коректного pipeline). <!-- q:code-delivery/Q8 -->
- [ ] 🔵 Знання синтаксису та структуру yaml конфігурації (що таке локальні env, глобальні env, secrets, variables, що таке job, workflow, conditionals, etc, вміння уніфікувати pipeline для різних environments) <!-- q:code-delivery/Q9 -->
- [ ] 🟣 Вміє запускати автоматичне code quality, linting & tests у CI/CD pipeline (на якому етапі pipeline його потрібно робити, який порядок, як оптимізувати формування білдів). Multi-staging pipelines. <!-- q:code-delivery/Q10 -->

## Software Development Methodology (19)
<sub>🟣 1 · 🔵 14 · 🟢 4</sub>

- [ ] 🔵 Розуміє принцип роботи GitFlow, та продвинуті операції Git. <!-- q:methodology/Q1 -->
- [ ] 🔵 Розуміє принцип роботи GitFlow та Trunk-based develpoment, різницю між ними, основні переваги та недоліки. <!-- q:methodology/Q2 -->
- [ ] 🔵 Розуміти та пояснити різницю між Vibe coding та Agentic development (AI code engineering) <!-- q:methodology/Q3 -->
- [ ] 🔵 Що таке spec-driven development (AI-assisted)? Які є його елементи, яка послідовність операцій? <!-- q:methodology/Q4 -->
- [ ] 🔵 Мати розуміння, як робити reuse AI prompts для software development (AI agents skills, workflows, commands). <!-- q:methodology/Q5 -->
- [ ] 🔵 Розуміти значення принципів: DRY, KISS, YAGNI й як змушувати AI code assistants дотримуватися їх (та розпізнати їх порушення) aka "simplicity is the key" <!-- q:methodology/Q6 -->
- [ ] 🔵 Має розуміння SDLC (software-development lifecycle). Знати всі фази, в т.ч. support&maintenance <!-- q:methodology/Q7 -->
- [ ] 🟣 Вміє якісно покривати юніт-тестами функціонал за допомогою AI code assistants. <!-- q:methodology/Q8 -->
- [ ] 🔵 Мати впевнене розуміння роботи Agile методологій (Scrum, Kanban). Що є не-agile методологія (навести приклад)? <!-- q:methodology/Q9 -->
- [ ] 🔵 Знати, які є Agile Scrum церемонії, що вони вирішують, скільки мають тривати, etc. <!-- q:methodology/Q10 -->
- [ ] 🟢 Має базові поняття Event-driven architecture – які є переваги та недоліки (logging, tracing, retry strategy). Знати які можливі компоненти (queues, functions, triggers). Time-driven vs User-driven підходи (які є trade-offs, які можливі, та де потрібно оптимізувати виконання, а де не потрібно). <!-- q:methodology/Q11 -->
- [ ] 🟢 Знає що таке prototype, PoC, MVP (які між ними різниця, яка у них ціль). <!-- q:methodology/Q12 -->
- [ ] 🟢 Знайомий з SDD (spec-driven development), BDD (behaviour-driven development), DDD (domain-driven development) <!-- q:methodology/Q13 -->
- [ ] 🔵 Розуміння big О та можливості оптимізувати продуктивність коду. <!-- q:methodology/Q14 -->
- [ ] 🟢 Має поняття, що таке PRD (product requirement document) та TDD (technical design document). <!-- q:methodology/Q15 -->
- [ ] 🔵 Має знання та розуміння Creational patterns <!-- q:methodology/Q16 -->
- [ ] 🔵 Має знання та розуміння Behavioural patterns <!-- q:methodology/Q17 -->
- [ ] 🔵 Має знання та розуміння Structural patterns <!-- q:methodology/Q18 -->
- [ ] 🔵 Знати способи оцінки US (time, Fibonacci numbers, T-shirt size) <!-- q:methodology/Q19 -->
