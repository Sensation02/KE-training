// Cloudflare Pages Function: прогрес користувача в KV (env.STUDY_STATE).
// Ідентичність береться з заголовка Cloudflare Access, який ставить сам Access
// (Access стоїть перед усім сайтом, тож підробити заголовок ззовні не можна).

const LEVEL_RE = /^[a-z0-9_-]{1,20}$/;
const MAX_BODY_BYTES = 64 * 1024;

function json(data, status) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

// Спільні перевірки для GET/PUT: користувач → рівень → наявність KV-біндингу.
// Повертає або {error: Response}, або {key} для подальшої роботи з KV.
function authorize(request, env) {
  const email = request.headers.get("Cf-Access-Authenticated-User-Email");
  if (!email) return { error: json({ error: "unauthorized" }, 401) };

  const level = new URL(request.url).searchParams.get("level") || "";
  if (!LEVEL_RE.test(level)) return { error: json({ error: "bad_level" }, 400) };

  if (!env.STUDY_STATE) return { error: json({ error: "kv_unavailable" }, 503) };

  return { key: `state:${email}:${level}` };
}

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

export async function onRequestPut({ request, env }) {
  const ctx = authorize(request, env);
  if (ctx.error) return ctx.error;

  // Розмір рахуємо з фактичного тіла (Content-Length може бути відсутнім/невірним).
  const text = await request.text();
  if (new TextEncoder().encode(text).length > MAX_BODY_BYTES) {
    return json({ error: "too_large" }, 413);
  }

  let body;
  try {
    body = JSON.parse(text);
  } catch (e) {
    return json({ error: "invalid_json" }, 400);
  }
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    return json({ error: "invalid_body" }, 400);
  }

  await env.STUDY_STATE.put(ctx.key, text);
  return json({ ok: true }, 200);
}

// Фолбек для будь-якого методу, крім GET/PUT (onRequestGet/onRequestPut мають пріоритет).
export async function onRequest() {
  return new Response(JSON.stringify({ error: "method_not_allowed" }), {
    status: 405,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", Allow: "GET, PUT" },
  });
}
