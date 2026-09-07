namespace Khaled.Core;

public readonly record struct VerificationCheck(string Name, bool Passed, string Detail);

public sealed class VerificationReport
{
    private readonly List<VerificationCheck> _checks = new();

    public IReadOnlyList<VerificationCheck> Checks => _checks;
    public bool AllPassed => _checks.Count > 0 && _checks.All(c => c.Passed);
    public int ExitCode => AllPassed ? ExitCodes.Ok : ExitCodes.VerifyFailed;

    public VerificationReport Add(string name, bool passed, string detail = "")
    {
        _checks.Add(new VerificationCheck(name, passed, detail));
        return this;
    }

    public string ToText()
        => string.Join(Environment.NewLine,
            _checks.Select(c => (c.Passed ? "PASS" : "FAIL") + " | " + c.Name + (string.IsNullOrEmpty(c.Detail) ? "" : " | " + c.Detail)));
}

public static class VerificationEngine
{
    /// <summary>Independent verification of a checked-out repository root.</summary>
    public static VerificationReport VerifyRepository(string rootDirectory)
    {
        var report = new VerificationReport();
        report.Add("plan-file-present", PlanReader.PlanExists(rootDirectory), PlanReader.PlanFileName);
        report.Add("solution-present", File.Exists(Path.Combine(rootDirectory, "KHALED.sln")), "KHALED.sln");
        report.Add("core-project-present", File.Exists(Path.Combine(rootDirectory, "src", "KHALED", "KHALED.csproj")));
        report.Add("tests-project-present", File.Exists(Path.Combine(rootDirectory, "tests", "KHALED.Tests", "KHALED.Tests.csproj")));
        report.Add("workflow-present", File.Exists(Path.Combine(rootDirectory, ".github", "workflows", "build.yml")));
        return report;
    }
}
