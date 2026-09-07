namespace Khaled.Adapters;

public readonly record struct AdapterStatus(string Product, string State, string Detail);

public interface IAutodeskAdapter
{
    string Product { get; }
    AdapterStatus Probe();
}

/// <summary>Revit adapter. Reports NOT_VERIFIED where no verified environment exists.</summary>
public sealed class RevitAdapter : IAutodeskAdapter
{
    public string Product => "Revit";
    public AdapterStatus Probe() => new(Product, "NOT_VERIFIED", "No verified Revit host in CI");
}

/// <summary>AutoCAD adapter. Reports NOT_VERIFIED where no verified environment exists.</summary>
public sealed class AutoCadAdapter : IAutodeskAdapter
{
    public string Product => "AutoCAD";
    public AdapterStatus Probe() => new(Product, "NOT_VERIFIED", "No verified AutoCAD host in CI");
}
