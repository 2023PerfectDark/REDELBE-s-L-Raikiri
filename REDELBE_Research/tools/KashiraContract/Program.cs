using Kashira.Core.Mods;
using System.IO.Compression;
if(args[0]=="restore-textures") { RestoreTextures.Run(args[1]);return; }
if(args[0]=="check-project") {
 var p=KtmodProject.Load(args[1]);var list=ProjectContent.ListLegacy(p);
 p.Build(args[2]);var package=KtmodPackage.Load(args[2])??throw new Exception("Build rejected");
 if(package.Legacy.Count!=0||package.BuildReplacements().Count!=0)throw new Exception("Layer2 build has global replacements");
 Console.WriteLine($"PASS: actual Editor enumerates {list.Count} content files and builds a Layer2 package with no global replacements.");return;
}
if(args[0]=="audit") { TextureAudit.Run(args[1],args[2]);return; }
if(args[0]=="inventory") { PackageInventory.Run(args[1],args[2]);return; }
if(args[0]=="verify-native") { PackageInventory.Verify(args[1]);return; }
var root=Path.GetFullPath(args[0]);
int assets=0,packages=0;
foreach(var file in Directory.GetFiles(Path.Combine(root,"Mods"),"*.ktmod")) {
    var mod=KtmodPackage.Load(file)??throw new Exception("Kashira rejected package "+file);
    if(!mod.Target.Equals("doa6lr",StringComparison.OrdinalIgnoreCase)||mod.Legacy.Count!=0||mod.CostumeManifests.Count!=0||mod.BuildReplacements().Count!=0)
        throw new Exception("Package could apply global replacements: "+file);
    packages++;
}
foreach(var file in Directory.GetFiles(Path.Combine(root,"KashiraProjects"),"*.ktproj",SearchOption.AllDirectories)) {
    var project=KtmodProject.Load(file);
    var list=ProjectContent.ListLegacy(project);
    assets+=list.Count(f=>f.Ktid.HasValue);
    if(!list.Any(f=>f.FileName=="redelbe_layer2.json"))throw new Exception("Editor omitted marker");
}
var first=Directory.GetFiles(Path.Combine(root,"KashiraProjects"),"*.ktproj",SearchOption.AllDirectories).First();
var output=Path.Combine(root,"contract-roundtrip.ktmod");
KtmodProject.Load(first).Build(output);
var check=KtmodPackage.Load(output)??throw new Exception("Editor output rejected");
using(var zip=ZipFile.OpenRead(output)) {
    if(zip.GetEntry("Content_Legacy/redelbe_layer2.json")==null||check.Legacy.Count!=0)
        throw new Exception("Editor roundtrip lost Layer2 contract");
}
Console.WriteLine($"PASS: {packages} manager packages, {assets} editor assets; actual Editor Build roundtrip preserves Layer2 marker and nested files without global replacements.");
