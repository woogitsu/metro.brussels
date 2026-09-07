#!/usr/bin/env python3
"""§1.3 `reports/droga-do-grywalnosci.md` liczyło tryby jazdy ręcznie.

**Skąd.** Nagłówek §1.3 mówił „Cztery tryby" nad tabelą, która przy pięciu wierszach
została nietknięta (6.C3 dopisał obok zdanie, ale liczby nie ruszył — słusznie, bo nie
była wynikiem JEGO pomiaru), a po dopisaniu wiersza `from-telemetry` miała już sześć.
To ta sama rodzina usterki, którą łapią `test_report_claims.py`
i `test_readme_claims.py`: **liczba stojąca w jednym miejscu i nigdzie nie liczona
rozjeżdża się bezszelestnie**.

**Źródło prawdy.** `src/Game/RunPlan.cs`, właściwość `Mode` — jedyne miejsce w kodzie,
które nazywa tryb przebiegu i wybiera go jednoznacznie (ternary, każda gałąź jeden
literał). Ten moduł liczy trzy rzeczy z drzewa, tak jak nakazuje zasada obu bramek
powyżej — **nie ma tu ani jednej oczekiwanej liczby wpisanej z pamięci**:

  1. ile odrębnych nazw trybów zwraca `RunPlan.Mode`,
  2. jaką liczbę słowem podaje nagłówek `### 1.3` przy słowie „tryb…",
  3. ile wierszy (nazw trybów w grawisach) ma tabela pod tym nagłówkiem.

Wszystkie trzy muszą się zgadzać. Gdy `RunPlan.Mode` dostanie kiedyś siódmą gałąź,
ten test ma paść — to jest jego zadanie, nie usterka.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUN_PLAN = os.path.join(ROOT, "src", "Game", "RunPlan.cs")
REPORT = os.path.join(ROOT, "reports", "droga-do-grywalnosci.md")

#: Podłoga zdrowego rozsądku na liczbę trybów znalezionych w kodzie — nie jest to
#: liczba trybów, jaką repozytorium ma DZIŚ (ta wychodzi z pomiaru, patrz raport
#: 6.C5), tylko próg, poniżej którego parser na pewno się popsuł: `RunPlan` od
#: początku rozróżniał więcej niż dwa źródła polecenia (człowiek i autopilot).
MINIMUM_MODES = 2

#: Liczebniki, którymi nagłówek §1.3 może zapisać liczbę trybów. Prozą, nie cyfrą —
#: ta sama konwencja co README (`test_readme_claims.py`).
NUMERALS = {
    "jeden": 1, "dwa": 2, "trzy": 3, "cztery": 4, "pięć": 5, "sześć": 6,
    "siedem": 7, "osiem": 8, "dziewięć": 9, "dziesięć": 10,
}

#: Właściwość `Mode` w `RunPlan.cs`: łańcuch `warunek ? "literał" : ...`, jeden
#: literał na gałąź, zakończony średnikiem. `.*?` jest nie-zachłanne i `DOTALL`,
#: żeby złapać całość mimo że wyrażenie zajmuje kilka wierszy.
MODE_PROPERTY = re.compile(r"public string Mode =>(.*?);", re.DOTALL)

#: Nagłówek `### 1.3 <liczebnik> tryb…,` — przecinek zamyka frazę tak samo
#: w „Cztery tryby," jak w „Sześć trybów,".
SECTION_HEADER = re.compile(r"^### 1\.3 (\S+) tryb\w*,", re.MULTILINE)

#: Wiersz tabeli, którego pierwsza kolumna jest nazwą trybu w grawisach — jedyna
#: postać, w jakiej tabela §1.3 naprawdę wymienia tryb (nagłówek i separator
#: tabeli nie mają grawisów w pierwszej kolumnie, więc nie trafiają).
TABLE_ROW = re.compile(r"^\|\s*`([a-z-]+)`\s*\|", re.MULTILINE)


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def code_modes(text):
    """Nazwy trybów, jakie potrafi zwrócić `RunPlan.Mode`, w kolejności gałęzi."""
    match = MODE_PROPERTY.search(text)
    if not match:
        return []
    return re.findall(r'"([a-z-]+)"', match.group(1))


def header_mode_count(text):
    """Liczba z nagłówka `### 1.3`, np. „Sześć" -> 6. `None`, gdy nie da się przeczytać."""
    match = SECTION_HEADER.search(text)
    if not match:
        return None
    return NUMERALS.get(match.group(1).lower())


def section_1_3(text):
    """Treść sekcji `### 1.3` do następnego nagłówka tego samego poziomu."""
    match = re.search(r"^### 1\.3 .*?$(.*?)(?=^### |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def table_modes(section_text):
    """Nazwy trybów z pierwszej kolumny tabeli, w kolejności wierszy."""
    return TABLE_ROW.findall(section_text)


def test_code_header_and_table_agree_on_the_number_of_run_modes():
    code = code_modes(_read(RUN_PLAN))
    assert len(code) >= MINIMUM_MODES, (
        f"parser znalazł tylko {len(code)} trybów we właściwości Mode w "
        f"{RUN_PLAN} — regex się popsuł albo właściwość zniknęła")
    assert len(set(code)) == len(code), (
        f"RunPlan.Mode zwraca zduplikowaną nazwę trybu: {code}")

    report_text = _read(REPORT)
    section = section_1_3(report_text)
    assert section, f"§1.3 zniknęło z {REPORT} albo zmieniło numer"

    table = table_modes(section)
    assert table, "tabela trybów pod nagłówkiem §1.3 jest pusta albo bramka jej nie widzi"
    assert len(set(table)) == len(table), (
        f"tabela §1.3 wymienia ten sam tryb dwa razy: {table}")

    claimed = header_mode_count(report_text)
    assert claimed is not None, (
        "nagłówek §1.3 nie podaje liczby trybów słownie w formie "
        "„### 1.3 <liczebnik> tryb…,”")

    assert set(table) == set(code), (
        f"tabela §1.3 wymienia {sorted(table)}, RunPlan.Mode zwraca {sorted(code)} — "
        f"tabela ma nadmiarowo {sorted(set(table) - set(code))}, brakuje jej "
        f"{sorted(set(code) - set(table))}")
    assert claimed == len(code) == len(table), (
        f"nagłówek §1.3 mówi {claimed} trybów, RunPlan.Mode zwraca {len(code)}, "
        f"tabela §1.3 ma {len(table)} wierszy — powinny być równe")


def test_parsers_reject_a_mismatch_and_read_what_is_really_there():
    """Kontrole detektorów — bez nich bramka wyżej byłaby zielona i z martwym
    parserem (zero trafień wszędzie), i z parserem, który czyta cokolwiek."""
    sample_code = (
        'public string Mode => A is not null ? "from-telemetry"\n'
        '    : B is not null ? "replay"\n'
        '    : C ? "line" : "manual";\n'
        '\n'
        'public string Other => "nie-to";\n'
    )
    assert code_modes(sample_code) == ["from-telemetry", "replay", "line", "manual"]
    assert code_modes("public string Nic => 1;") == []

    assert header_mode_count("### 1.3 Sześć trybów, i coś") == 6
    assert header_mode_count("### 1.3 Cztery tryby, i coś") == 4
    assert header_mode_count("### 1.3 Coś innego bez liczebnika") is None
    assert header_mode_count("### 1.4 Sześć trybów, zły numer sekcji") is None

    sample_report = (
        "## 1. Sekcja\n\n"
        "### 1.3 Sześć trybów, X\n\n"
        "| tryb | x |\n"
        "|---|---|\n"
        "| `manual` | y |\n"
        "| `line` | y |\n"
        "\n"
        "### 1.4 dalej\n\n"
        "| `nie-to` | z |\n"
    )
    section = section_1_3(sample_report)
    assert "1.4" not in section, "sekcja 1.3 wciągnęła zawartość sekcji 1.4"
    assert table_modes(section) == ["manual", "line"]

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
