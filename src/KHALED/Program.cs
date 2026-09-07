using Khaled.Core;

var root = Environment.GetEnvironmentVariable("KHALED_ROOT") ?? Directory.GetCurrentDirectory();
var lifecycle = new Lifecycle(root);
var result = CommandRouter.Route(lifecycle, args);
Console.WriteLine(SecretScanner.Redact(result.Message));
return result.ExitCode;
