# Patched Google Photos Takeout Helper: handles missing geoDataExif (KeyError fix)
FROM jgeusebroek/google-photos-takeout-helper:latest
# Clear entrypoint so RUN uses the shell directly; restore it after patching
ENTRYPOINT []
COPY patch_geo.py /tmp/patch_geo.py
RUN python3 /tmp/patch_geo.py
CMD ["tail", "-f", "/dev/null"]
