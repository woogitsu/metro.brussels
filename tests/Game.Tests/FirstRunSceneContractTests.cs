using System;
using System.IO;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using MetroBxl.Tests.Shared;

namespace MetroBxl.Game.Tests;

[TestClass]
public sealed class FirstRunSceneContractTests
{
    private static string Scene() => KorzenRepozytorium.Tresc("src", "Game", "Scenes", "FirstRun.tscn");

    [TestMethod]
    public void FirstRunSceneKeepsPlayableCamerasAndHudContract()
    {
        var scene = Scene();
        var required = new[]
        {
            "[node name=\"FirstRun\" type=\"Node3D\"]",
            "[node name=\"CabCamera\" type=\"Camera3D\" parent=\".\"]",
            "[node name=\"ChaseCamera\" type=\"Camera3D\" parent=\".\"]",
            "[node name=\"Hud\" type=\"CanvasLayer\" parent=\".\"]",
            "[node name=\"Panel\" type=\"PanelContainer\" parent=\"Hud\"]",
            "[node name=\"Rows\" type=\"VBoxContainer\" parent=\"Hud/Panel\"]"
        };
        foreach (var node in required)
        {
            StringAssert.Contains(scene, node, "brak wymaganego węzła sceny: " + node);
        }

        foreach (var label in new[] { "Speed", "Traction", "Station", "Position", "Controls", "Signalling", "View", "Help", "Summary" })
        {
            StringAssert.Contains(scene,
                $"[node name=\"{label}\" type=\"Label\" parent=\"Hud/Panel/Rows\"]",
                "HUD musi zachować etykietę: " + label);
        }
    }

    [TestMethod]
    public void FirstRunSceneDoesNotReintroduceDriverConsoleNode()
    {
        var scene = Scene();
        Assert.IsFalse(Regex.IsMatch(scene, @"\[node name=""(?:Console|DriverConsole|CabConsole)""", RegexOptions.CultureInvariant),
            "scena nie może ponownie dodawać usuniętego pulpitu maszynisty");
    }
}
