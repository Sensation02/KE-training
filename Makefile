# Makefile для навчального тренажера L3 Full-stack
# Генерує самодостатній L3_Study.html із .md-матеріалів.

PY     := python3
OUT    := L3_Study.html
SRC    := build_study.py study_template.html \
          01_Front-End.md 02_Back-end.md 03_Databases.md \
          04_Code-Delivery.md 05_Methodology.md L3_Checklist.md

.DEFAULT_GOAL := build
.PHONY: build open clean help

## build: згенерувати L3_Study.html із матеріалів (за замовчуванням)
build: $(OUT)

# перезбирати лише коли змінився будь-який зі SRC-файлів
$(OUT): $(SRC)
	$(PY) build_study.py

## open: згенерувати (за потреби) і відкрити тренажер у браузері
open: build
	open $(OUT)

## clean: видалити згенерований файл
clean:
	rm -f $(OUT)

## help: показати доступні команди
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## //'
