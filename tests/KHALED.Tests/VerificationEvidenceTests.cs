using Khaled.Adapters;
using Khaled.Core;
using Khaled.Integrations;
using Xunit;

namespace Khaled.Tests;

public class VerificationEvidenceTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "khaled-ev-" + Guid.NewGuid().ToString("N"));

    public VerificationEvidenceTests() => Directory.CreateDirectory(_root);

    public void Dispose()
    {
        if (Directory.Exists(_root)) Directory.Delete(_root, true);
        GC.SuppressFinalize(this);
    }

    [Fact]
    public void Verification_Fails_On_Empty_Directory()
    {
        var report = VerificationEngine.VerifyRepository(_root);
        Assert.False(report.AllPassed);
        Assert.Equal(ExitCodes.VerifyFailed, report.ExitCode);
        Assert.Contains("FAIL", report.ToText(), StringComparison.Ordinal);
    }

    [Fact]
    public void Evidence_Is_Written_With_Valid_Hash_And_Redacted()
    {
        var file = EvidenceWriter.Write(_root, "report.txt", "key AKIAABCDEFGHIJKLMNOP done");
        Assert.True(EvidenceWriter.Validate(file));
        Assert.DoesNotContain("AKIA", File.ReadAllText(file), StringComparison.Ordinal);
    }

    [Fact]
    public void Evidence_Validation_Detects_Tampering()
    {
        var file = EvidenceWriter.Write(_root, "tamper.txt", "original");
        File.WriteAllText(file, "changed");
        Assert.False(EvidenceWriter.Validate(file));
    }

    [Fact]
    public void Optional_Layers_Are_Safely_Disabled()
    {
        Assert.False(new DisabledAiProvider().IsEnabled);
        Assert.Equal("AI_DISABLED", new DisabledAiProvider().Suggest("x"));
        Assert.False(new NullBrowserEngine().IsAvailable);
    }

    [Fact]
    public void Autodesk_Adapters_Report_Not_Verified()
    {
        IAutodeskAdapter[] adapters = { new RevitAdapter(), new AutoCadAdapter() };
        Assert.All(adapters, a => Assert.Equal("NOT_VERIFIED", a.Probe().State));
    }
}
