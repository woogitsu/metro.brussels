# 6.D276 — próbka dowodu policzona jako całość, i trzy pomyłki przyrządu po drodze

**Data:** 18.09.2026 · **Gałąź:** `claude/6d276-probka-jako-calosc` · **Baza:** `8d35bb2`

## 1. Trzy liczby — i pierwsza prostuje pole „Wyjście" tej pozycji

Zmierzone na `tools/tests/`, w funkcjach **nie-testowych**, dla wycinków `[:N]`
o literale całkowitym dodatnim:

| co | ile |
|---|---|
| wycinków `[:N]` w czytnikach | **19** |
| plików, w których stoją | **12** |
| z tego **wychodzących** z czytnika (wartość dociera do wyniku) | **6** |
| z tego skracających **kolekcję**, a nie napis do wypisania | **3** |

Pole „Wyjście" pozycji mówiło **„20 wycinków w 13 plikach"**. Obie liczby są
nieprawdziwe i **każda z innego powodu**.

**Dwadzieścia bierze się z podwójnego liczenia.** `ast.walk` na funkcji zewnętrznej
odwiedza także węzły funkcji zagnieżdżonej, więc wycinek z `test_tool_refusals.py:84`
wpada raz jako `asserty` i raz jako `zejdz` — jeden wycinek, dwa wpisy. Błąd jest
odtwarzalny i **popełniłem go sam dwa razy**: w rozpoznaniu przed wzięciem pozycji
i we własnym przewidywaniu spisanym przed przebiegiem. Deduplikacja po
`(plik, wiersz, kolumna)` jest w czytniku treścią, nie ostrożnością.

**Trzynastu plików nie daje żadna sprawdzona definicja.** Odrzucone: literał dodatni
(12), literał dowolny łącznie z ujemnym (12), górna granica dowolna (32), literał > 1
(11), zakres `tools/tests` (12), zakres `tools` w całości (33). Odrzucone także trzy
drzewa historyczne — `7822a10`, `a1a643a` (drzewo, na którym pozycję pisano) i dzisiejsze
— każde daje 12. Sześć hipotez odrzuconych to **nie dowód**, tylko sześć hipotez;
najprościej tłumaczy to liczba wpisana z ręki, której nikt nie porównał z drzewem —
czyli kształt 6.D268, siedzący w pozycji, która sama jest **o liczeniu na próbce**.

## 2. Odpowiedź na pytanie o szkodę brzmi ZERO — i to nie jest brak znaleziska

Żaden z trzech wycinków skracających kolekcję nie daje dziś innej liczby niż pełny
zbiór, bo w dwóch przypadkach **autor postawił obok pełny licznik**, a trzeci jest
fiksturą, w której skrócenie jest treścią:

| miejsce | zapis | dlaczego nieszkodliwy |
|---|---|---|
| `mutation_sweep.py:check_one` | `"padly": failed[:5]` | tuż obok stoi `"ile_padlo": len(failed)` |
| `test_message_claims.py:pozycje_pokrycia` | `pokrywajace[:2]` | klasa liczona z pełnego zbioru (poprawka 6.D274, z komentarzem) |
| `test_validate_axis.py:z_forma` | `stops[:5]` | asercja obok mówi wprost „wśród pierwszych pięciu" |

**To jest wzorzec poprawny i to on stanowi treść bramki:** próbka wolno, ale obok ma
stać licznik z całości. Bramka nie zakazuje wycinków — zakazuje skrócenia kolekcji,
która **wychodzi** z czytnika, bez licznika liczonego z pełnego zbioru.

## 3. Klasyfikator mylił się TRZY RAZY i za każdym razem wyglądał wiarygodnie

To jest właściwe znalezisko tej pozycji i dotyczy przyrządu, nie drzewa.

| wersja | co robiła | ile dała `WYCHODZĄCYCH` | jak wypadał przypadek, który pozycję wywołał |
|---|---|---|---|
| 1 | kończyła łańcuch na każdym wywołaniu | 1 | `zjedzony-przez-wywolanie` |
| 2 | przepuszczała `append`, ale gubiła **odbiornik** | 1 | `przypisany`, potem `lokalny` |
| 3 | skakała przez odbiornik, ale liczyła funkcje zagnieżdżone dwa razy | 6 z 20 wpisów | `WYCHODZI`, ale populacja zawyżona |
| dzisiejsza | skok przez odbiornik + deduplikacja | **6 z 19** | `WYCHODZI` |

Każda z trzech pierwszych **dawała liczbę**, którą dało się przepisać do raportu.
Żadnej nie zdemaskował przebieg zestawu — wszystkie trzy znalazło sprawdzenie wyniku
**na przypadku, o który w pozycji chodziło**. Dlatego `pokrywajace[:2]` jest w bramce
żądane **po imieniu**, a nie przez sumę: suma zgadzałaby się przy każdej z wersji 3 i 4.

**Czwarta pomyłka, w tym samym pliku co reguła, która jej zakazuje.** Pierwsza wersja
zbioru przybitego kotwiczyła wpisy **po numerze wiersza** — i rozjechała się przy
mojej następnej edycji tego modułu, dziesięć ekranów pod komentarzem mówiącym, że
„kotwice po numerze wiersza ruszyły się w tym repozytorium ósmy raz w niecałe cztery
doby" (6.D229). Klucz to dziś `(plik, funkcja, wyrażenie)`.

**Piąta: „kolekcja czy napis" nie da się wyczytać z AST.** `wiersz[:60]`
i `pokrywajace[:2]` to dla parsera ten sam kształt. Pierwsza wersja bramki próbowała
wywnioskować to z tego, czy wycinana jest goła nazwa — i wpuściła `wiersz[:60]`, bo to
też goła nazwa. Werdykt jest więc **deklarowany**, a zbiór obejmuje wszystkie sześć
wychodzących i jest porównywany **w obie strony** (6.D243).

## 4. Kontrole

| | co | oczekiwane | wynik |
|---|---|---|---|
| KN1 | licznik z całości zamieniony na licznik z próbki (dosłownie błąd 6.D274) | czerwono | **czerwono**, na liczbie: `wycinkow [:N] w czytnikach jest 20 przy zapisanych 19` |
| KN1c | licznik przestaje stać na gołej nazwie, **liczba bez zmian** | czerwono na klauzuli towarzysza | **czerwono:** „…a `len(pokrywajace)` na PELNEJ nazwie w tej funkcji juz nie stoi" |
| KN2 | oślepienie czytnika do zera | czerwono | **czerwono:** `jest 0 przy zapisanych 19` + kontrola przyrządu |
| KN3 | cofnięcie skoku przez odbiornik (własna pomyłka nr 3) | czerwono | **czerwono:** `WYCHODZACYCH jest 2 przy zapisanych 6`, a kontrola przyrządu nazywa przyczynę |
| KP2 | kopia drzewa z kompletem, `root` przekazany **jawnie** | zgodność | **19 = 19** |
| KP3 | mutacja **kopii** | przyrząd żywy | **kopia 20, robocze 19**; nowy wycinek widziany tylko w kopii |

KN1 jest ważne, ale słabsze, niż wygląda: złapało mutację **na liczbie**, bo
`len(pokrywajace[:2])` sam dokłada wycinek. Dlatego stoi obok KN1c, które izoluje
klauzulę towarzysza przy niezmienionej liczbie. Bez tej pary raport mówiłby, że bramka
pilnuje towarzysza, nie pokazawszy tego.

## 5. Czego ta pozycja nie ruszała

- **Przepisywania znalezionych wycinków na pełne zbiory.** Każde zwiększa pamięć
  czytnika i jest osobnym kosztem; pole „Poza zakresem" tego zabrania, a odpowiedź
  z §2 brzmi i tak „zero szkody dzisiaj".
- **Zmiany `OKNO_PROZY` ani wzorca pogrubienia** — to 6.D259.
- **Poprawienia pola „Wyjście" pozycji w `docs/TASKS.md` bez podania definicji.**
  Liczby 19 i 12 wchodzą tam **razem** ze zdaniem, która definicja je daje — inaczej
  wymieniłbym jedną liczbę bez pokrycia na drugą bez pokrycia.
