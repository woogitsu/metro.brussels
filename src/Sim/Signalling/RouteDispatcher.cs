using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Signalling;

/// <summary>
/// Nastawnia automatyczna: zamawia składowi trasę na następny odcinek międzystacyjny.
///
/// <para><b>Po co to istnieje.</b> Do 04.09.2026 <b>nikt w tym repozytorium nie ryglował
/// tras</b>. <see cref="FixedBlockSystem"/> potrafi je zaryglować i sam je zwalnia, gdy
/// czoło wejdzie do bloku docelowego, ale zamówienie musi przyjść z zewnątrz — a jedyne
/// miejsce, w którym przychodziło, była PRYWATNA KLASA W TEŚCIE
/// (<c>ClassicSignallingScenarioTests.Runner</c>). Zmierzone na prawdziwym planie
/// pakietu A (<c>data/design/signalling/classic-2026.json</c>, <c>RequireRoute = true</c>):
/// <see cref="Line.LineCore"/> z jednym składem <b>nie ruszał</b> — autorytet miał 47,00 m
/// z powodem <see cref="AuthorityLimit.BlockNotReserved"/>, więc skład dojeżdżał do 46,7 m
/// i stawał. Zdanie „linia jest symulacją, która działa bez gracza" nie było więc pod
/// sygnalizacją prawdziwe.</para>
///
/// <para><b>Cała reguła, w jednym zdaniu:</b> skład bez zaryglowanej trasy zamawia trasę
/// wychodzącą z bloku peronowego, w którym stoi jego czoło. Nic więcej — zwalnianie należy
/// do <see cref="FixedBlockSystem"/>, wybór trasy do <see cref="SignallingPlan.NextRouteFrom"/>,
/// a jazda do prowadzenia. Ta klasa nie liczy ani jednej siły i nie zna prędkości.</para>
///
/// <para><b>Żądanie idzie RAZ NA SEKUNDĘ, nie co krok.</b> Odmowa jest normalną odpowiedzią
/// — blok przed nosem bywa zajęty i wtedy sygnał ma stać na stój — a każde żądanie i każda
/// odmowa trafiają do strumienia zdarzeń (<see cref="SignallingEvent"/>). Pytanie 120 razy
/// na sekundę zalałoby ten strumień niczym.</para>
///
/// <para><b>Liczba odmów NIE JEST faktem o sieci</b> i nie wolno jej tak cytować.
/// Poprzednia wersja tego akapitu mówiła „dwa składy na pakiecie A dają 3050 odmów",
/// a komentarz przy teście odstępu mówił w tym samym czasie 1118 i 158 — trzy liczby
/// o tej samej rzeczy. Żadna nie była błędem pomiaru: to były trzy różne budżety pętli.
/// Po zakleszczeniu linii (drugi skład staje przed zajętym peronem końcowym, bo model
/// nie zna zawracania) pytanie trwa w nieskończoność, więc licznik rośnie tak długo,
/// jak długo ktoś kręci zegarem. Zmierzone na pakiecie A, dwa składy, odstęp wyjazdu
/// 30 s: <b>155</b> odmów po 60 000 krokach, <b>451</b> po 120 000, <b>951</b> po
/// 180 000, <b>2451</b> po 360 000.</para>
///
/// <para><b>Faktem o dławiku jest TEMPO, nie suma.</b> W zakleszczeniu przyrost wynosi
/// dokładnie <b>500 odmów na 60 000 kroków, czyli jedną na sekundę</b> — tyle, ile
/// wynosi odstęp. Przy pytaniu co krok byłoby ich 120 razy więcej. Ta własność jest
/// przybita testem <c>Po_zakleszczeniu_odmowy_rosna_dokladnie_w_tempie_odstepu</c>,
/// bo tempo da się sprawdzić bez wybierania budżetu, a suma nie.</para>
///
/// <para><b>Przy planie, który nie wymaga tras</b> (<see cref="SignallingPlan.RequireRoute"/>
/// równe <c>false</c>) dyspozytor <b>nie robi nic</b>, i to nie jest optymalizacja.
/// Autorytet nie zależy wtedy od rezerwacji, więc zaryglowanie trasy nie odblokowałoby
/// niczego, a <b>odebrałoby</b> pojemność: rezerwacja odrzuca cudze żądania i skraca
/// cudzy autorytet. Ryglowanie trasy, której nikt nie wymaga, byłoby więc szkodą, nie
/// ostrożnością.</para>
/// </summary>
public sealed class RouteDispatcher
{
    /// <summary>
    /// Domyślny odstęp między żądaniami tego samego składu: jedna sekunda symulacji.
    /// </summary>
    public const long DefaultRequestIntervalSteps = FixedStep.SimulationHertz;

    private readonly SignallingPlan _plan;
    private readonly long _intervalSteps;
    private readonly Dictionary<string, long> _lastRequestStep = new(StringComparer.Ordinal);

    /// <summary>Nastawnia dla zadanego planu.</summary>
    /// <param name="plan">Plan sygnalizacji; z niego bierze się wybór trasy.</param>
    /// <param name="requestIntervalSteps">
    /// Ile kroków musi minąć między dwoma żądaniami tego samego składu. Zero i wartości
    /// ujemne są odmową, nie „pytaj zawsze": odstęp zerowy zalałby strumień zdarzeń,
    /// a to jest jedyny zapis tego, co robiła sygnalizacja.
    /// </param>
    public RouteDispatcher(SignallingPlan plan, long requestIntervalSteps = DefaultRequestIntervalSteps)
    {
        ArgumentNullException.ThrowIfNull(plan);
        if (requestIntervalSteps <= 0L)
        {
            throw new ArgumentOutOfRangeException(
                nameof(requestIntervalSteps), requestIntervalSteps,
                "Odstęp między żądaniami trasy musi być dodatni.");
        }

        _plan = plan;
        _intervalSteps = requestIntervalSteps;
    }

    /// <summary>Plan, dla którego ta nastawnia rygluje.</summary>
    public SignallingPlan Plan => _plan;

    /// <summary>Odstęp między żądaniami tego samego składu, w krokach.</summary>
    public long RequestIntervalSteps => _intervalSteps;

    /// <summary>Ile tras udało się zaryglować.</summary>
    public int Locked { get; private set; }

    /// <summary>Ile żądań odrzucono. Odmowa jest normalną odpowiedzią, nie usterką.</summary>
    public int Refused { get; private set; }

    /// <summary>
    /// Jeden krok nastawni dla jednego składu. Zwraca prawdę, gdy trasa została
    /// zaryglowana **w tym wywołaniu**.
    /// </summary>
    /// <param name="system">Sygnalizacja, w której skład jest zarejestrowany.</param>
    /// <param name="trainId">Skład.</param>
    /// <param name="frontChainageM">Kilometraż czoła składu.</param>
    /// <param name="steps">Numer kroku zegara — z niego liczy się odstęp żądań.</param>
    public bool Dispatch(FixedBlockSystem system, string trainId, double frontChainageM, long steps)
    {
        ArgumentNullException.ThrowIfNull(system);
        ArgumentNullException.ThrowIfNull(trainId);

        if (!_plan.RequireRoute || system.RouteOf(trainId) is not null)
        {
            return false;
        }

        if (_lastRequestStep.TryGetValue(trainId, out var last) && steps - last < _intervalSteps)
        {
            return false;
        }

        if (_plan.NextRouteFrom(frontChainageM) is not Route next)
        {
            // Za ostatnim peronem nie ma dokąd ryglować. Nie jest to usterka: skład
            // dojechał do końca planu i autorytet kończy się na `EndOfLine`.
            return false;
        }

        _lastRequestStep[trainId] = steps;
        if (system.RequestRoute(next.Id, trainId))
        {
            Locked++;
            return true;
        }

        Refused++;
        return false;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        var bezczynna = _plan.RequireRoute ? string.Empty : " (plan nie wymaga tras — bezczynna)";
        return string.Create(
            CultureInfo.InvariantCulture,
            $"nastawnia: {Locked} tras zaryglowanych, {Refused} odmów, żądanie co {_intervalSteps} kroków{bezczynna}");
    }
}
