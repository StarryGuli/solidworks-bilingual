# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-08-25

### Fixed

- An installation outside `C:` was not found. The SOLIDWORKS folder is now read
  from the registry, and every drive letter is tried as a fallback, so an
  installation on `E:` is located like any other.
- Selecting a Chinese pack folder that holds no DLLs reported only that nothing
  was there. The error now names the folders beside it that do contain a pack
  and says which Chinese script each one is written in, which is what a `lang`
  folder holding both `chinese` and `chinese-simplified` needs.
- The redundant second error about missing counterparts is no longer printed
  when one side is already reported as empty.

### Added

- Simplified and Traditional Chinese are told apart by reading the pack rather
  than by its folder name. SOLIDWORKS ships Chinese and Chinese Simplified as
  separate languages and installations disagree about which folder holds which:
  a folder named `chinese` contains Traditional Chinese on some machines and
  Simplified on others. `check` reports the script it found, and the desktop
  application logs it.
- **Find installed packs** on the Build tab fills in both source folders,
  choosing the Chinese pack by what it contains.

### Changed

- The documentation no longer states that the Chinese pack lives in
  `lang\chinese`. It explains that the folder name does not settle the question
  and that the tool reports what is actually inside.

## [1.0.0] - 2026-08-24

First public release.

### Fixed

- Output no longer fails on a Windows console using a legacy code page. Printing
  Chinese raised `UnicodeEncodeError` and ended the program, which affected the
  English interface as well because its own description contains the phrase
  "English 中文". The console is now asked for UTF-8 and the streams replace
  anything that still cannot be represented.

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
