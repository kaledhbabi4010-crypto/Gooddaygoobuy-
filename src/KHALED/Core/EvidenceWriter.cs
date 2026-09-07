using System.Text;

namespace Khaled.Core;

/// <summary>Writes tamper-evident evidence: a redacted report plus its SHA256 sidecar.</summary>
public static class EvidenceWriter
{
    public static string Write(string outputDirectory, string name, string content)
    {
        Directory.CreateDirectory(outputDirectory);
        var safe = SecretScanner.Redact(content);
        var file = Path.Combine(outputDirectory, name);
        File.WriteAllText(file, safe, Encoding.UTF8);
        File.WriteAllText(file + ".sha256", Hashing.Sha256OfFile(file) + "  " + name + Environment.NewLine, Encoding.UTF8);
        return file;
    }

    public static bool Validate(string evidenceFile)
    {
        var sidecar = evidenceFile + ".sha256";
        if (!File.Exists(evidenceFile) || !File.Exists(sidecar)) return false;
        var expected = File.ReadAllText(sidecar).Split(' ')[0].Trim();
        return string.Equals(expected, Hashing.Sha256OfFile(evidenceFile), StringComparison.OrdinalIgnoreCase);
    }
}
