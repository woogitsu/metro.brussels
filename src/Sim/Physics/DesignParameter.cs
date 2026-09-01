using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Jeden parametr o statusie <c>design_model</c>, wypisany tak samo jawnie jak
/// stałe <c>DESIGN_*</c> i słownik <c>DESIGN_ASSUMPTIONS</c> w
/// <c>tools/blender/m7_layout.py</c>: nazwa w kodzie, ścieżka w rejestrze,
/// wartość i powód, dla którego wartość jest właśnie taka.
/// </summary>
/// <param name="Name">Nazwa właściwości <c>Design*</c> w <see cref="VehicleModel"/>.</param>
/// <param name="RegistryPath">Ścieżka w <c>data/vehicle/m7-spec.json</c>.</param>
/// <param name="Value">Wartość użyta przez model.</param>
/// <param name="Reason">Dlaczego taka wartość i czego brakuje, żeby awansowała do <c>spec</c>.</param>
public readonly record struct DesignParameter(string Name, string RegistryPath, double Value, string Reason)
{
    /// <summary>Jedna linia raportu; kultura niezmienna, żeby wyjście nie zależało od maszyny.</summary>
    public override string ToString() =>
        string.Create(CultureInfo.InvariantCulture, $"{Name} = {Value:R}  ({RegistryPath}) — {Reason}");
}
