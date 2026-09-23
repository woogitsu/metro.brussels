using System;
using System.Collections.Generic;

namespace MetroBxl.Game;

/// <summary>
/// Które wyjątki czytnika pliku znaczą „plik jest ZŁY", a nie „kod jest zepsuty" — 6.D235.
///
/// <para><b>Dwie rodziny, bo różni je TEKST, a nie powaga.</b> Rodzina pierwsza to typy,
/// które rzuca <c>src/Sim/</c> i jego loadery (<see cref="ArgumentException"/>,
/// <see cref="FormatException"/>); ich komunikaty są po polsku, więc droga błędu może je
/// przepisać do wiersza odmowy. Rodzina druga to wyjątki <c>System.Text.Json</c>
/// rzucane przez <c>GetProperty</c> i <c>Enumerate*</c> na dokumencie poprawnym
/// składniowo, ale innego KSZTAŁTU: korzeń jest tablicą albo liczbą, pola brak, pole ma
/// zły typ. Ich komunikaty są po angielsku i do drogi błędu nie wchodzą — wiersz odmowy
/// mówi wtedy własnymi słowami, czym plik miał być.</para>
///
/// <para><b>Zmierzone, nie założone (22.09.2026).</b> Na kształtach <c>[]</c>, <c>5</c>
/// i <c>"napis"</c> uciekały z filtra rodziny pierwszej wszystkie trzy czytniki JSON
/// sceny (oś, manifest chunków, plan sygnalizacji) — jako
/// <see cref="InvalidOperationException"/>; manifest bez wymaganego pola uciekał jako
/// <see cref="KeyNotFoundException"/>. Scena z osią <c>[]</c> nie kończyła się wtedy
/// kodem wyjścia, tylko WISIAŁA do limitu czasu.</para>
///
/// <para><b>Rodzina pierwsza nie ma tu metody i to jest wybór.</b> Jej filtr stoi w
/// <c>FirstRun</c> jako wyrażenie <c>when (error is ArgumentException or FormatException)</c>
/// od 6.D229, a jego kopię trzyma <c>BrokenJsonRefusalTests.ZlapieFiltrFirstRun</c>;
/// przeniesienie go tutaj zmieniłoby kod, którego ta pozycja nie dotyczy.</para>
///
/// <para><b>Dlaczego klasa bez Godota.</b> Żeby test mógł podać jej prawdziwe wyjątki
/// prawdziwych loaderów, bez uruchamiania silnika.</para>
/// </summary>
public static class BadFile
{
    /// <summary>
    /// Dokument poprawny składniowo, ale innego kształtu. Komunikatu wyjątku nie wolno
    /// przepisywać — jest z <c>System.Text.Json</c> i jest po angielsku.
    /// </summary>
    /// <param name="error">Wyjątek z czytnika.</param>
    public static bool IsWrongJsonShape(Exception error) =>
        error is InvalidOperationException or KeyNotFoundException;
}
