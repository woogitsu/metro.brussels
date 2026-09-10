# Panel interfejsu ucinał wiersz przy węższym widoku (6.D82)

**Zmierzone 10.09.2026 na:** `9cf6d55`, kontener tej sesji, Godot 4.7.2-stable mono,
`xvfb-run` + `--rendering-driver opengl3`.
**Przyrząd:** sześć zrzutów z silnika (800 x 600, 1280 x 720, 1920 x 1080, przed
i po), `dotnet test tests/Game.Tests`, trzy kontrole negatywne z `md5sum -c`
po każdym powrocie.

---

## 1. Co było zepsute

```
[node name="Panel" type="PanelContainer" parent="Hud"]
anchors_preset = 2          ; lewy dolny róg
offset_left  = 24.0
offset_right = 900.0        ; szerokość STAŁA 876 px, niezależna od widoku
```

Panel miał szerokość wpisaną w pikselach. Przy 1280 px kończył się na x = 900
i miał widoczną prawą krawędź; przy 800 px sięgał **poza brzeg okna**.

## 2. Zrzuty, OBEJRZANE — po jednym zdaniu na każdy

Kadr z kabiny przy kilometrażu **2054 m**, czyli przy stacji
`Comte de Flandre|Graaf van Vlaanderen` — **najdłuższej nazwie stacji w danych osi**
(37 znaków, `data/track/L1_A.json`, wybrana przeliczeniem 61 nazw, nie na oko).

**PRZED, 800 x 600.** Tło panelu dochodzi do prawej krawędzi kadru bez odstępu,
a wiersz pozycji urywa się w połowie zdania: widać
`chainage 2054.1 m / 6686.7 m   Comte de Flandre|Graaf van Vlaanderen za 1`
i nic więcej — **jednostki `m` nie ma**. Trzeci wiersz (ciąg/hamulec) mieści się,
bo jest krótszy.

**PRZED, 1280 x 720.** Panel kończy się mniej więcej na dwóch trzecich szerokości,
z wyraźną prawą krawędzią i pustką za nią; wiersz pozycji jest **cały**, kończy się
`za 1 m`. Ten sam napis, ta sama scena — różni się tylko szerokość widoku.

**PRZED, 1920 x 1080.** Jak wyżej, tylko pustka za panelem zajmuje połowę kadru.

**PO, 800 x 600.** Wiersz pozycji **zawija się na dwie linie**:
`… Comte de Flandre|Graaf van` / `Vlaanderen za 1 m`. Odległość do peronu razem
z jednostką jest czytelna. Tło panelu kończy się przed krawędzią kadru.

**PO, 1280 x 720.** Wiersz pozycji mieści się w jednej linii i kończy `za 1 m`;
tło panelu sięga teraz na całą szerokość minus odstęp, więc prawa krawędź nie tnie
kadru w połowie. Treść wierszy i kolory bez zmian.

**PO, 1920 x 1080.** To samo; wiersz w jednej linii, panel na całą szerokość.

## 3. Dlaczego to nie jest ocena estetyczna

`CLAUDE.md` §8 wyklucza z kolejki **oceny estetyczne**. Ucięta jednostka i ucięte
cyfry nie są oceną: gracz przy 800 x 600 **nie odczyta, ile zostało do peronu**.
Przy tej stacji ucięło jednostkę; przy odległości trzycyfrowej ucięłoby liczbę.
To utrata informacji sterującej. Kolorów i układu wierszy nie tknąłem — one są
w polu „Poza zakresem".

## 4. Poprawka

```
anchors_preset = 12         ; dolna krawędź, cała szerokość
anchor_right = 1.0
offset_right = -24.0        ; odstęp taki sam jak z lewej
grow_horizontal = 2
```
plus `autowrap_mode = 3` na wierszu pozycji.

**Zawijanie MĄDRE (3), nie samo po słowach (2)**, i to jest zmierzone: nazwa
dwujęzyczna nie ma spacji przy pionowej kresce, więc
`Flandre|Graaf` jest dla podziału po słowach jednym słowem.

## 5. Czego testy NIE mierzą, i to jest wypisane, a nie przemilczane

Prostokątów **etykiet** nie da się policzyć w `dotnet test`: ich szerokość zależy od
metryk czcionki, a te zna wyłącznie silnik, którego ten zestaw nie uruchamia. Pole
„Skończone, gdy" żąda prostokąta „każdej widocznej etykiety" — dostarczone jest to,
co rozstrzyga i co JEST mierzalne:

- prostokąt **panelu** liczony z kotwic tą samą arytmetyką, co w Godocie
  (`lewa = anchor_left * szerokość + offset_left`), sprawdzony na trzech
  rozdzielczościach;
- **zawijanie** wiersza pozycji — bo etykieta zawijająca wewnątrz kontenera nie może
  być szersza od niego, więc jej zmieszczenie WYNIKA ze zmieszczenia panelu;
- najdłuższa nazwa stacji **przeliczona z danych** i przybita w teście, żeby dopisanie
  dłuższej było widoczne, a nie ciche.

Kadry zostały obejrzane (§2) i to one są dowodem na etykiety; testy pilnują, żeby
arytmetyka pod nimi nie wróciła do stałej szerokości.

## 6. Trzy kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | dzisiejsze kotwice przywrócone (`preset 2`, `offset_right = 900`) | **czerwona** 2/219 |
| KN-2 | zawijanie zdjęte z wiersza pozycji | **czerwona** 1/219 |
| KN-3 | panel przesunięty w lewo (`offset_right = 700`, bez prawej kotwicy) | **czerwona** 1/219 |

**KN-3 jest tu po to, żeby druga bramka nie była kopią pierwszej.** Panel o stałej
szerokości 676 px **mieści się** w 800 px, więc test na zawieranie przechodzi — i pada
dopiero test na symetrię odstępu: `800 px: odstęp z lewej 24 != odstęp z prawej 100`.
Bez tego drugiego testu „poprawka" polegająca na zwężeniu panelu byłaby zielona,
a przy 1920 px zostawiałaby 1200 px pustki.

## 7. Czego NIE zrobiłem

**Nie tknąłem kolorów ani układu wierszy** — pole „Poza zakresem".
**Nie dodałem zawijania do pozostałych sześciu wierszy.** Zmierzone: przy najdłuższej
nazwie stacji ucinał się wyłącznie wiersz pozycji, a pozycja mówi o „zawijaniu na
wierszu pozycji". Wiersz pomocy jest drugim kandydatem i zostaje **zauważony,
nie tknięty**.
**Nie zmieniłem rozdzielczości bazowej** w `project.godot` (1280 x 720) — nic tego
nie wymagało, a jest to zmiana widoczna w każdym zrzucie CI.

## 8. Weryfikacja

```
dotnet test tests/Game.Tests
  -> Passed!  Failed: 0, Passed: 219, Total: 219      (przed zmianą: 215)

dotnet test tests/Sim.Tests
  -> Passed!  Failed: 0, Passed: 597, Total: 597

python3 tools/tests/test_all.py
  -> RAZEM 97,170 s, 2143 testów, 113 modułów, kod 0

tools/ci/assert_no_godot_warnings.py na trzech logach PO:
  [OSTRZEŻENIA] 0 spoza listy, 2 środowiskowych   (x3, kod 0)
```

Zrzuty leżą w `build/d82/` i **nie są commitowane** — `build/` jest ignorowane
(`CLAUDE.md` §4.8).
