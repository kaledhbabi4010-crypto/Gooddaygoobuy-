using Khaled.Core;
using Xunit;

namespace Khaled.Tests;

public class SafetyTests
{
    [Theory]
    [InlineData("dotnet build", true)]
    [InlineData("git status", true)]
    [InlineData("rm -rf /", false)]
    [InlineData("../evil.sh", false)]
    [InlineData("", false)]
    public void Gate_Allows_Only_Allowlisted_Commands(string command, bool expected)
        => Assert.Equal(expected, new ExecutionGate().IsAllowed(command));

    [Fact]
    public void Gate_Blocks_With_Policy_Exit_Code()
    {
        var decision = new ExecutionGate().Evaluate("curl http://example.com");
        Assert.False(decision.Allowed);
        Assert.Equal(ExitCodes.PolicyBlocked, decision.ExitCode);
    }

    [Fact]
    public void SecretScanner_Detects_And_Redacts()
    {
        var text = "token ghp_" + new string('a', 30);
        Assert.True(SecretScanner.ContainsSecret(text));
        Assert.DoesNotContain("ghp_", SecretScanner.Redact(text), StringComparison.Ordinal);
        Assert.False(SecretScanner.ContainsSecret("nothing here"));
    }
}
