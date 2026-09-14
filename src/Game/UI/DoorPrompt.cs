using MetroBxl.Sim.Train;

namespace MetroBxl.Game.UI;

/// <summary>
/// Pole wiersza HUD-u o drzwiach RĘCZNYCH: co gracz może z nimi teraz zrobić,
/// a jeśli jego ostatnie polecenie zostało odrzucone — dlaczego (MB-08).
///
/// <para><b>Dlaczego osobny plik BEZ GODOTA.</b> Ta sama decyzja i ten sam powód, co
/// przy <see cref="TractionBlock"/>, <c>SignallingHud</c>, <c>RunPlan</c>
/// i <c>RunHeader</c>: napis złożony ze stanu przejazdu da się sprawdzić testem
/// jednostkowym tylko wtedy, gdy nie wymaga uruchomionego silnika. Przy MB-03 kosztowało
/// to jedną kontrolę negatywną, która wyszła ZIELONA (KN-4: <c>Visible = true</c> nie
/// zapaliło niczego, bo stało w węźle Godota) — ten plik istnieje po to, żeby ta sama
/// luka nie powtórzyła się przy drzwiach.</para>
///
/// <para><b>Ten wiersz NICZEGO NIE ROZSTRZYGA O TRAKCJI</b> — pyta o nią
/// <see cref="DoorCycle.TractionAllowed"/>, czyli dokładnie ten sam predykat, którym
/// rdzeń zeruje nastawnik (<c>StationStop.Filter</c>). Sygnał gotowości do odjazdu
/// z pola „Wyjście" MB-08 jest więc zdaniem o tym predykacie, a nie drugim stanem
/// obok niego: napis „można odjechać" nie ma prawa pojawić się w kroku, w którym rdzeń
/// odjechać nie pozwoli.</para>
/// </summary>
public static class DoorPrompt
{
    /// <summary>
    /// Podpowiedź do wiersza drzwi: odmowa, jeśli ostatnie polecenie ją dostało,
    /// a w przeciwnym razie to, co wolno zrobić w tej fazie.
    ///
    /// <para><b>Odmowa ma PIERWSZEŃSTWO</b>, bo odpowiada na pytanie, które gracz
    /// właśnie zadał; podpowiedź odpowiada na pytanie, którego nie zadał jeszcze
    /// nikt. Kolejność jest tu treścią, a nie wygodą: odwrotna kazałaby graczowi
    /// zgadywać, czemu naciśnięcie klawisza nic nie dało.</para>
    /// </summary>
    /// <param name="phase">Faza cyklu drzwi w tym kroku.</param>
    /// <param name="refusal">Powód odmowy ostatniego polecenia; <c>null</c>, gdy przeszło.</param>
    /// <returns>Napis do wiersza HUD-u.</returns>
    public static string For(DoorPhase phase, DoorRefusal? refusal)
    {
        // Nazwa `powodOdmowy`, a nie `powod` — i jest to ROZSTRZYGNIĘCIE, nie gust.
        // `powod` jest już w `src/Game/` nazwą wartości wyliczeniowej (`ChaseCameraAim`),
        // a bramka dwuznacznych nazw z 6.D185 rozpoznaje je LEKSYKALNIE, po samej nazwie.
        // Drugie `powod` wciągnęłoby dziurę `{powod}` z `ChaseCameraAim` na listę dziur
        // z wyliczeniem na drodze `Hud.Update` — zmierzone: wywraca trzy bramki naraz,
        // z których ani jedna nie dotyczy drzwi.
        if (refusal is DoorRefusal powodOdmowy)
        {
            return UiText.Format("hud.doors.refused", Reason(powodOdmowy));
        }

        // NIE JEST TO `switch` po fazie i to jest wybór, nie skrót — powód w opisie klasy.
        // Ósma faza dopisana do `DoorPhase` wpadłaby w ramię domyślne po stronie
        // „skrzydła w ruchu" bez pytania kogokolwiek, czy tak jest; pytanie
        // o `TractionAllowed` odpowiada za nią tym samym zdaniem, co rdzeń.
        if (phase == DoorPhase.Open)
        {
            return UiText.Get("hud.doors.prompt-close");
        }

        return DoorCycle.TractionAllowed(phase)
            ? UiText.Get("hud.doors.ready")
            : UiText.Get("hud.doors.working");
    }

    /// <summary>
    /// Powód odmowy po polsku — z katalogu tekstów, klucz na wartość wyliczenia.
    ///
    /// <para>Ta sama granica i to samo ramię domyślne, co w <c>FirstRun.Faza</c>:
    /// <see cref="DoorRefusal"/> jest wyliczeniem RDZENIA, a rdzeń nie pisze na ekran
    /// gracza. Ramię domyślne oddaje angielską nazwę członu — widoczną i zgłaszalną —
    /// zamiast rzucać wyjątkiem w metodzie składającej wiersz HUD-u, bo wyjątek
    /// przewróciłby klatkę zamiast powiedzieć graczowi, czego nie umiemy nazwać.</para>
    ///
    /// <para><see cref="DoorRefusal.None"/> nie ma tu klucza i nie jest to przeoczenie:
    /// nie jest odmową. <see cref="For"/> dostaje wtedy <c>null</c>, a nie „brak
    /// powodu" — i właśnie dlatego argument jest typem dopuszczającym <c>null</c>.</para>
    /// </summary>
    /// <param name="refusal">Powód odmowy.</param>
    /// <returns>Zdanie dla gracza.</returns>
    public static string Reason(DoorRefusal refusal) => refusal switch
    {
        DoorRefusal.AutomaticControl => UiText.Get("hud.doors.refusal.automatic"),
        DoorRefusal.TrainMoving => UiText.Get("hud.doors.refusal.moving"),
        DoorRefusal.OutsidePlatformWindow => UiText.Get("hud.doors.refusal.outside"),
        DoorRefusal.DoorsAlreadyOpen => UiText.Get("hud.doors.refusal.already-open"),
        DoorRefusal.DoorsNotOpen => UiText.Get("hud.doors.refusal.not-open"),
        _ => refusal.ToString(),
    };
}
