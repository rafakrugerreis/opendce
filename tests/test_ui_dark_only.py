"""
Trava o tema: a UI é dark-only, servida por componentes shadcn em CSS puro.

Falha se alguém reintroduzir variantes `dark:`, um seletor de tema, ou
redefinir os tokens HSL do shadcn fora de shadcn.css.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

TEMPLATES = Path("app/templates")
CSS = Path("app/static/css")

# dace.html é o DANFE/DC-e impresso em A4: papel branco, fora do tema.
PRINT_ONLY = {"dace.html"}

TOKEN_RE = re.compile(r"--(background|primary|border|destructive|success|warning)\s*:")


def _templates() -> list[Path]:
    return sorted(p for p in TEMPLATES.rglob("*.html") if p.name not in PRINT_ONLY)


def test_nenhuma_variante_dark() -> None:
    for path in _templates():
        assert "dark:" not in path.read_text(encoding="utf-8"), (
            f"{path} usa variante `dark:` — o tema é dark-only, remova a dualidade"
        )


def test_sem_seletor_de_tema() -> None:
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert 'class="dark"' not in base
    assert "darkMode" not in base
    assert not re.search(r"localStorage\.\w*[Tt]heme", base)

    for js in (Path("app/static/js")).rglob("*.js"):
        text = js.read_text(encoding="utf-8")
        assert not re.search(r"\b(initTheme|toggleTheme|setTheme)\b", text), (
            f"{js} ainda alterna tema"
        )


def test_tokens_shadcn_definidos() -> None:
    shadcn = (CSS / "shadcn.css").read_text(encoding="utf-8")
    root = shadcn.split(":root", 1)[1].split("}", 1)[0]
    for token in ("--background", "--primary", "--border", "--destructive"):
        assert token in root, f"{token} ausente no :root de shadcn.css"

    # styles.css carrega depois de shadcn.css no base.html: redefinir cor lá
    # sobrescreve o tema. (auth.css tem :root próprio e stack separada — ok.)
    offenders = TOKEN_RE.findall((CSS / "styles.css").read_text(encoding="utf-8"))
    assert not offenders, f"styles.css redefine tokens de cor do shadcn: {offenders}"


@pytest.mark.parametrize("componente", ["btn", "card", "input", "badge", "alert"])
def test_componentes_shadcn_existem(componente: str) -> None:
    shadcn = (CSS / "shadcn.css").read_text(encoding="utf-8")
    assert f".{componente}" in shadcn, f"componente .{componente} ausente em shadcn.css"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if name == "test_componentes_shadcn_existem":
                for c in ("btn", "card", "input", "badge", "alert"):
                    fn(c)
            else:
                fn()
            print(f"ok {name}")
