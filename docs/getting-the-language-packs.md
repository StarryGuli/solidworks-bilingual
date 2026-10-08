# Getting the two language packs

This tool merges two language packs that are already on your computer. It does
not ship them, and neither does this repository: language packs are Dassault
Systèmes software, covered by your SOLIDWORKS licence, and cannot be
redistributed.

There is a synthetic sample pack in [`samples/`](../samples) for trying the tool
out — see [Trying it without SOLIDWORKS](#trying-it-without-solidworks) below.

## Where the packs live

Both sit under the SOLIDWORKS installation, in the `lang` folder:

```
C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\english
C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\chinese-simplified
```

The drive and folder can differ — an installation on `E:` is perfectly normal,
and `locate` reads the real path from the registry rather than assuming `C:`.

List what is present, with build numbers:

```
python swbilingual-cli.py locate
```

English is always installed. The Chinese pack is only there if Chinese was
selected during installation, so on most machines it has to be added.

## Adding the Chinese pack

Use the SOLIDWORKS Installation Manager. This is the route to prefer, because it
fetches the pack matching the build you already have — which is exactly what
this tool requires.

1. Open Windows **Settings → Apps → Installed apps**, find your SOLIDWORKS
   entry, open its menu and choose **Modify**.
2. Choose **Modify your individual installation**, then **Next** until the
   **Product Selection** page.
3. Expand **SOLIDWORKS Languages** and tick **Chinese Simplified**.
4. A notice appears saying the language pack has to be downloaded. Accept it.
5. Confirm the pack is listed under the products to add, accept the licence
   terms, and choose **Download and Modify**.
6. When it finishes, the folder appears under `lang\`.

No reinstallation is needed and existing settings are untouched.

> **Which folder is the Simplified one?** SOLIDWORKS offers *Chinese* and
> *Chinese Simplified* as two separate languages, so a `lang` folder can hold
> `chinese` and `chinese-simplified` side by side — and installations disagree
> about which is which. A folder named `chinese` contains Traditional Chinese on
> some machines and Simplified on others, and is sometimes empty.
>
> Do not go by the name. `check` reads the pack and reports what is actually in
> it:
>
> ```
> Chinese script: Simplified
> ```
>
> If you point the tool at an empty or missing folder, the error names the
> folders beside it that do contain a pack, and says which script each one is
> written in.

## If the Installation Manager cannot download

The installer has to reach the Dassault Systèmes download servers, and the
account it uses needs an entitlement. When that fails, the media can be fetched
manually:

- **[SOLIDWORKS Downloads](https://www.solidworks.com/support/downloads)** — the
  official entry point, and the right place to start.
- Sign in with a **3DEXPERIENCE ID**. The former SOLIDWORKS Customer Portal at
  `customerportal.solidworks.com` was retired in October 2024, and downloads and
  licence management moved to Dassault Systèmes systems. Signing in with a
  SOLIDWORKS account on `my.solidworks.com` is not the same thing and does not
  grant download access.
- Downloads need an active subscription, or a serial number covered by one. With
  neither, your reseller (VAR) is the correct route — they can supply the media
  for the version you are licensed for.
- Choose the **same version and service pack** as your installation. A newer
  service pack gives you a Chinese pack that will not merge; the tool refuses
  it, but the download is wasted.

Students and educational users get their media from their institution's
SOLIDWORKS administrator, not from the public download page.

## Confirming the two packs match

```
python swbilingual-cli.py check "C:\...\lang\english" "C:\...\lang\chinese-simplified"
```

Both build numbers must be identical. They are read from the file version of
`sldresu.dll`. If they differ, the packs come from different builds: their
resource identifiers refer to different strings, and merging them would attach
Chinese labels to unrelated commands. Add the matching Chinese pack rather than
merging across builds.

## Trying it without SOLIDWORKS

The repository includes a small generated pair of packs, so the tool can be run
by anyone:

```
python swbilingual-cli.py check   samples/english samples/chinese
python swbilingual-cli.py preview samples/english samples/chinese
```

They hold invented labels for an imaginary modelling program, written for this
project; nothing in them comes from SOLIDWORKS. They carry a version resource
and string tables in the same format as a real pack, which is enough for `check`
and `preview`. A full build needs real packs and Windows.

Regenerate them with:

```
python tools/make_sample_pack.py samples
```

The sample deliberately includes entries the rules must refuse — a format
string, a file filter, a URL, a long sentence and an untranslated label — so the
preview shows both what is merged and what is left alone.
