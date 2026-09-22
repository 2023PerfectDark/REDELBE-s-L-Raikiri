"""Shared pair resolution for Open, Explorer drops and in-window drops."""
from pathlib import Path

def sibling(path,suffix):
    path=Path(path)
    wanted=path.stem.casefold()+suffix.casefold()
    matches=[p for p in path.parent.iterdir() if p.is_file() and p.name.casefold()==wanted]
    return matches[0] if len(matches)==1 else path.with_suffix(suffix)

def resolve(path,choose=None,pair=None):
    path=Path(path).resolve()
    if path.suffix.lower()=='.srst':
        stream=path;bank=sibling(path,'.srsa')
        if not bank.is_file() and choose:bank=choose('Select the SRSA bank matching '+path.name,'.srsa')
        if not bank or not Path(bank).is_file():raise ValueError('SRST requires its matching SRSA bank. Select or place the matching SRSA beside it.')
        return Path(bank).resolve(),stream
    if path.suffix.lower()!='.srsa':raise ValueError('Choose an SRSA bank or its matching SRST file.')
    return path,Path(pair).resolve() if pair else sibling(path,'.srst')

def choose_inputs(path,choose):
    from srsa_lr import Bank
    bank,pair=resolve(path,choose)
    data=bank.read_bytes();parsed=Bank(data)
    if any(parsed.info(p,e)['codec']=='external-ogg' for p,e in parsed.entries):
        valid=False
        if pair.is_file():
            with pair.open('rb') as f:valid=f.read(4) in (b'TSRS',b'KTSR')
        if not valid:
            selected=choose('Select the matching SRST for '+bank.name,'.srst')
            if not selected:raise ValueError('Opening cancelled: streamed audio requires its matching SRST.')
            pair=Path(selected)
    return bank,pair
