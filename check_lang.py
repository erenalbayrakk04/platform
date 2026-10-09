# Çeviri kontrolü: ekrana çıkan her Türkçe yazının İngilizcesi (lang.EN) var mı? Çalıştırmak: python check_lang.py
# Baktığı yerler:
# 1) Kodda t("...") ve mark("...") içindeki yazılar; draw_text / draw_title / draw_note / show_note'a doğrudan
#    verilen yazılar. Bunlara f-string verilmişse hata (çevrilemez: t("Rekor: {} m").format(n) kullanılmalı).
# 2) Listelerdeki yazılar: bölüm adları ve tanıtımları (stages.py), skin adları (skins.py), zorluk adları (settings.py).
# Ayrıca İngilizcedeki {} yer tutucuları Türkçesiyle aynı mı bakar; EN'de artık kullanılmayan yazıları da söyler.
# Eksik / hatalı çeviri varsa hata koduyla çıkar (GitHub'da oyun o zaman yayına çıkmaz).
import ast
import os
import re
import string
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lang import EN  # noqa: E402
from settings import DIFFICULTY_NAMES  # noqa: E402
from stages import STAGE_SETS  # noqa: E402
from skins import SKINS  # noqa: E402

TEXT_FUNCS = {"draw_text": 2, "draw_title": 1, "draw_note": 1, "show_note": 0}  # yazı kaçıncı argüman
MARK_FUNCS = ("t", "mark")


def has_words(text):
    # Çevrilecek kelime var mı ("37 m", "%80", "3 / 9" gibi yazılar çevrilmez)
    return any(word != "m" for word in re.findall(r"[^\W\d_]+", text))


def call_name(node):
    func = node.func
    return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None


def code_texts():
    # Kodda geçen çevrilecek yazılar {yazı: ilk geçtiği yer} ve hatalar (f-string)
    texts, errors = {}, []
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py") or name.startswith("check_"):
            continue
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = call_name(node)
            where = f"{name}:{node.lineno}"
            if func in MARK_FUNCS and node.args and isinstance(node.args[0], ast.Constant):
                if isinstance(node.args[0].value, str):
                    texts.setdefault(node.args[0].value, where)
            elif func in TEXT_FUNCS and len(node.args) > TEXT_FUNCS[func]:
                arg = node.args[TEXT_FUNCS[func]]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and has_words(arg.value):
                    texts.setdefault(arg.value, where)
                elif isinstance(arg, ast.JoinedStr):
                    fixed = "".join(part.value for part in arg.values if isinstance(part, ast.Constant))
                    if has_words(fixed):
                        errors.append(f"{where}: {func}'e f-string verilmiş, çevrilemez; t(\"...{{}}...\").format(...) kullan")
    return texts, errors


def data_texts():
    # Listelerdeki yazılar {yazı: nereden}
    texts = {}
    for mode, stages in STAGE_SETS.items():
        for i, stage in enumerate(stages):
            texts.setdefault(stage["name"], f"stages.py {mode} {i + 1}. bölüm adı")
            texts.setdefault(stage["intro"], f"stages.py {mode} {i + 1}. bölüm tanıtımı")
    for skin in SKINS:
        texts.setdefault(skin["name"], f"skins.py {skin['id']} adı")
    for mode, name in DIFFICULTY_NAMES.items():
        texts.setdefault(name, f"settings.py DIFFICULTY_NAMES {mode}")
    return texts


def fields(text):
    # Yazıdaki yer tutucular ({} / {total}) — sırası önemli değil
    return sorted(field or "" for _, field, _, _ in string.Formatter().parse(text) if field is not None)


def main():
    texts, errors = code_texts()
    for text, where in data_texts().items():
        texts.setdefault(text, where)
    missing = {text: where for text, where in texts.items() if has_words(text) and text not in EN}
    for text, value in EN.items():
        forms = value if isinstance(value, tuple) else (value,)
        if isinstance(value, tuple) and len(value) != 2:
            errors.append(f"EN[{text!r}]: tekil/çoğul ikilisi olmalı")
        for form in forms:
            if fields(form) != fields(text):
                errors.append(f"EN[{text!r}]: yer tutucular Türkçesiyle aynı değil: {form!r}")
    unused = [text for text in EN if text not in texts]
    for text, where in sorted(missing.items(), key=lambda item: item[1]):
        print(f"İngilizcesi yok: {text!r}  ({where})")
    for error in errors:
        print("HATA:", error)
    for text in unused:
        print(f"Uyarı: EN'de kullanılmayan yazı: {text!r}")
    print(f"{len(texts)} yazı, {len(EN)} çeviri, {len(missing)} eksik, {len(errors)} hata, {len(unused)} kullanılmayan")
    if missing or errors:
        sys.exit(1)
    print("Çeviriler tamam")


if __name__ == "__main__":
    main()
