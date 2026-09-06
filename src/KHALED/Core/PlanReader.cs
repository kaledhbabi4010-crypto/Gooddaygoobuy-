namespace Khaled.Core;

/// <summary>Minimal, real, testable core so the build has something to verify.</summary>
public static class PlanReader
{
    public const string PlanFileName = "KHALED-MASTER-PLAN.md";

    public static string Describe() => $"KHALED core is running. Plan file: {PlanFileName}";

    public static bool PlanExists(string rootDirectory) =>
        File.Exists(Path.Combine(rootDirectory, PlanFileName));
}
