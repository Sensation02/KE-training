#!/usr/bin/env python3
"""Генератор інтерактивних навчальних застосунків KE Training.

Читає рівні з levels/*/ (кожен — піддиректорія з розділами NN_*.md
і одним файлом *_Checklist.md), парсить питання/відповіді та пункти
компетенцій, і для кожного рівня вбудовує дані як JSON у
study_template.html. Результат — самодостатні dist/<рівень>/index.html
(відкриваються подвійним кліком або через Cloudflare Pages) плюс
кореневий dist/index.html зі списком рівнів.

Додавання нового рівня (L2, L4, …) — це просто нова піддиректорія
levels/<Рівень>/ з розділами й чеклистом; код нічого міняти не треба.

Запуск:  python3 build_study.py
"""
import json
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
LEVELS_DIR = ROOT / "levels"
DIST_DIR = ROOT / "dist"

SECTION_RE = re.compile(r"^(\d+)_.+\.md$")

# емодзі глибини → внутрішній код
DEPTH = {"🟣": "deep", "🔵": "mid", "🟢": "aware"}


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
        questions.append(
            {"id": num, "title": title, "depth": depth, "md": answer}
        )
    return questions


def parse_checklist(text):
    """Категорії чеклиста з пунктами компетенцій."""
    cats = []
    cur = None
    for line in text.splitlines():
        h = re.match(r"^## (.+?)(?:\s*\((\d+)\))?\s*$", line)
        if h:
            cur = {"name": h.group(1).strip(), "items": []}
            cats.append(cur)
            continue
        it = re.match(r"^- \[[ xX]\] (🟣|🔵|🟢)\s*(.*)$", line)
        if it and cur is not None:
            cur["items"].append(
                {"depth": DEPTH[it.group(1)], "text": it.group(2).strip()}
            )
    return [c for c in cats if c["items"]]


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


def build_level_data(level_dir):
    """Збирає дані одного рівня (категорії з питаннями + чеклист)."""
    sections = section_files(level_dir)
    if not sections:
        raise SystemExit(
            f"[{level_dir.name}] у {level_dir} немає жодного файла розділу NN_*.md"
        )
    checklists = checklist_file(level_dir)
    if len(checklists) != 1:
        raise SystemExit(
            f"[{level_dir.name}] очікувався рівно 1 файл *_Checklist.md "
            f"у {level_dir}, знайдено {len(checklists)}"
        )

    categories = []
    total_q = 0
    depth_counts = {"deep": 0, "mid": 0, "aware": 0}
    for path in sections:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        questions = parse_questions(body)
        total_q += len(questions)
        for q in questions:
            depth_counts[q["depth"]] += 1
        categories.append(
            {
                "key": section_key(path.name),
                "name": meta.get("title") or humanize(path.name),
                "stack": meta.get("stack", ""),
                "questions": questions,
            }
        )

    checklist = parse_checklist(checklists[0].read_text(encoding="utf-8"))

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
    """Підставляє дані рівня й сам ключ рівня (для localStorage) у шаблон."""
    if "JSON_DATA_PLACEHOLDER" not in template:
        raise SystemExit("У шаблоні відсутній маркер JSON_DATA_PLACEHOLDER")
    if "LEVEL_KEY_PLACEHOLDER" not in template:
        raise SystemExit("У шаблоні відсутній маркер LEVEL_KEY_PLACEHOLDER")
    out = template.replace("JSON_DATA_PLACEHOLDER", json_embed(data))
    out = out.replace("LEVEL_KEY_PLACEHOLDER", json_embed(level_key))
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
        "<title>KE Training</title>\n<style>" + ROOT_INDEX_CSS + "</style>\n"
        "</head>\n<body>\n"
        '<div class="wrap">\n'
        '  <div class="eyebrow">InterCode · Competency Matrix</div>\n'
        "  <h1>KE Training</h1>\n"
        '  <div class="sub">Оберіть рівень підготовки.</div>\n'
        '  <div class="levels">\n    ' + "\n    ".join(items) + "\n  </div>\n"
        '  <div class="footer">згенеровано з навчальних .md</div>\n'
        "</div>\n</body>\n</html>\n"
    )


def main():
    template = (ROOT / "study_template.html").read_text(encoding="utf-8")
    level_dirs = discover_levels()

    DIST_DIR.mkdir(exist_ok=True)
    summaries = []
    for level_dir in level_dirs:
        level_key = level_dir.name.lower()
        data = build_level_data(level_dir)
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


if __name__ == "__main__":
    main()
