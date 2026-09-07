using System.Text.RegularExpressions;

namespace Khaled.Core;

public enum FailureCategory
{
    Unknown,
    MissingDependency,
    Compilation,
    TestFailure,
    Network,
    Permission,
    Timeout
}

public readonly record struct Fingerprint(FailureCategory Category, string Hash);

/// <summary>Turns raw failure output into a stable, categorised fingerprint.</summary>
public static class FailureFingerprinter
{
    private static readonly (FailureCategory Category, Regex Pattern)[] Rules =
    {
        (FailureCategory.MissingDependency, new Regex("(not found|could not be found|NU1101|command not found)", RegexOptions.IgnoreCase)),
        (FailureCategory.Compilation, new Regex("(error CS[0-9]+|compilation failed)", RegexOptions.IgnoreCase)),
        (FailureCategory.TestFailure, new Regex("(failed!|test run failed|assert\\.)", RegexOptions.IgnoreCase)),
        (FailureCategory.Network, new Regex("(timed out while connecting|connection refused|dns|network)", RegexOptions.IgnoreCase)),
        (FailureCategory.Permission, new Regex("(permission denied|unauthorized|forbidden|403)", RegexOptions.IgnoreCase)),
        (FailureCategory.Timeout, new Regex("(timeout|timed out)", RegexOptions.IgnoreCase))
    };

    public static Fingerprint Create(string? output)
    {
        var safe = SecretScanner.Redact(output);
        var category = FailureCategory.Unknown;
        foreach (var rule in Rules)
        {
            if (rule.Pattern.IsMatch(safe)) { category = rule.Category; break; }
        }
        var normalized = Regex.Replace(safe, "[0-9]{2,}", "N").Trim().ToLowerInvariant();
        return new Fingerprint(category, Hashing.Sha256OfText(category + "|" + normalized)[..16]);
    }
}
