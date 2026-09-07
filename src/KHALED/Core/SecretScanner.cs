using System.Text.RegularExpressions;

namespace Khaled.Core;

/// <summary>Detects obvious secrets so they never leak into logs or evidence.</summary>
public static class SecretScanner
{
    private static readonly Regex[] Patterns =
    {
        new("ghp_[A-Za-z0-9]{16,}", RegexOptions.Compiled),
        new("github_pat_[A-Za-z0-9_]{20,}", RegexOptions.Compiled),
        new("AKIA[0-9A-Z]{16}", RegexOptions.Compiled),
        new("sk-[A-Za-z0-9]{20,}", RegexOptions.Compiled),
        new("-----BEGIN [A-Z ]*PRIVATE KEY-----", RegexOptions.Compiled)
    };

    public static bool ContainsSecret(string? text)
        => !string.IsNullOrEmpty(text) && Patterns.Any(p => p.IsMatch(text));

    public static string Redact(string? text)
    {
        if (string.IsNullOrEmpty(text)) return string.Empty;
        var result = text;
        foreach (var pattern in Patterns) result = pattern.Replace(result, "[REDACTED]");
        return result;
    }
}
