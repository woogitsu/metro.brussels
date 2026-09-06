using System;
using System.Globalization;
using System.Linq;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// <see cref="SpeedProfile"/> i <see cref="SpeedSample"/> — obserwacja przebiegu,
/// do 6.A8 nienazwana w żadnym pliku pod <c>tests/</c>.
///
/// <para><b>Czym te testy różnią się od <see cref="EnergyAndProfileTests"/>.</b> Tamte
/// czytają profil, żeby coś powiedzieć o <b>przebiegu</b>: że prędkość rośnie, że
/// próbkowanie niczego nie zmieniło, że zryw widać na pierwszej sekundzie. Profil jest
/// tam narzędziem pomiaru. Tu jest przedmiotem: co obiecują <see cref="SpeedProfile.PeakSpeedMps"/>
/// i <see cref="SpeedProfile.FirstAtLeast"/>, gdy próbek nie ma ani jednej, gdy jest
/// dokładnie jedna i gdy próg trafia w wartość próbki co do bitu.</para>
///
/// <para><b>Skąd profil jednopróbkowy.</b> Konstruktor <see cref="SpeedProfile"/> jest
/// <c>internal</c>, a testy nie widzą wnętrza <c>MetroBxl.Sim</c> — profil trzeba więc
/// wziąć z prawdziwego przebiegu. Przebieg z limitem czasu 0 s ma <c>maxSteps = 0</c>,
/// więc pętla całkowania nie wykonuje ani jednego kroku, a w buforze zostaje wyłącznie
/// próbka początkowa. To nie jest sztuczka na potrzeby testu: to najkrótszy przebieg,
/// jaki publiczne API tego rdzenia potrafi zwrócić, i profil takiego przebiegu też
/// trafia do raportu.</para>
/// </summary>
[TestClass]
public sealed class SpeedProfileTests
{
    private const double StartKmh = 80.0;

    private static double StartMps => Units.KmhToMps(StartKmh);

    /// <summary>Profil o dokładnie jednej próbce: przebieg, który nie zdążył zrobić kroku.</summary>
    private static SpeedProfile SingleSample() =>
        ServiceBrakingRun.M7.ToStop(StartKmh, FixedStep.Simulation, sampleEverySteps: 1, timeLimitSeconds: 0.0)
            .Profile;

    /// <summary>Profil rozruchu 0 → 80 km/h, próbkowany co 60 kroków (co pół sekundy).</summary>
    private static SpeedProfile Acceleration() =>
        AccelerationRun.M7
            .ToSpeed(RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0), StartKmh, sampleEverySteps: 60)
            .Profile;

    /// <summary>Profil hamowania 80 → 0 km/h, próbkowany co 60 kroków.</summary>
    private static SpeedProfile Braking() =>
        ServiceBrakingRun.M7.ToStop(StartKmh, FixedStep.Simulation, sampleEverySteps: 60).Profile;

    // --- profil pusty -----------------------------------------------------------------

    /// <summary>
    /// Profil pusty jest odpowiedzią na „przebieg bez próbkowania", a nie błędem, więc
    /// obie miary muszą coś sensownego zwrócić. Szczyt zera próbek to <b>zero</b>, a nie
    /// minus nieskończoność ani wyjątek — wynik trafia prosto do wiersza raportu.
    /// </summary>
    [TestMethod]
    public void Profil_pusty_ma_zerowy_szczyt_i_zerowy_odstep_probkowania()
    {
        var empty = SpeedProfile.Empty;

        Assert.AreEqual(0, empty.Samples.Count);
        Assert.AreEqual(0, empty.SampleEverySteps);
        Assert.AreEqual(0.0, empty.PeakSpeedMps, 0.0);
        Assert.IsFalse(double.IsNegativeInfinity(empty.PeakSpeedMps));
    }

    /// <summary>
    /// Na pustym profilu każdy próg jest nieosiągnięty — także próg zerowy, który na
    /// profilu niepustym trafiłby w pierwszą próbkę.
    /// </summary>
    [TestMethod]
    public void Profil_pusty_nie_znajduje_zadnej_probki_takze_dla_progu_zerowego()
    {
        var empty = SpeedProfile.Empty;

        Assert.IsNull(empty.FirstAtLeast(0.0));
        Assert.IsNull(empty.FirstAtLeast(-1.0));
        Assert.IsNull(empty.FirstAtLeast(StartMps));
    }

    /// <summary>
    /// Przebieg bez próbkowania oddaje profil pusty, a nie profil z jedną przypadkową
    /// próbką: obserwacja wyłączona ma znaczyć wyłączona.
    /// </summary>
    [TestMethod]
    public void Przebieg_bez_probkowania_oddaje_profil_pusty()
    {
        var run = AccelerationRun.M7.ToSpeed(RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0), StartKmh);

        Assert.AreEqual(0, run.Profile.Samples.Count);
        Assert.AreEqual(0, run.Profile.SampleEverySteps);
        Assert.AreEqual(0.0, run.Profile.PeakSpeedMps, 0.0);
    }

    // --- profil jednopróbkowy ---------------------------------------------------------

    /// <summary>
    /// Jedna próbka jest jednocześnie pierwszą i ostatnią, więc szczyt to ta próbka.
    /// Test pilnuje też tego, że przebieg naprawdę stanął na zerze kroków — inaczej
    /// mierzyłby coś innego, niż twierdzi.
    /// </summary>
    [TestMethod]
    public void Profil_jednoprobkowy_ma_szczyt_rowny_swojej_jedynej_probce()
    {
        var profile = SingleSample();

        Assert.AreEqual(1, profile.Samples.Count, "profil miał mieć dokładnie jedną próbkę");
        Assert.AreEqual(0L, profile.Samples[0].Steps);
        Assert.AreEqual(0.0, profile.Samples[0].DistanceM, 0.0);
        Assert.AreEqual(StartMps, profile.PeakSpeedMps, 0.0);
    }

    /// <summary>
    /// Próg <b>równy</b> prędkości próbki jest progiem osiągniętym — nazwa metody mówi
    /// „co najmniej". Granica jest sprawdzona z obu stron: przy progu większym o jeden
    /// ULP profil już nic nie znajduje.
    /// </summary>
    [TestMethod]
    public void Prog_rowny_predkosci_probki_jest_progiem_osiagnietym()
    {
        var profile = SingleSample();
        var speed = profile.Samples[0].SpeedMps;

        var hit = profile.FirstAtLeast(speed);
        Assert.IsNotNull(hit);
        Assert.AreEqual(speed, hit!.Value.SpeedMps, 0.0);

        Assert.IsNull(
            profile.FirstAtLeast(Math.BitIncrement(speed)),
            "próg o jeden ULP wyżej nie może być osiągnięty");
    }

    // --- profil wielopróbkowy ---------------------------------------------------------

    /// <summary>
    /// Szczyt to maksimum po wszystkich próbkach, a nie próbka ostatnia. Hamowanie jest
    /// tu przypadkiem rozstrzygającym: ostatnia próbka ma zero, a szczyt stoi na starcie.
    /// </summary>
    [TestMethod]
    public void Szczyt_profilu_hamowania_stoi_na_poczatku_a_nie_na_ostatniej_probce()
    {
        var profile = Braking();

        Assert.IsTrue(profile.Samples.Count > 2, $"profil ma {profile.Samples.Count} próbek");
        Assert.AreEqual(0.0, profile.Samples[^1].SpeedMps, 0.0, "hamowanie kończy się na zerze");
        Assert.AreEqual(StartMps, profile.PeakSpeedMps, 1e-12);
        Assert.AreEqual(profile.Samples.Max(s => s.SpeedMps), profile.PeakSpeedMps, 0.0);
    }

    /// <summary>
    /// „Pierwsza" znaczy pierwsza w czasie. Test bierze próg leżący w środku rozruchu
    /// i sprawdza dwie rzeczy naraz: znaleziona próbka jest nad progiem, a próbka
    /// bezpośrednio ją poprzedzająca jeszcze pod nim. Metoda idąca od końca albo
    /// zwracająca dowolne trafienie przechodzi pierwsze sprawdzenie i pada na drugim.
    /// </summary>
    [TestMethod]
    public void Znaleziona_jest_pierwsza_probka_nad_progiem_a_nie_dowolna()
    {
        var profile = Acceleration();
        var threshold = Units.KmhToMps(50.0);

        var found = profile.FirstAtLeast(threshold);
        Assert.IsNotNull(found);
        Assert.IsTrue(found!.Value.SpeedMps >= threshold);

        var index = profile.Samples.ToList().FindIndex(s => s.Steps == found.Value.Steps);
        Assert.IsTrue(index > 0, "próg 50 km/h nie może wypaść na próbce startowej");
        Assert.IsTrue(
            profile.Samples[index - 1].SpeedMps < threshold,
            string.Create(
                CultureInfo.InvariantCulture,
                $"próbka wcześniejsza ({profile.Samples[index - 1].SpeedKmh:F2} km/h) też była nad progiem"));
    }

    /// <summary>
    /// Próg powyżej szczytu daje <c>null</c> — i to na profilu <b>niepustym</b>, gdzie
    /// „nic nie znalazłem" łatwo pomylić z „oddam ostatnią próbkę".
    /// </summary>
    [TestMethod]
    public void Prog_powyzej_szczytu_nie_znajduje_nic_takze_na_profilu_niepustym()
    {
        var profile = Acceleration();

        Assert.IsTrue(profile.Samples.Count > 2);
        Assert.IsNull(profile.FirstAtLeast(Math.BitIncrement(profile.PeakSpeedMps)));
        Assert.IsNull(profile.FirstAtLeast(Units.KmhToMps(200.0)));
    }

    /// <summary>
    /// Profil pamięta, co ile kroków go próbkowano — bez tej liczby nie da się odczytać,
    /// czy dwie sąsiednie próbki dzieli pół sekundy, czy dziesięć.
    /// </summary>
    [TestMethod]
    public void Profil_pamieta_zadany_odstep_probkowania()
    {
        Assert.AreEqual(60, Acceleration().SampleEverySteps);
        Assert.AreEqual(1, SingleSample().SampleEverySteps);
        Assert.AreEqual(0, SpeedProfile.Empty.SampleEverySteps);
    }

    // --- SpeedSample ------------------------------------------------------------------

    /// <summary>
    /// Próbka trzyma prędkość w m/s, a raporty czytają km/h — przeliczenie idzie w tę
    /// stronę i tylko w tę. Zamiana kierunku daje liczby mniejsze zamiast większych
    /// i widać ją na dowolnej próbce niezerowej.
    /// </summary>
    [TestMethod]
    public void Probka_przelicza_metry_na_sekunde_na_kilometry_na_godzine()
    {
        var sample = SingleSample().Samples[0];

        Assert.AreEqual(StartKmh, sample.SpeedKmh, 1e-12);
        Assert.AreEqual(sample.SpeedMps * 3.6, sample.SpeedKmh, 1e-12);
        Assert.IsTrue(sample.SpeedKmh > sample.SpeedMps, "km/h musi być liczbą większą niż m/s");
    }

    /// <summary>
    /// Wiersz próbki idzie do raportu, więc nie zależy od kultury maszyny: przy kulturze
    /// z przecinkiem dziesiętnym w wyjściu nadal stoi kropka.
    /// </summary>
    [TestMethod]
    public void Wiersz_probki_nie_zalezy_od_kultury_maszyny()
    {
        var previous = CultureInfo.CurrentCulture;
        var comma = (CultureInfo)CultureInfo.InvariantCulture.Clone();
        comma.NumberFormat.NumberDecimalSeparator = ",";
        CultureInfo.CurrentCulture = comma;
        try
        {
            var line = SingleSample().Samples[0].ToString();

            Console.WriteLine(line);
            StringAssert.Contains(line, "80.00 km/h");
            StringAssert.Contains(line, "0.000 s");
        }
        finally
        {
            CultureInfo.CurrentCulture = previous;
        }
    }
}
