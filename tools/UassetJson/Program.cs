using UAssetAPI;
using UAssetAPI.UnrealTypes;
using UAssetAPI.Unversioned;

if (args.Length < 3)
{
    Console.Error.WriteLine("usage: uassetjson tojson <in.uasset> <out.json> [mappings.usmap]");
    Console.Error.WriteLine("       uassetjson fromjson <in.json> <out.uasset>");
    return 1;
}

var mode = args[0];
switch (mode)
{
    case "tojson":
    {
        Usmap mappings = args.Length > 3 ? new Usmap(args[3]) : null;
        var asset = new UAsset(args[1], EngineVersion.VER_UE5_1, mappings);
        File.WriteAllText(args[2], asset.SerializeJson(true));
        Console.WriteLine($"OK {args[1]} -> {args[2]}");
        return 0;
    }
    case "fromjson":
    {
        var asset = UAsset.DeserializeJson(File.ReadAllText(args[1]));
        asset.Write(args[2]);
        Console.WriteLine($"OK {args[1]} -> {args[2]}");
        return 0;
    }
    default:
        Console.Error.WriteLine($"unknown mode: {mode}");
        return 1;
}
