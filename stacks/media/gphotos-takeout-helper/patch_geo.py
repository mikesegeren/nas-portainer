#!/usr/bin/env python3
"""Patch Google Photos Takeout Helper to handle missing geoDataExif (KeyError fix)."""
import re
import sys
from pathlib import Path

# Find __main__.py in site-packages
for base in ["/usr/local/lib", "/usr/lib"]:
    for p in Path(base).rglob("google_photos_takeout_helper/__main__.py"):
        path = p
        break
    else:
        continue
    break
else:
    print("Could not find google_photos_takeout_helper/__main__.py", file=sys.stderr)
    sys.exit(1)

text = path.read_text()

# Replace direct json['geoDataExif'] access with safe .get() to avoid KeyError when key is missing
pattern = re.compile(
    r"(\s*)longitude = _str_to_float\(json\['geoDataExif'\]\['longitude'\]\)\s*\n"
    r"\s*latitude = _str_to_float\(json\['geoDataExif'\]\['latitude'\]\)\s*\n"
    r"\s*altitude = _str_to_float\(json\['geoDataExif'\]\['altitude'\]\)"
)
replacement = (
    r"\1exif_data = json.get('geoDataExif', {})\n"
    r"\1longitude = _str_to_float(exif_data.get('longitude', 0))\n"
    r"\1latitude = _str_to_float(exif_data.get('latitude', 0))\n"
    r"\1altitude = _str_to_float(exif_data.get('altitude', 0))"
)
if pattern.search(text):
    text = pattern.sub(replacement, text)
    path.write_text(text)
    print("Patched", path)
else:
    print("Pattern not found (may already be patched)", file=sys.stderr)
