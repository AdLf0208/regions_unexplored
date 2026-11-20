#!/usr/bin/env bash
# Counterfactual for the 0b14f8a fix: revert the 26.3 shape conversion in a
# scratch copy of the carried content (the jar's own 1.21.1 biome and
# advancement bytes) and run the same in-game leg. The level must NOT open.
#
#   1. the shape check is red on that copy (tools/upgrade_shapes.py --check);
#   2. the game refuses the world ("invalid world generation field: type" or
#      "No key type in predicate"), so the leg ends `FAIL:` + `EXIT:1`.
#
# Run through the slot registry:
#   ports/tools/build-slot.sh run --job ru-control --port ports/regions_unexplored \
#       --step e2e -- bash ports/regions_unexplored/tools/control_pre_fix.sh
set -euo pipefail

CLONE=/home/adlf/Desktop/all_the_mods_10_rust_rewrite
PORT=$CLONE/ports/regions_unexplored
JAR=$CLONE/ports/_shared/carry-work/regions_unexplored/regions_unexplored-neoforge-1.21.1-0.5.9.jar
E2E_TMP=${E2E_TMP:-/tmp/opencode}

[ -f "$JAR" ] || { echo "missing the cached jar: $JAR" >&2; exit 1; }

TMP=$(mktemp -d "$E2E_TMP/ru-pre-fix.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
cp -a "$PORT/content/carry" "$TMP/carry"

python3 - "$JAR" "$TMP/carry" <<'PY'
import pathlib, sys, zipfile

jar, content = sys.argv[1], pathlib.Path(sys.argv[2])
restored = 0
with zipfile.ZipFile(jar) as archive:
    for name in archive.namelist():
        if not name.endswith(".json"):
            continue
        if not (name.startswith("data/regions_unexplored/worldgen/biome/")
                or name.startswith("data/regions_unexplored/advancement/")):
            continue
        target = content / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(name))
        restored += 1
print(f"reverted {restored} carried files to the jar's 1.21.1 bytes")
PY

if python3 "$PORT/tools/upgrade_shapes.py" --check --content "$TMP/carry" >"$TMP/shape-check.log" 2>&1; then
    echo "FAIL: the pre-fix copy passed the 26.3 shape check" >&2
    exit 1
fi
echo "shape check on the pre-fix copy: red ($(grep -c . "$TMP/shape-check.log") line(s))"

if CONTENT="$TMP/carry" SKIP_VERIFY=1 bash "$PORT/tools/e2e.sh"; then
    echo "FAIL: the pre-fix content opened the level; the shape fix is not what makes it open" >&2
    exit 1
fi
exit 1
