using System;
using System.Text.Json;

namespace MetroBxl.Sim;

/// <summary>
/// Wejście do <c>System.Text.Json</c> dla loaderów czytających pliki podane przez
/// użytkownika.
/// </summary>
/// <remarks>
/// <para><b>Po co to istnieje.</b> <c>JsonDocument.Parse</c> przy zepsutej składni
/// rzuca <c>JsonReaderException</c> (po <c>JsonException</c>, po <c>Exception</c>),
/// a <b>żaden</b> filtr <c>catch</c> w tym repozytorium takiego typu nie wymienia:
/// ani wspólny handler w <c>Sim.Runner.Program.Main</c> (<c>IOException</c>,
/// <c>ArgumentException</c>, <c>FormatException</c>, <c>InvalidOperationException</c>),
/// ani filtry w <c>FirstRun.ReadSignallingPlan</c> i <c>ReadInputLog</c>
/// (<c>ArgumentException</c>, <c>FormatException</c>). Zmierzone 17.09.2026 (6.D229):
/// <c>dotnet run -- axis --axis &lt;plik z `{{{`&gt;</c> kończy się kodem <b>134</b>,
/// angielskim komunikatem .NET-a i stosem wywołań — zamiast polskim wierszem odmowy.
/// To ta sama rodzina co 6.A12 (<c>KeyNotFoundException</c>, kod 134 i stos),
/// domknięta wtedy dla <c>GetProperty</c> przez <c>SignallingPlan.Required</c>,
/// ale <b>samo parsowanie nigdy nie zostało owinięte</b>.</para>
/// <para><b>Dlaczego tu, a nie w filtrach.</b> Filtrów jest trzy, a miejsc, w których
/// wyjątek parsera przecieka — trzynaście; dwa z nich (<c>FirstRun</c>: oś i manifest
/// chunków) nie mają <c>try</c> w ogóle, więc dopisanie <c>JsonException</c> do filtrów
/// zostawiłoby je nietknięte. Dopisanie do filtru nie daje też komunikatu po polsku:
/// przepisany zostałby <c>error.Message</c> .NET-a. Owinięcie w źródle robi jedno i
/// drugie dla każdego wywołania naraz, a <c>FormatException</c> jest typem, który
/// wszystkie trzy filtry <b>już</b> łapią — więc żaden kod wyjścia się nie zmienia.</para>
/// </remarks>
public static class JsonText
{
    /// <summary>
    /// <c>JsonDocument.Parse</c> z odmową po polsku zamiast wyjątku parsera.
    /// </summary>
    /// <param name="json">Treść pliku.</param>
    /// <param name="what">Czym plik miał być — wchodzi wprost do komunikatu.</param>
    /// <exception cref="FormatException">Gdy treść nie jest poprawnym JSON-em.</exception>
    public static JsonDocument Parse(string json, string what)
    {
        ArgumentNullException.ThrowIfNull(json);

        try
        {
            return JsonDocument.Parse(json);
        }
        catch (JsonException error)
        {
            throw new FormatException(Refusal(what, error.LineNumber, error.BytePositionInLine), error);
        }
    }

    /// <summary>
    /// Wiersz odmowy zepsutej składni — po polsku, z pozycją błędu i <b>bez</b> tekstu
    /// parsera (6.D357).
    /// </summary>
    /// <remarks>
    /// <para><b>Dlaczego bez <c>error.Message</c>.</b> Do 6.D357 odmowa doklejała zdanie
    /// .NET-a, więc gracz czytał na przykład <c>oś trasy nie jest poprawnym JSON-em:
    /// '{' is an invalid start of a property name. Expected a '"'. LineNumber: 0 |
    /// BytePositionInLine: 1.</c> Jedyną informacją z tego zdania, której nie ma
    /// początek po polsku, jest <b>pozycja</b> — a ta stoi w wyjątku jako liczby
    /// (<c>LineNumber</c>, <c>BytePositionInLine</c>), więc da się ją podać bez
    /// przepisywania tekstu parsera. Sam wyjątek parsera zostaje jako
    /// <c>InnerException</c>, więc nic nie ginie dla kogoś, kto czyta stos.</para>
    /// <para><b>Liczone od 1, a nie od 0.</b> Obie liczby .NET podaje od zera; edytor,
    /// w którym gracz otworzy plik, numeruje wiersze od jedynki. Przepisanie zera
    /// wprost wskazałoby wiersz o jeden za wcześnie.</para>
    /// <para><b>Bajt, nie znak.</b> <c>BytePositionInLine</c> liczy bajty UTF-8, więc
    /// w wierszu z polską literą przed błędem różni się od numeru kolumny edytora.
    /// Komunikat mówi „bajt”, żeby nie obiecywać kolumny.</para>
    /// </remarks>
    private static string Refusal(string what, long? lineNumber, long? bytePositionInLine)
        => lineNumber is { } line && bytePositionInLine is { } position
            ? $"{what} nie jest poprawnym JSON-em: błąd składni w wierszu {line + 1}, bajt {position + 1}"
            : $"{what} nie jest poprawnym JSON-em: błąd składni bez podanej pozycji";
}
