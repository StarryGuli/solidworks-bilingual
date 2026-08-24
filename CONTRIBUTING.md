# Contributing

Thank you for taking the time to look at this project.

## Reporting a problem

Please include:

- The SOLIDWORKS version and build number, from `sldresu.dll` in either pack
  (the `check` command prints it).
- Which step failed: check, preview, build, verify, install.
- The log. The desktop application has a **Save log** button; the command line
  prints the same information.
- For a wrong or awkward translation, the exact label as it appears, so it can
  be found with `preview -t "<part of the label>"`.

Please do not attach language pack files or extracts of their contents. They are
Dassault Systèmes property and cannot be redistributed.

## Working on the code

The project uses the standard library only, and is written to stay that way.
Anything that needs a third-party package belongs in a separate tool.

```
git clone https://github.com/StarryGuli/solidworks-bilingual.git
cd solidworks-bilingual
python -m unittest discover -s tests
```

The tests run on any operating system. To include the tests that need a real
language pack:

```
SWBILINGUAL_SAMPLE_PACK=/path/to/lang/english python -m unittest discover -s tests
```

### Layout

| Path | Contents |
|---|---|
| `src/swbilingual.py` | Pass 1, string tables, and the merge rules |
| `src/swdialogs.py` | Pass 2, dialog templates |
| `src/swxaml.py` | Pass 3, XAML dictionaries |
| `src/verify.py`, `layout_audit.py`, `loadtest.py` | The three standalone checks |
| `src/pipeline.py` | Sequencing, progress reporting, install and restore |
| `src/pe_version.py`, `res_reader.py` | Read-only PE parsing, used by check and preview |
| `src/probe*.py`, `find_term.py`, `analyze_skips.py`, `check_terms.py`, `dlg_dryrun.py` | Diagnostic scripts |
| `swbilingual-cli.py`, `swbilingual-gui.py` | The two interfaces |

The three pass implementations are the part that has been validated against a
real installation. Changes there should come with a clear description of what
was tested and on which build.

### Conventions

- Both interfaces must offer the same capabilities, and every message must exist
  in English and in Chinese.
- Anything written into a resource must survive a byte-for-byte round trip
  first. When a structure cannot be reproduced exactly, skip it rather than
  guess.
- New merge rules need a test in `tests/test_merge_rules.py`, including the case
  that must **not** be merged.

## Continuous integration

| Workflow | What it does |
|---|---|
| [`tests.yml`](.github/workflows/tests.yml) | Runs the test suite on Windows and Linux against Python 3.8 and 3.12, starts the command line in both languages, and builds every widget of the desktop interface on a Windows runner |
| [`release.yml`](.github/workflows/release.yml) | Builds `SWBilingual.exe` and `swbilingual-cli.exe`, checks that both start, and attaches them to a release |

`tests/gui_smoke.py` is the interface check. It builds the whole window, renders
it in both languages, switches through every tab and confirms the pre-flight
check rejects an invalid pair of folders. It is not collected by
`unittest discover`, which only picks up `test*.py`, because it needs a
graphical session.

The Windows job also photographs the interface and uploads the images as a build
artifact named `interface-screenshots`. To refresh the pictures in the
documentation, download that artifact from a completed run and commit the images
under `docs/images/`.

## Releasing

```
git tag v1.2.0
git push origin v1.2.0
```

The release workflow builds the executables from the tag, runs the tests, starts
both executables, and publishes a release with a zip and a `SHA256SUMS.txt`.
Running the workflow manually from the Actions tab performs the same build and
uploads the result as an artifact without creating a release, which is the way
to test a packaging change.

Update [`CHANGELOG.md`](CHANGELOG.md) and the version in `APP_VERSION` at the
top of `swbilingual-gui.py` before tagging.

## Adding a translation of the interface

The interface strings live in the `UI` dictionary at the top of
`swbilingual-gui.py` and in `STRINGS` in `swbilingual-cli.py`. Both are keyed
tables; add a language code with the same keys. `tests/test_inspect.py` checks
that messages carry every language they claim to.
