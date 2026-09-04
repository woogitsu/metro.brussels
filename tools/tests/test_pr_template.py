#!/usr/bin/env python3
"""Szablon pull requesta i słowo kluczowe, które naprawdę zamyka Issue.

Audyt repozytorium z 02.09.2026 wskazał, że Issues zostają otwarte po scaleniu.
GitHub zamyka Issue automatycznie tylko po **angielskim** słowie kluczowym —
polskie „Zamyka #12" wygląda w opisie dokładnie tak samo, a nie robi nic.
"""
import os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE = os.path.join(ROOT, ".github", "pull_request_template.md")

# Pełna lista z dokumentacji GitHuba. Odmiany są znaczące: `close`, `closes`
# i `closed` działają, `closing` już nie.
GITHUB_CLOSING_KEYWORDS = frozenset(
    ["close", "closes", "closed", "fix", "fixes", "fixed",
     "resolve", "resolves", "resolved"])


def closing_keyword(line):
    """Słowo kluczowe otwierające linię, jeżeli GitHub je rozpozna; inaczej None.

    **Ten test jest surowszy niż GitHub, celowo.** GitHub szuka słowa kluczowego
    w dowolnym miejscu opisu, więc zamknąłby Issue także po zdaniu „nie pisz tu
    Closes #12". Szablon ma wymagać, żeby odwołanie **otwierało linię**, bo
    inaczej nie da się na nie spojrzeć i zobaczyć, co PR zamyka.
    """
    match = re.match(r"^\s*([A-Za-z]+)\s+#", line)
    if not match:
        return None
    word = match.group(1).lower()
    return word if word in GITHUB_CLOSING_KEYWORDS else None


def _template():
    with open(TEMPLATE, encoding="utf-8") as handle:
        return handle.read()


def test_pr_template_exists():
    assert os.path.isfile(TEMPLATE), TEMPLATE


def test_template_carries_a_keyword_github_actually_recognises():
    lines = [l for l in _template().splitlines() if closing_keyword(l)]
    assert lines, "szablon nie ma ani jednej linii, po której GitHub zamknie Issue"


def test_polish_zamyka_is_not_recognised():
    # Kontrola negatywna do testu wyżej. Gdyby ktoś „poprawił" szablon na polski,
    # opis wyglądałby tak samo, a Issue zostałoby otwarte — dokładnie ten rozjazd,
    # przez który tracker się rozjechał.
    assert closing_keyword("Zamyka #12") is None
    assert closing_keyword("Rozwiązuje #12") is None
    assert closing_keyword("Naprawia #12") is None


def test_keyword_matching_is_not_a_substring_match():
    # Dopasowanie ma być po CAŁYM słowie. Poniższe zawierają słowo kluczowe jako
    # podciąg — `prefixes` niesie `fix`, `closest` niesie `closes`, `unfixed`
    # niesie `fixed` — a GitHub żadnego z nich nie rozpoznaje. Gdyby test szukał
    # podciągu, przepuściłby szablon, który niczego nie zamyka.
    #
    # Pierwsza wersja tego testu używała „Closing", które NIE zawiera „close"
    # (c-l-o-s-i-n-g kontra c-l-o-s-e) i dlatego mutacji nie łapała.
    assert closing_keyword("Prefixes #12") is None
    assert closing_keyword("Closest #12") is None
    assert closing_keyword("Unfixed #12") is None
    assert closing_keyword("Closing #12") is None
    assert closing_keyword("Closes #12") == "closes"
    assert closing_keyword("FIXED #12") == "fixed"


def test_reference_must_open_the_line():
    # Kontrola negatywna do surowszej reguły opisanej przy `closing_keyword`.
    # GitHub zamknąłby Issue po obu poniższych; szablon ich nie uznaje, bo
    # odwołanie schowane w środku zdania jest niewidoczne przy przeglądaniu PR-a.
    assert closing_keyword("Nie pisz tutaj Closes #12") is None
    assert closing_keyword("por. Fixes #12") is None
    assert closing_keyword("  Closes #12") == "closes", "wcięcie jest dozwolone"


def test_keyword_must_be_followed_by_a_hash():
    # „Closes the door" nie jest odwołaniem do Issue.
    assert closing_keyword("Closes the door") is None
    assert closing_keyword("Resolves") is None


def test_template_asks_for_real_verification_output():
    body = _template()
    assert "Weryfikacja" in body
    assert "Kontrole negatywne" in body, "szablon nie pyta o mutacje"
    assert "Poza zakresem" in body


def test_template_does_not_promise_a_fixed_test_count():
    # Ten sam błąd, który konstytucja miała w §2: zaszyta liczba testów
    # rozjeżdża się przy każdym nowym module.
    assert not re.search(r"\b\d+\s+test", _template())
