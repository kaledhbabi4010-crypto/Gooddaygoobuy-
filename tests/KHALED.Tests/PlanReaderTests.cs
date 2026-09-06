using Khaled.Core;
using Xunit;

namespace Khaled.Tests;

public class PlanReaderTests
{
    [Fact]
    public void Describe_MentionsPlanFile()
    {
        Assert.Contains(PlanReader.PlanFileName, PlanReader.Describe());
    }

    [Fact]
    public void PlanExists_ReturnsFalse_ForEmptyDirectory()
    {
        var dir = Directory.CreateTempSubdirectory().FullName;
        Assert.False(PlanReader.PlanExists(dir));
    }
}
