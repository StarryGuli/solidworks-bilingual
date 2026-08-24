# Troubleshooting

## The tool refuses to start the build

**"Build numbers differ: English 33.0.0.5050, Chinese 32.2.0.4020"**

The two packs come from different SOLIDWORKS builds and cannot be merged. Their
resource identifiers refer to different strings, so the result would pair
unrelated labels. Install the Chinese pack matching your current build by
running the SOLIDWORKS installer again and adding Chinese as a language.

**"No DLL in the English folder has a counterpart in the Chinese folder"**

One of the paths is not a language pack. The pack folder contains
`sldresu.dll` and roughly 270 files. Its parent, `lang`, is one level up.

**"Could not read sldresu.dll"**

The folder is not a language pack, or the file is unreadable. The build proceeds
with a warning, but check the paths first.

## The build fails partway

**"Access is denied" or a permission error**

The output folder is not writable, or SOLIDWORKS has the files open. Choose an
output folder outside `Program Files`, for example `D:\bilingual`.

**Individual files reported as skipped**

Files without a Chinese counterpart, and files with nothing mergeable, are
normal — a few DLLs contain only bitmaps or cursors. A skipped file keeps its
original English content.

## Verification reports problems

**Controls past the right edge**

A widened control no longer fits its dialog. The dialog still works, but a label
may be clipped. Report it with the dialog name from the log.

**A DLL failed to load**

The patched file is not usable. Do not install the pack. Rebuild, and if the
same file fails again, open an issue with the file name and build number.

## After installing

**SOLIDWORKS still shows English only**

- SOLIDWORKS was not restarted.
- The pack was installed into the wrong folder. Check with
  `swbilingual-cli.py locate` that the folder replaced is the one under the
  running SOLIDWORKS installation, and confirm the tool did not report a
  permission error.
- SOLIDWORKS is set to a language other than English, so a different pack is in
  use. Either switch the interface language to English, or build the bilingual
  pack against the language you actually use.

**SOLIDWORKS does not start, or menus are empty**

Restore the backup and restart:

```
python swbilingual-cli.py restore "C:\...\lang\english.backup-20260824-153000" "C:\...\lang\english"
```

The backup folder sits next to the language folder and is named after the moment
of installation.

**Security software flags a patched DLL**

Editing resources invalidates the digital signature of each patched file, so a
signature check now fails. This is expected. If the software quarantines files,
restore the backup, then either add an exclusion or run without the bilingual
pack.

**A label reads badly, or shows an empty pair of brackets**

A small number of Chinese labels put the keyboard accelerator inside brackets;
when the marker is removed the brackets remain, for example `从组中移除()`. On
the reference build this affects 16 of 25,033 merged entries. Report the label
if it bothers you in daily use.

## Rebuilding after a SOLIDWORKS update

An update replaces the language pack. Run the build again with the new English
and Chinese packs, then install as before. Old backups can be deleted once the
new pack works.

## Getting help

Open an issue with the build number, the step that failed, and the log
(**Save log** in the desktop application). Do not attach language pack files.
