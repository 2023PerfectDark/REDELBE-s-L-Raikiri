"""Portable local-only animation library preparation; never modifies game archives."""
import argparse
import json
import sys
from pathlib import Path
from prepare_animation_library import prepare


def find_game(start):
    start = Path(start).resolve()
    for path in (start, *start.parents):
        if (path / 'DOA6LR.exe').is_file() and (path / 'fdata_package').is_dir():
            return path
    raise ValueError('Place this tool inside the DOA6LR game folder, or use --game PATH.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-pause', action='store_true')
    args = parser.parse_args()
    try:
        home = Path(sys.executable if getattr(sys, 'frozen', False) else __file__).parent
        game = find_game(args.game or home)
        bundle = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
        catalog = bundle / 'animation_names.json'
        output = args.output or game / 'REDELBE_LR' / 'AnimationBrowser'
        print('Reading animations from:', game)
        print('Preparing the local library. Game archives will not be changed.', flush=True)
        result = prepare(game, catalog, output)
        print(json.dumps(result))
        if not result['prepared']:
            raise ValueError('No supported animations were found. Keep the browser disabled.')
        print('Library ready. Enable [AnimationBrowser] enabled = true in REDELBE.ini.')
        print('Restart the game, open a character in Wardrobe, then press F8.')
        print('Matching animation cameras are prepared locally. C / Back toggles camera controls.')
        code = 0 if not result['errors'] else 2
    except (OSError, ValueError, KeyError) as exc:
        print('Preparation failed:', exc)
        code = 1
    if getattr(sys, 'frozen', False) and not args.no_pause:
        input('Press Enter to close.')
    return code


if __name__ == '__main__':
    sys.exit(main())
