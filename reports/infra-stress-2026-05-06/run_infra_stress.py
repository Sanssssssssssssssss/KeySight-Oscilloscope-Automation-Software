from __future__ import annotations

import csv
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path(r"D:\GPT_Project\KeysightSoftware\.venv\Scripts\python.exe")
if not PYTHON.exists():
    PYTHON = Path(sys.executable)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_command(args: list[str], timeout: int = 120) -> dict:
    start = time.perf_counter()
    proc = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "args": args,
        "returncode": proc.returncode,
        "seconds": round(time.perf_counter() - start, 3),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def time_command(name: str, args: list[str], iterations: int, timeout: int = 120) -> dict:
    runs = []
    for index in range(iterations):
        result = run_command(args, timeout=timeout)
        result["iteration"] = index + 1
        runs.append(result)
    seconds = [run["seconds"] for run in runs]
    return {
        "name": name,
        "iterations": iterations,
        "passes": sum(1 for run in runs if run["returncode"] == 0),
        "failures": sum(1 for run in runs if run["returncode"] != 0),
        "min_seconds": round(min(seconds), 3),
        "avg_seconds": round(sum(seconds) / len(seconds), 3),
        "max_seconds": round(max(seconds), 3),
        "runs": runs,
    }


def collect_environment() -> dict:
    pip_list = run_command([str(PYTHON), "-m", "pip", "list"], timeout=60)
    pip_check = run_command([str(PYTHON), "-m", "pip", "check"], timeout=60)
    git_head = run_command(["git", "rev-parse", "HEAD"], timeout=20)
    git_status = run_command(["git", "status", "--short"], timeout=20)
    git_files = run_command(["git", "ls-files"], timeout=20)
    return {
        "python": run_command([str(PYTHON), "--version"], timeout=20),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "pip_list": pip_list,
        "pip_check": pip_check,
        "git_head": git_head,
        "git_status": git_status,
        "tracked_file_count": len(git_files["stdout"].splitlines()),
    }


def import_pressure() -> dict:
    modules = [
        "keysight_software.config",
        "keysight_software.paths",
        "keysight_software.device.oscilloscope",
        "keysight_software.device.measure",
        "keysight_software.qt_app.app",
        "keysight_software.qt_app.window",
        "keysight_software.qt_app.pages.home",
        "keysight_software.qt_app.pages.waveform_capture",
        "keysight_software.qt_app.pages.axis_control",
        "keysight_software.qt_app.pages.script_editor",
        "keysight_software.qt_app.pages.run_script",
        "keysight_software.qt_app.pages.batch_process",
        "keysight_software.qt_app.pages.settings",
        "keysight_software.utils.waveform",
    ]
    start = time.perf_counter()
    records = []
    for module in modules:
        module_start = time.perf_counter()
        importlib.import_module(module)
        records.append(
            {"module": module, "seconds": round(time.perf_counter() - module_start, 4)}
        )
    return {
        "modules": len(modules),
        "seconds": round(time.perf_counter() - start, 4),
        "records": records,
    }


def qt_pressure() -> dict:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QPushButton
    from keysight_software.qt_app.window import MainWindow

    app = QApplication.instance() or QApplication([])
    tracemalloc.start()
    start = time.perf_counter()
    window = MainWindow()
    window.resize(1100, 720)
    window.show()
    app.processEvents()

    keys = list(window.page_indexes.keys())
    cycles = 200
    text_fit_issues = []
    for _ in range(cycles):
        for key in keys:
            window.show_page(key)
            app.processEvents()
            for widget in window.findChildren(QPushButton):
                if not widget.isVisible() or not widget.text().strip() or widget.width() <= 0:
                    continue
                if widget.sizeHint().width() > widget.width() + 8:
                    text_fit_issues.append(
                        {
                            "page": key,
                            "text": widget.text(),
                            "width": widget.width(),
                            "hint": widget.sizeHint().width(),
                        }
                    )
    current, peak = tracemalloc.get_traced_memory()
    elapsed = time.perf_counter() - start
    window.close()
    app.processEvents()
    return {
        "pages": len(keys),
        "cycles": cycles,
        "operations": len(keys) * cycles,
        "seconds": round(elapsed, 3),
        "current_mb": round(current / 1024 / 1024, 3),
        "peak_mb": round(peak / 1024 / 1024, 3),
        "text_fit_issues_count": len(text_fit_issues),
        "text_fit_issues_sample": text_fit_issues[:20],
    }


def config_io_pressure() -> dict:
    from keysight_software import paths

    originals = (
        paths.PROJECT_ROOT,
        paths.BUNDLE_ROOT,
        paths.CONFIGS_DIR,
        paths.BUNDLED_CONFIGS_DIR,
    )
    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as temp_dir:
        runtime = Path(temp_dir) / "runtime"
        bundle = Path(temp_dir) / "bundle"
        (bundle / "configs").mkdir(parents=True)
        runtime.mkdir()
        for index in range(1000):
            (bundle / "configs" / f"config_{index}.json").write_text(
                json.dumps({"index": index, "payload": "x" * 256}),
                encoding="utf-8",
            )

        paths.PROJECT_ROOT = runtime
        paths.BUNDLE_ROOT = bundle
        paths.CONFIGS_DIR = runtime / "configs"
        paths.BUNDLED_CONFIGS_DIR = bundle / "configs"
        for index in range(1000):
            resolved = paths.config_path(f"config_{index}.json")
            if not resolved.exists():
                raise RuntimeError(f"config copy failed: {resolved}")
        copied = len(list((runtime / "configs").glob("*.json")))

    paths.PROJECT_ROOT, paths.BUNDLE_ROOT, paths.CONFIGS_DIR, paths.BUNDLED_CONFIGS_DIR = originals
    return {"files": copied, "seconds": round(time.perf_counter() - start, 3)}


def waveform_export_pressure() -> dict:
    from keysight_software.utils.waveform import write_waveforms_to_csv

    channels = 4
    samples = 50000
    time_axis = [index * 1e-9 for index in range(samples)]
    waveforms = {
        channel: (time_axis, [channel * 0.1 + (index % 500) * 0.001 for index in range(samples)])
        for channel in range(1, channels + 1)
    }
    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "large_waveform.csv"
        write_waveforms_to_csv(csv_path, waveforms)
        size_bytes = csv_path.stat().st_size
        with csv_path.open(newline="", encoding="utf-8") as handle:
            row_count = sum(1 for _ in csv.reader(handle))
    return {
        "channels": channels,
        "samples_per_channel": samples,
        "rows": row_count,
        "size_mb": round(size_bytes / 1024 / 1024, 3),
        "seconds": round(time.perf_counter() - start, 3),
    }


def repo_hygiene_scan() -> dict:
    tracked = run_command(["git", "ls-files"], timeout=30)["stdout"].splitlines()
    status = run_command(["git", "status", "--short"], timeout=30)["stdout"].splitlines()
    generated_patterns = [
        "__pycache__/",
        ".pyc",
        "_internal/",
        "build/",
        ".idea/",
        ".vscode/",
        ".exe",
        "screenshot.png",
        "waveform_channel_3.csv",
    ]
    generated_tracked = [
        path
        for path in tracked
        if any(pattern in path or path.endswith(pattern) for pattern in generated_patterns)
    ]
    largest = []
    for path in tracked:
        full_path = ROOT / path
        if full_path.exists() and full_path.is_file():
            largest.append((path, full_path.stat().st_size))
    largest.sort(key=lambda item: item[1], reverse=True)
    return {
        "tracked_files": len(tracked),
        "dirty_entries": len(status),
        "dirty_sample": status[:40],
        "generated_tracked_count": len(generated_tracked),
        "generated_tracked_sample": generated_tracked[:80],
        "largest_tracked_files": [
            {"path": path, "size_mb": round(size / 1024 / 1024, 3)}
            for path, size in largest[:20]
        ],
    }


def packaging_probe() -> dict:
    spec_exists = (ROOT / "build.spec").exists()
    pyinstaller = run_command([str(PYTHON), "-m", "PyInstaller", "--version"], timeout=30)
    existing_exe = ROOT / "KeysightSoftware.exe"
    existing_exe_size = existing_exe.stat().st_size if existing_exe.exists() else None
    return {
        "spec_exists": spec_exists,
        "pyinstaller": pyinstaller,
        "existing_exe_size_mb": round(existing_exe_size / 1024 / 1024, 3) if existing_exe_size else None,
    }


def main() -> int:
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")
    results = {
        "started_at": started_at,
        "root": str(ROOT),
        "environment": collect_environment(),
        "compileall": time_command(
            "compileall",
            [
                str(PYTHON),
                "-m",
                "compileall",
                "main.py",
                "main_tk.py",
                "main_qt.py",
                "keysight_software",
                "tests",
            ],
            iterations=5,
            timeout=120,
        ),
        "unittest": time_command(
            "unittest",
            [str(PYTHON), "-m", "unittest", "discover", "-s", "tests", "-v"],
            iterations=10,
            timeout=180,
        ),
        "import_pressure": import_pressure(),
        "qt_pressure": qt_pressure(),
        "config_io_pressure": config_io_pressure(),
        "waveform_export_pressure": waveform_export_pressure(),
        "repo_hygiene": repo_hygiene_scan(),
        "packaging_probe": packaging_probe(),
        "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    output_path = Path(__file__).with_name("results.json")
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
