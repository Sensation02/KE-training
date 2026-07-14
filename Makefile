# Makefile для навчального тренажера KE Training (рівні L2/L3/L4…)
# Генерує самодостатні dist/<рівень>/index.html + кореневий dist/index.html
# із матеріалів у levels/*/.

PY  := python3
OUT := dist/index.html
SRC := build_study.py study_template.html $(shell find levels -name '*.md')

.DEFAULT_GOAL := build
.PHONY: build open clean help

## build: згенерувати dist/ із матеріалів (за замовчуванням)
build: $(OUT)

# перезбирати лише коли змінився будь-який зі SRC-файлів
$(OUT): $(SRC)
	$(PY) build_study.py

## open: згенерувати (за потреби) і відкрити кореневий індекс у браузері
open: build
	open dist/index.html

## clean: видалити згенеровані файли
clean:
	rm -rf dist

## help: показати доступні команди
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## //'
