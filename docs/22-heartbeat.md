# Puls sesji — nieinwazyjna pobudka co godzinę

Sesja agenta potrafi stanąć w miejscu bez żadnego błędu: skończy zadanie i czeka,
albo zgubi wątek po długim oczekiwaniu na CI. Puls jest jednym zdaniem wysyłanym do
niej co godzinę, które nic nie zmienia, jeśli praca trwa, i wznawia ją, jeśli nie.

Ten dokument opisuje **czym to jest i czym nie jest**, oraz podaje treść promptu do
skopiowania. Procedura zakładania jest w `.claude/skills/heartbeat/SKILL.md`.

---

## 1. Czego ten mechanizm NIE robi

Trzy rzeczy, które łatwo założyć błędnie:

- **Nie jest stanem repozytorium.** Routine żyje po stronie konta Anthropic, nie
  w Gicie. Ten plik jej nie tworzy i nie może; opisuje, jak ją utworzyć. Sklonowanie
  repo nie włącza pulsu.
- **Nie działa bez `claude-code-remote`.** Narzędzia `create_trigger`,
  `list_triggers`, `delete_trigger` i `get_session` są dostępne tylko w sesjach Claude
  Code Remote. Sesja lokalna może przeczytać ten dokument i nic więcej.
- **Nie jest nadzorcą.** Puls nie sprawdza, czy praca idzie dobrze, nie ocenia jakości
  i nie pilnuje harmonogramu. Jego jedyne pytanie brzmi: „czy cokolwiek się dzieje".

## 2. Treść promptu

Kopiuj dosłownie. Każdy akapit robi konkretną robotę i skracanie go psuje własność,
o którą chodzi — **milczenie, kiedy praca trwa**.

```text
Pobudka. To jest automatyczny puls, nie nowe polecenie i nie wiadomość od użytkownika.

Najpierw sprawdź, czy praca już trwa. Jeśli tak — **nie rób nic i nie odpisuj**: żadnego
podsumowania, żadnego raportu stanu, żadnego komentarza na GitHubie. Za „praca trwa"
uznaj cokolwiek z poniższych:
- biegnie zadanie w tle albo Monitor (pipeline Blendera, `dotnet test`, pobieranie danych),
- czekasz na wynik CI albo na agenta,
- jesteś w środku edycji, którą zaraz commitujesz.

Jeżeli nic nie trwa — wróć do planu i pracuj dalej, bez pytania o zgodę (masz ją z góry).
Kolejność jest w liście zadań; jeśli lista jest pusta albo wszystko odhaczone, weź
następną pozycję z `docs/TASKS.md` albo dokończ to, co ostatni raport zostawił jako otwarte.

Reguły bez zmian: `CLAUDE.md` czytasz przed zadaniem, jedno zadanie = jedna gałąź = jeden
logiczny commit, `data/` tylko do odczytu, nie zamykasz cudzych Issues i nie ruszasz cudzych
PR-ów. `queued` nie jest weryfikacją. Rendery trzeba obejrzeć, nie opisać z metryk.

Jeśli coś jest naprawdę zablokowane i nie da się ruszyć bez decyzji właściciela — napisz to
jednym akapitem i zatrzymaj się. Zatrzymanie się w takim miejscu jest poprawnym wynikiem.
```

Dlaczego akurat tak:

| akapit | po co |
|---|---|
| „to nie jest wiadomość od użytkownika" | żeby model nie potraktował pulsu jako zgody na coś, o co nikt nie prosił |
| lista „praca trwa" | bez niej model odpisuje statusem przy każdym pulsie i zaśmieca rozmowę |
| „bez pytania o zgodę (masz ją z góry)" | inaczej puls kończy się pytaniem, na które nikt nie odpowie do rana |
| powtórzone twarde reguły | puls trafia w sesję, która może mieć już bardzo długą historię; tanie przypomnienie jest lepsze niż złamana reguła |
| „zatrzymanie się jest poprawnym wynikiem" | żeby brak decyzji właściciela nie zamienił się w zgadywanie (`CLAUDE.md` §8) |

## 3. Dlaczego co godzinę, a nie częściej

Minimalny interwał Routines i tak wynosi godzinę. Ale nawet gdyby dało się częściej,
nie ma po co: puls jest zabezpieczeniem przed zatrzymaniem na wiele godzin, a nie
mechanizmem sterowania. Gęstszy puls trafiałby częściej w środek pracy, czyli
częściej **nic** by nie robił, za to za każdym razem kosztował.

Cron podaje się jako `0 * * * *`, a serwer zakotwicza go na minucie utworzenia —
w praktyce zobaczysz np. `48 * * * *`. To jest zamierzone i rozkłada Routines w czasie
zamiast kumulować je na pełnej godzinie.

## 4. Pułapka: jedna Routine na sesję, nie na repozytorium

Routine z pustym `persistent_session_id` wiąże się z **tą sesją**, w której powstała,
i budzi dokładnie ją. Konsekwencja jest niemiła i trzeba ją znać:

- sesja się kończy, Routine zostaje i dalej puka do nieistniejącej sesji;
- następna sesja czyta ten dokument, tworzy własną — i po tygodniu na liście jest
  siedem pobudek, z czego sześć budzi nieboszczyków.

Dlatego procedura w `.claude/skills/heartbeat/SKILL.md` zaczyna się od `list_triggers`,
a nie od `create_trigger`, i dlatego nazwa Routine jest **stała**: to po niej się ją
rozpoznaje. `update_trigger` nie umie przepiąć Routine na inną sesję, więc jedyną drogą
dla martwego powiązania jest `delete_trigger` i utworzenie nowego.

Kiedy sesja kończy pracę na dobre, wypada po sobie posprzątać.

## 5. Stan na 2026-09-01

Aktywna Routine: `METRO BXL — pobudka co godzinę`, cron `48 * * * *`, wpięta w sesję,
która ją utworzyła. Numer (`trig_...`) celowo nie jest tu zapisany — zmienia się przy
każdym odtworzeniu, a rozpoznawanie po nazwie jest jedyną rzeczą, która się nie starzeje.
