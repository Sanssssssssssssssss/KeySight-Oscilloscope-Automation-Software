import shutil
import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    BUNDLE_ROOT = Path(__file__).resolve().parent.parent
    PROJECT_ROOT = BUNDLE_ROOT

CONFIGS_DIR = PROJECT_ROOT / "configs"
BUNDLED_CONFIGS_DIR = BUNDLE_ROOT / "configs"


def project_path(*parts):
    return PROJECT_ROOT.joinpath(*parts)


def bundled_path(*parts):
    return BUNDLE_ROOT.joinpath(*parts)


def ensure_configs_dir():
    CONFIGS_DIR.mkdir(exist_ok=True)
    return CONFIGS_DIR


def config_path(filename):
    ensure_configs_dir()
    writable_path = CONFIGS_DIR / filename
    legacy_path = PROJECT_ROOT / filename
    bundled_config = BUNDLED_CONFIGS_DIR / filename

    if legacy_path.exists() and not writable_path.exists():
        legacy_path.replace(writable_path)
    elif bundled_config.exists() and not writable_path.exists():
        shutil.copy2(bundled_config, writable_path)

    return writable_path


def script_package_config_path(package_dir, filename):
    package_dir = Path(package_dir)
    candidate = package_dir / "configs" / filename
    if candidate.exists():
        return candidate
    return package_dir / filename
