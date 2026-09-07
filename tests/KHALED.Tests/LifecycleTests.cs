using Khaled.Core;
using Xunit;

namespace Khaled.Tests;

public class LifecycleTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "khaled-" + Guid.NewGuid().ToString("N"));

    public LifecycleTests()
    {
        Directory.CreateDirectory(_root);
        File.WriteAllText(Path.Combine(_root, PlanReader.PlanFileName), "# plan");
    }

    public void Dispose()
    {
        if (Directory.Exists(_root)) Directory.Delete(_root, true);
        GC.SuppressFinalize(this);
    }

    [Fact]
    public void Install_Succeeds_When_Plan_Present()
    {
        var lifecycle = new Lifecycle(_root);
        var result = lifecycle.Install();
        Assert.Equal(ExitCodes.Ok, result.ExitCode);
        Assert.Equal(LifecycleState.Installed, lifecycle.State);
    }

    [Fact]
    public void Install_Fails_When_Plan_Missing()
    {
        var empty = Path.Combine(_root, "empty");
        Directory.CreateDirectory(empty);
        var result = new Lifecycle(empty).Install();
        Assert.Equal(ExitCodes.PreconditionFailed, result.ExitCode);
    }

    [Fact]
    public void Upgrade_Requires_Install_And_Version()
    {
        var lifecycle = new Lifecycle(_root);
        Assert.Equal(ExitCodes.PreconditionFailed, lifecycle.Upgrade("1.1.0").ExitCode);
        lifecycle.Install();
        Assert.Equal(ExitCodes.InvalidArguments, lifecycle.Upgrade("").ExitCode);
        Assert.Equal(ExitCodes.Ok, lifecycle.Upgrade("1.1.0").ExitCode);
        Assert.Equal("1.1.0", lifecycle.Version);
    }

    [Fact]
    public void Repair_And_Uninstall_Behave()
    {
        var lifecycle = new Lifecycle(_root);
        Assert.Equal(ExitCodes.PreconditionFailed, lifecycle.Repair().ExitCode);
        lifecycle.Install();
        Assert.Equal(ExitCodes.Ok, lifecycle.Repair().ExitCode);
        Assert.Equal(ExitCodes.Ok, lifecycle.Uninstall().ExitCode);
        Assert.Equal(LifecycleState.Removed, lifecycle.State);
    }

    [Fact]
    public void Router_Handles_Unknown_And_Help()
    {
        var lifecycle = new Lifecycle(_root);
        Assert.Equal(ExitCodes.InvalidArguments, CommandRouter.Route(lifecycle, new[] { "nope" }).ExitCode);
        Assert.Equal(ExitCodes.Ok, CommandRouter.Route(lifecycle, Array.Empty<string>()).ExitCode);
        Assert.Equal(ExitCodes.Ok, CommandRouter.Route(lifecycle, new[] { "status" }).ExitCode);
    }
}
