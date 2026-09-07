namespace Khaled.Core;

/// <summary>Allowlist based execution gate. Anything not explicitly allowed is blocked.</summary>
public sealed class ExecutionGate
{
    private static readonly string[] DefaultAllowlist =
    {
        "dotnet", "git", "bash", "sha256sum", "echo"
    };

    private readonly HashSet<string> _allowed;

    public ExecutionGate(IEnumerable<string>? allowlist = null)
        => _allowed = new HashSet<string>(allowlist ?? DefaultAllowlist, StringComparer.OrdinalIgnoreCase);

    public IReadOnlyCollection<string> Allowlist => _allowed.ToArray();

    public bool IsAllowed(string command)
    {
        if (string.IsNullOrWhiteSpace(command)) return false;
        var head = command.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries)[0];
        if (head.Contains("..", StringComparison.Ordinal)) return false;
        return _allowed.Contains(head);
    }

    public GateDecision Evaluate(string command)
        => IsAllowed(command)
            ? new GateDecision(true, ExitCodes.Ok, "ALLOWED")
            : new GateDecision(false, ExitCodes.PolicyBlocked, "BLOCKED_BY_POLICY");
}

public readonly record struct GateDecision(bool Allowed, int ExitCode, string Reason);
