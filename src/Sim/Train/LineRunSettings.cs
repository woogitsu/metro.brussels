using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Założenia przejazdu z zatrzymaniami. **Wszystkie cztery są bez źródła** i dlatego
/// mieszkają w osobnym typie z katalogiem <see cref="Assumptions"/>, a nie jako stałe
/// w <see cref="LineRun"/>: stała w kodzie wygląda dokładnie tak samo jak liczba
/// z rejestru, a te nią nie są.
///
/// <para>Konstruktor **nie ma wartości domyślnych dla żadnej z tych czterech liczb**.
/// Ta sama decyzja, co w <see cref="DoorCycle"/>: kod woli nie skompilować się bez
/// podanej liczby, niż podstawić zmyśloną i pozwolić jej wyjść w raporcie jako fakt
/// o metrze w Brukseli.</para>
///
/// <para><b>Piąty parametr — <see cref="CoastFromM"/> — domyślną wartość ma, i to jest
/// wyjątek z powodem, a nie wyłom w powyższej regule.</b> Tamte cztery są liczbami:
/// pominięta liczba znaczy „podstawiłem zmyśloną". Wybieg nie jest liczbą, tylko
/// obecnością albo nieobecnością strategii jazdy, a jego domyślne <c>null</c> znaczy
/// dosłownie „maszynista nie zdejmuje trakcji" — czyli prowadzenie sprzed 6.A6, bit
/// w bit. Gdyby ten parametr był wymagany, każdy dotychczasowy wołający musiałby
/// wypisać <c>null</c>, żeby zachować zachowanie, którego nie zmienia.</para>
/// </summary>
public sealed class LineRunSettings
{
    /// <summary>Założenia przejazdu.</summary>
    /// <param name="speedLimitMps">
    /// Jedno ograniczenie prędkości na całą oś. W <c>data/track/*.json</c> pole
    /// <c>speed_limits</c> jest **pustą listą we wszystkich sześciu pakietach** i nie ma
    /// dla nich źródła; T-113 daje wyłącznie ograniczenie **dolne** (57,65 km/h dla AW0),
    /// a <c>max_speed_kmh</c> = 80 w rejestrze M7 jest prędkością konstrukcyjną pojazdu
    /// ze statusem <c>design_model</c>, nie prędkością dopuszczalną na torze.
    /// </param>
    /// <param name="passengerExchangeSeconds">
    /// Czas wymiany pasażerów. Nie ma go w żadnym źródle — patrz T-312. T-113 ogranicza
    /// go od góry rozkładowym postojem minus cykl drzwi: ≤ 10,5 s przy medianowym
    /// postoju 19 s, ≤ 3,5 s przy najkrótszym w sieci 12 s.
    /// </param>
    /// <param name="brakeUsageFraction">
    /// Ułamek hamulca służbowego, przy którym maszynista zaczyna hamować. 1,0 znaczy
    /// „hamuj w ostatniej możliwej chwili" i nie zostawia zapasu na nic. Nie ma na to
    /// liczby w żadnym dokumencie — praktyka prowadzenia nie jest publikowana.
    /// </param>
    /// <param name="stopWindowM">
    /// Jak blisko chainage stacji zatrzymanie liczy się jako zatrzymanie na tej stacji.
    /// Nie jest to dokładność zatrzymania M7 — jest to okno rozpoznania stacji przez
    /// pętlę. Rzeczywisty błąd zatrzymania jest **mierzony** i wychodzi w
    /// <see cref="StationCall.StopErrorM"/>.
    /// </param>
    /// <param name="coastFromM">
    /// Od którego metra odcinka — licząc od odjazdu z poprzedniej stacji — maszynista
    /// zdejmuje trakcję i jedzie WYBIEGIEM. <c>null</c> znaczy „nie zdejmuje wcale"
    /// i daje przejazd identyczny co do bitu z tym sprzed 6.A6.
    ///
    /// <para><b>To jest strategia prowadzenia, nie własność toru ani pojazdu.</b>
    /// Praktyka prowadzenia STIB nie jest publikowana (ta sama luka, co przy
    /// <paramref name="brakeUsageFraction"/>), więc liczba tu podana jest **pytaniem
    /// pomiarowym** — „ile kosztuje wybieg od tego metra" — a nie odwzorowaniem tego,
    /// jak jeżdżą prawdziwi maszyniści. Dlatego 6.A6 mierzy koszt i zysk, a wyboru
    /// profilu jazdy dla gry nie dokonuje.</para>
    ///
    /// <para><b>Czego to NIE zmienia.</b> Ani modelu oporów, ani krzywej hamowania.
    /// Wybieg wchodzi wyłącznie w gałąź „nie hamuję jeszcze": zamiast pełnej trakcji
    /// polecenie jest <see cref="DriverCommand.Coast"/>. Punkt hamowania nadal wychodzi
    /// z solvera T-311, więc odcinek, na którym hamowanie zaczyna się przed tym metrem,
    /// jedzie się dokładnie tak samo jak bez wybiegu.</para>
    /// </param>
    public LineRunSettings(
        double speedLimitMps,
        double passengerExchangeSeconds,
        double brakeUsageFraction,
        double stopWindowM,
        double? coastFromM = null)
    {
        Require(speedLimitMps, nameof(speedLimitMps), "Ograniczenie prędkości");
        Require(passengerExchangeSeconds, nameof(passengerExchangeSeconds), "Czas wymiany pasażerów", allowZero: true);
        Require(brakeUsageFraction, nameof(brakeUsageFraction), "Ułamek hamulca");
        Require(stopWindowM, nameof(stopWindowM), "Okno stacji");
        if (coastFromM is double coast)
        {
            Require(coast, nameof(coastFromM), "Początek wybiegu", allowZero: true);
        }

        if (brakeUsageFraction > 1.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(brakeUsageFraction), brakeUsageFraction,
                "Ułamek hamulca powyżej 1,0 znaczyłby hamowanie mocniejsze niż służbowe — to hamulec awaryjny.");
        }

        SpeedLimitMps = speedLimitMps;
        PassengerExchangeSeconds = passengerExchangeSeconds;
        BrakeUsageFraction = brakeUsageFraction;
        StopWindowM = stopWindowM;
        CoastFromM = coastFromM;
    }

    /// <summary>Jedno ograniczenie prędkości na całą oś.</summary>
    public double SpeedLimitMps { get; }

    /// <summary>Czas wymiany pasażerów przekazany do cyklu drzwi.</summary>
    public double PassengerExchangeSeconds { get; }

    /// <summary>Ułamek hamulca służbowego wyzwalający hamowanie.</summary>
    public double BrakeUsageFraction { get; }

    /// <summary>Okno rozpoznania stacji.</summary>
    public double StopWindowM { get; }

    /// <summary>
    /// Metr odcinka, od którego maszynista jedzie wybiegiem; <c>null</c> = bez wybiegu.
    /// </summary>
    public double? CoastFromM { get; }

    /// <summary>
    /// Katalog założeń tego przejazdu, w kolejności deklaracji — czyli stałej.
    ///
    /// <para>Wybieg dopisuje **piątą** pozycję, ale wyłącznie wtedy, gdy jest włączony.
    /// Przejazd bez wybiegu nie ma o czym założyć: <c>null</c> nie jest liczbą, więc
    /// wpis „CoastFromM = 0" mówiłby „wybieg od zerowego metra", czyli coś wprost
    /// przeciwnego do stanu faktycznego.</para>
    /// </summary>
    public IReadOnlyList<ScenarioAssumption> Assumptions
    {
        get
        {
            var catalogue = new List<ScenarioAssumption>(Base);
            if (CoastFromM is double coast)
            {
                catalogue.Add(new ScenarioAssumption(
                    nameof(CoastFromM), coast,
                    "metr odcinka, od którego maszynista zdejmuje trakcję i jedzie wybiegiem; " +
                    "strategia prowadzenia, nie własność toru — praktyka STIB nie jest publikowana, " +
                    "a 6.A6 mierzy koszt tej liczby, nie twierdzi, że tak się jeździ"));
            }

            return catalogue;
        }
    }

    private IReadOnlyList<ScenarioAssumption> Base => new[]
    {
        new ScenarioAssumption(
            nameof(SpeedLimitMps), SpeedLimitMps,
            "jedno ograniczenie na całą oś; speed_limits w data/track/*.json jest puste we " +
            "wszystkich sześciu pakietach, a 80 km/h z rejestru M7 to prędkość konstrukcyjna " +
            "pojazdu (design_model), nie prędkość dopuszczalna na torze"),
        new ScenarioAssumption(
            nameof(PassengerExchangeSeconds), PassengerExchangeSeconds,
            "brak źródła (T-312). T-113 ogranicza od góry: postój rozkładowy minus cykl drzwi " +
            "8,5 s, czyli ≤ 10,5 s przy medianowym postoju 19 s"),
        new ScenarioAssumption(
            nameof(BrakeUsageFraction), BrakeUsageFraction,
            "ułamek hamulca służbowego, przy którym maszynista zaczyna hamować; praktyka " +
            "prowadzenia STIB nie jest publikowana"),
        new ScenarioAssumption(
            nameof(StopWindowM), StopWindowM,
            "okno rozpoznania stacji przez pętlę, nie dokładność zatrzymania M7 — " +
            "rzeczywisty błąd zatrzymania jest mierzony i wychodzi w StationCall.StopErrorM"),
    };

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"limit {Units.MpsToKmh(SpeedLimitMps):F2} km/h, wymiana {PassengerExchangeSeconds:F1} s, " +
        $"hamulec {BrakeUsageFraction:P0} służbowego, okno stacji {StopWindowM:F1} m, " +
        $"wybieg {(CoastFromM is double coast ? coast.ToString("F1", CultureInfo.InvariantCulture) + " m odcinka" : "wyłączony")}");

    private static void Require(double value, string name, string label, bool allowZero = false)
    {
        if (!double.IsFinite(value) || value < 0.0 || (!allowZero && value <= 0.0))
        {
            throw new ArgumentOutOfRangeException(
                name, value, $"{label} musi być skończone i {(allowZero ? "nieujemne" : "dodatnie")}.");
        }
    }
}
