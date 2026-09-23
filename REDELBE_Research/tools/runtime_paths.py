"""Internal files live outside the public editable mod folder."""
from pathlib import Path

INTERNAL = {'bridge_tools', 'install_backups', 'Notices', 'bridge.json',
            'installed_files.json', 'settings.schema.json'}

def internal_root(game):
    app = Path(game) / "REDELBE's Last Raikiri"
    return app / '_REDELBE_Runtime (Not important to you)' / 'Data'

def internal_path(game, name):
    new = internal_root(game) / name
    old = Path(game) / 'REDELBE_LR' / name
    # Older installations keep working until migrated by the installer.
    return new if new.exists() or internal_root(game).exists() else old

def install_target(game, name):
    parts = Path(name).parts
    if len(parts) > 1 and parts[0] == 'REDELBE_LR' and parts[1] in INTERNAL:
        return internal_root(game).joinpath(*parts[1:])
    from kashira_bridge import safe_child
    return safe_child(game, name)
