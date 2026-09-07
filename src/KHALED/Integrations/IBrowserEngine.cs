namespace Khaled.Integrations;

/// <summary>Browser abstraction; a no-op implementation keeps CI headless and deterministic.</summary>
public interface IBrowserEngine
{
    bool IsAvailable { get; }
    string Fetch(string url);
}

public sealed class NullBrowserEngine : IBrowserEngine
{
    public bool IsAvailable => false;
    public string Fetch(string url) => "BROWSER_UNAVAILABLE";
}
