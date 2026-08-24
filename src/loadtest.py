# -*- coding: utf-8 -*-
"""Load every patched DLL with the real PE loader, not just as a data file."""
import ctypes, os, sys

k = ctypes.WinDLL('kernel32', use_last_error=True)
k.LoadLibraryW.restype = ctypes.c_void_p
k.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
k.FreeLibrary.argtypes = [ctypes.c_void_p]

d = sys.argv[1]
files = [f for f in sorted(os.listdir(d)) if f.lower().endswith('.dll')]
bad = []
for f in files:
    h = k.LoadLibraryW(os.path.join(d, f))
    if not h:
        bad.append((f, ctypes.get_last_error()))
    else:
        k.FreeLibrary(h)

print(f'loaded ok: {len(files) - len(bad)}   failed: {len(bad)}')
for f, e in bad:
    print(f'  !! {f} error {e}')
