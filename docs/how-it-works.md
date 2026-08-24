# How it works

SOLIDWORKS reads its interface text from the language pack folder named by the
active language. The English pack is a folder of about 270 files, of which 60
are resource DLLs, plus two XAML dictionaries. Nothing in it is encrypted or
obfuscated: the text sits in ordinary Win32 resources.

This tool copies the English pack, then rewrites the text inside the copy so
that each short label is followed by the corresponding Chinese label taken from
the Chinese pack of the same build. SOLIDWORKS still loads the English pack and
is unaware anything changed.

## Why the build numbers must match

Resources are addressed by numeric identifier, not by text. String id 4711 in
`sldresu.dll` means whatever that build assigned to it. Identifiers are
reassigned when a build changes, so pairing id 4711 from one build with id 4711
from another produces confident nonsense: a Chinese label for a completely
different command.

The tool reads the file version of `sldresu.dll` from both folders and refuses
to continue when they differ. The version is parsed straight out of the PE
header, so this check also works on a machine without SOLIDWORKS.

## Pass 1 — string tables

Most of the interface lives in `RT_STRING` resources. Windows stores them in
blocks of sixteen, each string prefixed by its length in UTF-16 code units.

For each DLL, the tool reads the English blocks and the Chinese blocks, pairs
them by block identifier, and rewrites the entries that pass the merge rules.
Blocks the Chinese pack does not have are left alone.

Chinese packs sometimes tag their resources with a different language
identifier, so the Chinese side is indexed by block identifier only. Entries are
then written back with the *English* pack's original language identifier, which
is what SOLIDWORKS looks up.

### Two-part entries

MFC stores a toolbar command as one string with two segments separated by a
newline:

```
Extrudes a sketch or selected sketch contours in one or two directions.\nExtruded Boss/Base
```

The first segment is the status-bar description, the second is the command name.
Each segment is judged separately against the merge rules. In practice the
description exceeds the 60-character limit and stays in English, while the
command name becomes bilingual. An entry with more than two segments is a
registration blob — file type associations, ProgIDs — and is never touched.

## Pass 2 — dialog templates

Dialog boxes carry their own text: the window title and the caption of every
button and static label live inside the `DIALOGEX` template, where the string
table pass never sees them.

The template is a packed binary structure. The tool parses it into a header, an
optional font block and a list of controls, then rebuilds it and compares the
result with the original bytes. **If the rebuild does not reproduce the original
exactly, the template is skipped.** This is the safeguard that keeps a
misunderstood structure from being written back in a corrupted form.

Templates that do round-trip are checked against the Chinese template: the
number of controls, and each control's identifier and class, must match.
Captions of buttons and static text are then merged.

### Widening controls

A bilingual caption is longer than the English one, so it can be clipped. After
merging a caption, the tool estimates the new width in dialog units — roughly
four per Latin character, eight per Chinese character — and grows the control by
the difference, but only into empty space: it stops at the left edge of any
control sharing the same rows, and at the dialog border. Controls that sit
inside the item, such as a group box, do not block growth.

Nothing is moved, and no dialog is resized. Where there is no room, the caption
is merged and the control keeps its width, which is the same clipping behaviour
the pack already had for long English text.

## Pass 3 — XAML dictionaries

The PropertyManager, the panel on the left of the SOLIDWORKS window, takes its
text from `DveDictionary.xaml` and `pmdictionary.xaml`. These are plain XML
resource dictionaries:

```xml
<sys:String x:Key="IDS_FILLET_TITLE">Fillet</sys:String>
```

Entries are paired by key and merged with the same rules. Keys containing
`NoTranslation`, and any entry containing escaped markup, are skipped. The
English file's encoding and line endings are preserved byte for byte outside the
replaced text.

## The three checks

Verification compares the built pack with the English original:

1. **Resource inventory.** Every resource type present in the original must
   still be present in the patched file, with at least as many entries. This
   catches a partial or failed resource update, which is the failure mode that
   would otherwise be discovered only when SOLIDWORKS shows an empty menu.
2. **Dialog layout.** Every modified dialog is re-parsed and its controls
   compared with the originals. A control that newly overlaps another, or that
   now crosses the dialog border, is reported. Controls widened into free space
   are counted but are not a problem.
3. **Load test.** Every patched DLL is loaded with the real Windows loader, not
   as a data file. A resource directory that is structurally invalid fails here.

The same three checks are available as standalone scripts —
`src/verify.py`, `src/layout_audit.py`, `src/loadtest.py` — which take
directories as arguments and print a report.

## Diagnostics

| Script | Purpose |
|---|---|
| `src/analyze_skips.py EN.dll CN.dll` | Counts why each string was skipped. Useful when a label you expected to be merged was not |
| `src/find_term.py EN.dll CN.dll Fillet` | Shows the English and Chinese text for entries containing a term, with the merge decision |
| `src/check_terms.py patched.dll` | Spot-checks a list of common command names in a built file |
| `src/dlg_dryrun.py EN_dir CN_dir` | Reports how many dialog templates round-trip cleanly, and what would change |
| `src/probe_types.py X.dll` | Lists the resource types in a file and how many entries each holds |

The `preview` command covers the common case of these and runs on any operating
system.
