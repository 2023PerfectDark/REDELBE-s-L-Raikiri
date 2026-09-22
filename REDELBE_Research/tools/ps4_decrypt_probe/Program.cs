using System;
using System.IO;
using System.Linq;
using System.Numerics;
using LibOrbisPkg.PKG;
using LibOrbisPkg.Util;
class Program {
static void Main(string[] args) {
foreach(var path in args) {
using var s=File.OpenRead(path); var p=new PkgReader(s).ReadPkg();
Console.WriteLine(Path.GetFileName(path));
var meta=p.Metas.Metas.First(m=>(uint)m.id==0x20 || (uint)m.id==0x21);
s.Position=meta.DataOffset; var b=new byte[meta.DataSize]; s.ReadExactly(b);
var layer=Entry.Decrypt(b,p,meta);
var key=RSAKeyset.FakeKeyset;
var m=BigInteger.ModPow(new BigInteger(layer,true,true),new BigInteger(key.PrivateExponent,true,true),new BigInteger(key.Modulus,true,true)).ToByteArray(true,true);
var block=new byte[256]; m.CopyTo(block,256-m.Length);
int separator=Array.IndexOf(block,(byte)0,2);
bool padding=block[0]==0 && block[1]==2 && separator>=10;
Console.WriteLine("Independent raw RSA fake-key PKCS1 padding valid: "+padding);
Console.WriteLine("Filesystem key verified: "+(padding && p.CheckEkpfs(block.Skip(separator+1).ToArray())));
}
}}
