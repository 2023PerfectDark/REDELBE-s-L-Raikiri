using System.Diagnostics;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Kashira.Core.Games;
using Kashira.Core.Mods;
using Kashira.Core.Formats;
using Kashira.Core.Doa6;
using Kashira.Core.Patching;

static class Program {
 const string Marker="Content_Legacy/redelbe_layer2.json";
 static readonly JsonSerializerOptions Json=new(){WriteIndented=true};
 static string Hash(string file)=>Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(file)));
 static void Save(string file,object value)=>File.WriteAllText(file,JsonSerializer.Serialize(value,Json));
 static int Main(string[] args) {
  try {if(args.Length!=2||(args[0]!="prepare"&&args[0]!="inspect"))throw new Exception("Usage: REDELBE_Kashira_Prepare prepare|inspect GAME_FOLDER");Run(Path.GetFullPath(args[1]),args[0]=="inspect");return 0;}
  catch(Exception e){Console.Error.WriteLine("Kashira Layer2 preparation failed: "+e.Message);return 1;}
 }
 static void Run(string game,bool inspect) {
  string exe=Path.Combine(game,"DOA6LR.exe");if(!File.Exists(exe))throw new Exception("DOA6LR.exe missing from selected installation");
  if(!File.Exists(Path.Combine(game,"Kashira-win-x64.exe"))||!File.Exists(Path.Combine(game,"KashiraEditor-win-x64.exe")))throw new Exception("Place Kashira-win-x64.exe and KashiraEditor-win-x64.exe beside DOA6LR.exe");
  if(!inspect)foreach(var p in Process.GetProcessesByName("DOA6LR"))using(p) {
   if(string.Equals(p.MainModule?.FileName,exe,StringComparison.OrdinalIgnoreCase))throw new Exception("Close the backup game before preparing mods.");
  }
  var install=new GameInstall{Id="doa6lr",DisplayName="DOA6LR",InstallPath=game,ExePath=exe,Databases=new[]{"root","system"}};
  var ws=new GameWorkspace(install);string root=Path.Combine(game,"REDELBE_LR");
  if(inspect){using var check=AssetExtractor.Open(ws);var current=Doa6SingletonSet.Load(check);Console.WriteLine("PASS: installed Kashira.Core reads current LR singleton databases.");return;}
  ws.EnsureFolders();Directory.CreateDirectory(root);
  string statePath=Path.Combine(root,"kashira_prepare_state.json");string initial=Fingerprint(ws);
  if(File.Exists(statePath)&&JsonDocument.Parse(File.ReadAllText(statePath)).RootElement.GetProperty("fingerprint").GetString()==initial){Console.WriteLine("Kashira preparation unchanged.");return;}
  string backup=Path.Combine(root,"kashira_backups",DateTime.Now.ToString("yyyyMMdd_HHmmss_fff"));Directory.CreateDirectory(backup);
  var previous=PatchRecord.Load(ws.PatchRecordPath);
  foreach(var db in new[]{"root","system"}) {
   var record=previous?.Databases.FirstOrDefault(d=>d.Db.Equals(db,StringComparison.OrdinalIgnoreCase));
   var rdx=File.ReadAllBytes(Path.Combine(ws.PackageDir,db+".rdx"));
   bool modded=false;for(int offset=0;offset+8<=rdx.Length;offset+=8)if((BitConverter.ToUInt32(rdx,offset+4)&0xffff0000)==0xca5e0000)modded=true;
   foreach(var ext in new[]{"rdb","rdx"}) {
    var part=db+"."+ext;var live=Path.Combine(ws.PackageDir,part);var pristine=Path.Combine(ws.BackupDir,part);
    File.Copy(live,Path.Combine(backup,part));
    if(File.Exists(pristine)){Directory.CreateDirectory(Path.Combine(backup,"pristine"));File.Copy(pristine,Path.Combine(backup,"pristine",part));}
    bool ours=record!=null?Hash(live).Equals(ext=="rdb"?record.RdbHash:record.RdxHash,StringComparison.OrdinalIgnoreCase):modded;
    if(!ours)File.Copy(live,pristine,true);
    else if(!File.Exists(pristine))throw new Exception("Missing Kashira original index; verify game files before preparing mods.");
   }
  }
  if(File.Exists(ws.PatchRecordPath))File.Copy(ws.PatchRecordPath,Path.Combine(backup,"rdbpatch.json"));
  foreach(var file in Directory.GetFiles(ws.PackageDir,"0xca5e*.fdata"))File.Copy(file,Path.Combine(backup,Path.GetFileName(file)));
  using var ex=AssetExtractor.Open(ws);var set=Doa6SingletonSet.Load(ex);
  var names=Encoding.ASCII.GetString(set.Scn.Records.First(r=>r.Type==Doa6SingletonSet.T_ScnRoot).Prop(Doa6SingletonSet.P_Names)!.Value).Split('\0',StringSplitOptions.RemoveEmptyEntries);
  File.WriteAllLines(Path.Combine(root,"slot_names.txt"),names.Where(n=>Regex.IsMatch(n,@"^[A-Z0-9]+_(COS|HAIR|FACE)_[0-9]+$")).Distinct().Order());
  var slotsByMesh=new Dictionary<uint,HashSet<string>>();
  foreach(var name in names.Where(n=>Regex.IsMatch(n,@"^[A-Z0-9]+_(COS|HAIR|FACE)_[0-9]+$"))) {
   var fk=set.ResolveAssets(set.CostumeOid(name)).G1m;if(!slotsByMesh.ContainsKey(fk))slotsByMesh[fk]=new();slotsByMesh[fk].Add(name);
  }
  var conversions=new List<(KtmodPackage pkg,string slot)>();
  foreach(var file in Directory.GetFiles(ws.ModsDir,"*.ktmod")) {
   var pkg=KtmodPackage.Load(file);if(pkg==null||!pkg.MatchesGame(install))continue;
   using var zip=ZipFile.OpenRead(file);if(zip.GetEntry(Marker)!=null)continue;
   var meshes=pkg.Legacy.Where(a=>a.Ext=="g1m").ToArray();if(meshes.Length==0)continue;
   var slots=meshes.SelectMany(m=>slotsByMesh.GetValueOrDefault(m.FileKtid,new())).Distinct().ToArray();
   // A costume bundle may also contain its face/hair mesh; its costume is primary.
   var costumes=slots.Where(s=>s.Contains("_COS_")).ToArray();
   var hairs=slots.Where(s=>s.Contains("_HAIR_")).ToArray();
   if(costumes.Length>0)slots=costumes;else if(hairs.Length>0)slots=hairs;
   if(slots.Length!=1)throw new Exception($"Costume/hair/face slot is ambiguous for '{pkg.Name}' ({string.Join(", ",slots)}). Supply an explicit Layer2 marker before launch.");
   if(pkg.CostumeManifests.Count!=0)throw new Exception("Authored material manifest needs explicit Layer2 conversion: "+pkg.Name);
   conversions.Add((pkg,slots[0]));
  }
  var converted=new List<object>();
  foreach(var (pkg,slot) in conversions) {
   string saved=Path.Combine(backup,Path.GetFileName(pkg.FilePath));File.Copy(pkg.FilePath,saved);
   string temporary=pkg.FilePath+".redelbe-next";if(File.Exists(temporary))throw new Exception("Previous incomplete conversion exists: "+temporary);
   string assetRoot="Content_Legacy/REDELBE_Layer2/"+slot;
   using(var source=ZipFile.OpenRead(pkg.FilePath))using(var dest=ZipFile.Open(temporary,ZipArchiveMode.Create)) {
    var legacy=pkg.Legacy.ToDictionary(a=>a.EntryName,StringComparer.OrdinalIgnoreCase);
    foreach(var entry in source.Entries) {
     if(entry.FullName.EndsWith('/'))continue;
     string target=legacy.TryGetValue(entry.FullName,out var asset)?$"{assetRoot}/0x{asset.FileKtid:x8}.{asset.Ext}":entry.FullName;
     using var input=entry.Open();using var output=dest.CreateEntry(target,CompressionLevel.Fastest).Open();input.CopyTo(output);
    }
    var identityBytes=SHA256.HashData(Encoding.UTF8.GetBytes("Kashira-Layer2/"+pkg.Name.ToLowerInvariant()))[..16];
    using var marker=new StreamWriter(dest.CreateEntry(Marker).Open());marker.Write(JsonSerializer.Serialize(new{schema=1,mode="Layer2",target="doa6lr",id=new Guid(identityBytes).ToString(),slot,name=pkg.Name,assets=assetRoot},Json));
   }
   var check=KtmodPackage.Load(temporary)??throw new Exception("Converted package could not be read");
   if(check.Legacy.Count!=0)throw new Exception("Converted package still has global legacy replacements");
   File.Move(temporary,pkg.FilePath,true);converted.Add(new{name=pkg.Name,slot,assets=pkg.Legacy.Count});Console.WriteLine($"Layer2: {slot} / {pkg.Name}");
   string journal=Path.Combine(root,"converted_packages.json");
   var history=File.Exists(journal)?JsonSerializer.Deserialize<List<Dictionary<string,string>>>(File.ReadAllText(journal))!:new();
   history.Add(new(){["package"]=Path.GetRelativePath(game,pkg.FilePath),["original"]=Path.GetRelativePath(game,saved),["converted_sha256"]=Hash(pkg.FilePath)});Save(journal,history);
  }
  // Gather now excludes the converted costume payloads. Apply restores their
  // pristine references while retaining the active profile's ordinary effects.
  var gather=ModApplier.Gather(ws,install);var report=PatchEngine.Apply(ws,gather.Replacements);
  if(report.Notes.Any(n=>n.Contains("SKIPPED")))throw new Exception(string.Join("; ",report.Notes));
  Save(statePath,new{version=1,fingerprint=Fingerprint(ws),backup,converted,globalApplied=report.Applied,globalRequested=report.Requested,notFound=report.NotFound.Select(x=>$"0x{x:x8}").ToArray()});
  Console.WriteLine($"Kashira global base rebuilt: {report.Applied}/{report.Requested} ordinary assets. Costume packages remain unloaded until Layer2 selection.");
 }
 static string Fingerprint(GameWorkspace ws) {
  var lines=new List<string>{"adapter-v3-hair"};
  foreach(var file in Directory.GetFiles(ws.ModsDir,"*.ktmod").Order()) {var s=new FileInfo(file);lines.Add($"{s.Name}|{s.Length}|{s.LastWriteTimeUtc.Ticks}");}
  foreach(var file in Directory.GetFiles(ws.DebugModsDir).Order()){var s=new FileInfo(file);lines.Add($"debug:{s.Name}|{s.Length}|{s.LastWriteTimeUtc.Ticks}");}
  if(File.Exists(ws.ProfilesPath))lines.Add(Hash(ws.ProfilesPath));
  foreach(var p in new[]{"root.rdb","root.rdx","system.rdb","system.rdx"})lines.Add(Hash(Path.Combine(ws.PackageDir,p)));
  return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(string.Join('\n',lines))));
 }
}
