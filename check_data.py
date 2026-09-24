"""Проверка tasks.json и tests.json.  Запуск из папки репозитория:  python check_data.py"""
import collections, json, sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
tasks = json.loads((root / "tasks.json").read_text(encoding="utf-8"))["tasks"]
tests = json.loads((root / "tests.json").read_text(encoding="utf-8"))
titles = {t["title"] for t in tasks}
errs, warns = [], []

for key, name in (("id", "id"), ("title", "название")):
    for v, c in collections.Counter(t[key] for t in tasks).items():
        if c > 1:
            errs.append(f"дубликат: {name} {v!r}")
for t in tasks:
    tag = f"#{t['id']} {t['title']}"
    if t.get("difficulty") not in ("Easy", "Medium", "Hard"):
        errs.append(f"{tag}: сложность {t.get('difficulty')!r}")
    if t.get("auto_tests") and t["title"] not in tests:
        errs.append(f"{tag}: auto_tests=true, но в tests.json нет тестов")
    if not t.get("auto_tests") and t["title"] in tests:
        warns.append(f"{tag}: тесты есть, но auto_tests=false")
    if not t.get("url"):
        warns.append(f"{tag}: нет url")
for key, spec in tests.items():
    if key not in titles:
        errs.append(f"tests.json: «{key}» нет в tasks.json")
    for i, item in enumerate(spec.get("tests", []), 1):
        if not isinstance(item, list) or len(item) < 2:
            errs.append(f"tests.json: «{key}», тест {i}: нужен список [аргументы..., ожидаемый ответ]")

by = collections.Counter(t["difficulty"] for t in tasks)
print(f"Задач: {len(tasks)} ({dict(by)}), тем: {len({t['topic'] for t in tasks})}")
print(f"С автотестами: {sum(bool(t.get('auto_tests')) for t in tasks)}, с описанием: {sum(bool(t.get('description')) for t in tasks)}")
for w in warns: print("предупреждение:", w)
for e in errs: print("ОШИБКА:", e)
print("OK" if not errs else f"Ошибок: {len(errs)}")
sys.exit(1 if errs else 0)
