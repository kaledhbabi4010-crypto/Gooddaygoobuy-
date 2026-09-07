namespace Khaled.Integrations;

/// <summary>Optional AI layer. The system must work fully with AI disabled.</summary>
public interface IAiProvider
{
    bool IsEnabled { get; }
    string Suggest(string context);
}

public sealed class DisabledAiProvider : IAiProvider
{
    public bool IsEnabled => false;
    public string Suggest(string context) => "AI_DISABLED";
}
