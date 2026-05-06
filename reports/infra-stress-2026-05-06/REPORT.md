# Infra Stress Report

Date: 2026-05-06
Repository: `D:\GPT_Project\KeysightSoftware_mainmerge`
Commit: `cb33ee1`
Python: `3.13.0`
OS: Windows 11 `10.0.26200`, AMD64

## Executive Summary

The application infrastructure is functionally healthy under a larger local stress pass. Source compilation, repeated unit tests, dependency checks, Qt page switching, config I/O, waveform CSV export, PyInstaller packaging, and packaged executable startup all passed.

Two areas need attention before treating the repository as release-grade infrastructure:

- The Qt UI still has text-fit pressure at narrower widths. The stress run found repeated button sizeHint overflow cases, especially on `Home`, `Capture`, and `Script Editor`.
- The repository is carrying many generated and packaged artifacts in Git. The scan counted 1053 tracked files that look like build outputs, IDE files, caches, binaries, or generated runtime files.

## Test Matrix

| Area | Load | Result | Key Metric |
| --- | ---: | --- | --- |
| Python compile | 5 iterations | PASS | avg `0.095s`, max `0.097s` |
| Unit tests | 10 iterations | PASS | 10/10 pass, avg `3.708s`, max `6.144s` |
| Dependency health | `pip check` | PASS | no broken requirements |
| Import pressure | 14 application modules | PASS | total `1.342s` |
| Qt page switching | 7 pages x 200 cycles | PASS with UI warnings | 1400 switches in `7.012s`, peak traced memory `4.298 MB` |
| UI text fit audit | 1400 page states | WARN | 4600 cumulative overflow observations |
| Config path I/O | 1000 bundled config copies | PASS | `1.882s` |
| Waveform CSV export | 4 channels x 50,000 samples | PASS | 50,001 rows, `2.89 MB`, `1.116s` |
| PyInstaller build | clean single-file build | PASS | `162.684s` |
| Packaged exe smoke | launch and hold 15s | PASS | still running after 15s |
| Repo hygiene scan | tracked files | WARN | 1113 tracked files, 1053 generated-looking files |

## Packaging Result

PyInstaller successfully produced a standalone executable:

- Path: `reports/infra-stress-2026-05-06/dist/KeysightSoftware.exe`
- Size: `84,119,298 bytes`
- SHA256: `749D5F01A4DC9D7245014648C56AAEEE6954C4901724A903B044970DC1E307D6`
- Smoke result: PASS, process was still running after 15 seconds

The `dist/` and `pyinstaller-work/` directories are ignored by the report-local `.gitignore` because they are generated artifacts. The build metrics above are preserved here.

## Detailed Findings

### 1. Runtime and tests are stable

All repeated test runs passed. The 10-run test suite showed normal timing variation, with the slowest run at `6.144s`. No dependency breakage was reported by `pip check`.

### 2. Qt page switching performs well

The Qt stress loop switched through all 7 pages for 200 cycles. That produced 1400 page changes in `7.012s`. Traced Python memory stayed low at about `4.3 MB` peak during the run. This is a good signal for basic navigation stability.

### 3. UI text fit still needs polish

The button audit found repeated width pressure. Representative cases:

- `Home`: `Detect`, `Connect`, `Browse`, `Save`
- `Capture`: `Edit Measurements`, `Capture Now`, `Save Defaults`
- `Axis`: `Apply Settings`
- `Script Editor`: `Clear Middle Steps`, `Move Down`, `Validate Sequence`, `Browse Save Folder`

This does not mean every button is visibly broken at every size, but it does mean Qt's requested text width is larger than the actual button width in stressed layouts. We should treat this as a real UI resilience issue.

### 4. Config and data export paths are solid

The config path layer copied 1000 bundled JSON files into a writable config directory in `1.882s`. Waveform export wrote 4 channels x 50,000 samples to CSV in `1.116s`. These are healthy numbers for the current desktop workflow.

### 5. Repository hygiene is the biggest infra risk

The repo currently tracks many files that normally should live in release artifacts or local build outputs:

- `_internal/`
- `build/`
- `KeysightSoftware.exe`
- `__pycache__/`
- `.idea/`
- generated CSV/screenshots

The scan found 1053 generated-looking tracked files out of 1113 tracked files. That makes diffs noisy, increases clone size, and raises the chance of stale packaged runtime files being mixed into source changes.

## Recommendations

1. Fix Qt text-fit pressure before the next UI release.
   Suggested approach: use compact labels where needed, set sane minimum widths for command buttons, and convert dense tool commands to icon+tooltip controls where the action is obvious.

2. Clean the repository artifact strategy.
   Suggested approach: keep source, configs, docs, tests, and build spec in Git; move exe, `_internal/`, and build output to GitHub Releases.

3. Strengthen `.gitignore`.
   Suggested entries: `.venv/`, `.idea/`, `__pycache__/`, `*.pyc`, `build/`, `dist/`, `_internal/`, `*.spec` only if generated, local CSV exports, screenshots, and report build output.

4. Add Windows CI.
   Minimum useful workflow: install dependencies, run `compileall`, run unit tests, and optionally run PyInstaller on release tags.

5. Add versioned release notes.
   A `CHANGELOG.md` would make the project easier to trust and maintain as releases continue.

## Limitations

This run did not test real oscilloscope hardware, long-duration VISA communication, or fresh-machine antivirus behavior. Those need physical hardware or a separate clean Windows VM. The current stress run focused on local app infrastructure and release packaging.

## Raw Data

Raw machine-readable results are in `results.json`. The repeatable runner is `run_infra_stress.py`.
