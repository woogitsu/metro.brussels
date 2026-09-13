using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Game;

/// <summary>Jedno założenie projektowe warstwy silnika.</summary>
/// <param name="Name">Nazwa stałej w kodzie.</param>
/// <param name="Value">Wartość.</param>
/// <param name="Unit">Jednostka.</param>
/// <param name="Reason">Dlaczego taka i czego brakuje, żeby przestała być założeniem.</param>
public readonly record struct ViewAssumption(string Name, double Value, string Unit, string Reason)
{
    /// <inheritdoc/>
    public override string ToString() =>
        string.Create(CultureInfo.InvariantCulture, $"{Name} = {Value:R} {Unit} — {Reason}");
}

/// <summary>
/// Wszystkie liczby warstwy silnika, dla których **nie ma źródła**, w jednym miejscu.
///
/// Konwencja przeniesiona z <c>tools/blender/m7_layout.py: DESIGN_ASSUMPTIONS</c>
/// i z <c>VehicleModel.DesignAssumptions</c>: wartość bez pochodzenia ma być widoczna
/// w kodzie jako założenie, a nie ukryta w literale w środku metody. Żadna z tych
/// liczb nie jest faktem o brukselskim metrze i wolno je zmienić bez pytania kogokolwiek
/// o zgodę (<c>docs/21-measured-vs-assumed.md</c> §6) — ale nie wolno o nich powiedzieć
/// „tak jest w kabinie M7".
///
/// Wysokość oka i położenie kamery kabinowej są tu **jawnie zablokowane danymi**:
/// STIB nie publikuje rysunku pulpitu M7, a <c>tools/blender/m7_shell.py</c> celowo
/// nie modeluje kabiny (T-220, §1.3 <c>docs/21-measured-vs-assumed.md</c>).
/// </summary>
public static class DesignAssumptions
{
    /// <summary>Wysokość oka maszynisty nad główką szyny.</summary>
    public const double CabEyeHeightM = 2.20;

    /// <summary>Odsunięcie oka maszynisty od czoła składu, wzdłuż osi pojazdu.</summary>
    public const double CabEyeSetbackM = 1.80;

    /// <summary>Poprzeczne przesunięcie oka względem osi pudła; 0 = na środku.</summary>
    public const double CabEyeLateralM = 0.0;

    /// <summary>Kąt widzenia kamery kabinowej w pionie.</summary>
    public const double CabFovDeg = 70.0;

    /// <summary>Odsunięcie kamery obserwacyjnej za ogon składu.</summary>
    public const double ChaseBehindM = 12.0;

    /// <summary>
    /// Kilometraż czoła, po minięciu którego ODSŁANIA SIĘ widok goniący.
    /// Osobna liczba obok długości składu, i to jest cała treść 6.B43: do 09.09.2026
    /// granicą była sama długość M7, więc kadr na 96 m był jeszcze płytą pudła.
    /// </summary>
    public const double ChaseRevealFromM = 110.0;

    /// <summary>Wysokość kamery obserwacyjnej nad główką szyny.</summary>
    public const double ChaseHeightM = 2.60;

    /// <summary>Wyprzedzenie kamery kontrolnej przed czołem składu.</summary>
    public const double OutsideAheadM = 26.0;

    /// <summary>Przesunięcie kamery kontrolnej w bok względem osi toru składu.</summary>
    public const double OutsideLateralM = -4.20;

    /// <summary>Wysokość kamery kontrolnej nad główką szyny.</summary>
    public const double OutsideHeightM = 2.60;

    /// <summary>
    /// Odsunięcie kamery inspekcyjnej wzdłuż osi od oglądanego kilometrażu.
    ///
    /// <para><b>Liczba jest WYPROWADZONA, nie dobrana wzrokiem</b> — i to jest tu
    /// istotne, bo pole „Poza zakresem" pozycji 6.C4 zostawia ocenę estetyczną
    /// T-902. Przekrój <c>box_double</c> z <c>tools/blender/profiles.py</c> ma
    /// <b>9,40 × 5,90 m</b> (x od −4,70 do 4,70, y od −1,20 do 4,70). Przy pionowym
    /// kącie widzenia <see cref="CabFovDeg"/> = 70° odległość, na której wysokość
    /// 5,90 m wypełnia kadr DOKŁADNIE, wynosi 5,90 / (2·tan 35°) = <b>4,2130 m</b>;
    /// szerokość jest luźniejsza (3,7757 m przy poziomym 102,45° dla 16:9), więc
    /// wiąże wysokość. 6,32 m daje zapas <b>1,50×</b> (6,32 / 4,2130 = 1,5001) —
    /// ściana zostaje w kadrze, a nie na jego krawędzi.</para>
    /// </summary>
    public const double InspectStandoffM = 6.32;

    /// <summary>
    /// Wysokość kamery inspekcyjnej nad główką szyny: <b>środek</b> przekroju,
    /// (−1,20 + 4,70) / 2 = 1,75 m. Kadr jest wtedy wyśrodkowany na rurze, a nie
    /// na główce szyny — inaczej połowa zapasu nad składem wychodziłaby z kadru.
    /// </summary>
    public const double InspectHeightM = 1.75;

    /// <summary>
    /// Poprzeczne przesunięcie kamery inspekcyjnej: <b>0</b>, czyli na osi tunelu.
    /// Nie jest to wartość domyślna z braku pomysłu: przy zerze niesymetryczność
    /// geometrii czyta się w kadrze JAKO niesymetryczność, a przy dowolnym
    /// przesunięciu trzeba ją najpierw odjąć od przesunięcia kamery.
    /// </summary>
    public const double InspectLateralM = 0.0;

    /// <summary>Tempo przestawiania nastawnika i hamulca przy trzymanym klawiszu.</summary>
    public const double ControlNotchRatePerSecond = 0.80;

    /// <summary>
    /// Przesunięcie osi toru względem osi trasy. Wartość z
    /// <c>tools/blender/profiles.py: PROFILES["box_double"]["track_offsets"]</c>;
    /// **wybór strony** źródła nie ma żadnego.
    /// </summary>
    public const double TrackOffsetM = 2.10;

    /// <summary>
    /// Połowa szerokości okna, w którym zatrzymanie liczy się jako wywołanie stacji.
    ///
    /// <b>Nie jest to dokładność zatrzymania M7</b> — ta jest mierzona i wychodzi
    /// w <c>StationCall.StopErrorM</c>. Jest to okno rozpoznania stacji przez pętlę,
    /// ta sama wielkość co <c>LineRunSettings.StopWindowM</c>, którą przejazd
    /// referencyjny T-401 woła z 5,0 m. Ta sama liczba stoi tutaj, żeby kabina liczyła
    /// stacje tak samo jak linia, której jest widokiem.
    ///
    /// <b>Górne ograniczenie jest znane i nieprzekraczalne:</b> peron w generatorze ma
    /// 95,0 m (<c>tools/track/station_components.py: DESIGN_PLATFORM_LENGTH_M</c>, decyzja
    /// właściciela T-212; R-007 daje kontrolę górną 109,1 m i dolne ograniczenie 94,0 m,
    /// czyli długość składu M7), więc okno szersze niż połowa peronu pozwalałoby otworzyć
    /// drzwi poza krawędzią. Ograniczeniem jest <b>połowa peronu, 47,5 m</b>, i 5,0 m to
    /// <b>10,5 % tej połowy</b> — jedna podstawa, ta sama w obu zdaniach.
    /// </summary>
    public const double StationStopWindowM = 5.0;

    /// <summary>
    /// Ile stacji trzeba obsłużyć, żeby sesja treningowa była zaliczona — <b>dwie</b>
    /// (M1, <c>docs/PLAYABILITY.md</c> §3, MB-02).
    ///
    /// <b>Tu stoi LICZBA, a nie identyfikatory stacji</b>, i to jest granica postawiona
    /// świadomie. Decyzją projektową jest, ile celów ma M1 i że są to pierwsze stacje
    /// za punktem startowym; KTÓRE to stacje, mówi <c>data/track/L1_A.json</c> —
    /// i dlatego <c>FirstRun</c> czyta je z osi, zamiast mieć tu wpisane <c>8742</c>
    /// i <c>8292</c>. Kontrakt M1 żąda tego wprost: „cele wyszukiwane po identyfikatorach
    /// z osi; kilometraży nie kopiuje się do logiki". Dwie kopie tej samej listy
    /// milczałyby po zmianie osi, a milczenie wyglądałoby jak działająca sesja.
    ///
    /// <b>Dlaczego akurat dwie.</b> Jedna nie sprawdza odjazdu z peronu, a tego dotyczy
    /// blokada trakcji i cały cykl drzwi; trzy nie dokładają ani jednej nowej rzeczy
    /// do sprawdzenia, a przedłużają sesję o kolejny przejazd. Dwie są pierwszą liczbą,
    /// przy której trening zawiera PEŁNĄ pętlę: rusz, jedź, stań, wymień pasażerów,
    /// rusz ponownie, stań.
    /// </summary>
    public const int TrainingTargets = 2;

    /// <summary>
    /// Czas wymiany pasażerów na stacji, przekazywany do <c>DoorCycle</c>.
    ///
    /// <b>Nie ma źródła</b> — zależy od potoku, pory dnia i stacji, a w rejestrze nie ma
    /// ani jednej z tych rzeczy (T-312). T-113 ogranicza go od góry rozkładowym postojem
    /// minus cykl drzwi 8,5 s: <b>≤ 10,5 s</b> przy medianowym postoju 19 s i ≤ 3,5 s
    /// przy najkrótszym w sieci 12 s. Wybrane 8,0 s mieści się pod medianą i daje postój
    /// 16,5 s, czyli krócej niż medianowe 19 s — po stronie, na której gra jest szybsza
    /// od rzeczywistości, a nie wolniejsza.
    /// </summary>
    public const double PassengerExchangeSeconds = 8.0;

    /// <summary>
    /// Ułamek hamulca służbowego, przy którym autopilot trybu <c>--line</c> zaczyna
    /// hamować do peronu.
    ///
    /// <b>Nie ma źródła</b> — praktyka prowadzenia STIB nie jest publikowana
    /// (<c>LineRunSettings.BrakeUsageFraction</c>). 1,0 znaczy „hamuj w ostatniej
    /// możliwej chwili" i nie zostawia zapasu na nic; przejazd referencyjny T-401
    /// woła to właśnie z 1,0, i ta sama liczba stoi tutaj, żeby scena jechała tym
    /// samym przejazdem, z którym się ją porównuje. Zmiana tej liczby zmienia czas
    /// przejazdu, więc nie jest kosmetyką.
    /// </summary>
    public const double LineBrakeUsageFraction = 1.0;

    /// <summary>Zasięg reflektora czołowego.</summary>
    public const double HeadlightRangeM = 70.0;

    /// <summary>Energia reflektora czołowego.</summary>
    public const double HeadlightEnergy = 2.5;

    /// <summary>Katalog założeń — do wypisania w logu przejazdu i w raporcie.</summary>
    public static IReadOnlyList<ViewAssumption> All { get; } = new[]
    {
        new ViewAssumption(nameof(CabEyeHeightM), CabEyeHeightM, "m",
            "wysokość oka nad główką szyny; podłoga M7 jest na 1,03 m (spec), reszta to postawa siedzącego maszynisty — STIB nie publikuje rysunku pulpitu"),
        new ViewAssumption(nameof(CabEyeSetbackM), CabEyeSetbackM, "m",
            "odsunięcie oka od czoła; mieści się w strefie kabiny 3,60 m z m7_layout.py, ale samo w sobie nie ma źródła"),
        new ViewAssumption(nameof(CabEyeLateralM), CabEyeLateralM, "m",
            "oko na osi pudła; rozmieszczenie pulpitu M7 nie jest publiczne, a zgadnięta strona byłaby zgadniętym faktem"),
        new ViewAssumption(nameof(CabFovDeg), CabFovDeg, "°",
            "kąt widzenia kamery kabinowej; parametr obrazu, nie wymiar pojazdu"),
        new ViewAssumption(nameof(ChaseBehindM), ChaseBehindM, "m",
            "kamera obserwacyjna za ogonem, wewnątrz tunelu; dobrana tak, żeby ogon składu i przekrój tunelu zmieściły się w kadrze"),
        new ViewAssumption(nameof(ChaseRevealFromM), ChaseRevealFromM, "m",
            "kilometraż, po minięciu którego odsłania się widok goniący; DECYZJA właściciela z 07.09.2026, nie wynik pomiaru — pomiar co 2 m z 09.09.2026 mówi, że czysty kadr zaczyna się już na 98 m (96 m → 46,67 % pikseli jaśniejszych niż 0,80 w górnych 60 % kadru, 98 m i dalej → 0,00 %), a pełne ChaseBehindM odstępu wraca na 106 m; 110 m jest o 12 m ostrożniejsze od pomiaru i to jest wybór właściciela"),
        new ViewAssumption(nameof(ChaseHeightM), ChaseHeightM, "m",
            "wysokość kamery obserwacyjnej; z zapasem pod stropem tunelu 4,70 m nad główką szyny"),
        new ViewAssumption(nameof(OutsideAheadM), OutsideAheadM, "m",
            "kamera kontrolna przed czołem składu; wyłącznie do oglądania geometrii, nie jest widokiem gry"),
        new ViewAssumption(nameof(OutsideLateralM), OutsideLateralM, "m",
            "kamera kontrolna na sąsiednim torze (−4,20 m to rozstaw torów profilu box_double); pokazuje skład z boku razem ze ścianą tunelu"),
        new ViewAssumption(nameof(OutsideHeightM), OutsideHeightM, "m",
            "wysokość kamery kontrolnej; jak wyżej"),
        new ViewAssumption(nameof(InspectStandoffM), InspectStandoffM, "m",
            "wyprowadzone: 5,90 / (2·tan 35°) = 4,2130 m wypełnia kadr dokładnie, zapas 1,50×"),
        new ViewAssumption(nameof(InspectHeightM), InspectHeightM, "m",
            "środek przekroju box_double: (−1,20 + 4,70) / 2 — kadr na rurze, nie na główce szyny"),
        new ViewAssumption(nameof(InspectLateralM), InspectLateralM, "m",
            "na osi tunelu, żeby niesymetryczność geometrii czytała się jako niesymetryczność"),
        new ViewAssumption(nameof(ControlNotchRatePerSecond), ControlNotchRatePerSecond, "1/s",
            "tempo przestawiania nastawnika; czułość sterowania jest decyzją o obsłudze, nie parametrem M7"),
        new ViewAssumption(nameof(TrackOffsetM), TrackOffsetM, "m",
            "oś toru względem osi trasy; wartość z profiles.py (design), a wybór prawego toru nie ma źródła — ACTU_LIGNES_BRUTES to trasa handlowa, nie geometria tor-po-torze"),
        new ViewAssumption(nameof(StationStopWindowM), StationStopWindowM, "m",
            "okno rozpoznania stacji, nie dokładność zatrzymania; ta sama liczba co LineRunSettings.StopWindowM w T-401, a górne ograniczenie to połowa peronu 95,0 m, czyli 47,5 m — 5,0 m to 10,5 % tej połowy"),
        new ViewAssumption(nameof(PassengerExchangeSeconds), PassengerExchangeSeconds, "s",
            "wymiana pasażerów; brak źródła (T-312), T-113 ogranicza od góry do 10,5 s przy medianowym postoju 19 s"),
        new ViewAssumption(nameof(LineBrakeUsageFraction), LineBrakeUsageFraction, "-",
            "ułamek hamulca służbowego, przy którym autopilot --line zaczyna hamować; brak źródła, ta sama liczba co przejazd referencyjny T-401"),
        new ViewAssumption(nameof(HeadlightRangeM), HeadlightRangeM, "m",
            "zasięg reflektora; parametr oświetlenia sceny, nie dane o taborze"),
        new ViewAssumption(nameof(HeadlightEnergy), HeadlightEnergy, "-",
            "jasność reflektora; jak wyżej"),
    };
}
