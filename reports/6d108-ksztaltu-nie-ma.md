# 6.D108 — pomiar mówi, że takiego kształtu nie ma

**Zmierzone 10.09.2026 na:** `34d9383`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_report_claims.py` (`CLAIM`, `claims_in_reports`,
`constant_values`), skan po `reports/`, `git worktree` na `bd0bc92` dla liczby z dnia
powstania wpisu, `git log -S` dla dat zmian stałych, `.github/workflows/python-tests.yml`
dla głębokości checkoutu.

**Ta pozycja NIE jest zrobiona.** Pole „Wyjście" żąda rozróżnienia „po kształcie, nie po
liście wyjątków", a **kształt do ustalenia pomiarem**. Pomiar jest zrobiony i mówi, że
takiego kształtu nie ma; wybór między trzema mechanizmami, które zostają, jest decyzją
właściciela, bo każdy zmienia to, **czym ta bramka jest**.

---

## 1. Liczba z wpisu się nie odtwarza

Wpis mówi: **18 miejsc w 12 plikach**. Policzone tym samym wzorcem:

| kiedy | miejsc | plików |
|---|---:|---:|
| dziś (`34d9383`) | **9** | **7** |
| `bd0bc92`, dzień powstania wpisu | **10** | **8** |

Żaden inny odczyt też nie daje 18/12 — sprawdzone cztery, na `bd0bc92`:

```
  zapadki znane kodowi                                  10 miejsc w  8 plikach
  zapadki, takze nieznane kodowi                        13 miejsc w 10 plikach
  wszystkie stale znane kodowi (= twierdzenia bramki)   26 miejsc w 15 plikach
  wszystkie nazwy w grawisach z liczba                 104 miejsc w 43 plikach
```

Spadek 10 → 9 jest prawdziwy i mój: część tych zdań przepisałem słownie w tej samej
sesji, wykonując 6.D96, 6.D99, 6.D103 i 6.D105. To jest właśnie obejście, które ta
pozycja miała zastąpić regułą.

## 2. Wszystkie dziewięć zdań wygląda tak samo

```
6d90-okno-mutacji-a-czyste-drzewo.md:88   `MAX_ZAPISOW_W_DRZEWIE` stoi na **5** i wolno jej wyłącznie maleć.
kolejka-uzupelnienie-drugie.md:235        `MINIMUM_READY_ITEMS` zostaje na 12.
kolejka-uzupelnienie-trzecie.md:140       `MINIMUM_READY_ITEMS` zostaje na 12.
kolejka-uzupelnienie.md:8                 …ile wynosi próg `MINIMUM_READY_ITEMS` = 12.
ramka-w-sciezce.md:432                    Próg `MIN_PATHS_IN_TREE` postawiony na **29**, `MIN_FILES_WITH_PATHS` na **8**,
ramka-w-sciezce.md:433                    zapadka `MAX_JUSTIFICATIONS` na **14** — wszystkie trzy na stanie faktycznym…
uzupelnienie-kolejki-10-09-druga.md:107   `MINIMUM_READY_ITEMS` **bez zmiany** (12).
zapadka-liczby-raportow.md:112            …nowa zapadka `MAX_REPORTS_WITHOUT_FIELD_LINE` = 5…
```

**Nie ma w nich znacznika czasu ani żadnego innego, który odróżniałby je od zdania
o wartości bieżącej** — bo w dniu napisania każde z nich BYŁO zdaniem o wartości
bieżącej. Informacja rozstrzygająca leży poza zdaniem.

## 3. Trzy mechanizmy, które zostają, i co każdy kosztuje

### 3.1 Data z nagłówka raportu

176 z 226 raportów ma nagłówek `**Zmierzone <data>`. Wszystkie siedem plików
z powyższej listy go ma. Reguła „raport datowany mówi o swojej dacie" **spełnia obie
połowy** pola „Skończone, gdy" dla raportów starszych niż dzień przebiegu.

Koszt, zmierzony: twierdzeń w raportach **datowanych 13**, w raportach **bez daty 12**
(w trzech plikach triażu). Wyłączenie datowanych zostawia bramkę nad trzema starymi
plikami i **oślepia ją na każdy przyszły raport** — bo każdy nowy raport jest datowany.
Drugi koszt: werdykt zależałby od kalendarza, a raport napisany „dziś" byłby sprawdzany
inaczej niż ten sam raport jutro.

### 3.2 Data ostatniej zmiany stałej, z gita

Rozstrzygałaby dokładnie to, co trzeba: raport datowany na D musi zgadzać się z kodem,
jeśli stała nie zmieniła się po D. Działa i jest szybka:

```
  MAX_ZAPISOW_W_DRZEWIE              ostatnia zmiana wartosci: 2026-09-10
  MINIMUM_READY_ITEMS                ostatnia zmiana wartosci: 2026-09-07
  MAX_REPORTS_WITHOUT_FIELD_LINE     ostatnia zmiana wartosci: 2026-09-08
```

**Nie działa w CI.** `.github/workflows/python-tests.yml` woła `actions/checkout` bez
`fetch-depth`, czyli z domyślną głębokością **1**: `git log -S` nie ma tam czego
przeszukać. Włączenie pełnej historii to zmiana dziesięciu workflowów i dłuższy
checkout — poza zakresem tej pozycji i osobna decyzja.

### 3.3 Kierunek zapadki

Jedyna reguła spełniająca obie połowy bez kalendarza i bez gita: wartość, którą zapadka
**mogła mieć**, jest zdaniem datowanym; wartość, której mieć **nie mogła**, jest fałszem.
Wymaga to znajomości kierunku każdej cytowanej zapadki. Przeczytane z ich własnych
komentarzy — i kierunek **nie jest jednolity nawet w obrębie przedrostka**:

| zapadka | co mówi jej komentarz | kierunek |
|---|---|---|
| `MAX_ZAPISOW_W_DRZEWIE` | „Wolno ją wyłącznie OBNIŻAĆ" | maleje |
| `MAX_JUSTIFICATIONS` | broni przed „rośnie po cichu" | maleje |
| `MAX_REPORTS_WITHOUT_FIELD_LINE` | „rośnie za cenę podniesienia tej stałej w tym samym commicie" | **rośnie za powodem** |
| `MIN_PATHS_IN_TREE`, `MIN_FILES_WITH_PATHS` | progi KW postawione pod stanem faktycznym | rosną |
| `MINIMUM_READY_ITEMS` | próg polityki, „nie obniżył progu" | **nie rusza się wcale** |

Dla dwóch z sześciu żaden kierunek nie jest bezpieczny: „rośnie za powodem" znaczy, że
wolno w obie strony, więc reguła degeneruje się do „przyjmij cokolwiek" i cichnie na
nich całkowicie. Tabela kierunków byłaby przy tym **danymi o każdej zapadce**, a nie
listą wyjątków — ale dla części zapadek byłaby zgadywaniem.

## 4. Co z tego wynika

Rozróżnienie, o które prosi pole „Wyjście", **nie da się oprzeć na kształcie zdania**:
zdanie datowane i zdanie o wartości bieżącej mają ten sam kształt, bo są tym samym
zdaniem powiedzianym w różnych dniach. Zostają trzy mechanizmy, każdy zmieniający coś
innego:

* **3.1** zawęża bramkę do raportów bez daty — czyli do przeszłości;
* **3.2** jest najbliższy zamierzeniu, ale wymaga pełnej historii w CI;
* **3.3** wymaga zadeklarowania kierunku dla każdej zapadki i milknie na tych, które
  wolno ruszać w obie strony.

To jest wybór **czym ta bramka ma być**, a nie szczegół implementacji — więc decyzja
właściciela, zgodnie z `CLAUDE.md` §8. Pozycja zostaje otwarta z tym pomiarem
i z polem „Zależy od" wskazującym na tę decyzję.

## 5. Czego świadomie nie zrobiłem

- **Nie zmieniałem `CLAIM` ani `CLAIM_EXCEPTIONS`.** Wpis wyklucza listę wyjątków,
  a żadnej zmiany wzorca nie da się uzasadnić przed rozstrzygnięciem z §4.
- **Nie przepisywałem żadnego z dziewięciu zdań** — pole „Poza zakresem" wyklucza
  przepisywanie raportów historycznych, a to jest dokładnie ta droga, którą pozycja
  miała zastąpić.
- **Nie ruszałem wartości żadnej zapadki** (to samo pole).
- **Nie dodawałem `fetch-depth: 0` do workflowów.** To dziesięć plików, dłuższy
  checkout i osobna decyzja — a bez niej mechanizm 3.2 nie działa w CI.

## 6. Co zauważyłem przy okazji

- **`MINIMUM_READY_ITEMS` nie jest zapadką, tylko progiem polityki.** Trzy z dziewięciu
  zdań mówią o nim „zostaje na 12" / „bez zmiany (12)" — czyli o tym, że NIE został
  obniżony. Gdyby kiedyś został, te trzy zdania stałyby się fałszem o wartości bieżącej
  i jednocześnie prawdą o dniu pomiaru; mechanizm 3.3 nie ma dla nich odpowiedzi.
- **Cztery z dziewięciu miejsc powstały w tej sesji jako obejście**, przez przepisanie
  liczby słownie. Obejście działa i nie jest kłamstwem, ale zamienia liczbę sprawdzalną
  na napis, którego bramka nie czyta — czyli kupuje ciszę kosztem pokrycia.
