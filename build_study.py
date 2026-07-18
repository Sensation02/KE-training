#!/usr/bin/env python3
"""Генератор інтерактивних навчальних застосунків KE Training.

Читає рівні з levels/*/ (кожен — піддиректорія з розділами NN_*.md
і одним файлом *_Checklist.md), парсить питання/відповіді та пункти
компетенцій, і для кожного рівня вбудовує дані як JSON у
study_template.html. Результат — самодостатні dist/<рівень>/index.html
(відкриваються подвійним кліком або через Cloudflare Pages) плюс
кореневий dist/index.html зі списком рівнів і dist/404.html для
неіснуючих шляхів (Cloudflare Pages підхоплює його автоматично).

Додавання нового рівня (L2, L4, …) — це просто нова піддиректорія
levels/<Рівень>/ з розділами й чеклистом; код нічого міняти не треба.

Запуск:  python3 build_study.py
         python3 build_study.py --check  # лише парсинг + валідація, без запису dist/
"""
import argparse
import json
import re
import pathlib
import sys

import pwa_assets

ROOT = pathlib.Path(__file__).parent
LEVELS_DIR = ROOT / "levels"
DIST_DIR = ROOT / "dist"

SECTION_RE = re.compile(r"^(\d+)_.+\.md$")

# емодзі глибини → внутрішній код
DEPTH = {"🟣": "deep", "🔵": "mid", "🟢": "aware"}

# блок «🎯 Відповідь на іспиті» — обов'язковий ПЕРШИЙ абзац кожної відповіді:
# еталонна усна відповідь для флеш-карток (див. ANSWER_SCHEMA.md). Витягується
# в окреме поле "exam" і прибирається з "md" (у читалці рендериться окремо).
EXAM_RE = re.compile(r"^\*\*🎯 Відповідь на іспиті:\*\*\s*(.+?)(?:\n\s*\n|\Z)", re.S)

# пункт чеклиста: '- [ ] 🟣|🔵|🟢 текст'. ЄДИНИЙ регекс і для парсингу
# (parse_checklist), і для валідації (validate_checklist_lines) — щоб вони
# ніколи не розійшлись: рядок, схожий на пункт (починається з '- [' після
# trim), але не зматчений САМЕ цим регексом, — це помилка перевірки,
# а не мовчазний пропуск.
CHECKLIST_ITEM_RE = re.compile(r"^- \[[ xX]\] (🟣|🔵|🟢)\s*(.*)$")

# посилання пункту чеклиста на питання, що його покривають:
# '<!-- q:front-end/Q1 -->' або кілька через кому '<!-- q:front-end/Q1, back-end/Q3 -->'.
# HTML-коментар — щоб у звичайному перегляді .md посилання не було видно.
CHECKLIST_QREF_RE = re.compile(r"<!--\s*q:\s*([^>]*?)\s*-->")


def parse_frontmatter(text):
    """Повертає (meta: dict, body: str)."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta, body = {}, text
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = text[m.end():]
    return meta, body


def strip_depth(title):
    """Витягує емодзі глибини з кінця заголовка. → (title_clean, depth_code)."""
    title = title.rstrip()
    for emoji, code in DEPTH.items():
        if title.endswith(emoji):
            return title[: -len(emoji)].rstrip(), code
    return title, "mid"


def parse_questions(body):
    """Розбиває тіло на блоки '## QN. Заголовок'."""
    parts = re.split(r"(?m)^## (Q\d+)\.[ ]*(.*)$", body)
    questions = []
    for i in range(1, len(parts), 3):
        num = parts[i]
        title, depth = strip_depth(parts[i + 1])
        answer = parts[i + 2].strip()
        # прибрати роздільник '---', що стоїть перед наступним питанням
        answer = re.sub(r"\s*\n---\s*$", "", answer).strip()
        exam = ""
        m = EXAM_RE.match(answer)
        if m:
            exam = m.group(1).strip()
            answer = answer[m.end():].strip()
        questions.append(
            {"id": num, "title": title, "depth": depth, "exam": exam, "md": answer}
        )
    return questions


def parse_checklist(text):
    """Категорії чеклиста з пунктами компетенцій.

    З тексту пункту витягуються (і прибираються) посилання на питання
    <!-- q:section/QN, ... --> — вони йдуть у поле "qs" як ключі
    'section:QN' (той самий формат, що qkey() у шаблоні).
    """
    cats = []
    cur = None
    for line in text.splitlines():
        h = re.match(r"^## (.+?)(?:\s*\((\d+)\))?\s*$", line)
        if h:
            cur = {"name": h.group(1).strip(), "items": []}
            cats.append(cur)
            continue
        it = CHECKLIST_ITEM_RE.match(line)
        if it and cur is not None:
            raw = it.group(2).strip()
            qs = []
            for m in CHECKLIST_QREF_RE.finditer(raw):
                for ref in m.group(1).split(","):
                    ref = ref.strip()
                    if ref:
                        qs.append(ref.replace("/", ":", 1))
            text_clean = CHECKLIST_QREF_RE.sub("", raw).strip()
            cur["items"].append(
                {"depth": DEPTH[it.group(1)], "text": text_clean, "qs": qs}
            )
    return [c for c in cats if c["items"]]


def validate_question_refs(checklist, categories, level_name, checklist_name):
    """Перевіряє посилання пунктів чеклиста на питання.

    Повертає (errors, warnings):
      - error: посилання на неіснуючий розділ/питання (битий реф — збірка падає,
        інакше в UI з'явився б мертвий чип);
      - warning: пункт чеклиста без жодного посилання, або питання, на яке не
        посилається жоден пункт (прогалина покриття — не фатально, але видимо).
    """
    valid = {
        f"{cat['key']}:{q['id']}" for cat in categories for q in cat["questions"]
    }
    errors, warnings = [], []
    referenced = set()
    for cat in checklist:
        for it in cat["items"]:
            if not it["qs"]:
                warnings.append(
                    f"[{level_name}/{checklist_name}] пункт без посилання на "
                    f"питання (<!-- q:... -->): «{it['text'][:60]}…»"
                )
            for ref in it["qs"]:
                referenced.add(ref)
                if ref not in valid:
                    errors.append(
                        f"[{level_name}/{checklist_name}] посилання на "
                        f"неіснуюче питання {ref.replace(':', '/', 1)!r} "
                        f"у пункті «{it['text'][:60]}…»"
                    )
    for ref in sorted(valid - referenced):
        warnings.append(
            f"[{level_name}] питання {ref.replace(':', '/', 1)} не покриває "
            f"жодного пункту чеклиста"
        )
    return errors, warnings


def validate_checklist_lines(text, checklist_path, level_name):
    """Рядки, схожі на пункт чеклиста, які parse_checklist НЕ розпізнає.

    «Схожий на пункт» = після trim починається з '- ['. Якщо такий рядок
    не матчиться CHECKLIST_ITEM_RE — тим САМИМ регексом, яким парсить
    parse_checklist(), — parse_checklist мовчки його пропустить, і пункт
    зникне з dist/ без сліду. Тому будь-яка розбіжність (немає мітки
    🟣/🔵/🟢, зайвий пробіл/таб після ']', відступ на початку, зламаний
    чекбокс тощо) — це помилка перевірки з файлом/рядком/текстом.
    """
    errors = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip().startswith("- ["):
            continue
        if CHECKLIST_ITEM_RE.match(line):
            continue
        snippet = line.strip()[:80]
        errors.append(
            f"[{level_name}/{checklist_path.name}:{lineno}] рядок схожий на "
            f"пункт чеклиста, але не відповідає формату "
            f"'- [ ] 🟣|🔵|🟢 текст' (парсер його мовчки пропустив би): "
            f"{snippet!r}"
        )
    return errors


def discover_levels():
    """Піддиректорії levels/*/, відсортовані за іменем."""
    if not LEVELS_DIR.is_dir():
        raise SystemExit(f"Не знайдено директорію рівнів: {LEVELS_DIR}")
    dirs = sorted((p for p in LEVELS_DIR.iterdir() if p.is_dir()), key=lambda p: p.name)
    if not dirs:
        raise SystemExit(f"У {LEVELS_DIR} немає жодної піддиректорії рівня")
    return dirs


def section_files(level_dir):
    """Файли розділів NN_*.md, відсортовані за числовим префіксом."""
    files = [p for p in level_dir.iterdir() if SECTION_RE.match(p.name)]
    files.sort(key=lambda p: int(SECTION_RE.match(p.name).group(1)))
    return files


def checklist_file(level_dir):
    """Рівно один файл *_Checklist.md у директорії рівня."""
    return sorted(level_dir.glob("*_Checklist.md"))


def strip_prefix(fname):
    """'NN_Some-Name.md' -> 'Some-Name' (без числового префікса й розширення)."""
    return re.sub(r"^\d+_", "", pathlib.Path(fname).stem)


def humanize(fname):
    """Запасний варіант людської назви розділу з імені файла.

    Дефіси лишаються як є — використовується, коли у файлі немає
    frontmatter-поля title.
    """
    return strip_prefix(fname).replace("_", " ").strip()


def section_key(fname):
    """Ключ розділу (для CSS/localStorage): ім'я файла без префікса/розширення, lowercase."""
    return strip_prefix(fname).lower()


def collect_level_data(level_dir, errors, warnings):
    """Парсить і валідує один рівень; усі знайдені проблеми додає в errors.

    Спільна для build і check логіка: жодна з перелічених нижче проблем
    не кидає SystemExit одразу — вона лише дописується в errors (переданий
    викликачем спільний список), щоб зібрати ВСІ проблеми відразу, а не
    зупинитись на першій. Викликач (run_pipeline) вирішує, коли саме
    перевірити errors і завершити роботу.

    Перевіряються інваріанти:
      1. рівень має ≥1 файл розділу NN_*.md і рівно один *_Checklist.md;
      2. кожне питання має номер (QN), непорожній заголовок, непорожнє
         тіло відповіді і блок «🎯 Відповідь на іспиті» першим абзацом;
      3. глибина кожного питання ∈ {deep, mid, aware};
      4. чеклист має ≥1 валідний пункт, і кожен рядок, схожий на пункт
         чеклиста, повністю відповідає формату '- [ ] 🟣|🔵|🟢 текст'
         (той самий регекс, що й у parse_checklist);
      5. рівень сумарно має ≥1 питання;
      6. посилання пунктів чеклиста на питання (<!-- q:... -->) резолвляться
         (битий реф — error; прогалини покриття йдуть у warnings).

    Повертає дані рівня (для рендеру HTML), або None, якщо рівень
    настільки зламаний (немає розділів і/або чеклиста), що дані зібрати
    неможливо.
    """
    level_name = level_dir.name

    sections = section_files(level_dir)
    if not sections:
        errors.append(
            f"[{level_name}] у {level_dir} немає жодного файла розділу NN_*.md"
        )
    checklists = checklist_file(level_dir)
    if len(checklists) != 1:
        errors.append(
            f"[{level_name}] очікувався рівно 1 файл *_Checklist.md "
            f"у {level_dir}, знайдено {len(checklists)}"
        )
    if not sections or len(checklists) != 1:
        return None

    categories = []
    total_q = 0
    depth_counts = {"deep": 0, "mid": 0, "aware": 0}
    for path in sections:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        questions = parse_questions(body)
        for q in questions:
            loc = f"[{level_name}/{path.name} {q['id'] or '?'}]"
            if not q["id"]:
                errors.append(f"{loc}: питання без номера QN")
            if not q["title"].strip():
                errors.append(f"{loc}: порожній заголовок питання")
            if not q["md"].strip():
                errors.append(f"{loc}: порожнє тіло відповіді")
            if not q["exam"]:
                errors.append(
                    f"{loc}: немає блоку «**🎯 Відповідь на іспиті:** …» "
                    f"першим абзацом відповіді (див. ANSWER_SCHEMA.md)"
                )
            if q["depth"] not in DEPTH.values():
                errors.append(
                    f"{loc}: недійсний код глибини {q['depth']!r} "
                    f"(очікується один з {sorted(DEPTH.values())})"
                )
            total_q += 1
            depth_counts[q["depth"]] = depth_counts.get(q["depth"], 0) + 1
        # у JSON ідуть лише поля, які реально читає шаблон (key/name/questions);
        # решта frontmatter (stack, source, purpose…) — документація самого .md
        categories.append(
            {
                "key": section_key(path.name),
                "name": meta.get("title") or humanize(path.name),
                "questions": questions,
            }
        )

    checklist_path = checklists[0]
    checklist_text = checklist_path.read_text(encoding="utf-8")
    checklist = parse_checklist(checklist_text)
    errors.extend(validate_checklist_lines(checklist_text, checklist_path, level_name))
    ref_errors, ref_warnings = validate_question_refs(
        checklist, categories, level_name, checklist_path.name
    )
    errors.extend(ref_errors)
    warnings.extend(ref_warnings)

    total_items = sum(len(c["items"]) for c in checklist)
    if total_items == 0:
        errors.append(
            f"[{level_name}/{checklist_path.name}] чеклист не містить жодного "
            f"пункту з валідною міткою глибини"
        )

    if total_q == 0:
        errors.append(f"[{level_name}] рівень не містить жодного питання")

    return {
        "categories": categories,
        "checklist": checklist,
        "totals": {"questions": total_q, "depth": depth_counts},
    }


def json_embed(value):
    """JSON з екрануванням, безпечним для вбудовування у <script>."""
    raw = json.dumps(value, ensure_ascii=False)
    return (
        raw.replace("<", "\\u003c")
        .replace(chr(0x2028), "\\u2028")
        .replace(chr(0x2029), "\\u2029")
    )


def render_level_html(template, level_key, data):
    """Підставляє дані рівня, ключ рівня (для localStorage) і PWA-фрагменти
    (мета-теги/маніфест/apple-touch-icon, реєстрація service worker) у шаблон."""
    for marker in (
        "JSON_DATA_PLACEHOLDER",
        "LEVEL_KEY_PLACEHOLDER",
        "PWA_HEAD_PLACEHOLDER",
        "PWA_SW_REGISTER_PLACEHOLDER",
    ):
        if marker not in template:
            raise SystemExit(f"У шаблоні відсутній маркер {marker}")
    out = template.replace("JSON_DATA_PLACEHOLDER", json_embed(data))
    out = out.replace("LEVEL_KEY_PLACEHOLDER", json_embed(level_key))
    out = out.replace("PWA_HEAD_PLACEHOLDER", pwa_assets.HEAD_TAGS)
    out = out.replace("PWA_SW_REGISTER_PLACEHOLDER", pwa_assets.SW_REGISTER_SCRIPT)
    return out


ROOT_INDEX_CSS = """
:root{
  --bg:#0d0f14; --panel:#161a23; --card:#191d28; --card-hi:#1e2330;
  --border:#262c3a; --text:#e7e9ef; --dim:#9aa2b1; --mute:#666e7e;
  --accent:#7c6cff; --accent-2:#22d3ee; --accent-soft:rgba(124,108,255,.16);
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 30px rgba(0,0,0,.28);
  --radius:16px;
  --font:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --mono:ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: light){
  :root{
    --bg:#f4f5f8; --panel:#ffffff; --card:#ffffff; --card-hi:#f7f8fa;
    --border:#e3e6ec; --text:#181b22; --dim:#5b6270; --mute:#8a919e;
    --accent:#6d4dff; --accent-soft:rgba(109,77,255,.1);
    --shadow:0 1px 2px rgba(20,30,50,.05),0 8px 24px rgba(20,30,50,.07);
  }
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--text);
  line-height:1.55;-webkit-font-smoothing:antialiased;min-height:100vh}
.wrap{max-width:720px;margin:0 auto;padding:64px 20px 90px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--accent);margin-bottom:10px}
h1{font-size:clamp(26px,5vw,36px);font-weight:700;letter-spacing:-.02em;margin-bottom:12px}
.sub{color:var(--dim);font-size:15px;margin-bottom:38px}
.levels{display:flex;flex-direction:column;gap:14px}
a.level{display:flex;align-items:center;gap:16px;padding:20px 22px;border-radius:var(--radius);
  border:1px solid var(--border);background:var(--card);box-shadow:var(--shadow);
  text-decoration:none;color:var(--text);transition:.16s}
a.level:hover{border-color:var(--accent);transform:translateY(-1px)}
.level-name{font-size:19px;font-weight:700;letter-spacing:-.01em;flex:1;min-width:0}
.level-meta{font-family:var(--mono);font-size:12.5px;color:var(--dim);text-align:right;flex:none}
.level-arrow{flex:none;color:var(--mute);font-size:16px}
.footer{margin-top:46px;font-size:11.5px;color:var(--mute);font-family:var(--mono)}
"""


def render_root_index(level_summaries):
    """Кореневий dist/index.html — самодостатній список рівнів."""
    items = []
    for s in level_summaries:
        items.append(
            '<a class="level" href="{link}">'
            '<span class="level-name">{name}</span>'
            '<span class="level-meta">{q} питань · {c} пунктів чеклиста</span>'
            '<span class="level-arrow">→</span>'
            "</a>".format(
                link=f"{s['key']}/",
                name=s["name"],
                q=s["questions"],
                c=s["checklist_items"],
            )
        )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="uk">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>KE Training</title>\n" + pwa_assets.HEAD_TAGS +
        "<style>" + ROOT_INDEX_CSS + "</style>\n"
        "</head>\n<body>\n"
        '<div class="wrap">\n'
        '  <div class="eyebrow">InterCode · Competency Matrix</div>\n'
        "  <h1>KE Training</h1>\n"
        '  <div class="sub">Оберіть рівень підготовки.</div>\n'
        '  <div class="levels">\n    ' + "\n    ".join(items) + "\n  </div>\n"
        '  <div class="footer">згенеровано з навчальних .md</div>\n'
        "</div>\n" + pwa_assets.SW_REGISTER_SCRIPT +
        "</body>\n</html>\n"
    )


def render_404_page():
    """Самодостатня dist/404.html у стилі кореневого індексу.

    Cloudflare Pages автоматично віддає dist/404.html як відповідь для
    неіснуючих шляхів. Без цього файлу такі шляхи мовчки резолвляться в
    кореневий dist/index.html (Pages-фолбек), і 404 замаскується під
    головну сторінку замість чіткого «не знайдено».
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="uk">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>404 · KE Training</title>\n<style>" + ROOT_INDEX_CSS + "</style>\n"
        "</head>\n<body>\n"
        '<div class="wrap">\n'
        '  <div class="eyebrow">InterCode · Competency Matrix</div>\n'
        "  <h1>Сторінку не знайдено</h1>\n"
        '  <div class="sub">Такої адреси немає — можливо, її перенесли або тут ніколи нічого не було.</div>\n'
        '  <div class="levels">\n'
        '    <a class="level" href="/">\n'
        '      <span class="level-name">На головну</span>\n'
        '      <span class="level-arrow">→</span>\n'
        "    </a>\n"
        "  </div>\n"
        "</div>\n</body>\n</html>\n"
    )


def run_pipeline(check_only):
    """Парсить і валідує всі рівні; якщо check_only — на цьому й зупиняється.

    Одна й та сама логіка парсингу/валідації (collect_level_data) працює
    і для `--check`, і для звичайної збірки: build падає на тих самих
    помилках, що й check, — просто ще й пише dist/, коли помилок немає.
    """
    level_dirs = discover_levels()

    errors = []
    warnings = []
    level_data = []
    for level_dir in level_dirs:
        data = collect_level_data(level_dir, errors, warnings)
        level_data.append((level_dir, data))

    if errors:
        print(f"FAIL: знайдено {len(errors)} проблему(и) валідації:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        raise SystemExit(1)

    if warnings:
        print(f"WARN: {len(warnings)} попередження покриття (не фатально):", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)

    if check_only:
        for level_dir, data in level_data:
            d = data["totals"]
            checklist_items = sum(len(c["items"]) for c in data["checklist"])
            print(
                f"OK -> {level_dir.name}: {d['questions']} питань "
                f"(deep {d['depth']['deep']} · mid {d['depth']['mid']} · aware {d['depth']['aware']}) · "
                f"{checklist_items} пунктів чеклиста"
            )
        print(f"CHECK OK · {len(level_data)} рівень(-ні/-ів) пройшли валідацію (dist/ не змінено)")
        return

    template = (ROOT / "study_template.html").read_text(encoding="utf-8")
    DIST_DIR.mkdir(exist_ok=True)
    summaries = []
    for level_dir, data in level_data:
        level_key = level_dir.name.lower()
        html = render_level_html(template, level_key, data)

        out_dir = DIST_DIR / level_key
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding="utf-8")

        d = data["totals"]
        checklist_items = sum(len(c["items"]) for c in data["checklist"])
        summaries.append(
            {
                "key": level_key,
                "name": level_dir.name,
                "questions": d["questions"],
                "checklist_items": checklist_items,
            }
        )
        print(
            f"OK -> dist/{level_key}/index.html · {d['questions']} питань "
            f"(deep {d['depth']['deep']} · mid {d['depth']['mid']} · aware {d['depth']['aware']}) · "
            f"{checklist_items} пунктів чеклиста"
        )

    (DIST_DIR / "index.html").write_text(
        render_root_index(summaries), encoding="utf-8"
    )
    print(f"OK -> dist/index.html · {len(summaries)} рівень(-ні/-ів)")

    (DIST_DIR / "404.html").write_text(render_404_page(), encoding="utf-8")
    print("OK -> dist/404.html")

    # ---- PWA: маніфест + іконки + service worker (Ярус A/B) ----
    manifest_bytes = json.dumps(
        pwa_assets.build_manifest(), ensure_ascii=False, indent=2
    ).encode("utf-8") + b"\n"
    (DIST_DIR / "manifest.webmanifest").write_bytes(manifest_bytes)
    print("OK -> dist/manifest.webmanifest")

    icons_dir = DIST_DIR / "icons"
    icons_dir.mkdir(exist_ok=True)
    (icons_dir / "icon.svg").write_text(pwa_assets.render_icon_svg(), encoding="utf-8")
    for size in pwa_assets.ICON_SIZES:
        (icons_dir / f"icon-{size}.png").write_bytes(pwa_assets.render_icon(size))
    apple_name = f"apple-touch-icon-{pwa_assets.APPLE_TOUCH_SIZE}.png"
    (icons_dir / apple_name).write_bytes(
        pwa_assets.render_icon(pwa_assets.APPLE_TOUCH_SIZE)
    )
    print(f"OK -> dist/icons/ · {len(pwa_assets.ICON_SIZES) + 2} іконки")

    # хеш рахуємо ПІСЛЯ всього іншого і ДО sw.js (sw.js не хешує сам себе)
    cache_version = pwa_assets.compute_cache_version(DIST_DIR)
    (DIST_DIR / "sw.js").write_text(
        pwa_assets.render_sw_js(cache_version), encoding="utf-8"
    )
    print(f"OK -> dist/sw.js · версія кеша {cache_version}")


def main():
    parser = argparse.ArgumentParser(
        description="Збірка навчального тренажера KE Training з levels/*/."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="лише перевірити інваріанти матеріалів (парсинг+валідація), не писати dist/",
    )
    args = parser.parse_args()
    run_pipeline(check_only=args.check)


if __name__ == "__main__":
    main()
