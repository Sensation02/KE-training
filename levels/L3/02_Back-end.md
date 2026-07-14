---
category: Back-end
title: Back-end
level: L3 (Middle)
source: InterCode Competency Matrix — Full-stack
purpose: RAG knowledge base — навчальні матеріали
stack: NestJS + TypeScript, PostgreSQL (TypeORM/Prisma), SSE-стрімінг
lang: uk
legend: "🟣 треба добре знати · 🔵 знати · 🟢 поверхнево"
---

# Back-end (L3 / Middle)

> **Питання → Відповідь.** Кожен блок самодостатній (готовий чанк для RAG).
> Колір = наскільки глибоко вивчати: 🟣 треба добре знати · 🔵 знати · 🟢 поверхнево.

---

## Q1. Що таке CORS і навіщо він потрібен? 🟢

Браузер за замовчуванням **забороняє** сторінці з одного домену (`app.site.com`) робити запити на інший домен (`api.site.com`). Це захист, щоб зловмисний сайт не смикав від імені користувача чужий API. **CORS (Cross-Origin Resource Sharing)** — механізм, яким *сервер* повідомляє браузеру, яким доменам дозволено до нього звертатись.

**Ключове:** CORS перевіряє **браузер**, а не сервер. Тому CORS-помилку видно в консолі фронта, а не в логах бекенду; запити з Postman/curl CORS не обмежує. Для «непростих» запитів (кастомні заголовки, `PUT`/`DELETE`) браузер спершу шле **preflight** — запит `OPTIONS`, питаючи дозволу.

```ts
// main.ts (NestJS)
app.enableCors({
  origin: ["https://app.site.com"], // дозволені домени фронта
  credentials: true,                 // дозволити cookies
  methods: ["GET", "POST", "PATCH", "DELETE"],
});
```

**➕ Пов'язане: що таке preflight-запит і коли він шлеться? 🟢**
Preflight — автоматичний запит `OPTIONS`, який браузер шле **перед** основним, якщо запит «непростий» (метод не GET/POST/HEAD, або є кастомні заголовки типу `Authorization`). Сервер відповідає, які методи/заголовки/джерела дозволені; лише тоді браузер шле справжній запит.

**➕ Пов'язане: чи захищає CORS сам API від зловмисника? 🔵**
Ні. CORS обмежує лише **браузер** легітимного користувача. Зловмисник із curl/скрипта проігнорує CORS повністю. Тому CORS — не заміна автентифікації/авторизації: API все одно має перевіряти токен і права на кожен запит.

---

## Q2. Що таке CSP (Content Security Policy)? 🟢

CSP — «білий список» джерел, з яких сторінці дозволено вантажити код, стилі, зображення. Мета — захист від **XSS**: навіть якщо зловмисник вставив `<script>`, браузер відмовиться його виконати, якщо джерело не в списку. Задається HTTP-заголовком від сервера.

```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.site.com; img-src 'self' data:;
```

```ts
import helmet from "helmet"; // у NestJS зручно через helmet
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'", "https://cdn.site.com"],
    imgSrc: ["'self'", "data:"],
  },
}));
```

**Trade-off:** сувора CSP ламає inline-скрипти й сторонні віджети (треба свідомо додавати джерела); занадто м'яка (`unsafe-inline`) зводить захист нанівець.

**➕ Пов'язане: чим CSP відрізняється від CORS? 🟢**
Обидва — браузерні механізми, але про різне. **CORS** керує, з яких доменів можна *звертатися до твого API*. **CSP** керує, які джерела *твоя сторінка може завантажувати* (скрипти, стилі). CORS — про вихідні запити, CSP — про вхідні ресурси.

**➕ Пов'язане: що таке nonce/hash у CSP для inline-скриптів? 🟢**
Щоб дозволити конкретний inline-скрипт без небезпечного `unsafe-inline`, сервер додає до нього одноразовий `nonce` (випадкове число) або хеш вмісту, і вказує його в заголовку CSP. Браузер виконає лише скрипти з правильним nonce/хешем.

---

## Q3. Як ефективно працювати з TypeScript (основні фічі)? 🟣

TypeScript — це JavaScript із типами; на бекенді типи ловлять цілий клас багів *до* запуску (неправильне поле в DTO, забутий `null`, невірний контракт між сервісами). Важливо не просто «додати `: string`», а користуватись потужними фічами системи типів.

**1. Generics — перевикористовувані типізовані контейнери:**
```ts
type ApiResponse<T> = { data: T; meta: { page: number; total: number } };
function paginate<T>(items: T[], page: number): ApiResponse<T> {
  return { data: items, meta: { page, total: items.length } };
}
```

**2. Discriminated unions — безпечні варіанти:**
```ts
type IngestJob =
  | { status: "processing"; progress: number }
  | { status: "done"; chunks: number }
  | { status: "failed"; error: string };

function describe(job: IngestJob): string {
  switch (job.status) {
    case "processing": return `${job.progress}%`; // TS знає, що тут є progress
    case "done": return `${job.chunks} чанків`;
    case "failed": return job.error;
  }
}
```

**3. Utility types — похідні типи без дублювання:**
```ts
type Course = { id: string; title: string; expertId: string; createdAt: Date };
type CreateCourseDto = Omit<Course, "id" | "createdAt">;
type CourseUpdate = Partial<Pick<Course, "title">>;
```

**4. `unknown` замість `any` — безпечна робота з невідомим:**
```ts
function parse(raw: unknown): Course {
  if (typeof raw !== "object" || raw === null) throw new Error("bad payload");
  return raw as Course; // TS змусить перевірити перед використанням
}
```

**➕ Пов'язане: type чи interface — коли що? 🔵**
`interface` розширюваний (declaration merging, `extends`) — зручний для об'єктних контрактів і публічних API. `type` гнучкіший — union, intersection, mapped/conditional типи, примітиви. Практика: для форм об'єктів однаково добрі, але union і складні композиції — тільки `type`.

**➕ Пов'язане: що таке type guards і звуження (narrowing)? 🔵**
Narrowing — коли TS звужує тип за перевіркою (`typeof`, `in`, `instanceof`, порівняння з літералом). Type guard — функція-предикат `x is Course`, що навчає TS звужувати тип у розгалуженнях. Це те, що робить discriminated unions безпечними.

**➕ Пов'язане: навіщо `satisfies`? 🟢**
`satisfies` перевіряє, що значення відповідає типу, **не розширюючи й не втрачаючи** його конкретність. Напр. `const config = {...} satisfies Config` — отримаєш і перевірку відповідності, і точні літеральні типи полів (на відміну від анотації `: Config`, яка «стирає» конкретику).

---

## Q4. Як проєктувати REST API операції (контролер, модуль, коли новий контролер)? 🟣

REST — коли ресурси (курси, уроки, записи) виражені як URL, а дії — HTTP-методами (`GET` читати, `POST` створювати, `PATCH` оновлювати, `DELETE` видаляти). Головне рішення: **де живе операція** — у наявному контролері чи це вже окремий ресурс. Правило: один контролер = один ресурс.

```ts
@Controller("courses")
export class CoursesController {
  @Get() list(@Query() q: ListCoursesDto) {}          // GET /courses
  @Get(":id") getOne(@Param("id") id: string) {}       // GET /courses/:id
  @Post() create(@Body() dto: CreateCourseDto) {}      // POST /courses
  @Patch(":id") update(@Param("id") id: string, @Body() dto: UpdateCourseDto) {}
}
```

**Коли новий контролер, а не метод у наявному:** з'явився під-ресурс зі своїм життєвим циклом (`enrollments.controller.ts`), або окрема сутність (`agents.controller.ts`). **Вкладені ресурси** — через URL-ієрархію:
```ts
@Controller("courses/:courseId/lessons")
export class LessonsController {
  @Get() list(@Param("courseId") courseId: string) {}
}
```

**Модуль — межа фічі.** Якщо контролер відповідає за один ресурс, то `@Module` групує **все, що стосується цієї фічі**: контролери + провайдери (сервіси, репозиторії). Правило дзеркалить контролери: один модуль = одна доменна область. Новий модуль створюють не на кожен контролер, а коли з'явився окремий «шматок» системи (`payments`, `notifications`), а не просто ще один ендпоінт.
```ts
@Module({
  controllers: [CoursesController],
  providers: [CoursesService],   // внутрішнє, приватне для модуля
  exports: [CoursesService],     // що модуль віддає назовні
  imports: [DbModule],           // чужі модулі, чиї exports тут потрібні
})
export class CoursesModule {}
```
Саме `imports`/`exports` і є межею: `CoursesService` побачить інший модуль, лише якщо його **явно експортовано** і той зробив `imports: [CoursesModule]`. Тобто модуль ховає внутрішнє й віддає лише потрібне — інкапсуляція на рівні бекенду.

Погана ознака («RPC замість REST») — ендпоінти-дієслова типу `POST /createCourseAndEnroll`; краще окремі ресурсні операції.

**➕ Пов'язане: які HTTP статус-коди варто знати? 🔵**
`200` OK, `201` Created, `204` No Content; `400` Bad Request (невалідні дані), `401` Unauthorized (не автентифікований), `403` Forbidden (немає прав), `404` Not Found, `409` Conflict (напр. дубль), `422` Unprocessable Entity; `500` Internal Server Error. Різниця `401` vs `403` — часте питання: перше «не знаю, хто ти», друге «знаю, але тобі не можна».

**➕ Пов'язане: що таке ідемпотентність і які методи ідемпотентні? 🔵**
Ідемпотентний метод дає той самий результат при повторному виклику. `GET`, `PUT`, `DELETE` — ідемпотентні; `POST` — ні (два `POST` створять два записи). Важливо для ретраїв: клієнт може безпечно повторити `PUT`, але не `POST` (для нього застосовують ключі ідемпотентності).

**➕ Пов'язане: чим REST відрізняється від GraphQL/RPC? 🟢**
REST — ресурси й HTTP-методи, кілька ендпоінтів. **GraphQL** — один ендпоінт, клієнт сам описує, які поля хоче (розв'язує over/under-fetching), ціною складнішого сервера. **RPC/gRPC** — виклик віддалених «функцій», ефективний для внутрішньої комунікації сервісів.

---

## Q5. Як працює JWT (частини, поля, як формується)? 🔵

JWT (JSON Web Token) — «перепустка», яку сервер видає після логіну; клієнт шле її з кожним запитом, і сервер за нею впізнає користувача **без звернення до БД**, бо токен підписаний.

**Три частини** `header.payload.signature`:
- **Header** — алгоритм підпису (`HS256`, `RS256`);
- **Payload (claims)** — `sub` (id користувача), `exp` (протухання), `iat` (видано), + свої поля;
- **Signature** — підпис секретом сервера; підмінити payload не можна.

**Критично:** payload лише **закодований (base64), не зашифрований** — його видно будь-кому. Тому в JWT **не кладуть секрети**. Захищає підпис, а не таємність.

```ts
const token = this.jwt.sign(
  { sub: user.id, role: user.role }, // claims
  { expiresIn: "15m" },              // exp
);
const payload = this.jwt.verify(token); // кине помилку, якщо підпис/термін невірні
```

Стандартні claims: `sub`, `exp`, `iat`, `iss` (хто видав), `aud` (для кого).

**➕ Пов'язане: чим HS256 відрізняється від RS256? 🔵**
`HS256` — **симетричний**: той самий секрет і підписує, і перевіряє (простіше, але всі перевіряльники знають секрет). `RS256` — **асиметричний**: приватний ключ підписує, публічний перевіряє. RS256 кращий, коли токен перевіряють кілька сервісів — їм роздають лише публічний ключ, а підписувати може тільки auth-сервер.

**➕ Пов'язане: як «розлогінити» JWT до його `exp`? 🔵**
JWT самодостатній і не звертається до БД, тому його не можна просто «видалити» на сервері. Рішення: тримати короткий TTL access-токена + список відкликаних (denylist у Redis) для logout/компрометації, або зберігати `tokenVersion` у користувача й звіряти. Це компроміс: повертає частину «серверного стану», який JWT намагався прибрати.

---

## Q6. Як працювати з ORM (TypeORM/Prisma): entity, relations, aggregations? 🟣

ORM дозволяє працювати з базою як з об'єктами. Треба вміти: додати сутність, описати зв'язки, робити запити з відношеннями та агрегаціями.

```ts
@Entity("courses")
export class Course {
  @PrimaryGeneratedColumn("uuid") id: string;
  @Column() title: string;
  @OneToMany(() => Lesson, (l) => l.course) lessons: Lesson[]; // один-до-багатьох
}
@Entity("lessons")
export class Lesson {
  @PrimaryGeneratedColumn("uuid") id: string;
  @ManyToOne(() => Course, (c) => c.lessons) course: Course;
}
```

**Запит із relations:**
```ts
const course = await this.courseRepo.findOne({ where: { id }, relations: { lessons: true } });
```

**Aggregation через QueryBuilder:**
```ts
const stats = await this.enrollmentRepo.createQueryBuilder("e")
  .select("e.courseId", "courseId").addSelect("COUNT(*)", "students")
  .groupBy("e.courseId").getRawMany();
```

**Обережно з N+1** — тягнути relations одним JOIN, а не в циклі:
```ts
// ❌ N+1: запит на курси + по запиту на уроки кожного
for (const c of courses) c.lessons = await lessonRepo.find({ where: { courseId: c.id } });
// ✅ один запит із JOIN
const courses = await courseRepo.find({ relations: { lessons: true } });
```

**➕ Пов'язане: що таке міграції і чому не `synchronize: true` у проді? 🔵**
Міграція — версійований скрипт, що змінює схему БД (додати колонку, індекс). `synchronize: true` автоматично підганяє схему під entity — зручно локально, але в проді **небезпечно**: може мовчки видалити колонку з даними. У проді — тільки явні, переглянуті міграції.

**➕ Пов'язане: чим TypeORM відрізняється від Prisma? 🟢**
TypeORM — декоратори на класах-entity, підтримує Active Record і Data Mapper, гнучкий QueryBuilder. Prisma — окрема schema-мова + згенерований типобезпечний клієнт, чудовий DX і автокомпліт, але менше «сирого» контролю. Обидва вирішують ту саму задачу — вибір здебільшого про стиль і DX.

**➕ Пов'язане: що таке eager vs lazy loading relations? 🔵**
**Eager** — relations підвантажуються автоматично з основною сутністю (зручно, але тягне зайве). **Lazy** — підвантажуються лише при доступі (економніше, але легко впасти в N+1). Практика: relations вантажити явно під конкретний запит (`relations: {...}`), а не робити все eager.

---

## Q7. Що таке кешування, Redis, Memcache — які проблеми вирішує і які створює? 🟢

Кеш — швидке тимчасове сховище для даних, які дорого діставати щоразу (напр. список, що рідко змінюється, а читається часто). Знижує навантаження на БД і прискорює відповіді (Redis у пам'яті — мілісекунди).

**Redis vs Memcache:** Memcache — простий кеш «ключ-значення». Redis — теж швидкий, але вміє більше: структури даних, TTL, pub/sub, персистентність. Частіше беруть Redis.

```ts
async getCourses(expertId: string) {
  const key = `courses:${expertId}`;
  const cached = await this.redis.get(key);
  if (cached) return JSON.parse(cached);                           // швидкий шлях
  const courses = await this.courseRepo.find({ where: { expertId } });
  await this.redis.set(key, JSON.stringify(courses), "EX", 300);   // TTL 5 хв
  return courses;
}
```

**Які проблеми СТВОРЮЄ кеш:** інвалідація (створив запис — кеш віддає старе; треба чистити), устарілі дані (stale), додаткова складність. Правило: кешуй те, що часто читається й рідко змінюється, і завжди продумай, *коли* чистити.

**➕ Пов'язане: які є стратегії інвалідації? 🔵**
Головні: **TTL** (просто прострочити за часом), **write-through** (оновлювати кеш одночасно із записом у БД), **event-based** (чистити ключ на подію зміни). TTL простий, але допускає stale; write-through свіжіший, але складніший. Часто комбінують TTL + чистку ключа при зміні.

**➕ Пов'язане: що таке cache stampede (thundering herd)? 🟢**
Коли популярний ключ протухає, багато запитів одночасно промахуються повз кеш і разом б'ють по БД. Лікують: блокування на перерахунок (лише один рахує, решта чекають), «м'який» TTL із фоновим оновленням, невеликий випадковий джиттер до TTL, щоб ключі не протухали одночасно.

---

## Q8. Які бувають типи архітектур (моноліт, модульний моноліт, мікросервіси)? 🟢

Це про те, як «нарізаний» застосунок.
- **Моноліт** — весь код в одному застосунку, один деплой. Просто починати, легко дебажити.
- **Модульний моноліт** — один деплой, але код розділений на чіткі модулі з межами. Золота середина.
- **Мікросервіси** — багато окремих застосунків, кожен свій деплой і БД. Масштабуються незалежно, ціною складності (мережа, розподілені транзакції, моніторинг).

| | Моноліт | Мікросервіси |
|---|---|---|
| Складність старту | Низька | Висока |
| Незалежне масштабування | Ні | Так |
| Деплой | Один | Багато |
| Коли брати | MVP, мала команда | Велика система/команда |

Практичне правило: починати з модульного моноліту, різати на мікросервіси **лише за реальної потреби**. Передчасні мікросервіси — часта дорога помилка.

**➕ Пов'язане: що таке модуль у NestJS і навіщо межі модулів? 🔵**
Модуль — одиниця організації в NestJS (`@Module`), що групує контролери й провайдери й керує їхньою видимістю через `imports`/`exports`. Межі модулів — це і є «модульний моноліт» на практиці: кожна фіча (courses, chat, auth) інкапсульована, залежності явні, і згодом такий модуль легше винести в окремий сервіс.

**➕ Пов'язане: monorepo — це те саме, що моноліт? 🟢**
Ні. **Моноліт** — про рантайм (один застосунок, що деплоїться). **Monorepo** — про організацію коду (кілька проєктів/пакетів в одному репозиторії). У monorepo можуть жити і мікросервіси, і фронт, і спільні пакети одночасно.

---

## Q9. Як дебажити серверний код правильно (breakpoints, а не console.log)? 🟣

Дебагер дозволяє **зупинити код** у точці, подивитись усі змінні, пройти покроково — на відміну від розкиданих `console.log`.

```jsonc
// .vscode/launch.json
{
  "type": "node", "request": "launch", "name": "Debug Nest",
  "runtimeExecutable": "npm", "runtimeArgs": ["run", "start:debug"],
  "console": "integratedTerminal"
}
```
`start:debug` зазвичай `nest start --debug --watch`. Ставиш breakpoint → запускаєш Debug → на запиті код спиниться.

**Що вміє дебагер (і чого не дає console.log):** conditional breakpoint (спинитись лише коли `expertId === "X"`), step over/into (покроково, зайти у функцію), watch (стежити за виразом), call stack (звідки прийшов виклик).

```ts
async ingestDocument(dto: IngestDto) {
  const chunks = this.splitter.split(dto.text);          // ← breakpoint
  const embeddings = await this.embedder.embed(chunks);  // ← крок далі
  await this.vectorRepo.save(embeddings);
}
```

**➕ Пов'язане: що таке `--inspect` і як приєднати дебагер? 🔵**
`node --inspect` (або `nest start --debug`) відкриває дебаг-порт (9229), до якого приєднується інспектор — VS Code чи `chrome://inspect`. Так дебажать без вбудованого launch-конфіга, приєднавшись до вже запущеного процесу (attach), у т.ч. на віддаленому сервері.

**➕ Пов'язане: чим відрізняється дебаг у Docker? 🟢**
У контейнері треба, щоб `--inspect` слухав `0.0.0.0` (а не `127.0.0.1`) і порт 9229 був прокинутий назовні (`-p 9229:9229`). Тоді локальний VS Code приєднується до процесу всередині контейнера через attach-конфіг.

---

## Q10. Що таке token lifecycle: навіщо access_token і refresh_token, TTL, валідація? 🟢

Проблема: довгий access-токен небезпечний (вкрали = довгий доступ), короткий — постійно розлогінює. Рішення — **два токени**:
- **access_token** — короткий (15 хв), шлеться з кожним запитом;
- **refresh_token** — довгий (дні), зберігається безпечно (HttpOnly cookie), лише щоб отримати новий access.

```
login → access (15хв) + refresh (7дн)
access протух → клієнт шле refresh на /auth/refresh → сервер валідує → новий access
logout / refresh протух → логін заново
```

```ts
@Post("auth/refresh")
async refresh(@Body("refreshToken") token: string) {
  const payload = this.jwt.verify(token, { secret: REFRESH_SECRET }); // валідація підпису+терміну
  if (await this.isRevoked(token)) throw new UnauthorizedException();
  return { accessToken: this.issueAccess(payload.sub) };
}
```

Good practices: access короткий, refresh довший; refresh у HttpOnly cookie; уміти **відкликати** refresh (Redis/БД); rotation — на кожен refresh новий, старий гасити.

**➕ Пов'язане: що таке refresh token rotation і навіщо? 🔵**
Rotation — на кожному оновленні видавати **новий** refresh, а старий негайно гасити. Якщо вкрадений старий refresh спробують використати після того, як його вже «прокрутили» — сервер бачить повторне використання й може відкликати всю сесію. Це рання детекція крадіжки токена.

**➕ Пов'язане: де безпечно зберігати refresh на клієнті? 🟢**
Найбезпечніше — **HttpOnly + Secure + SameSite cookie**: JS до неї не має доступу (захист від XSS), і вона автоматично йде лише на ендпоінт `/auth/refresh`. localStorage — вразливий до XSS, тому для refresh не рекомендується.

---

## Q11. Як ефективно працювати з асинхронністю (async/await, Promises, паралелізм)? 🟣

Node.js однопотоковий — «чекання» (БД, LLM, диск) не має блокувати решту. Важливо розуміти, **коли паралельно, а коли послідовно**.

```ts
// ❌ послідовно: суми часів
const course = await getCourse(id);
const lessons = await getLessons(id);
// ✅ паралельно: незалежні запити разом → час ≈ max
const [course, lessons, agent] = await Promise.all([getCourse(id), getLessons(id), getAgent(id)]);
```

**Паралельно з обмеженням конкурентності** (щоб не забити LLM/БД):
```ts
import pLimit from "p-limit";
const limit = pLimit(5);
await Promise.all(docs.map((doc) => limit(() => ingest(doc))));
```

`Promise.all` падає весь при одній помилці; коли треба зібрати й успіхи, і фейли — `Promise.allSettled`. Пастка: `forEach` з async **не чекає** — використовуй `for...of` або `Promise.all`.

**➕ Пов'язане: що таке event loop у Node (macro/microtasks)? 🔵**
Event loop — цикл, що обробляє відкладені задачі. **Microtasks** (проміси, `queueMicrotask`) виконуються раніше — одразу після поточного коду, до наступної фази. **Macrotasks** (`setTimeout`, I/O) — у своїх фазах циклу. Тому `Promise.then` спрацює раніше за `setTimeout(…, 0)`.

**➕ Пов'язане: як «заблокувати» event loop і чому це погано? 🔵**
Синхронна важка операція (великий цикл, синхронний хеш, `JSON.parse` величезного тіла) тримає єдиний потік і **блокує всі** запити, поки не завершиться. Лікують: виносити CPU-важке у worker threads/окремий сервіс, розбивати на частини, використовувати async-варіанти API.

**➕ Пов'язане: що таке backpressure у стрімах? 🟢**
Коли джерело даних швидше за споживача (читаємо файл швидше, ніж пишемо в мережу), дані накопичуються в пам'яті. Backpressure — механізм, що пригальмовує джерело, поки споживач не наздожене (`pipe`/`pipeline` у Node роблять це автоматично).

---

## Q12. Що таке SSR і навіщо він потрібен (Next.js/Nuxt)? 🟢

У звичайному SPA браузер отримує майже порожній HTML і сам малює сторінку через JS. **SSR (Server-Side Rendering)** — сервер віддає готовий HTML одразу. Зиски: швидший перший показ і краще SEO.

Ключові поняття: **pre-rendering** (HTML генерується на сервері), **hydration** (браузер «оживляє» готовий HTML — навішує обробники), **file-based routing** (роут = файл), **fetch на сервері** (дані тягнуться до рендеру).

```tsx
// Next.js (App Router): дані фетчаться на СЕРВЕРІ
async function CoursePage({ params }: { params: { id: string } }) {
  const course = await getCourse(params.id); // виконується на сервері
  return <h1>{course.title}</h1>;
}
```

Коли треба: публічні сторінки з важливим SEO і швидким першим показом. Для закритої адмінки за логіном SSR майже не дає користі.

**➕ Пов'язане: чим SSG відрізняється від SSR? 🟢**
**SSG (Static Site Generation)** — HTML генерується **один раз під час білду** (блог, документація); найшвидше, але контент статичний до наступного білду. **SSR** — HTML генерується **на кожен запит** (персоналізовані/свіжі дані). Next дозволяє обидва, навіть на різних сторінках одного застосунку.

**➕ Пов'язане: що таке hydration mismatch? 🟢**
Помилка, коли HTML, згенерований на сервері, не збігається з тим, що React очікує намалювати на клієнті (напр. рендер `Date.now()` чи `window`). React лається й перемальовує. Лікують: не використовувати клієнт-специфічне під час серверного рендеру, вивіряти детермінованість виводу.

---

## Q13. Що таке request scope (transient/singleton/scoped) і як працює об'єкт req? 🔵

У NestJS сервіси за замовчуванням — **singleton** (один екземпляр на застосунок). Іноді потрібен окремий екземпляр *на кожен запит* (зберегти контекст тенанта/користувача) — це scope.

- **`DEFAULT` (singleton)** — один назавжди, найшвидше;
- **`REQUEST` (scoped)** — новий на кожен запит, має доступ до `req`, дорожче;
- **`TRANSIENT`** — новий щоразу при інжекті.

```ts
@Injectable({ scope: Scope.REQUEST })
export class TenantContext {
  constructor(@Inject(REQUEST) private req: Request) {}
  get expertId(): string { return this.req.headers["x-tenant-id"] as string; }
}
```

**Об'єкт `req`** — вхідний HTTP-запит: headers, body, query, params + те, що додали middleware/guards (`req.user`). Збагачують через middleware:
```ts
@Injectable()
export class TenantMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    (req as any).expertId = req.headers["x-tenant-id"]; // enrich
    next();
  }
}
```

Trade-off: `REQUEST` scope зручний, але кожен запит створює нові екземпляри (і залежностей) — повільніше. Не роби scoped усе підряд.

**➕ Пов'язане: чим відрізняються middleware / guard / interceptor / pipe? 🔵**
Це етапи обробки запиту в NestJS: **middleware** — найраніше, до роутингу (логування, enrich req); **guard** — вирішує «пускати чи ні» (авторизація); **pipe** — валідує/трансформує вхідні дані (DTO); **interceptor** — обгортає виклик до і після (логування часу, трансформація відповіді). Порядок: middleware → guard → interceptor → pipe → handler.

**➕ Пов'язане: що таке DI-контейнер і як NestJS резолвить залежності? 🔵**
NestJS має контейнер інверсії керування: ти оголошуєш `@Injectable`-провайдери, а фреймворк сам створює й підставляє їх у конструктори за типом. Це прибирає ручне `new`, спрощує заміну реалізацій (напр. mock у тестах) і керує їхнім життєвим циклом (scope).

---

## Q14. Як реалізувати Global error handling і логування? 🟣

Помилки не мають протікати до клієнта стектрейсами чи падати мовчки. Потрібна **одна точка**, що ловить будь-яку помилку, повертає акуратну відповідь і пише лог. У NestJS це **exception filter**.

```ts
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger("Exceptions");
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const res = ctx.getResponse<Response>();
    const req = ctx.getRequest<Request>();
    const status = exception instanceof HttpException ? exception.getStatus() : 500;
    const message = exception instanceof HttpException
      ? exception.getResponse() : "Internal server error"; // не світимо деталі назовні
    this.logger.error({ status, path: req.url, method: req.method,
      error: exception instanceof Error ? exception.stack : String(exception) });
    res.status(status).json({ statusCode: status, message, path: req.url });
  }
}
app.useGlobalFilters(new AllExceptionsFilter());
```

**Логування** — друга половина питання. Стандарт у контейнерах: писати **structured JSON у stdout** (збирач Loki/ELK/Datadog підхоплює звідти, файли не потрібні). Реалізують структурованим логером `nestjs-pino`, який ще й **сам логує кожен HTTP-запит** із request-id:
```ts
// app.module.ts — підключення
LoggerModule.forRoot({
  pinoHttp: {
    autoLogging: true,                                     // рядок логу на кожен запит
    genReqId: (req) => req.headers["x-request-id"] ?? randomUUID(),
    redact: ["req.headers.authorization"],                 // не писати секрети в лог
  },
});
app.useLogger(app.get(Logger)); // Nest використовує pino замість дефолтного логера
```
Кожен запит дає структурований рядок, зручний для пошуку й фільтрації у збирачі:
```json
{"level":"info","reqId":"a1b2","method":"POST","url":"/courses","statusCode":201,"responseTime":42}
```
Ідея: клієнту — чиста відповідь, а в лог — повний контекст структуровано, з request-id для зшивання всього ланцюга однієї операції.

**➕ Пов'язане: чим exception filter відрізняється від interceptor? 🔵**
**Interceptor** обгортає нормальний потік — може змінити відповідь, заміряти час, трансформувати дані (працює й на успіху). **Exception filter** спрацьовує **лише коли кинуто виняток** — його задача перетворити помилку на HTTP-відповідь. Тобто interceptor — про успішний і винятковий шлях, filter — тільки про винятковий.

**➕ Пов'язане: що таке correlation/request id і навіщо? 🔵**
Унікальний id, який присвоюють кожному запиту (з заголовка `X-Request-Id` або генерують) і додають до кожного лог-рядка цього запиту. Дозволяє в морі логів (особливо між сервісами) зібрати весь ланцюг однієї операції — незамінне при розслідуванні інцидентів.

---

## Q15. Що таке rate limiting і його особливості при кількох репліках? 🔵

Rate limiting — обмеження кількості запитів від клієнта за проміжок часу. Навіщо: захист від зловживань (брутфорс) і від перевантаження дорогих ендпоінтів (виклики LLM коштують грошей).

Параметри: **ліміт** (скільки), **вікно** (за який час), **ключ** (на кого — IP, userId).

```ts
@Throttle({ default: { limit: 10, ttl: 60_000 } }) // 10 запитів / 60с
@Post("chat/message")
sendMessage(@Body() dto: ChatDto) {}
```

**Особливість — кілька реплік:** якщо лічильник у пам'яті кожної репліки, ліміт «розмивається» (3 репліки × 10 = 30 проходить). Рішення — **спільне сховище** (Redis), одне на всі репліки:
```ts
ThrottlerModule.forRoot({
  throttlers: [{ limit: 10, ttl: 60_000 }],
  storage: new ThrottlerStorageRedisService(redis),
});
```

**➕ Пов'язане: чим token bucket відрізняється від sliding window? 🔵**
**Fixed window** — рахує запити у фіксованому вікні (просто, але сплеск на межі двох вікон). **Sliding window** — рухоме вікно, точніше згладжує. **Token bucket** — «відро» токенів, що поповнюється зі сталою швидкістю: дозволяє короткі сплески (накопичені токени), але тримає середню швидкість. Bucket — найгнучкіший для API.

**➕ Пов'язане: де ставити rate limit — у застосунку чи на gateway? 🟢**
Часто на обох рівнях. **API Gateway / reverse proxy** (nginx, Kong) — груба перша лінія за IP, знімає навантаження ще до застосунку. **У застосунку** — точні ліміти за userId/планом/ендпоінтом, де вже є контекст авторизації. Gateway дешевший, застосунок — розумніший.

---

## Q16. Що таке WebSockets і SSE, коли що брати, і особливості при кількох репліках? 🟣

Звичайний HTTP: спитав — відповів — закрив. Для «живих» даних (стрім відповіді агента, нотифікації) потрібен постійний канал.
- **SSE (Server-Sent Events)** — **односторонній** потік сервер→клієнт поверх HTTP. Простий, авто-reconnect, ідеальний для **стрімінгу LLM токен-за-токеном**.
- **WebSockets** — **двосторонній** постійний канал. Потрібен, коли клієнт теж активно шле (реалтайм-чат, колаборація).

| | SSE | WebSockets |
|---|---|---|
| Напрям | Сервер → клієнт | Двосторонній |
| Протокол | HTTP | ws:// |
| Коли | Стрім LLM, нотифікації | Реалтайм-чат, колаборація |

```ts
@Sse("chat/stream") // SSE-стрім відповіді агента
streamAnswer(@Query("q") q: string): Observable<MessageEvent> {
  return this.agent.stream(q).pipe(map((token) => ({ data: { token } }) as MessageEvent));
}
// клієнт — рідний EventSource, без бібліотек:
// const es = new EventSource("/api/chat/stream?q=...");
```

**Особливість при кількох репліках:** з'єднання прив'язане до конкретної репліки; подія на іншій репліці клієнта не дістане. Рішення: **sticky sessions** (тримати клієнта на тій самій репліці) та/або **Redis Pub/Sub adapter** (репліки обмінюються подіями через Redis).

**➕ Пов'язане: чим WebSocket відрізняється від long-polling? 🟢**
**Long-polling** — клієнт шле запит, сервер тримає його відкритим до появи даних, потім клієнт одразу шле новий (імітація «пушу» поверх звичайного HTTP). **WebSocket** — одне справжнє постійне двостороннє з'єднання, без повторних запитів. Long-polling — старий фолбек; WebSocket ефективніший, коли підтримується.

**➕ Пов'язане: як тримати WS-з'єднання живим (heartbeat)? 🔵**
Проксі/файрволи рвуть «тихі» з'єднання. Тому періодично шлють ping/pong (heartbeat); якщо на ping немає pong за таймаут — з'єднання вважають мертвим і перепідключаються. Socket.IO робить це автоматично; на «голому» WS реалізують вручну.

**➕ Пов'язане: як автентифікувати WebSocket-з'єднання? 🔵**
У WS немає заголовків на кожне повідомлення, тому токен передають при handshake — через query-параметр, під-протокол або першим повідомленням — і валідують у guard на підключенні. Далі з'єднання вважається автентифікованим; при протуханні токена його розривають.

---

*Кінець категорії Back-end. Наступний файл: `03_Databases.md`.*
