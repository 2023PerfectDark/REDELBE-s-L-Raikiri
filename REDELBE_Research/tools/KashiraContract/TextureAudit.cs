using Kashira.Core.Doa6;
using Kashira.Core.Formats;
using Kashira.Core.Games;
using System.Buffers.Binary;
using System.Text;
using System.Text.Json;

static class TextureAudit {
    public static void Run(string game,string output) {
        using var ex=AssetExtractor.Open(new GameWorkspace(new GameInstall {
            Id="doa6lr",DisplayName="Read-only texture audit",InstallPath=Path.GetFullPath(game),
            PackageDir="fdata_package",Databases=new[]{"root","system"}}));
        var set=Doa6SingletonSet.Load(ex);
        var scn=set.Scn.Records.First(r=>r.Type==Doa6SingletonSet.T_ScnRoot);
        var names=Encoding.ASCII.GetString(scn.Prop(Doa6SingletonSet.P_Names)!.Value).Split('\0',StringSplitOptions.RemoveEmptyEntries);
        var uses=new Dictionary<uint,HashSet<string>>();var rows=new List<object>();
        var errors=new List<string>();
        foreach(var name in names.Where(n=>n.Contains("_COS_")).Distinct()) {
            try {
                var oid=set.CostumeOid(name);var mat=set.ResolveMaterial(oid);var textures=new HashSet<uint>();
                var materials=mat.Mi.Concat(mat.Mrnh.Where((_,i)=>i%2==1)).Distinct();
                foreach(var mbeId in materials) {
                    var mbe=set.MatEditor.Find(mbeId);if(mbe==null)continue;
                    var tbc=set.MatEditor.Find(mbe.ReadU32(Doa6SingletonSet.P_Dm_TbcObj));if(tbc==null)continue;
                    var mpr=ex.Extract(tbc.ReadU32(Doa6SingletonSet.P_Tbc_Ktid));if(mpr==null||mpr.Length%8!=0)continue;
                    for(int i=4;i<mpr.Length;i+=8) {
                        var tid=BinaryPrimitives.ReadUInt32LittleEndian(mpr.AsSpan(i));
                        var tex=set.MatEditor.Find(tid)??set.Ce.Find(tid);if(tex==null)continue;
                        uint fk=tex.ReadU32(Doa6SingletonSet.P_Tex_G1t);if(fk==0)continue;
                        textures.Add(fk);
                    }
                }
                foreach(var fk in textures){if(!uses.ContainsKey(fk))uses[fk]=new();uses[fk].Add(name);}
                rows.Add(new{slot=name,textures=textures.Select(x=>$"0x{x:x8}").Order().ToArray()});
            }catch(Exception e){errors.Add(name+": "+e.Message);}
        }
        var shared=uses.Where(p=>p.Value.Select(n=>n.Split('_')[0]).Distinct().Count()>1)
            .Select(p=>new{id=$"0x{p.Key:x8}",costumes=p.Value.Order().ToArray()}).ToArray();
        Directory.CreateDirectory(output);
        File.WriteAllText(Path.Combine(output,"texture-sharing.json"),JsonSerializer.Serialize(new {
            baseline="Kashira pristine backup indexes (read-only); MI/MRNH material chains only",costumes=rows,shared,errors
        },new JsonSerializerOptions{WriteIndented=true}));
        Console.WriteLine($"Audited {rows.Count} costume chains, {shared.Length} cross-character texture IDs; {errors.Count} unresolved costumes. No game writes.");
        // Offline structural proof only: a private clone for Tina's first costume.
        // No DOK or new resource is installed into the game by this audit.
        uint cos=set.CostumeOid("TIN_COS_001");var mi=set.ResolveMaterial(cos).Mi;
        foreach(var mbeId in mi.Distinct()) {
            var mbe=set.MatEditor.Find(mbeId);if(mbe==null)continue;
            var tbc=set.MatEditor.Find(mbe.ReadU32(Doa6SingletonSet.P_Dm_TbcObj));if(tbc==null)continue;
            var mpr=ex.Extract(tbc.ReadU32(Doa6SingletonSet.P_Tbc_Ktid));if(mpr==null)continue;
            for(int i=4;i<mpr.Length;i+=8) {
                var texId=BinaryPrimitives.ReadUInt32LittleEndian(mpr.AsSpan(i));
                var tex=set.MatEditor.Find(texId)??set.Ce.Find(texId);if(tex==null)continue;
                uint original=tex.ReadU32(Doa6SingletonSet.P_Tex_G1t);
                if(!uses.TryGetValue(original,out var users)||!users.Any(n=>n.StartsWith("KAS_")))continue;
                var payload=ex.Extract(original);if(payload==null)continue;
                var before=set.MatEditor.Records.ToDictionary(r=>r.Oid,r=>r.Build());
                uint privateFk=set.AllocFk();
                var cloned=MaterialChainFactory.Create(set,mbeId,new Dictionary<int,uint>{{i/8,privateFk}});
                foreach(var pair in before)
                    if(!set.MatEditor.Find(pair.Key)!.Build().SequenceEqual(pair.Value))throw new Exception("Clone mutated original material record");
                var proof=Path.Combine(output,"private_tina_proof");Directory.CreateDirectory(proof);
                File.WriteAllBytes(Path.Combine(proof,$"0x{privateFk:x8}.g1t"),payload);
                foreach(var asset in cloned.NewAssets)File.WriteAllBytes(Path.Combine(proof,$"0x{asset.FileKtid:x8}.{asset.Ext}"),asset.Bytes);
                foreach(var dok in set.DirtyBytes()) {
                    var parsed=SingletonDb.Parse(dok.Value);
                    if(parsed.Find(cloned.MbeOid)==null)throw new Exception("Serialized clone missing");
                    File.WriteAllBytes(Path.Combine(proof,$"0x{dok.Key:x8}.dok"),dok.Value);
                }
                File.WriteAllText(Path.Combine(proof,"proof.json"),JsonSerializer.Serialize(new {
                    status="STRUCTURAL PROOF ONLY - NOT INSTALLED OR IN-GAME TESTED",costume="TIN_COS_001",
                    originalTexture=$"0x{original:x8}",privateTexture=$"0x{privateFk:x8}",
                    originalMaterial=$"0x{mbeId:x8}",privateMaterial=$"0x{cloned.MbeOid:x8}",
                    preservedOriginalMaterialRecords=before.Count,sharedWith=users.Where(n=>n.StartsWith("KAS_")||n.StartsWith("HEL_")||n.StartsWith("HON_")).Order().ToArray(),
                    remaining="Repoint only Tina's costume, register new resources against live Kashira indexes, route Layer2 replacements to private IDs, then test two characters together."
                },new JsonSerializerOptions{WriteIndented=true}));
                Console.WriteLine($"Private Tina material clone verified: {original:x8} -> {privateFk:x8}; {before.Count} original records preserved.");return;
            }
        }
        throw new Exception("No shared Tina/Kasumi material found for private-clone proof");
    }
}
