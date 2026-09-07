namespace Khaled.Core;

/// <summary>Maps CLI arguments onto lifecycle commands and exit codes.</summary>
public static class CommandRouter
{
    public static readonly string[] KnownCommands =
        { "install", "verify", "status", "upgrade", "repair", "uninstall", "help" };

    public static CommandResult Route(Lifecycle lifecycle, string[] args)
    {
        ArgumentNullException.ThrowIfNull(lifecycle);
        if (args is null || args.Length == 0)
            return new CommandResult(ExitCodes.Ok, HelpText());

        var command = args[0].Trim().ToLowerInvariant();
        return command switch
        {
            "install" => lifecycle.Install(),
            "verify" => lifecycle.Verify(),
            "status" => lifecycle.Status(),
            "upgrade" => lifecycle.Upgrade(args.Length > 1 ? args[1] : string.Empty),
            "repair" => lifecycle.Repair(),
            "uninstall" => lifecycle.Uninstall(),
            "help" => new CommandResult(ExitCodes.Ok, HelpText()),
            _ => new CommandResult(ExitCodes.InvalidArguments, "UNKNOWN_COMMAND: " + command)
        };
    }

    public static string HelpText()
        => "KHALED CLI\nCommands: " + string.Join(", ", KnownCommands);
}
