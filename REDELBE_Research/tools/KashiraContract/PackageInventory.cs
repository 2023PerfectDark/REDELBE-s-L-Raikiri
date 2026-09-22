using Kashira.Core.Mods;
using Kashira.Core.Games;
using Kashira.Core.Doa6;
using Kashira.Core.Formats;
using System.Text;
using System.Text.Json;
static class PackageInventory {
 public static void Verify(string game) {
  var ws=new GameWorkspace(new GameInstall{Id="doa6lr",DisplayName="DOA6LR",InstallPath=Path.GetFullPath(game),Databases=new[]{"root","system"}});
  using var ex=AssetExtractor.Open(ws);
  string root=Path.Combine(game,"REDELBE_LR");string generation=Path.Combine(root,File.ReadAllText(Path.Combine(root,"active_package.txt")).Trim());
  using var manifest=JsonDocument.Parse(File.ReadAllText(Path.Combine(generation,"manifest.json")));
  foreach(var (slot,id) in new[]{("MNT_COS_011",0xd0bac93cu),("MOM_COS_105",0xc532d03eu),("RAC_COS_005",0x549de776u)}) {
   var asset=manifest.RootElement.GetProperty("assets").EnumerateArray().Single(a=>a.GetProperty("slot").GetString()==slot&&a.GetProperty("id").GetString()==$"0x{id:x8}");
   string hash=Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(ex.Extract(id)!)).ToLowerInvariant();
   if(hash!=asset.GetProperty("vanilla_sha256").GetString())throw new Exception(slot+" fallback is not pristine");
   if(hash==asset.GetProperty("payload_sha256").GetString())throw new Exception(slot+" mod equals its fallback");
   Console.WriteLine($"PASS: {slot} has a pristine model fallback and a distinct selectable mod model.");
  }
 }
 public static void Run(string game,string output) {
  var install=new GameInstall{Id="doa6lr",DisplayName="DOA6LR",InstallPath=Path.GetFullPath(game),ExePath=Path.Combine(Path.GetFullPath(game),"DOA6LR.exe"),Databases=new[]{"root","system"}};
  var ws=new GameWorkspace(install);using var ex=AssetExtractor.Open(ws);var set=Doa6SingletonSet.Load(ex);
  var names=Encoding.ASCII.GetString(set.Scn.Records.First(r=>r.Type==Doa6SingletonSet.T_ScnRoot).Prop(Doa6SingletonSet.P_Names)!.Value).Split('\0',StringSplitOptions.RemoveEmptyEntries);
  var mesh=new Dictionary<uint,List<string>>();
  foreach(var name in names.Where(n=>n.Contains("_COS_")).Distinct())try{var fk=set.ResolveAssets(set.CostumeOid(name)).G1m;if(!mesh.ContainsKey(fk))mesh[fk]=new();mesh[fk].Add(name);}catch{}
  var rows=new List<object>();
  foreach(var file in Directory.GetFiles(ws.ModsDir,"*.ktmod")) {
   var pkg=KtmodPackage.Load(file);if(pkg==null||pkg.Legacy.Count==0)continue;
   rows.Add(new {name=pkg.Name,path=file,assets=pkg.Legacy.Select(a=>new{id=$"0x{a.FileKtid:x8}",ext=a.Ext,entry=a.EntryName,costumes=mesh.GetValueOrDefault(a.FileKtid,new())}).ToArray()});
  }
  File.WriteAllText(output,JsonSerializer.Serialize(rows,new JsonSerializerOptions{WriteIndented=true}));
  Console.WriteLine($"Saved {rows.Count} native Kashira packages to {output}");
 }
}
