# Command line reference

```
python swbilingual-cli.py [-q] [-l {en,zh}] <command> ...
```

`--lang zh` prints every message in Chinese. Without it, the language is taken
from `SWBILINGUAL_LANG`, then from the system locale.

`--quiet` suppresses the progress bar; log lines are still printed.

Exit status is `0` on success and `1` when a command reports a problem, which
makes the commands usable in a script.

---

## check

```
python swbilingual-cli.py check <english> <chinese>
```

Compares two language packs without writing anything: DLL counts, build numbers
read from `sldresu.dll`, how many files exist on both sides, and whether the
XAML dictionaries are present. Exits with `1` when the packs cannot be merged.

Runs on any operating system.

## preview

```
python swbilingual-cli.py preview <english> <chinese> [-n 25] [-t TERM] [-f FILE]
```

Shows what the merge would produce. Reads string tables directly from the files,
so nothing is written and Windows is not required.

| Option | Meaning |
|---|---|
| `-n`, `--limit` | How many examples to print. Default 25 |
| `-t`, `--term` | Only entries whose English text contains this word |
| `-f`, `--file` | Restrict the preview to one DLL, for example `sldresu.dll` |

The header line reports how many string pairs were examined and how many would
become bilingual.

## build

```
python swbilingual-cli.py build <english> <chinese> <output>
```

Copies the English pack to the output folder, then runs the three merge passes
over the copy. The source folders are only read. Verification runs afterwards
unless `--no-verify` is given.

| Option | Meaning |
|---|---|
| `--no-copy` | The output folder already holds a copy of the English pack |
| `--no-verify` | Do not run the checks after building |

Requires Windows.

## verify

```
python swbilingual-cli.py verify <english> <output>
```

Runs the three checks against an existing built pack: resource inventory, dialog
layout, and loading every DLL. Requires Windows.

## install

```
python swbilingual-cli.py install <source> <target> [-y]
```

Copies the current contents of `<target>` to
`<target>.backup-YYYYmmdd-HHMMSS`, then copies the built pack over `<target>`.
Asks for confirmation unless `-y` is given.

Close SOLIDWORKS first and run the command from an administrator command
prompt.

## restore

```
python swbilingual-cli.py restore <backup> <target>
```

Copies a backup back over the language folder.

## locate

```
python swbilingual-cli.py locate
```

Lists the SOLIDWORKS language folders found in the standard installation
locations, with their build numbers. Reports `1` when none is found, so it can
be used as a test in a script.

---

## A complete run

```
python swbilingual-cli.py locate
python swbilingual-cli.py check   "C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\english" ^
                                  "C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\chinese-simplified"
python swbilingual-cli.py preview "C:\...\lang\english" "C:\...\lang\chinese-simplified" -t Fillet
python swbilingual-cli.py build   "C:\...\lang\english" "C:\...\lang\chinese-simplified" D:\bilingual
python swbilingual-cli.py install D:\bilingual "C:\...\lang\english"
```
