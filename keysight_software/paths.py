import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIGS_DIR = PROJECT_ROOT / "configs"


def project_path(*parts):
    return PROJECT_ROOT.joinpath(*parts)


def ensure_configs_dir():
    CONFIGS_DIR.mkdir(exist_ok=True)
    return CONFIGS_DIR


def config_path(filename):
    ensure_configs_dir()
    new_path = CONFIGS_DIR / filename
    legacy_path = PROJECT_ROOT / filename
    if legacy_path.exists() and not new_path.exists():
        legacy_path.replace(new_path)
    return new_path


def script_package_config_path(package_dir, filename):
    package_dir = Path(package_dir)
    candidate = package_dir / "configs" / filename
    if candidate.exists():
        return candidate
    return package_dir / filename
