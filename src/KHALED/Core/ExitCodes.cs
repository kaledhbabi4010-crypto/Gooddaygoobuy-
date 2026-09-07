namespace Khaled.Core;

/// <summary>Stable process exit codes used by the KHALED CLI.</summary>
public static class ExitCodes
{
    public const int Ok = 0;
    public const int GeneralError = 1;
    public const int InvalidArguments = 2;
    public const int PreconditionFailed = 3;
    public const int BuildFailed = 4;
    public const int TestFailed = 5;
    public const int VerifyFailed = 6;
    public const int PolicyBlocked = 7;
    public const int RepairExhausted = 8;
    public const int NotVerified = 9;
}
