using System;
using System.Globalization;
using Godot;

namespace MetroBxl.Game.World;

/// <summary>
/// Odpowiedź na jedno pytanie: czy widok goniący da się w tej chwili pokazać, a jeśli
/// nie — od kiedy.
/// </summary>
/// <param name="Available">Czy widok goniący jest dostępny.</param>
/// <param name="FromChainageM">
/// Kilometraż czoła, PO MINIĘCIU którego widok się otwiera — sama ta liczba należy
/// jeszcze do pasma ukrycia. Do 6.B43 była równa długości składu; dziś jest to
/// `max(długość składu, próg odsłonięcia)` — patrz <see cref="ChaseCameraAim.Availability"/>.
/// </param>
/// <param name="RemainingM">Ile jeszcze metrów do tego kilometrażu; zero, gdy dostępny.</param>
/// <param name="TrainLengthM">
/// Długość składu — potrzebna do NAZWANIA POWODU, nie do policzenia granicy.
/// Doszła 09.09.2026 razem z progiem odsłonięcia (6.B43), bo od tej pozycji pasmo
/// ukrycia ma dwie części o dwóch różnych powodach: do długości składu kamera
/// naprawdę siedzi w skorupie, a dalej widok jest ukryty DECYZJĄ właściciela.
/// Jedno zdanie dla obu byłoby na jednej z nich nieprawdziwe — a to jest zdanie,
/// które czyta człowiek w HUD-zie i w odmowie zrzutu.
/// </param>
public readonly record struct ChaseAvailability(
    bool Available,
    double FromChainageM,
    double RemainingM,
    double TrainLengthM)
{
    /// <summary>
    /// Zdanie dla HUD-u i dla odmowy zrzutu; puste, gdy widok jest dostępny.
    ///
    /// <para>Treść jest TUTAJ, a nie w <c>FirstRun</c>, z tego samego powodu, dla
    /// którego tutaj jest arytmetyka kadru: <c>dotnet test</c> nie uruchamia silnika,
    /// więc napis złożony w węźle sceny nie ma jak dostać testu. Jedno źródło zdania
    /// znaczy też, że wiersz HUD-u i komunikat odmowy nie mogą podać dwóch różnych
    /// kilometraży.</para>
    ///
    /// <para><b>„po minięciu", nie „od".</b> Granica należy do pasma ukrycia, więc
    /// zdanie „dostępny od 94,0 m" byłoby na kilometrażu 94,0 m odmową i obietnicą
    /// naraz. „Jeszcze 0,0 m" z tego samego powodu nie jest dopisywane — przy czole
    /// dokładnie na granicy nie brakuje żadnej wielkości, którą da się wypisać
    /// z jednym miejscem po przecinku, a napis „jeszcze 0,0 m" czytałoby się jak
    /// usterka.</para>
    /// </summary>
    public string Reason
    {
        get
        {
            if (Available)
            {
                return string.Empty;
            }

            var ile = RemainingM > 0.0
                ? string.Create(CultureInfo.InvariantCulture, $", jeszcze {RemainingM:F1} m")
                : string.Empty;
            // POWÓD ZALEŻY OD CZĘŚCI PASMA i to jest zmierzone, nie stylistyczne.
            // Drugi powód jest KRÓTKI świadomie: `FirstRun` dokleja do odmowy zrzutu
            // własny ogon („kadr byłby płytą pudła, a plik nazywałby się chase"), więc
            // opis kadru w obu miejscach czytał się jak zająknięcie.
            // Do 09.09.2026 zdanie mówiło „kamera siedzi w skorupie składu" na całym
            // paśmie, bo pasmo kończyło się na długości składu. Po odsunięciu granicy
            // na 110 m to samo zdanie byłoby na 96..110 m nieprawdziwe: kamera jest
            // już za ogonem (zmierzone: przy czole 100 m odstęp wynosi 6,0 m), a widok
            // jest ukryty decyzją właściciela z 07.09.2026.
            var powod = FromChainageM > TrainLengthM && RemainingM < FromChainageM - TrainLengthM
                ? "pasmo ukrycia z decyzji właściciela"
                : "kamera siedzi w skorupie składu";
            return string.Create(
                CultureInfo.InvariantCulture,
                $"widok chase niedostępny — {powod}; "
                + $"dostępny po minięciu {FromChainageM:F1} m{ile}");
        }
    }
}

/// <summary>
/// Kadr kamery goniącej: kilometraż kamery, kilometraż celu i to, czy oś ma je czym
/// rozdzielić.
/// </summary>
/// <param name="CameraChainageM">Kilometraż kamery, już przycięty do osi.</param>
/// <param name="TargetChainageM">Kilometraż punktu, na który kamera patrzy.</param>
/// <param name="FrontChainageM">Kilometraż czoła składu, przycięty do osi.</param>
/// <param name="TrainLengthM">Długość składu.</param>
public readonly record struct ChaseFraming(
    double CameraChainageM,
    double TargetChainageM,
    double FrontChainageM,
    double TrainLengthM)
{
    /// <summary>Kilometraż ogona składu; ujemny, dopóki cały skład nie wjedzie na oś.</summary>
    public double RearChainageM => FrontChainageM - TrainLengthM;

    /// <summary>
    /// Czy kilometraż kamery mieści się w kilometrażu zajętym przez skład.
    ///
    /// <para>Kamera goniąca stoi na osi toru (<c>CabEyeLateralM</c> = 0 m) na wysokości
    /// <c>ChaseHeightM</c> = 2,60 m, a dach M7 jest 3,60 m nad główką szyny — więc
    /// pokrycie kilometrażu znaczy tu wprost „kamera siedzi w skorupie składu".
    /// Ten predykat NIE zmienia kadru; jest po to, żeby pozycja 6.B11 z
    /// <c>docs/TASKS.md</c> („kamera obserwacyjna siedzi wewnątrz geometrii przez
    /// pierwsze ~106 m") była twierdzeniem, które da się zmierzyć testem, a nie
    /// liczbą przepisywaną z cudzego raportu. Zmierzone 04.09.2026: okno to
    /// <b>0..94 m</b>, czyli długość składu, a nie 106 m — bo od 94 m ogon jest już
    /// na osi i kamera przyciśnięta do zera stoi ZA nim, tylko bliżej niż 12 m.</para>
    /// </summary>
    public bool CameraWithinTrainSpan =>
        CameraChainageM >= RearChainageM && CameraChainageM <= FrontChainageM;
}

/// <summary>
/// Celowanie kamery goniącej — cała decyzja o kadrze, bez ani jednego wywołania
/// silnika.
///
/// <para><b>Po co ta klasa istnieje.</b> <c>Node3D.LookAtFromPosition</c> potrzebuje
/// kierunku, a kierunek pionowy albo zerowy go nie ma: Godot wypisuje wtedy
/// <c>WARNING: Target and up vectors are colinear</c> i obraca kamerę o kąt, którego
/// nikt nie wybrał. Zmierzone 04.09.2026 na <c>--line --limit-kmh=70</c>:
/// <b>10 takich ostrzeżeń na przebieg</b>, jedno z <c>_Ready</c> i dziewięć
/// z <c>_Process</c>, wszystkie z <c>FirstRun.PlaceEverything</c>. Przyczyna jest
/// arytmetyczna: przy kilometrażu czoła ≤ 47 m kamera (przycięta do 0 m) i cel
/// (środek składu, też przycięty do 0 m) wypadają w TYM SAMYM punkcie osi
/// i różnią się wyłącznie wysokością — 2,60 m wobec 1,80 m. Odcinek między nimi jest
/// wtedy pionowy, czyli równoległy do „w górę".</para>
///
/// <para><b>Co robi zamiast tego.</b> To samo, co <see cref="SceneAxis.CabPoint"/>
/// robi dla kamery kabinowej i z tego samego powodu: kamera bez zdefiniowanego celu
/// patrzy <b>wzdłuż osi</b>, bo innej prawdy o kierunku w tym miejscu nie ma,
/// a zmyślona byłaby gorsza od wziętej z cięciwy. Wyciszenie ostrzeżenia
/// (<c>LookAtFromPosition</c> z innym „w górę") dałoby ten sam nieokreślony obrót,
/// tylko bez wpisu w logu.</para>
///
/// <para><b>Gdzie jest decyzja.</b> Nie w <c>FirstRun</c>. Ta sama droga, którą
/// przeszły <see cref="TrainLayout"/> i <see cref="PlatformFit"/> po audycie
/// mutacyjnym: <c>dotnet test</c> nie jest silnikiem, więc kod trzymany w węźle sceny
/// nie ma jak dostać testu jednostkowego. <see cref="Vector3"/> jest strukturą
/// zarządzaną z GodotSharp i liczy się bez uruchomionego silnika, więc cała
/// arytmetyka wchodzi tutaj, a <c>PlaceEverything</c> zostaje cienkie.</para>
/// </summary>
public static class ChaseCameraAim
{
    /// <summary>
    /// Najkrótszy odcinek kamera–cel, który jeszcze niesie kierunek [m].
    ///
    /// <para>Poniżej tego progu odcinek jest punktem i kierunku nie ma wcale — to jest
    /// osobny przypadek od „odcinek pionowy", bo wektor zerowy nie ma też czego
    /// znormalizować.</para>
    /// </summary>
    public const float MinAimM = 1e-4f;

    /// <summary>
    /// Najmniejszy sinus kąta między kierunkiem patrzenia a pionem, przy którym kierunek
    /// jest jeszcze użyteczny.
    ///
    /// <para>Próg jest <b>celowo dużo wyższy</b> niż ten, przy którym ostrzega Godot.
    /// Godot bada <c>up × kierunek</c> swoim <c>CMP_EPSILON</c> na KWADRACIE długości,
    /// więc ostrzega jeszcze przy sinusie rzędu 3·10⁻³; gdyby ta stała była równa
    /// epsilonowi silnika, bramka <c>tools/ci/assert_no_godot_warnings.py</c> łapałaby
    /// wąskie pasmo kilometraży tuż nad granicą. 10⁻² to 0,57° od pionu — kadr goniący
    /// ma nominalnie 59 m wybiegu poziomego na 0,80 m różnicy wysokości, czyli 0,8°
    /// od POZIOMU, więc ten próg nie ma jak zabrać ani jednego prawdziwego celu.</para>
    /// </summary>
    public const float ColinearSine = 1e-2f;

    /// <summary>
    /// Kilometraż kamery i celu dla składu, którego czoło stoi w
    /// <paramref name="frontChainageM"/>.
    ///
    /// <para>Kamera stoi <paramref name="behindM"/> za ogonem, cel jest w połowie
    /// składu. Oba kilometraże są przycięte do osi, bo poza nią nie ma z czego zbudować
    /// ramki toru — i to przycięcie jest źródłem całej degeneracji: dopóki czoło nie
    /// minie połowy składu, oba wychodzą zerem.</para>
    /// </summary>
    public static ChaseFraming Frame(
        double frontChainageM, double trainLengthM, double axisLengthM, double behindM)
    {
        if (trainLengthM < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(trainLengthM), trainLengthM, "skład nie ma ujemnej długości");
        }

        if (axisLengthM <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(axisLengthM), axisLengthM, "oś bez długości nie niesie kadru");
        }

        var front = Math.Clamp(frontChainageM, 0.0, axisLengthM);
        var camera = Math.Clamp(front - trainLengthM - behindM, 0.0, axisLengthM);
        var target = Math.Clamp(front - (trainLengthM * 0.5), 0.0, axisLengthM);
        return new ChaseFraming(camera, target, front, trainLengthM);
    }

    /// <summary>
    /// Czy widok goniący jest dostępny przy czole składu w
    /// <paramref name="frontChainageM"/>, a jeśli nie — od kiedy będzie.
    ///
    /// <para><b>Decyzja właściciela z 05.09.2026:</b> widok <c>chase</c> jest
    /// NIEDOSTĘPNY, dopóki cały skład nie wjedzie na oś. Nie „przyciągany do
    /// minimalnego kilometraża" i nie pokazywany mimo wszystko — niedostępny, i
    /// mówiący o tym wprost. Powodem jest to, co widać na zrzutach z pasma:
    /// kamera przyciśnięta przycięciem do początku osi stoi WEWNĄTRZ skorupy M7
    /// i kadr jest płytą pudła z bliska. Zmierzone 05.09.2026 na
    /// <c>--line --limit-kmh=70</c>, ułamek pikseli o jasności &gt; 0,80 w górnych
    /// 60 % kadru: 20 m → 0,1 %, 48 m → <b>56,4 %</b>, 50 m → <b>38,3 %</b>,
    /// 90 m → 0,0 %, 2000 m → 0,0 %.</para>
    ///
    /// <para><b>SKĄD GRANICA — PRZEPISANE 09.09.2026 (6.B43), a nie dopisane obok.</b>
    /// Do tej pozycji granicą była sama <paramref name="trainLengthM"/> („cały skład
    /// na osi") i predykat był tożsamy z
    /// <see cref="ChaseFraming.CameraWithinTrainSpan"/>. Dziś granicą jest
    /// <c>max(trainLengthM, revealFromM)</c>, więc te dwa twierdzenia
    /// <b>przestały być tożsame</b> i to jest napisane, a nie przemilczane: kamera
    /// wychodzi ze skorupy przy 94,0 m, ale kadr jest płytą pudła jeszcze na 96 m.
    /// Zmierzone 09.09.2026, dziewięć punktów co 2 m, ułamek pikseli o jasności
    /// &gt; 0,80 w górnych 60 % kadru: 96 m → <b>46,67 %</b>, 98 m → 0,00 %,
    /// 100..112 m → 0,00 % na każdym punkcie. Punktów jest dziewięć, a nie dwanaście,
    /// bo 90, 92 i 94 m odmawiają zrzutu kodem 13 — granica NALEŻY do pasma ukrycia,
    /// więc pasma 90..94 m nie da się zmierzyć narzędziem, które samo jest tą regułą.
    /// Właściciel wybrał 07.09.2026 <b>110 m</b>, czyli o 12 m ostrożniej, niż każe
    /// pomiar — liczba jest decyzją, nie wynikiem, i tak jest zapisana
    /// w <c>DesignAssumptions.ChaseRevealFromM</c>. Pełne <c>ChaseBehindM</c> odstępu
    /// wraca przy 106 m i to zostaje prawdą o kadrze, nie o dostępności.</para>
    /// <para><b>Granica NALEŻY do pasma ukrycia</b> i to zostaje bez zmian: na
    /// kilometrażu dokładnie równym granicy widok jest jeszcze niedostępny. Przy
    /// starej granicy powód był geometryczny (ogon leżał dokładnie na przyciętej
    /// kamerze); przy nowej jest ten sam co przy każdym progu — „po minięciu" znaczy
    /// ostro większe, a zdanie „dostępny od 110,0 m" byłoby na 110,0 m odmową
    /// i obietnicą naraz.</para>
    ///
    /// <para><b>Pasmo 94..110 m nie jest już odsłonięte</b> — i to jest różnica wobec
    /// stanu z 05.09.2026, kiedy zostało odsłonięte świadomie, z wpisem w „Czego agent
    /// nie ruszy bez decyzji". Decyzja z 07.09.2026 to pasmo domknęła.</para>
    /// </summary>
    /// <param name="frontChainageM">Kilometraż czoła składu.</param>
    /// <param name="trainLengthM">Długość składu [m].</param>
    /// <param name="revealFromM">
    /// Kilometraż odsłonięcia z <c>DesignAssumptions.ChaseRevealFromM</c> — decyzja
    /// właściciela, podawana z zewnątrz tak samo jak <c>ChaseBehindM</c> do
    /// <see cref="Frame"/>. Parametr jest WYMAGANY, bez wartości domyślnej: domyślna
    /// równa długości składu przywróciłaby po cichu stan sprzed 6.B43 w każdym
    /// miejscu, które o nią nie zapyta.
    /// </param>
    public static ChaseAvailability Availability(
        double frontChainageM, double trainLengthM, double revealFromM)
    {
        if (trainLengthM < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(trainLengthM), trainLengthM, "skład nie ma ujemnej długości");
        }

        if (revealFromM < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(revealFromM), revealFromM, "kilometraż odsłonięcia nie jest ujemny");
        }

        // MAKSIMUM, nie sama decyzja: gdyby kiedyś skład był dłuższy niż próg, granicą
        // musi zostać długość składu — inaczej kamera wróciłaby do wnętrza skorupy,
        // czyli do usterki, którą zamknęła decyzja z 05.09.2026. Próg odsłonięcia
        // odsuwa granicę DALEJ, nigdy bliżej.
        var granica = Math.Max(trainLengthM, revealFromM);
        return new ChaseAvailability(
            frontChainageM > granica,
            granica,
            Math.Max(0.0, granica - frontChainageM),
            trainLengthM);
    }

    /// <summary>
    /// Sam predykat: czy widok goniący jest dostępny. Szczegóły i pomiary przy
    /// <see cref="Availability"/>.
    /// </summary>
    /// <param name="frontChainageM">Kilometraż czoła składu.</param>
    /// <param name="trainLengthM">Długość składu [m].</param>
    /// <param name="revealFromM">Kilometraż odsłonięcia; patrz <see cref="Availability"/>.</param>
    public static bool IsAvailable(double frontChainageM, double trainLengthM, double revealFromM)
        => Availability(frontChainageM, trainLengthM, revealFromM).Available;

    /// <summary>
    /// Czy odcinek <paramref name="aim"/> niesie kierunek nadający się dla
    /// <c>LookAtFromPosition</c> przy pionie <paramref name="up"/>.
    ///
    /// <para>Dwa powody odmowy i oba są tu osobno, bo mają osobne progi: odcinek za
    /// krótki, żeby go znormalizować, i odcinek równoległy do pionu.</para>
    /// </summary>
    public static bool IsDegenerate(Vector3 aim, Vector3 up)
    {
        var length = aim.Length();
        if (length < MinAimM)
        {
            return true;
        }

        var upLength = up.Length();
        if (upLength < MinAimM)
        {
            return true;
        }

        return (aim / length).Cross(up / upLength).Length() < ColinearSine;
    }

    /// <summary>
    /// Punkt, na który kamera stojąca w <paramref name="cameraPosition"/> ma patrzeć:
    /// <paramref name="targetPosition"/>, a gdy ten kierunek jest zdegenerowany —
    /// punkt o metr do przodu wzdłuż osi.
    ///
    /// <para><paramref name="axisForward"/> jest styczną cięciwy z
    /// <see cref="SceneAxis.CabPoint"/>, czyli wektorem jednostkowym wzdłuż toru.
    /// Odpowiedź zastępcza jest tym samym, co dostaje kamera kabinowa
    /// (<c>eye + forward</c>), więc obie kamery w tym samym miejscu patrzą w tę samą
    /// stronę.</para>
    /// </summary>
    public static Vector3 LookTarget(
        Vector3 cameraPosition, Vector3 targetPosition, Vector3 axisForward, Vector3 up)
        => IsDegenerate(targetPosition - cameraPosition, up)
            ? cameraPosition + axisForward
            : targetPosition;
}
