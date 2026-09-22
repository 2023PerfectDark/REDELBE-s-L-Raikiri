using Kashira.Core.Formats;
using System.Text.Json;
using System.Security.Cryptography;
static class RestoreTextures {
 public static void Run(string dir) {
  using var plan=JsonDocument.Parse(File.ReadAllText(Path.Combine(dir,"restoration_plan.json")));
  var original=File.ReadAllBytes(Path.Combine(dir,"MaterialEditor.before.dok"));
  if(!Convert.ToHexString(SHA256.HashData(original)).Equals(plan.RootElement.GetProperty("lr_material_sha256").GetString(),StringComparison.OrdinalIgnoreCase))throw new Exception("Baseline hash mismatch");
  var db=SingletonDb.Parse(original);
  if(!db.Serialize().SequenceEqual(original))throw new Exception("Baseline does not roundtrip byte exactly");
  var before=db.Records.ToDictionary(r=>r.Oid,r=>r.Build());
  var changed=new HashSet<uint>();
  foreach(var change in plan.RootElement.GetProperty("changes").EnumerateArray()) {
   uint oid=change.GetProperty("oid").GetUInt32(),from=change.GetProperty("lr_resource").GetUInt32(),to=change.GetProperty("old_resource").GetUInt32();
   var rec=db.Find(oid)??throw new Exception($"Missing record {oid:x8}");
   if(rec.Type!=0xff7dbfd4||rec.ReadU32(0x6c7321d2)!=from||!changed.Add(oid))throw new Exception("Reference conflict; regenerate plan for current game");
   if(!rec.SetU32(0x6c7321d2,to))throw new Exception("Property missing");
  }
  foreach(var r in db.Records)if(!changed.Contains(r.Oid)&&!r.Build().SequenceEqual(before[r.Oid]))throw new Exception("Unrelated record changed");
  var result=db.Serialize();var verify=SingletonDb.Parse(result);
  foreach(var c in plan.RootElement.GetProperty("changes").EnumerateArray())if(verify.Find(c.GetProperty("oid").GetUInt32())!.ReadU32(0x6c7321d2)!=c.GetProperty("old_resource").GetUInt32())throw new Exception("Verification failed");
  File.WriteAllBytes(Path.Combine(dir,"0xd956e4a2.dok"),result);
  Console.WriteLine($"PASS: {changed.Count} texture references restored; {before.Count-changed.Count} other records preserved byte-for-byte; LR database version retained. Offline only.");
 }
}
