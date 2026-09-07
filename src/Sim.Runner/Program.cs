using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;

namespace MetroBxl.Sim.Runner;

/// <summary>
/// Gospodarz rdzenia bez silnika. Cztery polecenia, każde odpowiada na jedno pytanie
/// z pętli weryfikacji <c>CLAUDE.md</c> §5:
///
/// <list type="bullet">
/// <item><c>drive</c> — jak wygląda przejazd policzony samym rdzeniem;</item>
/// <item><c>compare</c> — o ile rozjeżdża się z przejazdem policzonym w Godocie;</item>
/// <item><c>axis</c> — czy oś w C# jest tą samą krzywą, po której zamiatany jest tunel;</item>
/// <item><c>parity</c> — czy kontroler przy pełnej trakcji to nadal rdzeń z T-310;</item>
/// <item><c>braking</c> — tablice referencyjne hamowania z T-311, do porównania
/// z <c>tools/physics/braking.py</c> wiersz po wierszu.</item>
/// </list>
/// </summary>
public static class Program
{
    /// <summary>
    /// Identyfikator składu w przejeździe pod sygnalizacją; ten sam, co używa scena,
    /// żeby zdarzenia sygnalizacji z obu stron dały się porównać po nazwie, a nie po
    /// domysłach.
    /// </summary>
    private const string SignalledTrainId = "KABINA";

    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    /// <summary>
    /// Opcje, które każde polecenie naprawdę czyta — osobno te z wartością i osobno
    /// flagi bez wartości.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Powód jest zmierzony, nie wymyślony. 6.D15 (#301) uruchomiło komendę z pola
    /// „Weryfikacja" pozycji 6.A6: <c>line … --coast-from-m X</c>. Opcji
    /// <c>--coast-from-m</c> nie było wtedy nigdzie w <c>src/</c>, <c>X</c> nie jest
    /// liczbą — a proces kończył się <b>kodem 0</b> i normalnym przebiegiem. Dwa
    /// wywołania, z opcją i bez niej, dały pliki identyczne co do bajtu. Literówka
    /// w nazwie opcji była więc nieodróżnialna od opcji działającej, a weryfikacja
    /// oparta na takiej komendzie spełniała się przez NIEZROBIENIE zadania.
    /// </para>
    /// <para>
    /// <b>Ten akapit jest przepisany przy 6.A6, a nie dopisany obok.</b> Poprzednia
    /// wersja mówiła o <c>--coast-from-m</c> w czasie teraźniejszym — „nie ma jej
    /// nigdzie w <c>src/</c>" — i to już nieprawda: 6.A6 dopisała wybieg do polecenia
    /// <c>line</c>, więc ta konkretna nazwa jest dziś opcją ZNANĄ. Przykładem literówki
    /// nieodróżnialnej od opcji działającej jest teraz <c>--headway-s</c> podane
    /// poleceniu <c>line</c> (istnieje, ale w <c>budget</c>) i taką parę trzyma
    /// <c>RunnerCommandTests</c>. Sam powód istnienia tabeli się nie zmienił.
    /// </para>
    /// <para>
    /// Kształt odmowy jest wzięty z <c>RunPlan.KnownArguments</c> po stronie Godota,
    /// która odmawia nieznanemu argumentowi od dawna; tu chodziło o to, żeby rdzeń
    /// przestał być pod tym względem łagodniejszy od sceny.
    /// </para>
    /// <para>
    /// Tabela jest ręczna, ale nie jest zdana na czyjąś pamięć:
    /// <c>tools/tests/test_runner_options.py</c> wyprowadza te same nazwy z wywołań
    /// <c>Option</c>, <c>RequiredNumber</c>, <c>OptionalNumber</c> i
    /// <c>Array.IndexOf</c> w treści każdego polecenia i porównuje zbiory. Opcja
    /// dopisana do kodu bez dopisania jej tutaj zapala tę bramkę.
    /// </para>
    /// </remarks>
    private static readonly IReadOnlyDictionary<string, (string[] Values, string[] Flags, int Positional)> KnownOptions =
        new Dictionary<string, (string[] Values, string[] Flags, int Positional)>(StringComparer.Ordinal)
        {
            ["drive"] = (new[] { "--out", "--sample-every" }, Array.Empty<string>(), 0),
            ["replay"] = (new[]
            {
                "--axis", "--exchange-s", "--keys", "--limit-kmh", "--notch-rate",
                "--out", "--sample-every", "--signalling", "--stop-window-m",
            }, new[] { "--atp" }, 0),
            ["compare"] = (new[] { "--tolerance" }, Array.Empty<string>(), 2),
            ["axis"] = (new[] { "--axis", "--dump-points", "--manifest" }, Array.Empty<string>(), 0),
            ["parity"] = (Array.Empty<string>(), Array.Empty<string>(), 0),
            ["braking"] = (Array.Empty<string>(), Array.Empty<string>(), 0),
            ["line"] = (new[]
            {
                "--axis", "--brake-usage", "--calls", "--coast-from-m", "--exchange-s",
                "--limit-kmh", "--load", "--signalling", "--stop-window-m", "--timetable",
                "--trace",
            }, Array.Empty<string>(), 0),
            ["budget"] = (new[]
            {
                "--axis", "--brake-usage", "--coast-from-m", "--exchange-s", "--headway-s",
                "--limit-kmh", "--load", "--out", "--repeats", "--signalling", "--steps",
                "--stop-window-m", "--trains", "--turnback-s", "--warmup",
            }, new[] { "--atp" }, 0),
            ["service-day"] = (new[] { "--at", "--out", "--timetable" }, Array.Empty<string>(), 0),
        };

    /// <summary>
    /// Wiersze <c>#</c> z nastawami, ktore wyprodukowaly plik — przed naglowkiem CSV.
    /// </summary>
    /// <remarks>
    /// <para>
    /// 6.A20. Wypis na konsole ginie razem z konsola; plik z <c>--out</c> PRZEZYWA
    /// proces i to on trafia do raportow. Do tej pozycji zaden pisarz CSV nie zapisywal
    /// ani jednej kolumny scenariusza, wiec dwa przebiegi o roznych nastawach dawaly
    /// pliki nieodroznialne — przy nastawach, ktore zmieniaja PRZEJAZD, nie tylko jego
    /// koszt (6.A18 zmierzyla <c>N_sr</c> 6,69 / 6,67 / 6,40 przy tym samym
    /// <c>--trains 9</c>).
    /// </para>
    /// <para>
    /// Jedna metoda, nie dwie kopie: gdyby kazdy pisarz sklejal ten naglowek sam,
    /// rozjazd formatu wygladalby jak roznica nastawy, a nie jak roznica wypisu — ta
    /// sama pulapka, ktora <c>LineRunSettings.CoastDescription</c> zamknelo przy 6.A18.
    /// </para>
    /// <para>
    /// Wiersze <c>#</c>, a nie dodatkowe kolumny: kolumna powtorzona w kazdym wierszu
    /// duplikuje te sama nastawe tyle razy, ile jest pomiarow, a <c>#</c> jest
    /// pomijane przez `pandas.read_csv(comment="#")` i przez `csv` z jednym filtrem.
    /// </para>
    /// </remarks>
    private static IEnumerable<string> Provenance(string command, params (string Name, string Value)[] settings)
    {
        yield return "# polecenie: " + command;
        foreach (var (name, value) in settings)
        {
            yield return "# " + name + ": " + value;
        }
    }

    /// <summary>Punkt wejścia.</summary>
    public static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Usage();
            return 2;
        }

        try
        {
            RejectUnknownOptions(args[0], args);
            return args[0] switch
            {
                "drive" => Drive(args),
                "replay" => Replay(args),
                "compare" => Compare(args),
                "axis" => Axis(args),
                "parity" => Parity(),
                "braking" => Braking(),
                "line" => LineCommand(args),
                "budget" => Budget(args),
                "service-day" => ServiceDayCommand(args),
                _ => Unknown(args[0]),
            };
        }
        catch (Exception exception) when (exception is IOException or ArgumentException or FormatException or InvalidOperationException)
        {
            Console.Error.WriteLine("BŁĄD: " + exception.Message);
            return 1;
        }
    }

    /// <summary>
    /// Odmawia, gdy polecenie dostało opcję, której nie czyta.
    /// </summary>
    /// <remarks>
    /// Sprawdzane są wyłącznie człony zaczynające się od <c>--</c>; argumenty
    /// pozycyjne (dwie ścieżki polecenia <c>compare</c>) przechodzą nietknięte.
    /// Człon następujący po znanej opcji z wartością jest pomijany, żeby wartość
    /// nigdy nie została wzięta za opcję. Polecenia nieznanego ta metoda nie tyka —
    /// zajmuje się nim <see cref="Unknown"/> i to on ma o nim powiedzieć.
    /// </remarks>
    private static void RejectUnknownOptions(string command, string[] args)
    {
        if (!KnownOptions.TryGetValue(command, out var known))
        {
            return;
        }

        // Opcje z wartoscia widziane w tym wierszu polecen — do wykrycia powtorzenia
        // (6.A23). FLAG to NIE dotyczy i jest to pole „Poza zakresem" tamtej pozycji:
        // `--atp --atp` znaczy dokladnie to samo, co `--atp`, wiec nie ginie tam zadna
        // wartosc; sprawdzone uruchomieniem (kod 0 przed zmiana i po niej).
        var seen = new HashSet<string>(StringComparer.Ordinal);

        // Czlony POZYCYJNE, czyli te bez minusa i nie bedace wartoscia znanej opcji
        // (6.A25). Do tej pozycji nie liczyl ich nikt, wiec `budget ... --atp 1`
        // konczylo sie kodem 0 i wypisem NIEODROZNIALNYM od `budget ... --atp`:
        // `1` przechodzilo jako czlon pozycyjny, ktorego zadna odmowa nie widzi.
        // To samo robil `budget ... zmyslony_czlon`.
        //
        // Odmowa 6.A11 i 6.A15 odsiewa czlony bez minusa CELOWO — `compare` bierze
        // dwie sciezki pozycyjnie, wiec „odmawiaj wszystkiemu, czego nie znam"
        // wywrociloby to polecenie w calosci. Zaleta tamtej decyzji zostaje; brakowalo
        // jedynie LICZBY, ile czlonow pozycyjnych polecenie naprawde czyta.
        //
        // Jedna liczba przy poleceniu, a nie nowy rozbior — i to jest ZMIERZONE, nie
        // zalozone: w calym `Program.cs` jedynymi odczytami `args[N]` dla N > 0 poza
        // samym rozbiorem opcji sa `args[1]` i `args[2]` w `Compare`. Zadne inne
        // polecenie nie czyta ani jednego czlonu pozycyjnego, wiec zero stoi wszedzie
        // indziej. Pilnuje tego bramka po stronie Pythona, ktora wyprowadza te liczby
        // z odczytow `args[N]` w cialach polecen i porownuje z tabela — tak samo jak
        // robi to od 6.A11 dla samych nazw opcji. Pomiar: `reports/czlon-pozycyjny.md`.
        var positional = 0;

        for (var i = 1; i < args.Length; i++)
        {
            var token = args[i];

            // JEDEN minus tez sie liczy (6.A15). 6.A11 sprawdzala wylacznie czlony
            // z dwoma minusami i SAMA wypisala te dziure: `-zmyslona 7` konczylo sie
            // kodem 0, dokladnie tak jak przed ta odmowa.
            //
            // Rozszerzenie jest bezpieczne i to jest ZMIERZONE, nie zalozone
            // (`reports/jeden-minus.md`): w calym repozytorium nie ma ani jednej
            // komendy podajacej `Sim.Runner` czlon z jednym minusem — `-c Release`
            // stoi PRZED separatorem `--`, wiec jest flaga `dotnet run` i nigdy nie
            // dochodzi do `args`. Nie ma tez ani jednej wartosci ujemnej, a jedyne
            // argumenty pozycyjne to dwie SCIEZKI polecenia `compare`.
            //
            // Wartosc ujemna nadal przechodzi, bo czlon po znanej opcji z wartoscia
            // jest pomijany razem z nia (i++ nizej) — `--brake-usage -0.5` dziala.
            // Czlon `-` sam w sobie nie jest opcja: to konwencja „standardowe
            // wejscie", ktorej to repozytorium nie uzywa, ale odmawianie jej byloby
            // odmowa czegos, co nie jest literowka.
            if (!token.StartsWith("-", StringComparison.Ordinal) || token == "-")
            {
                positional++;
                if (positional > known.Positional)
                {
                    throw new ArgumentException(
                        $"polecenie {command} dostało człon pozycyjny {token}, "
                        + (known.Positional == 0
                            ? "a nie bierze ani jednego. Człon bez minusa nie jest "
                              + "opcją, więc wartość podana po fladze (np. --atp 1) "
                              + "trafia właśnie tutaj"
                            : $"a bierze ich {known.Positional} — ten jest "
                              + $"{positional} w kolejności"));
                }

                continue;
            }

            if (Array.IndexOf(known.Values, token) >= 0)
            {
                // Powtorzona opcja jest ODMOWA, nie nadpisaniem (6.A23). `Option`
                // szuka PIERWSZEGO wystapienia i nie patrzy dalej, wiec do 07.09.2026
                // `--limit-kmh 72 --limit-kmh 50` jechalo 72, a odwrotna kolejnosc 50,
                // oba kodem 0 i bez ani jednego zdania o tym, ze druga wartosc
                // zniknela. Wartosc skuteczna nie byla niewidoczna — `[LINIA]`
                // i `[ZALOZENIE]` ja podaja, to zasluga 6.A5/6.A6 — ale czytajacy
                // widzial 72 i nie mial powodu przypuszczac, ze wiersz polecen mowil
                // takze 50. Od 6.A20 nastawy ida rowniez do plikow z `--out`, wiec ta
                // sama luka byla w artefakcie, ktory PRZEZYWA proces.
                //
                // Odmowa, a nie wypis o nadpisaniu: jest spojna z 6.A16 („kazda odmowa
                // argumentowa = 1") i wolno ja tu postawic, bo ZMIERZONE — w calym
                // repozytorium nie ma ani jednej komendy podajacej `Sim.Runner` tej
                // samej opcji dwa razy. Cztery dopasowania, ktore znalazl licznik, to
                // proza raportow i pole „Weryfikacja" tej pozycji; `--no-build` stoi
                // PRZED separatorem `--`, wiec jest flaga `dotnet run`.
                // Pomiar: `reports/powtorzona-opcja.md`.
                if (!seen.Add(token))
                {
                    throw new ArgumentException(
                        $"polecenie {command} dostało opcję {token} więcej niż raz. "
                        + "Wygrałaby pierwsza wartość, a pozostałe zniknęłyby bez słowa "
                        + "— podaj ją dokładnie raz");
                }

                i++;
                continue;
            }

            if (Array.IndexOf(known.Flags, token) >= 0)
            {
                continue;
            }

            // Postac `--opcja=wartosc` (6.A22). Do 07.09.2026 `--limit-kmh=72` konczylo
            // sie komunikatem „nie zna opcji --limit-kmh=72", ktory jest SPRZECZNY
            // z faktem: `--limit-kmh` stoi w tabeli. Runner nie zna POSTACI, a to jest
            // inna wiadomosc — i wazna, bo wartosc odmowy z 6.A11 lezy w tym, ze
            // czytajacy jej wierzy. Komunikat mowiacy raz na jakis czas nieprawde
            // o zawartosci tabeli uczy czytac go z zastrzezeniem, a wtedy przestaje
            // dzialac takze tam, gdzie mial racje.
            //
            // Dlaczego postac jest ODRZUCANA, a nie obslugiwana: w calym repozytorium
            // nie ma ani jednej komendy podajacej `Sim.Runner` czlon z rownosciem.
            // Zmierzone przez sklejenie kontynuacji wierszy i klasyfikacje kazdego
            // wystapienia po wolanym programie: `--limit-kmh=` wystepuje **70** razy,
            // z tego **11** w komendach SCENY Godota, **58** w prozie i w testach
            // rozbioru argumentow sceny, a **1** w komendzie `Sim.Runner` — i jest nia
            // pole „Weryfikacja" TEJ pozycji w `docs/TASKS.md`. Scena
            // (`$GODOT_BIN --path src/Game -- --line --limit-kmh=70`) postaci
            // z rownosciem WYMAGA, bo taki jest jej `RunPlan`.
            // Szczegoly: `reports/postac-z-rownosciem.md`.
            // Dwie polowy projektu maja wiec dwie konwencje i to jest wlasnie powod,
            // dla ktorego komunikat ma nazywac postac: czytajacy przychodzi tu
            // z drugiej polowy i pisze to, co tam dziala.
            var equals = token.IndexOf('=', StringComparison.Ordinal);
            if (equals > 0)
            {
                var prefix = token[..equals];
                if (Array.IndexOf(known.Values, prefix) >= 0)
                {
                    throw new ArgumentException(
                        $"polecenie {command} nie przyjmuje postaci --opcja=wartość. "
                        + $"Opcję {prefix} zna — podaj ją jako dwa człony: "
                        + $"{prefix} {token[(equals + 1)..]}");
                }

                // Flaga to inna rada, i to wyszlo z WLASNEGO sondowania tej pozycji:
                // pierwsza wersja komunikatu mowila flagom „podaj jako dwa czlony:
                // --atp 1", co jest nieprawda — flaga wartosci nie bierze, a `1`
                // zostaloby czlonem pozycyjnym, ktorego odmowa nie widzi. Komunikat
                // radzacy rzecz niedzialajaca jest dokladnie ta usterka, ktora ta
                // pozycja zamyka, tylko przesunieta o jedno miejsce.
                if (Array.IndexOf(known.Flags, prefix) >= 0)
                {
                    throw new ArgumentException(
                        $"polecenie {command} nie przyjmuje postaci --opcja=wartość, "
                        + $"a {prefix} jest flagą i wartości nie bierze — podaj samo {prefix}");
                }

                // Przedrostek TEZ nieznany: komunikat o nieznanej opcji zostaje, ale
                // nazywa `--zmyslona`, a nie `--zmyslona=7` — bo opcja, ktorej nie ma
                // w tabeli, nazywa sie `--zmyslona`. To nie jest osobna funkcja,
                // tylko druga polowa tego samego rozbioru.
                throw new ArgumentException(Nieznana(command, prefix, known));
            }

            throw new ArgumentException(Nieznana(command, token, known));
        }
    }

    /// <summary>
    /// Tresc odmowy nieznanej opcji — JEDEN pisarz, bo od 6.A22 wola ja dwoch
    /// (czlon bez rownosci i przedrostek czlonu z rownoscia), a dwoch pisarzy
    /// rozjezdza sie przy pierwszej poprawce; ta sama zasada co przy 6.A20 i 6.A14.
    /// </summary>
    private static string Nieznana(string command, string option, (string[] Values, string[] Flags, int Positional) known)
    {
        var all = new List<string>(known.Values);
        all.AddRange(known.Flags);
        all.Sort(StringComparer.Ordinal);
        return $"polecenie {command} nie zna opcji {option}. Zna: "
            + (all.Count == 0 ? "żadnej" : string.Join(", ", all));
    }

    private static int Unknown(string command)
    {
        Console.Error.WriteLine($"nieznane polecenie: {command}");
        Usage();
        return 2;
    }

    private static void Usage()
    {
        Console.Error.WriteLine("""
            MetroBxl.Sim.Runner — konsolowy gospodarz rdzenia symulacji

              drive   [--out PLIK] [--sample-every N]     telemetria przejazdu z rdzenia
              replay  --keys PLIK --signalling PLIK.json  przejazd ręczny z zapisu wejść, bez silnika
                      [--out CSV] [--axis PLIK] [--notch-rate X]
                      [--exchange-s X] [--stop-window-m X] [--sample-every N]
                      [--atp]                              plan nie tylko daje limit, ale PILNUJE
                      [--limit-kmh X]                      sufit maszynisty; wymaga --atp
              compare PLIK_A PLIK_B [--tolerance METRY]   rozjazd dwóch telemetrii
              axis    --axis PLIK [--manifest PLIK]       kontrola osi wobec manifestu chunków
              parity                                      kontroler vs AccelerationRun z T-310
              braking                                     tablice referencyjne hamowania (T-311)
              line    --axis PLIK --limit-kmh X            przejazd z zatrzymaniem na każdej stacji
                      --exchange-s X [--load AW0|AW2]
                      [--brake-usage X] [--stop-window-m X] [--timetable PLIK]
                      [--trace PLIK.csv] [--calls PLIK.csv]
                      [--coast-from-m X]                    wybieg od X metra KAŻDEGO odcinka
                      [--signalling PLIK.json]              przejazd pod blokadami i z ATP
              service-day --timetable PLIK.json            doba służby odtworzona z obiegów
                      [--out PLIK.csv] [--at HH:MM:SS]
              budget  --axis PLIK --signalling PLIK.json    koszt kroku rdzenia przy N składach
                      --limit-kmh X --exchange-s X
                      --headway-s X --trains 1,2,4,8 --steps N
                      [--repeats R] [--warmup W] [--turnback-s X]
                      [--atp] [--load AW0|AW2] [--out PLIK.csv]
                      [--coast-from-m X]                    wybieg od X metra KAŻDEGO odcinka
            """);
    }

    // --- drive --------------------------------------------------------------------

    private static int Drive(string[] args)
    {
        var output = Option(args, "--out");
        var sampleEvery = LongValue(Command(args), "--sample-every",
            Option(args, "--sample-every") ?? DriveTelemetry.DefaultSampleEverySteps.ToString(Inv));

        var model = VehicleModel.M7;
        var scenario = DriveScenario.PackageAFirstRun(model);
        var drive = NewDrive(model, scenario);

        var lines = new List<string> { DriveTelemetry.Header };
        lines.Add(DriveTelemetry.Row(drive));
        while (drive.Step())
        {
            if (DriveTelemetry.IsSample(drive.State.Steps, sampleEvery) || drive.Finished)
            {
                lines.Add(DriveTelemetry.Row(drive));
            }
        }

        if (output is null)
        {
            foreach (var line in lines)
            {
                Console.Out.WriteLine(line);
            }
        }
        else
        {
            File.WriteAllLines(output, lines);
        }

        // 6.A30: KAŻDY wiersz `[XXX]` idzie na stdout — ten też, choć do 07.09.2026 szedł
        // na stderr. Powód jest zmierzony, nie estetyczny. Znaczników `[XXX]` wypisuje ten
        // plik 38: **33 na stdout, 5 na stderr**, a `[ATP]` stał na OBU STRUMIENIACH
        // naraz — stdout w `line`, stderr w `replay --atp` — więc `grep '^\[ATP\]'` po
        // jednym strumieniu widział raz jeden wiersz, raz drugi, raz żaden. Kształt
        // wyjścia jest wyrocznią dla czytającego log CI i dla `grep` (6.A16, 6.A27),
        // a `2>/dev/null` — odruch przy skryptach — usuwał tu część WYNIKU, nie tylko
        // diagnostyki.
        //
        // Dlaczego PRZENIESIONE, a nie usunięte: pomiar pola „Wyjście" pozycji dał
        // **0 duplikatów i 5 unikalnych** — ani jeden z tych pięciu wierszy nie miał
        // swojego bajt w bajt odpowiednika na stdout (33 wiersze stdout z `drive`,
        // `replay`, `replay --atp` i `line` razem), więc żadnego nie wolno było skasować.
        //
        // Na stderr zostają WYŁĄCZNIE odmowy — `BŁĄD: `, `nieznane polecenie:` i wiersz
        // pomocy. Tam należą i to rozstrzygnęły 6.A16 oraz 6.A27; ta pozycja ich nie
        // rusza. Obu kierunków pilnuje `tools/tests/test_runner_output_streams.py`.
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[RDZEŃ] {scenario.Id}: kroków={drive.State.Steps} t={drive.State.TimeSeconds(drive.TimeStep):F3} s " +
            $"chainage={drive.ChainageM:F3} m droga={drive.State.DistanceM:F3} m koniec={drive.FinishReason}"));

        return 0;
    }

    /// <summary>
    /// Warunki przejazdu. Pochylenie 0 nie jest wyborem: profil pionowy pakietu A ma
    /// status <c>not_modelled</c> i <c>docs/21-measured-vs-assumed.md</c> §3 zabrania
    /// wyprowadzania z niego rzędnych. Otoczenie <c>Tunnel</c> jest z geometrii pakietu A.
    /// </summary>
    internal static ScenarioDrive NewDrive(VehicleModel model, DriveScenario scenario) =>
        new(
            model,
            scenario,
            new RunConditions(model.MassKg(TrainLoad.Aw2), 0.0, model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
            FixedStep.Simulation);

    // --- replay -------------------------------------------------------------------

    /// <summary>
    /// Przejazd ręczny odtworzony z zapisu wejść — <b>bez silnika</b>.
    ///
    /// <para><b>Po co to jest.</b> Scena umie odtworzyć zapis wejść (<c>--replay</c>),
    /// ale porównanie jej wyniku z nią samą nie mówi nic. Ta metoda liczy TEN SAM
    /// przejazd tą samą drogą przez rdzeń — <see cref="DriverNotch"/>,
    /// <see cref="StationService"/>, <see cref="TrainController"/> — i dopiero różnica
    /// między nią a sceną jest odpowiedzią na pytanie „czy warstwa silnika czegoś nie
    /// dokłada". Ta sama rola, co <c>drive</c> wobec przebiegu skryptowego.</para>
    ///
    /// <para><b>Kolejność w kroku jest ta sama, co w <c>FirstRun.StepOnce</c>, i to jest
    /// warunek sensu porównania przy progu 0.</b> Klawisze bierze się po numerze kroku
    /// PRZED przesunięciem stanu, kilometraż do filtra stacji liczy się ze stanu SPRZED
    /// kroku, a telemetria pokazuje polecenie PO filtrze stacji. Zamiana którejkolwiek
    /// z tych trzech rzeczy miejscami daje przejazd, który wygląda tak samo, a nie jest
    /// ten sam.</para>
    ///
    /// <para><b>Liczby bez źródła są argumentami, nie stałymi.</b> Tempo nastawnika,
    /// czas wymiany pasażerów i okno zatrzymania mieszkają po stronie silnika
    /// w <c>Game.DesignAssumptions</c>, a <c>src/Sim</c> nie ma prawa tego pliku
    /// zobaczyć (<c>CLAUDE.md</c> §4.9). Kopia stałej tutaj byłaby drugą prawdą, która
    /// rozjeżdża się po cichu, więc wartości podaje WOŁAJĄCY — tak samo, jak krok
    /// <c>line</c> w CI podaje <c>--limit-kmh</c>, <c>--exchange-s</c>
    /// i <c>--stop-window-m</c>. Domyślne wartości są tu wyłącznie po to, żeby
    /// polecenie dało się uruchomić ręcznie.</para>
    ///
    /// <para><b>Prędkość dopuszczalna jest wyjątkiem od zdania wyżej: nie ma
    /// domyślnej.</b> Do 05.09.2026 brała się z <c>DriveScenario.SpeedLimitMps</c>,
    /// czyli z rejestru pojazdu — 80 km/h to prędkość KONSTRUKCYJNA M7, nie
    /// ograniczenie na torze. Scena od #246 czyta ją z planu sygnalizacji
    /// (<c>data/design/signalling/classic-2026.json</c>, 72,00 km/h), a to polecenie
    /// zostało wtedy pominięte — i bramka CI tego nie zobaczyła, bo jej wzorzec wejść
    /// dochodzi najwyżej do 65,22 km/h, więc obie strony liczyły to samo mimo różnicy
    /// ośmiu km/h w limicie. Zmierzone na wzorcu, który limit PRZEKRACZA: 870,554 m
    /// przy 80 km/h wobec 869,969 m przy 72 km/h.</para>
    ///
    /// <para>Dlatego <c>--signalling</c> jest OBOWIĄZKOWE, a plan musi opisywać tę samą
    /// oś. Brak argumentu albo plan cudzej osi to odmowa — dokładnie tak, jak w scenie
    /// (<c>FirstRun.BuildSimulation</c>). Cichy odwrót na 80 km/h wygląda tak samo, jak
    /// przejazd poprawny, i to jest jedyny powód, dla którego ta ścieżka nie ma
    /// wartości domyślnej.</para>
    ///
    /// <para><b><c>--atp</c>: plan nie tylko DAJE limit, ale go PILNUJE.</b> Bez tej
    /// flagi przejazd jest dokładnie taki, jak przed 05.09.2026 — plan jest czytany,
    /// skład nie jest zarejestrowany w sygnalizacji, nie dostaje autorytetu jazdy i nikt
    /// nie ingeruje w polecenie. Z flagą wchodzi <see cref="CabProtection"/>: bloki,
    /// nastawnia, autorytet i ochrona, która hamuje za maszynistę. Flaga jest opcją, bo
    /// jej brak jest dziś stanem WSZYSTKICH bramek trybu ręcznego w CI i te bramki mają
    /// zostać co do bitu tym, czym są; nie jest to wyłącznik ochrony w rozgrywce —
    /// w scenie ATP włącza się razem z argumentem <c>--signalling</c> i nie da się go
    /// z kabiny zdjąć (Issue #26: „nie można ominąć ATP przez input gracza").</para>
    ///
    /// <para><b><c>--limit-kmh</c> jest SUFITEM MASZYNISTY, a nie prędkością
    /// dopuszczalną.</b> To dwie różne liczby i dopiero ich rozdzielenie czyni ochronę
    /// obserwowalną: sufit ogranicza to, o co maszynista MOŻE poprosić
    /// (<c>TrainController</c>), a prędkość dopuszczalna z planu jest tym, czego ochrona
    /// PILNUJE. Póki sufit jest równy limitowi planu, ochrona nie ma czego łapać —
    /// sterownik i tak nie przekroczy 72,00 km/h. Dlatego <c>--limit-kmh</c> bez
    /// <c>--atp</c> jest ODMOWĄ: byłby wtedy przejazdem ręcznym z wymyślonym sufitem
    /// i bez żadnego nadzoru, czyli dokładnie tą usterką, którą naprawiło #246.</para>
    /// </summary>
    private static int Replay(string[] args)
    {
        var keysPath = Option(args, "--keys")
            ?? throw new ArgumentException("replay wymaga --keys PLIK z zapisem wejść");
        var signallingPath = Option(args, "--signalling")
            ?? throw new ArgumentException(
                "replay wymaga --signalling PLIK.json: prędkość dopuszczalną tryb ręczny "
                + "bierze z planu sygnalizacji, a scenariusz podaje 80 km/h — prędkość "
                + "konstrukcyjną M7, nie ograniczenie na torze");
        var axisPath = Option(args, "--axis") ?? "data/track/L1_A.json";
        var output = Option(args, "--out");
        var sampleEvery = LongValue(Command(args), "--sample-every",
            Option(args, "--sample-every") ?? DriveTelemetry.DefaultSampleEverySteps.ToString(Inv));
        var notchRate = OptionalNumber(args, "--notch-rate") ?? 0.80;
        var exchangeSeconds = OptionalNumber(args, "--exchange-s") ?? 8.0;
        var stopWindowM = OptionalNumber(args, "--stop-window-m") ?? 5.0;
        var atp = Array.IndexOf(args, "--atp") >= 0;
        var limitKmh = OptionalNumber(args, "--limit-kmh");
        if (limitKmh is not null && !atp)
        {
            throw new ArgumentException(
                "replay --limit-kmh wymaga --atp: sufit maszynisty ponad limit planu bez "
                + "ochrony pociągu jest przejazdem ręcznym z wymyśloną prędkością i bez "
                + "nadzoru — dokładnie tym, co naprawiło #246");
        }

        if (limitKmh is double ceiling && (!double.IsFinite(ceiling) || ceiling <= 0.0))
        {
            throw new ArgumentException(
                // Dwa czlony, nie rownosc (6.A22): od tej pozycji runner postac
                // `--opcja=wartosc` ODRZUCA, wiec komunikat pisany w tej postaci
                // radzilby komende, ktora sam odmowi wykonac. Znalezione wlasnym
                // sondowaniem tej pozycji, nie wpisem.
                $"replay --limit-kmh {ceiling.ToString(Inv)} nie jest dodatnią prędkością");
        }

        var log = InputLog.Parse(File.ReadAllText(keysPath));
        var axis = TrackAxis.FromJson(File.ReadAllText(axisPath));
        var manualPlan = SignallingPlan.FromFile(signallingPath);
        if (!string.Equals(manualPlan.AxisId, axis.Id, StringComparison.Ordinal))
        {
            throw new ArgumentException(string.Create(
                Inv,
                $"plan {signallingPath} opisuje oś {manualPlan.AxisId}, a przejazd idzie " +
                $"po {axis.Id}: prędkość dopuszczalna z cudzej osi nie jest prędkością " +
                $"dopuszczalną tej"));
        }

        var model = VehicleModel.M7;
        var scenario = DriveScenario.PackageAFirstRun(model);
        var step = FixedStep.Simulation;

        // Te same warunki, co w `Drive` i w `FirstRun.BuildSimulation`: pochylenie 0,
        // bo profil pionowy pakietu A ma status `not_modelled`.
        var conditions = new RunConditions(
            model.MassKg(TrainLoad.Aw2), 0.0, model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel);

        var controller = new TrainController(model);
        var notch = new DriverNotch(notchRate);

        // Obsługa stacji istnieje wyłącznie wtedy, gdy oś ma co obsługiwać — ten sam
        // warunek, co w scenie (`_axis.Stations.Count >= 2`). Pierwszą stację
        // `StationService` pomija jako punkt startowy.
        var stations = axis.Stations.Count >= 2
            ? new StationService(axis.Stations, new DoorCycle(exchangeSeconds), step, stopWindowM)
            : null;

        // Ochrona pociągu dla kabiny: bloki, nastawnia, autorytet i ingerencja. `null`
        // znaczy „plan jest czytany, nie prowadzi" i wtedy przejazd jest bit w bit taki,
        // jak przed dodaniem tej gałęzi — ani jedno wołanie `Supervise` się nie odbywa.
        var cab = atp
            ? CabProtection.M7(manualPlan, SignalledTrainId, scenario.StartChainageM)
            : null;

        var state = DriveState.AtRest;
        var command = DriverCommand.Coast;
        var acceleration = 0.0;

        // SUFIT MASZYNISTY i PRĘDKOŚĆ DOPUSZCZALNA to dwie różne liczby, i dopiero ich
        // rozdzielenie czyni ochronę obserwowalną. Bez `--limit-kmh` są tą samą liczbą
        // z planu i wtedy ochronie nie ma czego łapać — sterownik nie przekroczy limitu,
        // którego mu nie wolno przekroczyć.
        var speedLimitMps = limitKmh is double kmh
            ? Units.KmhToMps(kmh)
            : manualPlan.PermittedSpeedMps;

        double Chainage() => scenario.StartChainageM + state.DistanceM;

        // Ten sam wiersz, co `[LIMIT]` sceny, i to nie jest ozdoba: bramka CI porównuje
        // telemetrię CO DO BITU, a telemetria nie ma kolumny z limitem. Gdyby obie
        // strony wzięły inną liczbę, a przejazd jej nie dotknął, porównanie i tak
        // wyszłoby zielone — dokładnie to działo się między #246 a tą zmianą.
        //
        // Początek wiersza — do ścieżki planu włącznie — jest STAŁY, bo tyle wycina
        // `grep -o` w bramce „Manual mode — both sides must hold the same speed ceiling".
        // Zmienia się dopiero ogon, i ma się zmieniać: przejazd pod ochroną a przejazd
        // czytający tę samą liczbę to dwie różne rzeczy i log ma je odróżniać.
        var limitTail = cab is null
            ? "plan jest czytany, nie prowadzi — bez blokad i bez ochrony pociągu"
            : string.Create(
                Inv,
                $"plan PILNUJE — bloki, autorytet jazdy i ATP; sufit maszynisty " +
                $"{Units.MpsToKmh(speedLimitMps):F2} km/h");
        // 6.A30: stdout, jak cała rodzina `[XXX]` — powód i pomiar stoją przy `[RDZEŃ]`
        // w `Drive`. Bramka CI wycina ten wiersz z logu złożonego przez `2>&1 | tee`,
        // więc przeniesienie nie zmienia jej wejścia; zmierzone przed zmianą: żaden krok
        // `.github/workflows/` nie czyta tych wierszy z SAMEGO stderr.
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[LIMIT] tryb ręczny: {Units.MpsToKmh(manualPlan.PermittedSpeedMps):F2} km/h " +
            $"z planu {manualPlan.PlanId} ({signallingPath}); {limitTail}"));

        var lines = new List<string> { DriveTelemetry.Header };

        // Wiersz zerowy: stan PRZED pierwszym krokiem, dokładnie jak w `_Ready` sceny.
        lines.Add(DriveTelemetry.Row(
            state, step, Chainage(), acceleration, command, DriveTelemetry.ManualPhase));

        // DWA LICZNIKI, i to jest treść, nie porządek. `sessionStep` indeksuje ZAPIS
        // i nie wraca nigdy; `state.Steps` indeksuje PRZEJAZD i po resecie zaczyna od
        // zera. Do 05.09.2026 była tu jedna liczba, bo reset nie mógł wystąpić w zapisie;
        // od wariantu W1 może, a pętla po `state.Steps` liczyłaby po resecie te same
        // kroki drugi raz i nigdy nie doszłaby do końca pliku.
        var sessionStep = 0L;
        var resets = 0;
        var topSpeedMps = 0.0;
        while (sessionStep < log.Steps)
        {
            // Reset obowiązuje PRZED swoim krokiem — ta sama kolejność, co w scenie.
            // `RunRestart` jest jedną odpowiedzią na pytanie „co reset zeruje" dla obu
            // stron porównania; osobna lista tutaj rozjechałaby się po cichu. Ochrona
            // kabiny jest w tej odpowiedzi, a nie obok niej: `FixedBlockSystem.MoveTrain`
            // odmawia cofnięcia czoła, więc pierwszy meldunek ruchu po resecie
            // skończyłby się wyjątkiem, a bramka porównująca scenę z rdzeniem przy
            // progu 0 wymaga, żeby obie strony zerowały DOKŁADNIE to samo.
            if (log.IsResetAt(sessionStep))
            {
                var restarted = RunRestart.Apply(notch, stations, cab, lines);
                state = restarted.Drive;
                command = restarted.Command;
                acceleration = restarted.AccelerationMps2;
                resets++;

                // Wiersz zerowy nowego przejazdu — tak samo jak przy starcie, bo po
                // resecie przejazd jest przed pierwszym krokiem.
                lines.Add(DriveTelemetry.Row(
                    state, step, Chainage(), acceleration, command, DriveTelemetry.ManualPhase));
            }

            var keys = log.KeysAt(sessionStep);

            // Nastawnia i nadzór PRZED krokiem, ze stanu sprzed kroku — fazy 1b i 2
            // `LineCore.Step`. Decyzja powstaje tu, a stosuje się ją niżej, za filtrem
            // stacji: ochrona ma być OSTATNIM filtrem polecenia.
            //
            // Zegarem nastawni jest numer kroku PRZEJAZDU, a nie sesji, i to jest ta
            // sama liczba, którą podaje scena. Po resecie ochrona powstaje od nowa
            // (`CabProtection.Reset`), więc jej odstęp żądań tras ma liczyć się od zera
            // razem z nią; `sessionStep` dałby tu zegar, który przeżył przejazd.
            cab?.Supervise(state.Steps, Chainage(), state.SpeedMps);

            var requested = notch.Advance(keys, step);

            // `Filter` posuwa licznik cyklu drzwi, więc DOKŁADNIE RAZ na krok.
            var effective = stations?.Filter(state, requested, Chainage()) ?? requested;

            // ATP na samym końcu łańcucha poleceń — Issue #26: „nie można ominąć ATP
            // przez input gracza". Bez ochrony `Apply` nie istnieje i polecenie idzie
            // do kontrolera dokładnie takie, jak przedtem.
            effective = cab is null ? effective : cab.Apply(effective);

            state = controller.Advance(state, conditions, effective, speedLimitMps, step, out var forces);
            acceleration = forces.AccelerationMps2;
            command = effective;
            sessionStep++;
            if (state.SpeedMps > topSpeedMps)
            {
                topSpeedMps = state.SpeedMps;
            }

            // Meldunek ruchu PO kroku — faza 3 `LineCore.Step`. Przed krokiem opisywałby
            // położenie, z którego skład właśnie odjechał.
            cab?.Move(Chainage());

            // Próbkowanie idzie po numerze kroku PRZEJAZDU — po resecie od zera, tak samo
            // jak wiersz zerowy. Koniec pliku jest natomiast pytaniem o SESJĘ.
            if (DriveTelemetry.IsSample(state.Steps, sampleEvery) || sessionStep >= log.Steps)
            {
                lines.Add(DriveTelemetry.Row(
                    state, step, Chainage(), acceleration, command, DriveTelemetry.ManualPhase));
            }
        }

        if (output is null)
        {
            foreach (var line in lines)
            {
                Console.Out.WriteLine(line);
            }
        }
        else
        {
            File.WriteAllLines(output, lines);
        }

        var served = stations?.Calls.Count ?? 0;
        var missed = stations?.Missed.Count ?? 0;
        // 6.A30: stdout — powód i pomiar przy `[RDZEŃ]` w `Drive`. Ten znacznik był
        // najgorszym przypadkiem rozjazdu: scena wypisuje `[ODTWORZENIE] koniec: …` na
        // stdout (`GD.Print`), rdzeń wypisywał swoje dwa wiersze na stderr, więc
        // czytający, który potokował stdout, dostawał część rodziny i nie dostawał reszty.
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[ODTWORZENIE] {keysPath}: kroków={state.Steps} t={state.TimeSeconds(step):F3} s " +
            $"chainage={Chainage():F3} m droga={state.DistanceM:F3} m " +
            $"sesja={sessionStep} kroków resetów={resets} " +
            $"szczyt={Units.MpsToKmh(topSpeedMps):F3} km/h " +
            $"zmian klawiszy={log.Entries.Count} stacji obsłużonych={served} przejechanych={missed}"));

        // Podsumowanie ochrony jest LICZBAMI, a nie zdaniem „ATP działało". Zero ingerencji
        // przy przejeździe pod limitem planu jest wynikiem, nie brakiem wyniku — dlatego
        // wiersz wychodzi zawsze, gdy ochrona była wpięta.
        if (cab is not null)
        {
            // 6.A30: stdout. To JEDYNY znacznik, który przed tą zmianą stał naprawdę na
            // obu strumieniach jednego programu — `line` wypisuje `[ATP]` na stdout,
            // `replay --atp` wypisywał swój tutaj na stderr. Dwa różne wiersze, ten sam
            // wzorzec `grep`; pomiar wykluczył duplikat (treści i pola są inne), więc
            // wiersz został przeniesiony, a nie usunięty.
            Console.Out.WriteLine(string.Create(
                Inv,
                $"[ATP] ostrzeżeń={cab.Warnings} ingerencji służbowych={cab.ServiceInterventions} " +
                $"awaryjnych={cab.EmergencyInterventions} " +
                $"max żądanie={cab.MaxBrakeDemandMps2:F3} m/s² " +
                $"(hamulec służbowy {cab.Protection.ServiceBrakeMps2:F3} m/s²) " +
                $"tras zaryglowanych={cab.Dispatcher.Locked} odmów={cab.Dispatcher.Refused}"));
        }
        foreach (var call in stations?.Calls ?? (IReadOnlyList<StationCall>)Array.Empty<StationCall>())
        {
            // 6.A30: stdout — piąty i ostatni z wierszy przeniesionych tą pozycją.
            Console.Out.WriteLine(string.Create(
                Inv,
                $"[ODTWORZENIE] stacja {call.Name}: postój od {call.ArrivalSeconds:F3} s " +
                $"do {call.DepartureSeconds:F3} s, błąd zatrzymania {call.StopErrorM:F3} m"));
        }

        return 0;
    }

    // --- compare ------------------------------------------------------------------

    private static int Compare(string[] args)
    {
        if (args.Length < 3)
        {
            // 6.A16, decyzja wlasciciela z 06.09.2026: kazda odmowa argumentowa konczy
            // sie kodem 1, a 2 zostaje wylacznie dla „nie wiem, co uruchomic" — czyli
            // dla nieznanego polecenia i dla wywolania bez ani jednego argumentu.
            //
            // To jest jedyne miejsce, ktore sie zmienilo. `compare` sprawdzalo liczbe
            // argumentow RECZNIE i wracalo kodem 2, zamiast rzucic wyjatek lapany
            // wspolnym handlerem jak wszystkie pozostale odmowy. Cztery pozycje
            // (6.A10, 6.A11, 6.A13, 6.D20) nazwaly te niespojnosc i zostawily wybor
            // wlascicielowi, przybijajac stan testem; test zmienil sie razem z kodem.
            //
            // Wyjatek, a nie `return 1`: dzieki temu komunikat dostaje ten sam
            // przedrostek `BLAD: `, co reszta odmow, wiec ujednolica sie nie tylko
            // liczba, ale i ksztalt wyjscia.
            throw new ArgumentException("compare wymaga dwóch plików");
        }

        var tolerance = NumberValue(Command(args), "--tolerance", Option(args, "--tolerance") ?? "1E-9");
        var left = File.ReadAllLines(args[1]);
        var right = File.ReadAllLines(args[2]);

        if (left.Length != right.Length)
        {
            // 6.A27: wyjatek, nie `Console.Error` + `return 1`. Kod wyjscia byl juz
            // dobry — ujednolicila go 6.A16 — ale KSZTALT wyjscia nie: przedrostka
            // `BLAD: ` dodaje wspolny handler w `Main`, a te odmowy go omijaly.
            // Ksztalt jest wyrocznia dla czytajacego log CI i dla `grep`; wyjatek od
            // wzorca psuje go tak samo, jak komunikat mowiacy nieprawde psul odmowe
            // przy 6.A22. Tresc bez zmian, to pole „Poza zakresem" tej pozycji.
            throw new ArgumentException(
                $"różna liczba wierszy: {left.Length} vs {right.Length}");
        }

        if (!string.Equals(left[0], right[0], StringComparison.Ordinal) ||
            !string.Equals(left[0], DriveTelemetry.Header, StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "nagłówki telemetrii nie zgadzają się z formatem rdzenia");
        }

        var worst = new double[DriveTelemetry.ColumnCount - 1];
        var worstRow = new int[DriveTelemetry.ColumnCount - 1];
        var identicalBytes = true;

        // Nazwy kolumn potrzebne SA JUZ TUTAJ, nie tylko w podsumowaniu (6.A24):
        // odmowa na nieliczbowej komorce ma powiedziec, KTORA to kolumna, a nie sam
        // jej numer. To ten sam odczyt naglowka, ktory stal nizej — jedno miejsce,
        // przesuniete w gore, bez drugiego pisarza.
        var columnNames = DriveTelemetry.Header.Split(',');

        for (var i = 1; i < left.Length; i++)
        {
            if (!string.Equals(left[i], right[i], StringComparison.Ordinal))
            {
                identicalBytes = false;
            }

            var a = left[i].Split(',');
            var b = right[i].Split(',');
            if (a.Length != DriveTelemetry.ColumnCount || b.Length != DriveTelemetry.ColumnCount)
            {
                // Trzecia i czwarta odmowa tej petli. Pole „Poza zakresem" 6.A27
                // wylaczalo je WARUNKOWO — „jezeli pomiar pokaze, ze ona juz
                // przedrostek ma". Pomiar pokazal, ze NIE ma: `Console.Error` +
                // `return 1`, tak samo jak dwie wyzej. Warunek nie zaszedl, wiec
                // pozycja obejmuje cztery odmowy, nie dwie.
                throw new ArgumentException($"wiersz {i}: zła liczba kolumn");
            }

            if (!string.Equals(a[^1], b[^1], StringComparison.Ordinal))
            {
                throw new ArgumentException(
                    $"wiersz {i}: różna faza scenariusza ({a[^1]} vs {b[^1]})");
            }

            for (var c = 0; c < DriveTelemetry.ColumnCount - 1; c++)
            {
                var delta = Math.Abs(
                    Cell(args[1], i, c, columnNames, a[c]) - Cell(args[2], i, c, columnNames, b[c]));
                if (delta > worst[c])
                {
                    worst[c] = delta;
                    worstRow[c] = i;
                }
            }
        }

        var names = columnNames;
        var failed = false;
        Console.Out.WriteLine($"[PORÓWNANIE] wierszy={left.Length - 1} identyczne co do bajtu={(identicalBytes ? "TAK" : "NIE")}");
        for (var c = 0; c < worst.Length; c++)
        {
            var over = worst[c] > tolerance;
            failed |= over;
            Console.Out.WriteLine(string.Create(
                Inv, $"[PORÓWNANIE] {names[c],-12} max |Δ| = {worst[c]:E3} (wiersz {worstRow[c]}) {(over ? "PONAD PRÓG" : "ok")}"));
        }

        Console.Out.WriteLine(string.Create(Inv, $"[PORÓWNANIE] próg = {tolerance:E3}"));
        return failed ? 1 : 0;
    }

    // --- axis ---------------------------------------------------------------------

    private static int Axis(string[] args)
    {
        var axisPath = Option(args, "--axis") ?? throw new ArgumentException("axis wymaga --axis");
        var axis = TrackAxis.FromJson(File.ReadAllText(axisPath));

        Console.Out.WriteLine(string.Create(
            Inv,
            $"[OŚ] {axis.Id}: punktów źródłowych={axis.SourcePoints.Count} zagęszczonych={axis.Points.Count} " +
            $"długość_źródłowa={axis.DeclaredLengthM:F3} m długość_zagęszczona={axis.LengthM:F3} m"));
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[OŚ] odchyłka od łamanej STIB = {axis.MaxDeviationFromSourceM():F4} m, stacji={axis.Stations.Count}, " +
            $"profil_pionowy={axis.VerticalStatus}"));

        // Zrzut punktów istnieje po to, żeby dało się porównać oś z C# z osią z Pythona
        // punkt po punkcie, a nie tylko po długości. Format R — bez zaokrągleń.
        var dump = Option(args, "--dump-points");
        if (dump is not null)
        {
            var rows = new List<string>(axis.Points.Count);
            foreach (var point in axis.Points)
            {
                rows.Add(string.Create(Inv, $"{point.X:R},{point.Y:R},{point.Z:R}"));
            }

            File.WriteAllLines(dump, rows);
            Console.Out.WriteLine($"[OŚ] zrzut {rows.Count} punktów -> {dump}");
        }

        var manifestPath = Option(args, "--manifest");
        if (manifestPath is null)
        {
            return 0;
        }

        using var manifest = System.Text.Json.JsonDocument.Parse(File.ReadAllText(manifestPath));
        var manifestLength = manifest.RootElement.GetProperty("axis_length_m").GetDouble();
        var delta = Math.Abs(manifestLength - axis.LengthM);

        // Manifest zapisuje długość zaokrągloną do 1 mm (sort_keys + round w generatorze),
        // więc zgodność poniżej 1 mm jest maksimum, jakie ten plik potrafi potwierdzić.
        const double toleranceM = 1e-3;
        var ok = delta <= toleranceM;
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[OŚ] manifest chunków: {manifestLength:F3} m, C#: {axis.LengthM:F3} m, |Δ| = {delta:E3} m -> {(ok ? "ZGODNE" : "ROZJAZD")}"));

        return ok ? 0 : 1;
    }

    // --- line ---------------------------------------------------------------------

    /// <summary>
    /// Przejazd całej osi z zatrzymaniem na każdej stacji, z opcjonalnym zestawieniem
    /// z rozkładem STIB zmierzonym w T-113.
    ///
    /// <para>Cztery liczby wejściowe są <b>obowiązkowe i bez wartości domyślnych</b>,
    /// bo żadna z nich nie ma źródła. Wartość domyślna w tym miejscu wyszłaby potem
    /// w raporcie jako fakt o metrze w Brukseli — patrz <see cref="LineRunSettings"/>.</para>
    /// </summary>
    private static int LineCommand(string[] args)
    {
        var axisPath = Option(args, "--axis") ?? throw new ArgumentException("line wymaga --axis");
        var limitKmh = RequiredNumber(args, "--limit-kmh");
        var exchange = RequiredNumber(args, "--exchange-s");
        var brakeUsage = OptionalNumber(args, "--brake-usage") ?? 1.0;
        var stopWindow = OptionalNumber(args, "--stop-window-m") ?? 5.0;
        var load = Option(args, "--load") ?? "AW0";

        // WYBIEG (6.A6). Brak opcji to `null`, a nie liczba — przejazd jest wtedy bit
        // w bit ten sam, co przed dopisaniem tej opcji. `?? 0.0` byłoby tu usterką:
        // znaczyłoby „wybieg od zerowego metra", czyli przejazd BEZ ani jednego metra
        // trakcji, i to przy opcji, której nikt nie podał.
        var coastFromM = OptionalNumber(args, "--coast-from-m");

        var axis = TrackAxis.FromJson(File.ReadAllText(axisPath));
        var model = VehicleModel.M7;
        var trainLoad = load switch
        {
            "AW0" => TrainLoad.Aw0,
            "AW2" => TrainLoad.Aw2,
            _ => throw new ArgumentException($"nieznane obciążenie: {load}; dozwolone AW0 albo AW2"),
        };

        var conditions = RunConditions.Level(model, trainLoad);
        var massKg = conditions.MassKg;
        var settings = new LineRunSettings(
            Units.KmhToMps(limitKmh), exchange, brakeUsage, stopWindow, coastFromM);
        var tracePath = Option(args, "--trace");
        var traceRows = tracePath is null ? null : new List<string> { "t_s,chainage_m,speed_mps,brake_mps2,throttle,brake,door" };
        Action<LineRun.TracePoint>? trace = traceRows is null ? null : point => traceRows.Add(string.Create(
            Inv,
            $"{point.TimeSeconds:R},{point.ChainageM:R},{point.SpeedMps:R},{point.BrakeRateMps2:R}," +
            $"{point.Command.Throttle:R},{point.Command.Brake:R},{point.Phase}"));

        // `--signalling` zamienia `LineRun` na `LineCore` z OCHRONĄ POCIĄGU — i to jest
        // cały powód, dla którego ta opcja istnieje. Bramka CI porównuje przejazd sceny
        // z przejazdem rdzenia co do bitu; bez tej opcji nie dałoby się porównać
        // przejazdu, w którym ATP naprawdę ingeruje, bo rdzeń nie miałby jak go wykonać.
        // Zgodność zmierzona przy limicie pod planem nie mówi nic o przejeździe nad
        // planem: pod limitem ochrona milczy, więc porównywałaby się z samą sobą.
        var signallingPath = Option(args, "--signalling");
        LineRunResult result;
        LineCore? core = null;
        if (signallingPath is null)
        {
            result = new LineRun(model).Run(
                axis, conditions, settings, LineRun.DefaultStepBudget, trace);
        }
        else
        {
            var plan = SignallingPlan.FromJson(File.ReadAllText(signallingPath));
            core = LineCore.M7(plan, axis, conditions, settings, turnbackSeconds: 0.0, atp: true);
            core.Add(SignalledTrainId, 0L);
            while (!core.Finished && core.Steps < LineRun.DefaultStepBudget)
            {
                core.Step(trace is null ? null : (_, point) => trace(point));
            }

            result = core.ResultOf(SignalledTrainId, core.Finished ? "arrived" : "step-budget");
        }
        if (tracePath is not null && traceRows is not null)
        {
            File.WriteAllLines(tracePath, traceRows);
            Console.Out.WriteLine($"[LINIA] ślad {traceRows.Count - 1} kroków -> {tracePath}");
        }

        // Zatrzymania w postaci maszynowej. Istnieje po to, żeby przejazd SCENY dał się
        // porównać z przejazdem RDZENIA po liczbach, a nie po tym, że oba się nie
        // wywróciły. `--trace` odpowiada na inne pytanie: co dzieje się w każdym kroku.
        var callsPath = Option(args, "--calls");
        if (callsPath is not null)
        {
            var rows = new List<string>
            {
                "name,stop_id,chainage_m,stopped_at_m,stop_error_m,arrival_s,departure_s",
            };
            foreach (var call in result.Calls)
            {
                rows.Add(string.Create(
                    Inv,
                    $"{call.Name},{call.StopId},{call.ChainageM:R},{call.StoppedAtChainageM:R}," +
                    $"{call.StopErrorM:R},{call.ArrivalSeconds:R},{call.DepartureSeconds:R}"));
            }

            File.WriteAllLines(callsPath, rows);
            Console.Out.WriteLine($"[LINIA] {result.Calls.Count} zatrzymań -> {callsPath}");
        }


        Console.Out.WriteLine(string.Create(
            Inv,
            $"[LINIA] {result.AxisId}: {result.Calls.Count} zatrzymań, {result.TotalDistanceM:F2} m, " +
            $"{result.TotalSeconds:F2} s, postoje {result.DwellSeconds:F2} s, " +
            $"kroków {result.Steps}, koniec={result.FinishReason}"));
        Console.Out.WriteLine($"[LINIA] {settings}, obciążenie {load} {massKg:F0} kg");
        foreach (var assumption in settings.Assumptions)
        {
            Console.Out.WriteLine($"[ZAŁOŻENIE] {assumption}");
        }

        var worstStopError = 0.0;
        foreach (var call in result.Calls)
        {
            Console.Out.WriteLine("[STACJA] " + call.ToString());
            worstStopError = Math.Max(worstStopError, Math.Abs(call.StopErrorM));
        }

        Console.Out.WriteLine(string.Create(
            Inv, $"[LINIA] największy błąd zatrzymania: {worstStopError:F3} m"));

        // Bilans energii CAŁEGO przejazdu (6.A5) — druga, niezależna droga do wyniku,
        // dokładnie jak T-310 i T-311: rachunek sił i całkowanie muszą dać tę samą
        // liczbę. Dwa warianty odzysku są SKRAJNE (0 % i 100 %), nie jedną wpisaną
        // sprawnością — karta M7 potwierdza sam fakt hamowania odzyskowego i nic ponadto.
        var energy = result.Energy;
        Console.Out.WriteLine(string.Create(Inv, $"[ENERGIA] {energy}"));
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[ENERGIA] netto z sieci przy odzysku 0%: {energy.NetGridWorkKwh(fullRecovery: false):F4} kWh, " +
            $"przy odzysku 100%: {energy.NetGridWorkKwh(fullRecovery: true):F4} kWh"));

        // Rozkład tej samej pracy trakcji NA ODCINKI (6.A6). Jedna liczba na całą oś nie
        // odpowiada na pytanie „ile wybieg kosztuje i ile oszczędza", bo rezerwa
        // rozkładowa z T-113 jest wielkością odcinkową — najciaśniejszy odcinek pakietu A
        // ma jej kilka sekund, a najluźniejszy kilkanaście.
        for (var index = 0; index < result.Calls.Count; index++)
        {
            var call = result.Calls[index];
            var from = index == 0 ? axis.Stations[0].Name : result.Calls[index - 1].Name;
            var work = call.TractionWorkFromPreviousJ is double joules
                ? string.Create(Inv, $"{joules / 3_600_000.0:F4} kWh")
                : "brak pomiaru";
            Console.Out.WriteLine(string.Create(
                Inv,
                $"[ODCINEK] {from} → {call.Name}: {call.DistanceFromPreviousM:F2} m " +
                $"w {call.RunSecondsFromPrevious:F2} s, trakcja {work}"));
        }

        if (core is not null)
        {
            // Liczniki są WYNIKIEM, nie napisem: podnosi je ta sama gałąź, która stosuje
            // decyzję ochrony. Zero ingerencji przy limicie pod planem i niezerowe nad
            // planem to dwie rzeczy, które bramka może porównać z liczbą, a nie z tym,
            // że przejazd się nie wywrócił.
            Console.Out.WriteLine(string.Create(
                Inv,
                $"[SYGNALIZACJA] {core.Signalling.Plan.Blocks.Count} bloków, "
                + $"tras zaryglowanych {core.Dispatcher.Locked}, odmów {core.Dispatcher.Refused}, "
                + $"limit planu {Units.MpsToKmh(core.Signalling.Plan.PermittedSpeedMps):F2} km/h"));
            Console.Out.WriteLine(string.Create(
                Inv,
                $"[ATP] ostrzeżenia {core.ProtectionWarnings}, "
                + $"ingerencje służbowe {core.ServiceInterventions}, "
                + $"awaryjne {core.EmergencyInterventions}, "
                + $"największe żądanie {core.MaxBrakeDemandMps2:F3} m/s² "
                + $"przy hamulcu służbowym {core.Protection!.ServiceBrakeMps2:F3} m/s²"));
        }

        var timetable = Option(args, "--timetable");
        return timetable is null
            ? Finish(result)
            : CompareWithTimetable(result, axis, timetable) is var mismatch && mismatch
                ? 1
                : Finish(result);

        static int Finish(LineRunResult result) => result.FinishReason == "arrived" ? 0 : 1;
    }

    /// <summary>
    /// Zestawienie czasów jazdy z modelu z rozkładowymi z <c>build/timetable.json</c> (T-113).
    ///
    /// <para><b>Co ma wyjść.</b> Rozkład zawiera rezerwę, więc czas modelu ma być
    /// <b>krótszy</b> od rozkładowego na każdym odcinku. Odcinek, na którym model jest
    /// wolniejszy od rozkładu, znaczy, że przy tych założeniach STIB-owskiego rozkładu
    /// nie da się wykonać — i to jest wynik, a nie usterka do przemilczenia.</para>
    /// </summary>
    private static bool CompareWithTimetable(LineRunResult result, TrackAxis axis, string path)
    {
        using var document = System.Text.Json.JsonDocument.Parse(File.ReadAllText(path));
        if (!document.RootElement.TryGetProperty("segments", out var segments))
        {
            throw new ArgumentException($"{path} nie ma pola segments — to nie jest wyjście tools/track/timetable.py");
        }

        var scheduled = new Dictionary<(string From, string To), double>();
        foreach (var segment in segments.EnumerateArray())
        {
            if (!segment.TryGetProperty("package", out var package) || package.GetString() != axis.Id)
            {
                continue;
            }

            // Klucz to para identyfikatorów peronu, nie nazw. Nazwa na osi jest dwujęzyczna
            // i ma diakrytyki, w GTFS jest jedna i wersalikami; dopasowanie po tekście
            // wymagałoby normalizacji Unicode, której ten projekt nie ma — csproj ma
            // InvariantGlobalization, więc Normalize(FormD) jest tu pustą operacją.
            var key = (segment.GetProperty("from_stop").GetString() ?? string.Empty,
                       segment.GetProperty("to_stop").GetString() ?? string.Empty);
            scheduled[key] = segment.GetProperty("median_s").GetDouble();
        }

        var slower = false;
        var matched = 0;
        for (var i = 1; i < result.Calls.Count; i++)
        {
            var from = result.Calls[i - 1];
            var to = result.Calls[i];
            if (from.StopId.Length == 0 || to.StopId.Length == 0
                || !scheduled.TryGetValue((from.StopId, to.StopId), out var reference))
            {
                continue;
            }

            matched++;
            var modelled = to.RunSecondsFromPrevious;
            var reserve = reference - modelled;
            slower |= reserve < 0.0;
            Console.Out.WriteLine(string.Create(
                Inv,
                $"[ROZKŁAD] {from.Name} → {to.Name}: model {modelled:F2} s, rozkład {reference:F0} s, " +
                $"rezerwa {reserve:+0.00;-0.00;0.00} s{(reserve < 0.0 ? "  MODEL WOLNIEJSZY" : string.Empty)}"));
        }

        Console.Out.WriteLine(string.Create(
            Inv, $"[ROZKŁAD] dopasowanych odcinków: {matched} z {result.Calls.Count - 1}"));
        return slower;
    }

    /// <summary>
    /// Liczba spod opcji, ktorej brak jest odmowa nazywajaca <b>wolane</b> polecenie.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Nazwa polecenia bierze sie z <c>args[0]</c>, a nie ze stalej w tresci komunikatu,
    /// i to jest cala tresc pozycji 6.D20. Zmierzone 06.09.2026 przy 6.D15 (#301):
    /// <c>budget</c> bez <c>--limit-kmh</c> konczyl sie komunikatem
    /// <c>BLAD: line wymaga --limit-kmh</c>, czyli kierowal czytajacego do polecenia,
    /// ktorego nie uruchamial. Ten pomocnik jest wspolny dla <c>line</c>, <c>budget</c>
    /// i <c>replay</c>, wiec zaszyta nazwa mylila w dwoch przypadkach na trzy.
    /// </para>
    /// <para>
    /// Wszystkie POZOSTALE komunikaty „X wymaga …" w tym pliku sa literalami stojacymi
    /// w ciele jednego polecenia i nazywaja je poprawnie; sprawdzone po jednym.
    /// Poprawka dotyczy wylacznie tego miejsca, bo tylko tutaj nazwa moze sie rozjechac
    /// z wywolaniem.
    /// </para>
    /// </remarks>
    private static double RequiredNumber(string[] args, string name)
    {
        var command = Command(args);
        var text = Option(args, name) ?? throw new ArgumentException($"{command} wymaga {name}");
        return NumberValue(command, name, text);
    }

    private static double? OptionalNumber(string[] args, string name)
    {
        var text = Option(args, name);
        return text is null ? null : NumberValue(Command(args), name, text);
    }

    /// <summary>
    /// Nazwa polecenia z <c>args[0]</c> — jedno miejsce, bo od 6.D20 wiadomo, ile
    /// kosztuje zaszycie jej w treści komunikatu: <c>RequiredNumber</c> mówiło
    /// <c>line</c> także wtedy, gdy uruchomiono <c>budget</c>.
    /// </summary>
    private static string Command(string[] args) => args.Length > 0 ? args[0] : "polecenie";

    /// <summary>
    /// JEDYNY pisarz komunikatu o nieliczbowej wartości opcji (6.A14). Osobny, bo
    /// trzech rozbierających pomocników poniżej mówiłoby to samo trzy razy, a wtedy
    /// treść rozjeżdża się przy pierwszej poprawce — ta sama zasada, która przy 6.A20
    /// wydzieliła <see cref="Provenance"/>.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Do 6.A14 wartość nieliczbowa kończyła się komunikatem platformy .NET —
    /// <c>BŁĄD: The input string 'abc' was not in a correct format.</c> — który nie
    /// mówił ANI której opcji dotyczy, ANI którego polecenia, a był jedynym śladem,
    /// jaki dostawał czytający. Nazwa polecenia bierze się z <c>args[0]</c>, nie
    /// z nowej zaszytej stałej; nazwę opcji podaje wołający, bo tylko on ją zna.
    /// </para>
    /// </remarks>
    private static string NotANumber(string command, string name, string text) =>
        $"{command} nie rozumie wartości {name}: " + NieJestLiczba(text);

    /// <summary>
    /// Końcówka wspólna dla odmowy wartości OPCJI (<see cref="NotANumber"/>)
    /// i odmowy KOMÓRKI pliku (<see cref="Cell"/>) — jeden pisarz, dwa nagłówki.
    /// </summary>
    /// <remarks>
    /// Wydzielona przy 6.A24, bo bramka `test_one_writer_of_the_message` zapaliła się
    /// na drugim wystąpieniu tego samego zdania i **miała rację**: dwa pisarze tej
    /// samej treści rozjeżdżają się przy pierwszej poprawce. Nagłówek musi być inny —
    /// zła komórka nie jest złą opcją — ale zdanie o tym, że wartość nie jest liczbą,
    /// jest jedno.
    /// </remarks>
    private static string NieJestLiczba(string text) => $"„{text}” nie jest liczbą";

    /// <summary>
    /// Rozbiór wartości zmiennoprzecinkowej z komunikatem nazywającym polecenie,
    /// opcję i wartość. Zbiór dopuszczalnych postaci jest <b>ten sam</b>, co miał
    /// <c>double.Parse(text, Inv)</c> (<see cref="NumberStyles.Float"/> razem
    /// z <see cref="NumberStyles.AllowThousands"/>) — ta pozycja zmienia komunikat,
    /// nie to, co runner przyjmuje.
    /// </summary>
    private static double NumberValue(string command, string name, string text)
    {
        if (!double.TryParse(text, NumberStyles.Float | NumberStyles.AllowThousands, Inv, out var value))
        {
            throw new ArgumentException(NotANumber(command, name, text));
        }

        return value;
    }

    /// <summary>
    /// Rozbiór KOMÓRKI pliku telemetrii z komunikatem nazywającym plik, wiersz
    /// i kolumnę (6.A24).
    /// </summary>
    /// <remarks>
    /// <para>
    /// Osobny pisarz niż <see cref="NotANumber"/> i to jest sedno tej pozycji, a nie
    /// jej niedoróbka: 6.A14 przeszła po jedenastu drogach wartości OPCJI do liczby
    /// i tę jedną zostawiła nietkniętą, wpisując ją jako jedyne usprawiedliwienie
    /// w <c>tools/tests/test_runner_number_parsing.py</c> — bo zła komórka nie jest
    /// złą opcją i komunikat 6.A14 byłby tu nieprawdą. Nietknięta nie znaczyła jednak
    /// dobra: komunikat był tam dokładnie ten, który 6.A14 wyjęła z opcji —
    /// <c>The input string 'x' was not in a correct format.</c> — bez pliku, bez
    /// wiersza i bez kolumny.
    /// </para>
    /// <para>
    /// <c>compare</c> jest <b>wyrocznią parzystości</b> rdzenia i sceny; jego odmowa
    /// jest jedynym śladem, jaki dostaje czytający, gdy jeden z dwóch plików jest
    /// zepsuty. Numer wiersza jest indeksem w tablicy wierszy pliku, w której nagłówek
    /// ma numer <b>0</b> — tak samo jak w dwóch sąsiednich odmowach tej pętli
    /// („zła liczba kolumn", „różna faza scenariusza") — i komunikat mówi to wprost,
    /// zamiast zostawiać do zgadnięcia.
    /// </para>
    /// </remarks>
    private static double Cell(string path, int row, int column, string[] names, string text)
    {
        if (!double.TryParse(text, NumberStyles.Float | NumberStyles.AllowThousands, Inv, out var value))
        {
            var name = column < names.Length ? names[column] : "?";
            throw new ArgumentException(
                $"{path}: wiersz {row} (nagłówek to wiersz 0), kolumna {column + 1} "
                + $"„{name}” — " + NieJestLiczba(text));
        }

        return value;
    }

    /// <summary>
    /// To samo dla wartości całkowitych szerokich (<c>--steps</c>, <c>--sample-every</c>);
    /// zbiór postaci ten sam, co miał <c>long.Parse(text, Inv)</c>.
    /// </summary>
    private static long LongValue(string command, string name, string text)
    {
        if (!long.TryParse(text, NumberStyles.Integer, Inv, out var value))
        {
            throw new ArgumentException(NotANumber(command, name, text));
        }

        return value;
    }

    /// <summary>
    /// To samo dla wartości całkowitych wąskich (<c>--repeats</c>, <c>--warmup</c>,
    /// człony <c>--trains</c>); zbiór postaci ten sam, co miał <c>int.Parse(text, Inv)</c>.
    /// Osobny od <see cref="LongValue"/>, a nie rzutowanie z niego: rzutowanie
    /// zamieniłoby wartość poza zakresem <see cref="int"/> na inną liczbę w milczeniu,
    /// czyli na dokładnie tę klasę wyrocznia-zepsuta-w-dobrą-stronę, którą ta rodzina
    /// pozycji zamyka.
    /// </summary>
    private static int IntValue(string command, string name, string text)
    {
        if (!int.TryParse(text, NumberStyles.Integer, Inv, out var value))
        {
            throw new ArgumentException(NotANumber(command, name, text));
        }

        return value;
    }

    // --- parity -------------------------------------------------------------------

    /// <summary>
    /// Kontrola, że <see cref="TrainController"/> nie jest drugą fizyką: przy pełnym
    /// nastawniku, odpuszczonym hamulcu i rozruchu z postoju musi dać **co do bitu** to
    /// samo, co <see cref="AccelerationRun"/> z T-310 — a ten odtwarza
    /// <c>tools/physics/reference.py</c>.
    /// </summary>
    private static int Parity()
    {
        var model = VehicleModel.M7;
        var step = FixedStep.Simulation;
        var target = Units.KmhToMps(model.DesignMaxSpeedKmh);
        var failed = false;

        foreach (var load in new[] { TrainLoad.Aw0, TrainLoad.Aw2 })
        {
            var conditions = RunConditions.Level(model, load);
            var reference = new AccelerationRun(model).ToSpeed(conditions, model.DesignMaxSpeedKmh, step);

            var controller = new TrainController(model);
            var state = DriveState.AtRest;
            while (state.SpeedMps < target && state.Steps < 300 * FixedStep.SimulationHertz)
            {
                state = controller.Advance(state, conditions, DriverCommand.FullPower, target, step, out _);
            }

            var sameSteps = state.Steps == reference.Steps;
            var sameBits = BitConverter.DoubleToInt64Bits(state.DistanceM) == BitConverter.DoubleToInt64Bits(reference.DistanceM);
            failed |= !sameSteps || !sameBits;

            Console.Out.WriteLine(string.Create(
                Inv,
                $"[PARYTET] {load}: kroki {state.Steps} vs {reference.Steps} ({(sameSteps ? "==" : "!=")}), " +
                $"droga {state.DistanceM:F3} m vs {reference.DistanceM:F3} m ({(sameBits ? "co do bitu" : "ROZJAZD")})"));
        }

        // Hamowanie: kontroler **nie** ma dawać tej samej drogi, co ServiceBrakingRun,
        // i warto, żeby to było widać liczbą. Tamten model jest czysto kinematyczny —
        // nie zna oporów ruchu. Kontroler dokłada do zadanego opóźnienia opory Davisa,
        // bo prowadzony skład jedzie w tunelu, a nie w próżni. Różnica jest **całą**
        // pracą oporów na drodze hamowania i nie wolno jej nazwać tolerancją.
        var brakeConditions = RunConditions.Level(model, TrainLoad.Aw2);
        var kinematic = new ServiceBrakingRun(model).ToStop(model.DesignMaxSpeedKmh, step);
        var controlled = new TrainController(model);
        var braking = new DriveState(0, target, 0.0, 0.0);
        while (braking.SpeedMps > 0.0 && braking.Steps < 120 * FixedStep.SimulationHertz)
        {
            braking = controlled.Advance(braking, brakeConditions, DriverCommand.FullServiceBrake, target, step, out _);
        }

        Console.Out.WriteLine(string.Create(
            Inv,
            $"[HAMOWANIE] kinematyczne (T-310) {kinematic.DistanceM:F3} m / {kinematic.TimeSeconds:F3} s, " +
            $"kontroler z oporami {braking.DistanceM:F3} m / {braking.TimeSeconds(step):F3} s, " +
            $"różnica {kinematic.DistanceM - braking.DistanceM:F3} m = praca oporów Davisa"));

        return failed ? 1 : 0;
    }

    // --- braking ------------------------------------------------------------------

    /// <summary>
    /// Tablice referencyjne hamowania z T-311, w formacie jeden do jednego z
    /// <c>tools/physics/braking.py</c> — po to, żeby dało się je porównać wiersz po
    /// wierszu, a nie „na oko". Rdzeń i referencja są tu dwiema niezależnymi drogami
    /// do tych samych liczb, dokładnie tak jak w T-310.
    /// </summary>
    private static int Braking()
    {
        var model = VehicleModel.M7;
        var solver = new BrakingPointSolver(model);
        var step = FixedStep.Simulation;

        Console.Out.WriteLine(string.Create(
            Inv,
            $"zryw = {model.DesignJerkMps3:R} m/s^3, lambda = {model.DesignEffectiveMassFactor:R}, " +
            $"sluzbowe = {model.DesignServiceBrakeMps2:R} m/s^2, awaryjne = {model.DesignEmergencyBrakeMps2:R} m/s^2"));
        Console.Out.WriteLine();

        Console.Out.WriteLine("SUFIT PRZYCZEPNOSCIOWY (design_assumption: udzial osi hamowanych)");
        Console.Out.WriteLine("rail  mu     wariant             f       b_max     b_max_bez_lambda  1.10  1.30");
        var limits = new[] { BrakeAdhesionLimit.AllAxles(model), BrakeAdhesionLimit.PoweredAxlesOnly(model) };
        foreach (var (rail, mu) in new[]
                 {
                     ("dry", model.DesignAdhesionDry), ("wet", model.DesignAdhesionWet),
                 })
        {
            foreach (var limit in limits)
            {
                var service = !limit.IsAdhesionLimited(model.DesignServiceBrakeMps2, mu);
                var emergency = !limit.IsAdhesionLimited(model.DesignEmergencyBrakeMps2, mu);
                Console.Out.WriteLine(string.Create(
                    Inv,
                    $"{rail,-5} {mu,-6:0.00} {limit.Variant,-19} {limit.DesignBrakedMassFraction:0.0000}  " +
                    $"{limit.MaxDecelerationMps2(mu),8:0.0000}  {limit.MaxRigidBodyDecelerationMps2(mu),16:0.0000}  " +
                    $"{(service ? "tak" : "NIE"),4}  {(emergency ? "tak" : "NIE"),4}"));
            }
        }

        Console.Out.WriteLine();
        Console.Out.WriteLine("PROGI KRYTYCZNE");
        var allAxles = BrakeAdhesionLimit.AllAxles(model);
        foreach (var (decel, name) in new[]
                 {
                     (model.DesignServiceBrakeMps2, "sluzbowe"), (model.DesignEmergencyBrakeMps2, "awaryjne"),
                 })
        {
            foreach (var (rail, mu) in new[]
                     {
                         ("dry", model.DesignAdhesionDry), ("wet", model.DesignAdhesionWet),
                     })
            {
                var required = allAxles.RequiredBrakedMassFraction(decel, mu);
                var note = required > 1.0 ? "  -> NIEOSIAGALNE przy kazdym ukladzie osi" : string.Empty;
                Console.Out.WriteLine(string.Create(
                    Inv, $"  {name} {decel:0.00} m/s^2 {rail}: f_min = {required:0.000000}{note}"));
            }

            Console.Out.WriteLine(string.Create(
                Inv, $"  {name} {decel:0.00} m/s^2 przy f=1: mu_min = {allAxles.RequiredAdhesion(decel):0.000000}"));
        }

        Console.Out.WriteLine();
        Console.Out.WriteLine("DROGA HAMOWANIA, hamulec sluzbowy, krok 1/120 s");
        Console.Out.WriteLine(
            "v0[km/h]  wzor[m]   bez_oporow[m]  tunel[m]  powierzchnia[m]  dS_tunel  dS_pow  " +
            "dS_tunel_z_energii  dS_pow_z_energii");
        var conditions = RunConditions.Level(model, TrainLoad.Aw2);
        var speeds = new[] { 30.0, 40.0, 50.0, 60.0, 70.0, 80.0 };
        foreach (var row in new BrakingRun(model).ReferenceTable(conditions, speeds, model.DesignServiceBrakeMps2, step))
        {
            Console.Out.WriteLine(string.Create(
                Inv,
                $"{row.StartSpeedKmh,8:0}  {row.ClosedFormDistanceM,8:0.000}  {row.KinematicDistanceM,13:0.000}  " +
                $"{row.TunnelDistanceM,8:0.000}  {row.SurfaceDistanceM,15:0.000}  {row.TunnelShorteningM,8:0.000}  " +
                $"{row.SurfaceShorteningM,6:0.000}  {row.TunnelShorteningFromEnergyM,18:0.000}  " +
                $"{row.SurfaceShorteningFromEnergyM,16:0.000}"));
        }

        Console.Out.WriteLine();
        Console.Out.WriteLine("SOLVER PUNKTU HAMOWANIA (bez oporow, z ograniczeniem zrywu)");
        var top = Units.KmhToMps(model.DesignMaxSpeedKmh);
        Console.Out.WriteLine(string.Create(
            Inv,
            $"  minimum ze zrywu z {model.DesignMaxSpeedKmh:0} km/h do 0 = {solver.MinimumDistanceM(top, 0.0):0.000} m " +
            $"(b_progowe = {solver.PlateauCeilingMps2(top, 0.0):0.0000} m/s^2)"));
        foreach (var distance in new[] { 150.0, 200.0, 240.0, 300.0, 400.0 })
        {
            var point = solver.RequiredDeceleration(top, 0.0, distance);
            var back = solver.DistanceM(top, 0.0, point.DecelerationMps2);
            Console.Out.WriteLine(string.Create(
                Inv,
                $"  s = {distance,6:0.0} m -> b = {point.DecelerationMps2:0.000000} m/s^2, " +
                $"kontrola s(b) = {back:0.000000} m, |delta| = {Math.Abs(back - distance):0.000e+00} m"));
        }

        return 0;
    }

    // --- service-day ----------------------------------------------------------------

    /// <summary>
    /// Doba służby odtworzona z obiegów rozkładu — liczby liczy RDZEŃ, nie narzędzie
    /// Pythona, i o to w pozycji 6.A3 chodzi.
    /// </summary>
    private static int ServiceDayCommand(string[] args)
    {
        var timetablePath = Option(args, "--timetable")
            ?? throw new ArgumentException(
                "service-day wymaga --timetable: doba służby powstaje z obiegów rozkładu, "
                + "a nie z osi — bez pliku nie ma czego odtwarzać");

        var day = ServiceDay.FromJson(File.ReadAllText(timetablePath));

        var peak = day.Peak;
        Console.WriteLine(string.Create(Inv,
            $"[SŁUŻBA] dzień {day.Date}: obiegów {day.BlockCount}, "
            + $"naraz w służbie {peak.Blocks} o {peak.AtClock}"));
        Console.WriteLine(string.Create(Inv,
            $"[SŁUŻBA] nakładających się par kursów w jednym obiegu: {day.OverlappingTripsInABlock}"));

        var at = Option(args, "--at");
        if (at is not null)
        {
            var seconds = ParseClock(Command(args), "--at", at);
            Console.WriteLine(string.Create(Inv,
                $"[SŁUŻBA] o {ServiceDay.Clock(seconds)} w służbie {day.ConcurrentAt(seconds)} obiegów"));
        }

        var output = Option(args, "--out");
        if (output is not null)
        {
            var directory = Path.GetDirectoryName(Path.GetFullPath(output));
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }

            var lines = new List<string>(Provenance(
                "service-day",
                ("timetable", timetablePath),
                ("blocks", day.Blocks.Count.ToString(Inv)),
                ("peak_blocks", peak.Blocks.ToString(Inv)),
                ("peak_at", peak.AtClock)))
            {
                "block_id,first_departure_s,last_arrival_s,span_s,trips",
            };
            foreach (var block in day.Blocks)
            {
                lines.Add(string.Create(Inv,
                    $"{block.Id},{block.FirstDepartureS},{block.LastArrivalS},{block.SpanSeconds},{block.Trips}"));
            }

            File.WriteAllLines(output, lines);
            Console.WriteLine($"[SŁUŻBA] zapisano {output}");
        }

        return 0;
    }

    /// <summary>
    /// <c>HH:MM:SS</c> na sekundy od północy. Godzina wolno przekroczyć 24 — doba
    /// służby kończy się po północy i GTFS zapisuje to właśnie tak.
    /// </summary>
    private static double ParseClock(string command, string name, string text)
    {
        var parts = text.Split(':');
        if (parts.Length != 3)
        {
            throw new ArgumentException($"czas ma mieć postać HH:MM:SS, a jest „{text}”", nameof(text));
        }

        // Cytowana jest CALA wartosc, nie czlon: zegar jest jedna wartoscia, a `xx`
        // wyjete z `10:xx:00` nie powiedzialoby czytajacemu, ktora opcje poprawic.
        // Inaczej niz w ParseTrainCounts, i z tego jednego powodu.
        var weights = new[] { 3600.0, 60.0, 1.0 };
        var seconds = 0.0;
        for (var i = 0; i < parts.Length; i++)
        {
            if (!double.TryParse(parts[i], NumberStyles.Float | NumberStyles.AllowThousands, Inv, out var part))
            {
                throw new ArgumentException(NotANumber(command, name, text));
            }

            seconds += part * weights[i];
        }

        return seconds;
    }

    // --- budget -------------------------------------------------------------------

    /// <summary>
    /// Ile kosztuje krok rdzenia linii przy N składach na osi — pozycja 5.7
    /// z <c>docs/TASKS.md</c>.
    ///
    /// <para><b>Dlaczego to nie jest opcja polecenia <c>line</c>.</b> <c>line</c> zgłasza
    /// dokładnie jeden skład (<c>KABINA</c>), bo odpowiada na pytanie „czy rdzeń liczy ten
    /// sam przejazd, co scena". Doklejenie do niego N składów zmieniłoby to, co porównuje
    /// bramka CI, więc pomiar dostaje własne polecenie, a <c>line</c> zostaje bit w bit
    /// takie, jak było.</para>
    ///
    /// <para><b>Co polecenie wypisuje i czego nie wypisuje.</b> Wypisuje medianę i rozstęp
    /// z powtórzeń, stosunek czasu procesora do ściennego oraz obsadę linii — ile składów
    /// naprawdę było na planie, bo to ona, a nie liczba zgłoszonych, jest tym N, o którym
    /// mówi raport. Nie wypisuje jednej ładnej liczby: na maszynie dzielonej z innymi
    /// procesami byłaby ona zmyśleniem o dokładności, której pomiar nie ma.</para>
    /// </summary>
    private static int Budget(string[] args)
    {
        var axisPath = Option(args, "--axis") ?? throw new ArgumentException("budget wymaga --axis");
        var signallingPath = Option(args, "--signalling")
            ?? throw new ArgumentException(
                "budget wymaga --signalling: bez planu bloków nie ma LineCore, a bez LineCore "
                + "nie ma kroku linii, którego koszt można zmierzyć");
        var limitKmh = RequiredNumber(args, "--limit-kmh");
        var exchange = RequiredNumber(args, "--exchange-s");
        var headway = RequiredNumber(args, "--headway-s");
        var brakeUsage = OptionalNumber(args, "--brake-usage") ?? 1.0;
        var stopWindow = OptionalNumber(args, "--stop-window-m") ?? 5.0;
        var turnback = OptionalNumber(args, "--turnback-s") ?? 0.0;
        var load = Option(args, "--load") ?? "AW0";

        // WYBIEG (6.A18). Ta sama nastawa i ta sama decyzja o `null`, co w `line`
        // (6.A6): brak opcji to `null`, nie `0.0`, wiec pomiar bez tej opcji jest bit
        // w bit tym samym pomiarem, co przed jej dopisaniem — a to jest warunek, pod
        // ktorym `reports/linecore-budget.md` i prog w `linecore-step-budget.json`
        // pozostaja porownywalne z dzisiejszym przebiegiem.
        var coastFromM = OptionalNumber(args, "--coast-from-m");
        var atp = Array.IndexOf(args, "--atp") >= 0;
        var steps = LongValue(Command(args), "--steps",
            Option(args, "--steps") ?? throw new ArgumentException("budget wymaga --steps"));
        var repeats = IntValue(Command(args), "--repeats", Option(args, "--repeats") ?? "7");
        var warmup = IntValue(Command(args), "--warmup", Option(args, "--warmup") ?? "2");
        var counts = ParseTrainCounts(Command(args), "--trains", Option(args, "--trains")
            ?? throw new ArgumentException("budget wymaga --trains, np. --trains 1,2,4,8"));

        var axis = TrackAxis.FromJson(File.ReadAllText(axisPath));
        var plan = SignallingPlan.FromJson(File.ReadAllText(signallingPath));
        var model = VehicleModel.M7;
        var trainLoad = load switch
        {
            "AW0" => TrainLoad.Aw0,
            "AW2" => TrainLoad.Aw2,
            _ => throw new ArgumentException($"nieznane obciążenie: {load}; dozwolone AW0 albo AW2"),
        };

        var conditions = RunConditions.Level(model, trainLoad);
        var settings = new LineRunSettings(
            Units.KmhToMps(limitKmh), exchange, brakeUsage, stopWindow, coastFromM);
        var budgetSeconds = FixedStep.Simulation.Seconds;

        Console.Out.WriteLine(string.Create(
            Inv,
            $"[BUDŻET] oś {axis.Id}, plan {plan.PlanId} ({plan.Blocks.Count} bloków), "
            + $"{axis.Stations.Count} stacji, ATP={(atp ? "tak" : "nie")}, "
            + $"nawrót {turnback:F0} s, odstęp {headway:F0} s, "
            + $"{settings.CoastDescription}"));
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[BUDŻET] okno {steps} kroków, rozgrzewka {warmup}, powtórzeń {repeats}, "
            + $"rdzeni {Environment.ProcessorCount}, budżet kroku 1/{FixedStep.SimulationHertz} s "
            + $"= {budgetSeconds * 1e6:F1} µs"));
        Console.Out.WriteLine(
            "[BUDŻET] N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;min;max;rozstęp_%;µs_krok;CPU/ścienny;%budżetu");

        var rows = new List<string>(Provenance(
            "budget",
            ("axis", axis.Id),
            ("signalling_plan", plan.PlanId),
            ("limit_kmh", limitKmh.ToString("F2", Inv)),
            ("exchange_s", exchange.ToString("F1", Inv)),
            ("headway_s", headway.ToString("F1", Inv)),
            ("turnback_s", turnback.ToString("F1", Inv)),
            ("brake_usage", brakeUsage.ToString("F3", Inv)),
            ("stop_window_m", stopWindow.ToString("F1", Inv)),
            ("load", load),
            ("atp", atp ? "tak" : "nie"),
            ("coast", settings.CoastDescription),
            ("steps", steps.ToString(Inv)),
            ("warmup", warmup.ToString(Inv)),
            ("repeats", repeats.ToString(Inv))))
        {
            "trains_declared,trains_on_line_max,trains_on_line_mean,trains_waiting_mean,steps,repeats,"
            + "median_steps_per_s,min_steps_per_s,max_steps_per_s,spread_pct,"
            + "us_per_step,cpu_over_wall,frame_budget_pct",
        };

        var scenarios = new List<LineBudgetScenario>(counts.Count);
        foreach (var trains in counts)
        {
            scenarios.Add(new LineBudgetScenario(
                plan, axis, conditions, settings, trains, headway, turnback, atp));
        }

        var measured = LineBudget.Sweep(scenarios, steps, warmup, repeats);

        var fits = 0;
        var lastMicroseconds = 0.0;
        var lastOnLine = 0;
        for (var index = 0; index < counts.Count; index++)
        {
            var trains = counts[index];
            var (census, runs) = measured[index];

            var median = LineBudget.MedianStepsPerSecond(runs);
            var slowest = double.MaxValue;
            var fastest = 0.0;
            var cpu = 0.0;
            var wall = 0.0;
            foreach (var run in runs)
            {
                slowest = Math.Min(slowest, run.StepsPerSecond);
                fastest = Math.Max(fastest, run.StepsPerSecond);
                cpu += run.CpuSeconds;
                wall += run.WallSeconds;
            }

            var spreadPct = 100.0 * (fastest - slowest) / median;
            var microseconds = 1e6 / median;
            var frameBudgetPct = 100.0 * microseconds / (budgetSeconds * 1e6);
            if (frameBudgetPct <= 100.0)
            {
                fits++;
            }

            lastMicroseconds = microseconds;
            lastOnLine = census.MaxOnLine;

            Console.Out.WriteLine(string.Create(
                Inv,
                $"[BUDŻET] {trains};{census.MaxOnLine};{census.MeanOnLine:F2};{census.MeanWaiting:F2};{median:F0};{slowest:F0};"
                + $"{fastest:F0};{spreadPct:F1};{microseconds:F3};{cpu / wall:F2};{frameBudgetPct:F2}"));

            rows.Add(string.Create(
                Inv,
                $"{trains},{census.MaxOnLine},{census.MeanOnLine:F4},{census.MeanWaiting:F4},{steps},{repeats},"
                + $"{median:F1},{slowest:F1},{fastest:F1},{spreadPct:F2},"
                + $"{microseconds:F4},{cpu / wall:F3},{frameBudgetPct:F3}"));
        }

        Console.Out.WriteLine(string.Create(
            Inv,
            $"[BUDŻET] mieści się w 1/{FixedStep.SimulationHertz} s: {fits} z {counts.Count} "
            + $"zmierzonych N; największe zmierzone N={counts[^1]} zajmuje "
            + $"{100.0 * lastMicroseconds / (budgetSeconds * 1e6):F2}% budżetu kroku "
            + $"przy {lastOnLine} składach faktycznie na planie"));

        var outPath = Option(args, "--out");
        if (outPath is not null)
        {
            File.WriteAllLines(outPath, rows);
            Console.Out.WriteLine($"[BUDŻET] {rows.Count - 1} wierszy -> {outPath}");
        }

        return 0;
    }

    /// <summary>
    /// Lista N z przecinkami. Pusta lista, zero i wartość ujemna są odmową: pomiar
    /// „przy zerze składów" mierzyłby pustą pętlę, a nie koszt składu.
    /// </summary>
    private static List<int> ParseTrainCounts(string command, string name, string text)
    {
        var counts = new List<int>();
        foreach (var part in text.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            // Cytowany jest CZLON, nie cala lista: przy `--trains 1,2,4,abc` czytajacy
            // ma zobaczyc, ktory z czterech jest zly, a nie przepisac sobie liste.
            var value = IntValue(command, name, part);
            if (value < 1)
            {
                throw new ArgumentException($"{name} ma mieć liczby dodatnie, a ma {value}");
            }

            counts.Add(value);
        }

        if (counts.Count == 0)
        {
            throw new ArgumentException("--trains nie zawiera ani jednej liczby");
        }

        return counts;
    }

    // --- pomocnicze ---------------------------------------------------------------

    private static string? Option(string[] args, string name)
    {
        for (var i = 0; i < args.Length - 1; i++)
        {
            if (string.Equals(args[i], name, StringComparison.Ordinal))
            {
                return args[i + 1];
            }
        }

        return null;
    }
}
