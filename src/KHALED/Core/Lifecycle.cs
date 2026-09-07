namespace Khaled.Core;

public enum LifecycleState { NotInstalled, Installed, Upgraded, Repaired, Removed }

public readonly record struct CommandResult(int ExitCode, string Message);

/// <summary>Implements the six lifecycle commands: install, verify, status, upgrade, repair, uninstall.</summary>
public sealed class Lifecycle
{
    private readonly string _root;

    public Lifecycle(string rootDirectory) => _root = rootDirectory;

    public LifecycleState State { get; private set; } = LifecycleState.NotInstalled;
    public string Version { get; private set; } = "0.0.0";

    public CommandResult Install()
    {
        if (!PlanReader.PlanExists(_root))
            return new CommandResult(ExitCodes.PreconditionFailed, "PLAN_MISSING");
        State = LifecycleState.Installed;
        Version = "1.0.0";
        return new CommandResult(ExitCodes.Ok, "INSTALLED");
    }

    public CommandResult Verify()
    {
        var report = VerificationEngine.VerifyRepository(_root);
        return new CommandResult(report.ExitCode, report.AllPassed ? "VERIFIED" : "VERIFY_FAILED");
    }

    public CommandResult Status()
        => new(ExitCodes.Ok, $"state={State};version={Version}");

    public CommandResult Upgrade(string targetVersion)
    {
        if (State == LifecycleState.NotInstalled)
            return new CommandResult(ExitCodes.PreconditionFailed, "NOT_INSTALLED");
        if (string.IsNullOrWhiteSpace(targetVersion))
            return new CommandResult(ExitCodes.InvalidArguments, "MISSING_VERSION");
        Version = targetVersion;
        State = LifecycleState.Upgraded;
        return new CommandResult(ExitCodes.Ok, "UPGRADED");
    }

    public CommandResult Repair()
    {
        if (State == LifecycleState.NotInstalled)
            return new CommandResult(ExitCodes.PreconditionFailed, "NOT_INSTALLED");
        State = LifecycleState.Repaired;
        return new CommandResult(ExitCodes.Ok, "REPAIRED");
    }

    public CommandResult Uninstall()
    {
        State = LifecycleState.Removed;
        Version = "0.0.0";
        return new CommandResult(ExitCodes.Ok, "UNINSTALLED");
    }
}
