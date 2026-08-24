# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-24

First public release.

### Added

- Desktop application with an English and a Chinese interface: pack selection,
  pre-flight check, merge preview, build with live progress, install and
  restore.
- Command line interface with `check`, `preview`, `build`, `verify`, `install`,
  `restore` and `locate`, all available in English and Chinese.
- Automatic build-number check. The version is read from `sldresu.dll` in both
  packs and a merge across different builds is refused.
- Merge preview that reads string tables directly from the files, so a pair of
  packs can be inspected on any operating system before anything is written.
- Installation step that backs up the language folder in use before replacing
  it, with a matching restore step.
- Test suite covering the merge rules, the string-block codec, version reading
  and the pre-flight check. Runs on any operating system.
- PyInstaller specification and a build script producing `SWBilingual.exe` and
  `swbilingual-cli.exe`.
- Continuous integration: the test suite runs on Windows and Linux against
  Python 3.8 and 3.12, and the desktop interface is built and photographed on a
  Windows runner.
- Release workflow. Pushing a version tag builds both executables on a clean
  Windows machine, checks that they start, and publishes them with a
  `SHA256SUMS.txt`.
