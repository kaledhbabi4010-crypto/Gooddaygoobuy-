using Khaled.Core;
using Xunit;

namespace Khaled.Tests;

public class DiagnosticsTests
{
    [Fact]
    public void Fingerprint_Categorises_Compilation_Errors()
    {
        var fp = FailureFingerprinter.Create("Program.cs(3,5): error CS1002: ; expected");
        Assert.Equal(FailureCategory.Compilation, fp.Category);
        Assert.Equal(16, fp.Hash.Length);
    }

    [Fact]
    public void Fingerprint_Is_Stable_Across_Numbers()
    {
        var a = FailureFingerprinter.Create("error CS1002 at line 1234");
        var b = FailureFingerprinter.Create("error CS1002 at line 5678");
        Assert.Equal(a.Hash, b.Hash);
    }

    [Fact]
    public void Repair_Stops_After_Five_Attempts()
    {
        var engine = new RepairEngine();
        var fp = FailureFingerprinter.Create("permission denied");
        for (var i = 0; i < RepairEngine.MaxAttemptsPerCategory; i++)
            Assert.Equal(ExitCodes.GeneralError, engine.TryRepair(fp, () => false).ExitCode);

        var exhausted = engine.TryRepair(fp, () => true);
        Assert.Equal(ExitCodes.RepairExhausted, exhausted.ExitCode);
    }

    [Fact]
    public void Repair_Succeeds_And_Rollback_Resets()
    {
        var engine = new RepairEngine();
        var fp = FailureFingerprinter.Create("connection refused");
        Assert.True(engine.TryRepair(fp, () => true).Repaired);
        Assert.Equal(1, engine.AttemptsFor(fp.Category));
        engine.Rollback(fp.Category);
        Assert.Equal(0, engine.AttemptsFor(fp.Category));
    }
}
