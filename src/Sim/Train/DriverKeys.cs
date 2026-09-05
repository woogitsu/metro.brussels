using System;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Stan trzymanych klawiszy maszynisty w jednym kroku symulacji — **wejście**, a nie
/// polecenie. Położenie nastawnika, które z tego wynika, liczy <see cref="DriverNotch"/>.
///
/// <para><b>Dlaczego to jest w rdzeniu, a nie w warstwie Godota.</b> Zapis wejść
/// (<see cref="InputLog"/>) musi dać się odtworzyć bez silnika — inaczej nie da się
/// porównać przejazdu gracza z rdzeniem, a to jest jedyny powód, dla którego zapis
/// w ogóle powstaje (<c>docs/01-architecture.md</c> §Determinizm: „z ziarna + zapisu
/// wejść da się odtworzyć przejazd"). Klawiatura zostaje w <c>src/Game</c>; to, co
/// z niej wyszło, jest już danymi rdzenia.</para>
///
/// <para><b>Cztery pola, nie jeden klawisz.</b> Zapis jest bezstratny: człowiek potrafi
/// trzymać W i S naraz, a pierwszeństwo między nimi jest regułą modelu
/// (<see cref="DriverNotch"/>), nie własnością klawiatury. Gdyby log trzymał już
/// rozstrzygnięty klawisz, zmiana tej reguły cicho zmieniłaby znaczenie starych
/// plików.</para>
///
/// <para><b><see cref="Emergency"/> nie jest czwartym stopniem hamowania.</b>
/// <see cref="DriverCommand"/> ma nastawnik i hamulec SŁUŻBOWY i nic poza tym —
/// hamulec awaryjny jako osobna fizyka w tym modelu nie istnieje. Ten klawisz jest
/// GESTEM maszynisty: „rzuć dźwignię na pełny hamulec od razu", bez przesuwu
/// <see cref="DriverNotch.RatePerSecond"/>. Decyzja właściciela z 05.09.2026: osobny
/// klawisz ma robić dokładnie to samo, co pełny hamulec służbowy, a HUD ma to mówić
/// wprost, zamiast udawać fizykę, której nie ma.</para>
/// </summary>
/// <param name="Power">Klawisz ciągu (W / strzałka w górę).</param>
/// <param name="Brake">Klawisz hamulca (S / strzałka w dół).</param>
/// <param name="Coast">Klawisz wybiegu (X).</param>
/// <param name="Emergency">Klawisz hamulca awaryjnego — pełny hamulec służbowy naraz.</param>
public readonly record struct DriverKeys(bool Power, bool Brake, bool Coast, bool Emergency)
{
    /// <summary>Znak pustego stanu w zapisie. Pusty napis wyglądałby jak uszkodzony wiersz.</summary>
    public const char NoneCode = '-';

    /// <summary>Znak klawisza ciągu w zapisie.</summary>
    public const char PowerCode = 'W';

    /// <summary>Znak klawisza hamulca w zapisie.</summary>
    public const char BrakeCode = 'S';

    /// <summary>Znak klawisza wybiegu w zapisie.</summary>
    public const char CoastCode = 'X';

    /// <summary>
    /// Znak klawisza hamulca awaryjnego w zapisie. Dopisany NA KOŃCU kodu, za
    /// <see cref="CoastCode"/>, żeby każdy stan bez tego klawisza zapisywał się
    /// dokładnie tak samo jak przed 05.09.2026 — stare pliki zapisu odtwarzają się
    /// bez zmiany ani jednego bajtu.
    /// </summary>
    public const char EmergencyCode = 'E';

    /// <summary>Nic nie jest trzymane.</summary>
    public static DriverKeys None => default;

    /// <summary>Sam ciąg.</summary>
    public static DriverKeys Powering => new(true, false, false, false);

    /// <summary>Sam hamulec.</summary>
    public static DriverKeys Braking => new(false, true, false, false);

    /// <summary>Sam wybieg.</summary>
    public static DriverKeys Coasting => new(false, false, true, false);

    /// <summary>Sam hamulec awaryjny.</summary>
    public static DriverKeys EmergencyBraking => new(false, false, false, true);

    /// <summary>Czy trzymany jest którykolwiek klawisz.</summary>
    public bool Any => Power || Brake || Coast || Emergency;

    /// <summary>
    /// Zapis stanu do jednego pola tekstowego: <c>-</c>, albo znaki <c>W</c>, <c>S</c>,
    /// <c>X</c>, <c>E</c> w tej stałej kolejności. Kolejność jest stała, żeby ten sam
    /// stan dawał zawsze ten sam napis — plik zapisu jest porównywany <c>cmp</c>,
    /// nie „na oko".
    /// </summary>
    /// <returns>Kod stanu klawiszy, nigdy pusty napis.</returns>
    public string Code()
    {
        if (!Any)
        {
            return NoneCode.ToString();
        }

        Span<char> buffer = stackalloc char[4];
        var length = 0;
        if (Power)
        {
            buffer[length++] = PowerCode;
        }

        if (Brake)
        {
            buffer[length++] = BrakeCode;
        }

        if (Coast)
        {
            buffer[length++] = CoastCode;
        }

        if (Emergency)
        {
            buffer[length++] = EmergencyCode;
        }

        return new string(buffer[..length]);
    }

    /// <summary>
    /// Odczyt stanu z kodu. Nieznany znak, powtórzony znak i <c>-</c> zmieszane
    /// z klawiszem są BŁĘDEM, a nie „najlepszym dopasowaniem": plik zapisu wejść ma
    /// odtwarzać przejazd co do bitu, więc cicho poprawiony wiersz odtworzyłby inny
    /// przejazd i nikt by nie wiedział który.
    /// </summary>
    /// <param name="code">Kod z pliku zapisu.</param>
    /// <returns>Stan klawiszy opisany tym kodem.</returns>
    /// <exception cref="FormatException">Kod jest pusty albo zawiera znak spoza zestawu.</exception>
    public static DriverKeys Parse(string code)
    {
        ArgumentNullException.ThrowIfNull(code);
        if (code.Length == 0)
        {
            throw new FormatException("Kod klawiszy jest pusty; brak klawiszy zapisuje się znakiem '-'.");
        }

        if (code.Length == 1 && code[0] == NoneCode)
        {
            return None;
        }

        var power = false;
        var brake = false;
        var coast = false;
        var emergency = false;
        foreach (var character in code)
        {
            switch (character)
            {
                case PowerCode when !power:
                    power = true;
                    break;
                case BrakeCode when !brake:
                    brake = true;
                    break;
                case CoastCode when !coast:
                    coast = true;
                    break;
                case EmergencyCode when !emergency:
                    emergency = true;
                    break;
                default:
                    throw new FormatException(
                        $"Kod klawiszy '{code}' zawiera nieznany albo powtórzony znak '{character}'. "
                        + $"Znane: {PowerCode}, {BrakeCode}, {CoastCode}, {EmergencyCode}, "
                        + $"albo samo {NoneCode}.");
            }
        }

        return new DriverKeys(power, brake, coast, emergency);
    }

    /// <inheritdoc/>
    public override string ToString() => Code();
}
