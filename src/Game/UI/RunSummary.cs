using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using MetroBxl.Game.Input;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game.UI;

/// <summary>
/// Panel wyniku sesji treningowej — to, co gracz widzi, kiedy przejazd się skończy,
/// <b>bez zamykania aplikacji</b> (punkt 4 odbioru M1).
///
/// <para><b>Dlaczego to jest osobny plik BEZ GODOTA.</b> Ta sama decyzja i ten sam
/// powód, co przy <see cref="MetroBxl.Game.RunHeader"/>, <see cref="MetroBxl.Game.RunPlan"/>
/// i <see cref="MetroBxl.Game.RunReset"/>: panel jest tekstem złożonym z liczb wyniku,
/// a złożenie liczb da się sprawdzić testem jednostkowym tylko wtedy, gdy nie wymaga
/// uruchomionego silnika. Scenie zostaje jedna etykieta i ani jedna decyzja.</para>
///
/// <para><b>Ani jednej liczby liczonej tutaj.</b> Wszystko przychodzi
/// z <see cref="TrainingResult"/>, czyli z obiektu, który prowadził sesję. Ta sama
/// reguła co w <c>RunHeader</c>, i ten sam powód: liczba w panelu, która nie jest
/// wynikiem niczego, nie ma czego porównać i rozjeżdża się po cichu.</para>
///
/// <para><b>Słowa przychodzą z <see cref="UiText"/>, klawisze z
/// <see cref="DriverActions"/>.</b> Panel mówiący „naciśnij R" byłby drugą kopią
/// przypisania klawiszy — a przypisanie już raz się w tym projekcie rozjechało
/// (`play.sh`, MB-01 §10). Tutaj nazwa klawisza przychodzi z tej samej tabeli, którą
/// czyta <c>InputMap</c>.</para>
/// </summary>
public static class RunSummary
{
    /// <summary>
    /// Panel wyniku jako tekst wielowierszowy. Kultura niezmienna, żeby wyjście nie
    /// zależało od maszyny — tak samo jak w <see cref="TrainingResult.ToString"/>.
    /// </summary>
    /// <param name="result">Wynik sesji.</param>
    /// <returns>Gotowy tekst etykiety.</returns>
    public static string Compose(TrainingResult result)
    {
        var panel = new StringBuilder();
        panel.AppendLine(Naglowek(result.Ending));
        panel.AppendLine(UiText.Format(
            "summary.targets", result.TargetsServed, result.Targets.Count));

        foreach (var target in result.Targets)
        {
            // `StopErrorM` jest `double?`, a nie `NaN`, i tutaj widać po co: cel
            // pominięty NIE MA błędu zatrzymania, a nie „ma błąd, którego nie da się
            // porównać". `NaN` wszedłby tu w szablon jako słowo „NaN" i wyglądał
            // jak zmierzona wartość.
            panel.AppendLine(target.StopErrorM is { } blad
                ? UiText.Format(
                    "summary.target.served",
                    target.DisplayName,
                    blad.ToString("+0.000;-0.000;0.000", CultureInfo.InvariantCulture))
                : UiText.Format("summary.target.missed", target.DisplayName));
        }

        panel.AppendLine(UiText.Format(
            "summary.time",
            result.TotalSeconds.ToString("F1", CultureInfo.InvariantCulture),
            result.TotalDistanceM.ToString("F1", CultureInfo.InvariantCulture)));
        panel.AppendLine(UiText.Format(
            "summary.atp",
            result.AtpWarningEvents,
            result.AtpInterventionEvents,
            result.AtpEmergencyEvents));
        panel.Append(UiText.Format(
            "summary.again", KlawiszAkcji(DriverActions.Reset), KlawiszAkcji(DriverActions.Quit)));

        return panel.ToString();
    }

    /// <summary>
    /// Nagłówek panelu dla danego zakończenia.
    ///
    /// <para><b>Ramię domyślne RZUCA, a nie zwraca nazwy członu.</b> Ta sama decyzja, co
    /// w <c>UiText.Get</c> i z tego samego powodu (6.D83): panel wyświetlający
    /// <c>AllTargetsServed</c> wygląda na ekranie jak usterka tekstu i zostaje zgłoszony
    /// po dwóch dniach przez kogoś innego. <c>TrainingEnding.Running</c> też tu rzuca —
    /// panelu trwającej sesji nie ma, bo nie ma wyniku, który by go opisał
    /// (<see cref="TrainingSession.Result"/> jest wtedy <c>null</c>).</para>
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">Zakończenie nie ma nagłówka.</exception>
    private static string Naglowek(TrainingEnding ending) => ending switch
    {
        TrainingEnding.AllTargetsServed => UiText.Get("summary.passed"),
        TrainingEnding.TargetMissed => UiText.Get("summary.failed.missed"),
        _ => throw new ArgumentOutOfRangeException(
            nameof(ending), ending,
            "panel wyniku nie ma nagłówka dla tego zakończenia — nowy człon "
            + "`TrainingEnding` ma dostać wpis w katalogu tekstów w tym samym commicie"),
    };

    private static string KlawiszAkcji(string action)
    {
        foreach (var binding in DriverActions.All)
        {
            if (string.Equals(binding.Action, action, StringComparison.Ordinal))
            {
                return binding.KeyName;
            }
        }

        throw new KeyNotFoundException(
            $"`DriverActions.All` nie zna akcji `{action}` — panel wyniku obiecywałby "
            + "klawisz, którego `InputMap` nie ma");
    }
}
