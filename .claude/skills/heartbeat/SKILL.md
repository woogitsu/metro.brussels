---
name: heartbeat
description: Nieinwazyjny puls co godzinę, który wybudza długo działającą sesję, gdy ta stanie, i nie robi nic, gdy praca trwa.
---

# Puls sesji

**Nie dla każdej sesji.** Zakładaj go tylko wtedy, gdy sesja ma pracować długo albo bez
nadzoru. Dla poprawki na dziesięć minut jest zbędny i tylko zaśmieca listę Routines.

Wymaga serwera MCP `claude-code-remote` (`create_trigger`, `list_triggers`,
`delete_trigger`, `get_session`). Sesja lokalna bez niego **nie może** tego zrobić —
to jest stan konta, nie stan repozytorium, więc żaden plik w repo sam go nie utworzy.

Nazwa jest stała i po niej się go rozpoznaje: **`METRO BXL — pobudka co godzinę`**.

## Zanim utworzysz

1. `list_triggers(enabled=true)` — szukaj Routine o tej nazwie.
2. Jeśli **nie ma** — utwórz (poniżej) i skończ.
3. Jeśli **jest**, sprawdź `persistent_session_id`:
   - to **twoja** sesja → nic nie rób, jest gotowe;
   - to **inna, żywa** sesja (`get_session` → aktywna) → **nie twórz drugiego**.
     Dwie pobudki to dwie sesje dłubiące przy tym samym repo;
   - to **inna, martwa** sesja (zarchiwizowana albo nieistniejąca) → `delete_trigger`,
     potem utwórz nowy. `update_trigger` **nie umie** przepiąć Routine na inną sesję.

Bez tego kroku każda kolejna sesja dokłada Routine budzącą nieboszczyka.

## Utworzenie

`create_trigger` z `cron_expression: "0 * * * *"`, `initiation: "human_request"`,
bez `persistent_session_id` i bez `create_new_session_on_fire` — wtedy puls wchodzi
do **tej** sesji i kontynuuje rozmowę, zamiast startować od zera.

Serwer zakotwiczy cron na minucie utworzenia (np. `48 * * * *`) i to jest w porządku:
nadal co godzinę, tylko Routines nie kumulują się na pełnej godzinie.

Pełna treść promptu: `docs/22-heartbeat.md` §2. Skopiuj ją dosłownie — jej sensem jest
to, żeby puls **milczał**, kiedy praca trwa.

## Sprzątanie

Kiedy sesja kończy pracę na dobre, skasuj swoją Routine (`delete_trigger`). Zostawiona
budzi sesję, której już nie ma, aż ktoś ją zauważy na liście.
