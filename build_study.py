#!/usr/bin/env python3
"""Генератор інтерактивного навчального застосунку L3_Study.html.

Читає навчальні .md-файли + чеклист, парсить питання/відповіді та пункти
компетенцій, і вбудовує все як JSON у study_template.html.
Результат — самодостатній L3_Study.html (відкривається подвійним кліком).

Запуск:  python3 build_study.py
"""
import json
import re
import pathlib

ROOT = pathlib.Path(__file__).parent

# (ключ, людська назва, файл) — порядок = порядок у застосунку
FILES = [
    ("front-end", "Front-End", "01_Front-End.md"),
    ("back-end", "Back-end", "02_Back-end.md"),
    ("databases", "Databases", "03_Databases.md"),
    ("code-delivery", "Code Delivery", "04_Code-Delivery.md"),
    ("methodology", "Methodology", "05_Methodology.md"),
]
CHECKLIST_FILE = "L3_Checklist.md"

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


def build_data():
    categories = []
    total_q = 0
    depth_counts = {"deep": 0, "mid": 0, "aware": 0}
    for key, name, fname in FILES:
        text = (ROOT / fname).read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        questions = parse_questions(body)
        total_q += len(questions)
        for q in questions:
            depth_counts[q["depth"]] += 1
        categories.append(
            {
                "key": key,
                "name": name,
                "stack": meta.get("stack", ""),
                "questions": questions,
            }
        )

    checklist = parse_checklist(
        (ROOT / CHECKLIST_FILE).read_text(encoding="utf-8")
    )

    return {
        "categories": categories,
        "checklist": checklist,
        "totals": {"questions": total_q, "depth": depth_counts},
    }


def main():
    data = build_data()
    raw = json.dumps(data, ensure_ascii=False)
    # захист від закриття </script> та роздільників рядків JS (U+2028/U+2029)
    safe = (
        raw.replace("<", "\\u003c")
        .replace(chr(0x2028), "\\u2028")
        .replace(chr(0x2029), "\\u2029")
    )

    template = (ROOT / "study_template.html").read_text(encoding="utf-8")
    if "JSON_DATA_PLACEHOLDER" not in template:
        raise SystemExit("У шаблоні відсутній маркер JSON_DATA_PLACEHOLDER")
    out = template.replace("JSON_DATA_PLACEHOLDER", safe)
    (ROOT / "L3_Study.html").write_text(out, encoding="utf-8")

    d = data["totals"]
    print(
        f"OK -> L3_Study.html · {d['questions']} питань "
        f"(deep {d['depth']['deep']} · mid {d['depth']['mid']} · aware {d['depth']['aware']}) · "
        f"{sum(len(c['items']) for c in data['checklist'])} пунктів чеклиста"
    )


if __name__ == "__main__":
    main()
