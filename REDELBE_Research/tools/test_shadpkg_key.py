from pathlib import Path
import re,json,hashlib
source=Path("external/ShadPKG/core/crypto/keys.h").read_text()

def key_bytes(name):
 match=re.search(r"static constexpr CryptoPP::byte "+name+r"\[\]\s*=\s*\{([^}]+)\}",source)
 return bytes(int(x.strip(),0) for x in match.group(1).split(",") if x.strip())
n=int.from_bytes(key_bytes("Modulus"),"big");d=int.from_bytes(key_bytes("PrivateExponent"),"big");e=int.from_bytes(key_bytes("PublicExponent"),"big")
# Positive control: verify parser and raw RSA with a locally generated valid block.
test=b"\x00\x02"+b"\x55"*221+b"\x00"+b"\x42"*32
control=pow(pow(int.from_bytes(test,"big"),e,n),d,n).to_bytes(256,"big")==test
report={"source_commit":"7a02c1e56b40477b26a660884deda1f3ca8d2eab","positive_control":control,"tested":"Current ShadPKG fake-key RSA stage, independently evaluated; full GUI not run","packages":[]}
for p in Path("analysis/ps4_hair_color/dump").glob("*/*_*.outer_decrypted.bin"):
 if not ("image_key" in p.name or "unknown_21" in p.name): continue
 b=p.read_bytes(); plain=pow(int.from_bytes(b,"big"),d,n).to_bytes(256,"big")
 sep=plain.find(b"\0",2)
 valid=plain[:2]==b"\0\2" and sep>=10 and len(plain)-sep-1==32
 report["packages"].append({"package":p.parent.name,"valid_32_byte_pkcs1_message":valid})
out=Path("analysis/ps4_hair_color/shadpkg_key_test.json")
out.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

