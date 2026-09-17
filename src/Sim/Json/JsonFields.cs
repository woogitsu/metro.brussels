using System;
using System.Text.Json;

namespace MetroBxl.Sim.Json;

/// <summary>
/// Odczyt pola wymaganego z dokumentu JSON — jeden dla wszystkich czytników rdzenia
/// i warstwy silnika.
/// </summary>
/// <remarks>
/// Zmierzone 17.09.2026 przy 6.D233: gołych <c>JsonElement.GetProperty</c> jest
/// w <c>src/</c> <b>69</b>, z czego <b>50</b> w czterech czytnikach plików danych
/// (24 <c>ChunkManifest</c>, 13 <c>CbtcTestArea</c>, 10 <c>SignallingPlan</c>,
/// 3 <c>TrackAxis</c>). <c>GetProperty</c> rzuca <c>KeyNotFoundException</c>, której
/// wspólny handler <c>Sim.Runner</c> nie łapie (łapie <c>IOException</c>,
/// <c>ArgumentException</c>, <c>FormatException</c>, <c>InvalidOperationException</c>),
/// więc <c>axis --axis plik-o-treści-{}</c> kończył się <b>kodem 134</b> i stosem
/// zamiast komunikatem narzędzia.
///
/// Komunikat złapanego wyjątku ma mówić, <b>którego pola brakło</b> — to jedyna
/// informacja, po którą sięga ten, kto plik poprawia. Nazwę pliku dokłada
/// <c>Sim.Runner</c>, bo czytniki dostają treść, a nie ścieżkę.
///
/// <c>FormatException</c> jest tu wybrana, bo używają jej już wszystkie pozostałe
/// odmowy tych loaderów — ta osłona nie wprowadza nowego kodu wyjścia.
/// </remarks>
public static class JsonFields
{
    /// <summary>Pole, którego brak jest odmową czytnika, a nie zrzutem środowiska.</summary>
    /// <param name="owner">Obiekt JSON, w którym pole ma stać.</param>
    /// <param name="field">Nazwa pola.</param>
    /// <param name="what">Czym jest <paramref name="owner"/> — trafia do komunikatu.</param>
    /// <returns>Wartość pola.</returns>
    /// <exception cref="FormatException">Gdy pola nie ma albo gdy właściciel nie jest obiektem.</exception>
    public static JsonElement RequiredField(this JsonElement owner, string field, string what)
    {
        ArgumentNullException.ThrowIfNull(field);
        ArgumentNullException.ThrowIfNull(what);

        if (owner.ValueKind != JsonValueKind.Object)
        {
            throw new FormatException(
                $"{what} nie jest obiektem JSON (jest {owner.ValueKind}), więc nie ma pola '{field}'");
        }

        if (!owner.TryGetProperty(field, out var value))
        {
            throw new FormatException($"{what} nie ma wymaganego pola '{field}'");
        }

        return value;
    }
}
