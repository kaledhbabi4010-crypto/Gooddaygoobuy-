namespace Khaled.Core;

public readonly record struct RepairResult(bool Repaired, int Attempts, int ExitCode, string Message);

/// <summary>Bounded self-repair: at most MaxAttemptsPerCategory tries per failure category.</summary>
public sealed class RepairEngine
{
    public const int MaxAttemptsPerCategory = 5;

    private readonly Dictionary<FailureCategory, int> _attempts = new();

    public int AttemptsFor(FailureCategory category)
        => _attempts.TryGetValue(category, out var value) ? value : 0;

    public RepairResult TryRepair(Fingerprint fingerprint, Func<bool> repairAction)
    {
        ArgumentNullException.ThrowIfNull(repairAction);
        var used = AttemptsFor(fingerprint.Category);
        if (used >= MaxAttemptsPerCategory)
            return new RepairResult(false, used, ExitCodes.RepairExhausted, "REPAIR_EXHAUSTED");

        _attempts[fingerprint.Category] = used + 1;
        var success = repairAction();
        return success
            ? new RepairResult(true, used + 1, ExitCodes.Ok, "REPAIRED")
            : new RepairResult(false, used + 1, ExitCodes.GeneralError, "REPAIR_FAILED");
    }

    public void Rollback(FailureCategory category) => _attempts.Remove(category);
}
