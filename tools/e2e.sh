#!/usr/bin/env bash
# In-game check for the Regions Unexplored content port (844 blocks, 733 items,
# 71 biomes + 307 configured + 343 placed features carried as JSON).
# Minecraft 26.3 on the SDK pin 0b14f8a (launcher Nightly 2026-11-18).
#
# Content-only port (no native module): the unmodded game at the pin, launched
# with `--dev-mod content/carry`.
#
# Default run (offscreen, creative, The End):
#   0. tools/upgrade_shapes.py --check and tools/upgrade_features.py --check
#      prove every carried biome, advancement and feature is in the 26.3 shape
#      (and that the features live under worldgen/feature/, the folder 26.3
#      reads), then tools/verify_content.py compares
#      the carried folder mod with the 1.21.1 jar (block declarations,
#      templates, items, models/textures, recipes and their tags, loot, lang,
#      tags, worldgen counts and shapes, advancements);
#   1. the mod loads (no "content mods not loaded"), the level opens (no
#      "invalid world generation field"/"biome attributes" warnings), and the
#      content root's bundles hold 343 placed features, the 733-item creative
#      tab and all **71** regions_unexplored biomes, whose 26.3 `attributes`
#      carry the colours, sounds, particles and spawns;
#   2. all 844 carried ids `setblock` and read their default state back;
#   3. the patched state sets bind: 88 sign forms, 27 leaves, 33 saplings,
#      4 multiface flowers, 9 petal covers, 3 pointed blocks, 10 snowy
#      grass/podzol blocks, 2 farmland and 14 single-state blocks;
#   4. 10 representative items give (plain items, boat/chest boat, signs);
#   5. four recipes work in a real table (willow planks via the carried tag,
#      `#minecraft:planks`+`#c:yellow_dyes`, `#c:glass`+crystals, and the
#      restored magnolia-flower recipe), each with a wrong-ingredient control;
#   6. the 307 carried configured features register (26.3 reads
#      `worldgen/feature/`), and one feature per converted family **places its
#      block**: tree, random_patch, flower, simple_block, disk, huge mushroom,
#      ore, bamboo, waterlogged_vegetation_patch, block_blob (the retired
#      `forest_rock`) and random_selector, each counted with `fill … replace`
#      after `/place feature`; the vanilla oak control places, and a kept
#      Java-type feature (`ocean_rock`) does not — the differential;
#   7. `/locate biome` transcript: a RU biome id **resolves** in the registry
#      ("Could not find a biome of type … within a reasonable distance": it is
#      registered, TerraBlender's placement is unported), while an unknown id is
#      refused by the registry ("Can't find element … of type
#      'minecraft:worldgen/biome'") — the differential for the fix;
#   8. controls: `give`/`setblock` of a made-up id fail.
#
# Modes:
#   default        the whole scenario; PASS + EXIT:0.
#   NEGATIVE=1     keeps the scenario and expects `ashen_dirt[smouldering=true]`
#                  to read `false`: the run MUST fail with `FAIL:` + EXIT:1,
#                  proving the state read-back is not vacuous.
#   CONTENT=<dir>  run against another content tree (tools/control_pre_fix.sh
#                  builds the 1.21.1-shape copy: the level must NOT open).
#   SKIP_VERIFY=1  skips the jar comparison (debugging only).
set -euo pipefail

CLONE=/home/adlf/Desktop/all_the_mods_10_rust_rewrite
PORT=$CLONE/ports/regions_unexplored
CONTENT=${CONTENT:-$PORT/content/carry}
RES=${RES:-${HORIZON_RES:-/home/adlf/Desktop/horizon/.local/horizon-client/26.3}}
SOCK=${SOCK:-/tmp/opencode/regions-unexplored-e2e.sock}
NEGATIVE=${NEGATIVE:-0}
SKIP_VERIFY=${SKIP_VERIFY:-0}
E2E_TMP=${E2E_TMP:-/tmp/opencode}

if [ -z "${CTL:-}" ] || [ -z "${GAME:-}" ]; then
    eval "$("$CLONE/ports/tools/shared-bin.sh" env)"
fi
[ -x "$CTL" ] || { echo "missing horizon-ctl: $CTL" >&2; exit 1; }
[ -x "$GAME" ] || { echo "missing horizon-client: $GAME" >&2; exit 1; }
[ -d "$RES/assets" ] || { echo "missing prepared resources: $RES" >&2; exit 1; }
[ -f "$CONTENT/horizon-mod.toml" ] || { echo "missing content mod: $CONTENT" >&2; exit 1; }

# The lists come from the patched declarations, the same files the game loads.
lists=$(
    python3 - "$CONTENT/data/regions_unexplored/horizon/block" <<'PY'
import json, sys, pathlib
root = pathlib.Path(sys.argv[1])
decl = {p.stem: json.loads(p.read_text()) for p in root.glob("*.json")}
def names(pred):
    return sorted(n for n, d in decl.items() if pred(n, d))
groups = {
    "ALL": sorted(decl),
    "SIGN": names(lambda n, d: n.endswith("_sign") and not n.endswith("_wall_sign")
                  and not n.endswith("_hanging_sign") and not n.endswith("_wall_hanging_sign")),
    "WALL_SIGN": names(lambda n, d: n.endswith("_wall_sign") and not n.endswith("_wall_hanging_sign")),
    "HANGING_SIGN": names(lambda n, d: n.endswith("_hanging_sign") and not n.endswith("_wall_hanging_sign")),
    "WALL_HANGING_SIGN": names(lambda n, d: n.endswith("_wall_hanging_sign")),
    "LEAVES": names(lambda n, d: d["template"] == "minecraft:oak_leaves" and n.endswith("_leaves")),
    "SAPLING": names(lambda n, d: n.endswith("_sapling") and not n.startswith("potted_")),
    "MULTIFACE": names(lambda n, d: d["template"] == "minecraft:glow_lichen"),
    "PETALS": names(lambda n, d: d["template"] == "minecraft:pink_petals"),
    "POINTED": names(lambda n, d: d["template"] == "minecraft:pointed_dripstone"),
    "SNOWY": names(lambda n, d: d["template"] in ("minecraft:grass_block", "minecraft:podzol")),
    "FARMLAND": names(lambda n, d: d["template"] == "minecraft:farmland"),
}
for k, v in groups.items():
    print(f"{k}=({' '.join(v)})")
PY
)
eval "$lists"

[ "${#ALL[@]}" -eq 844 ] || { echo "expected 844 blocks, found ${#ALL[@]}" >&2; exit 1; }
[ "${#SIGN[@]}" -eq 22 ] && [ "${#WALL_SIGN[@]}" -eq 22 ] \
    && [ "${#HANGING_SIGN[@]}" -eq 22 ] && [ "${#WALL_HANGING_SIGN[@]}" -eq 22 ] \
    || { echo "sign family lists are wrong" >&2; exit 1; }
[ "${#LEAVES[@]}" -eq 27 ] && [ "${#SAPLING[@]}" -eq 33 ] && [ "${#MULTIFACE[@]}" -eq 4 ] \
    && [ "${#PETALS[@]}" -eq 9 ] && [ "${#POINTED[@]}" -eq 3 ] \
    && [ "${#SNOWY[@]}" -eq 10 ] && [ "${#FARMLAND[@]}" -eq 2 ] \
    || { echo "state-family lists are wrong" >&2; exit 1; }

say() { echo "== $* =="; }
fail() { echo "FAIL: $*" >&2; exit 1; }

if [ "$SKIP_VERIFY" = 1 ]; then
    echo "== jar comparison skipped (SKIP_VERIFY=1) =="
else
    say "26.3 shapes: every carried biome, advancement and feature"
    python3 "$PORT/tools/upgrade_shapes.py" --check --content "$CONTENT" \
        || fail "the carried world data is not in 26.3's shape"
    python3 "$PORT/tools/upgrade_features.py" --check --content "$CONTENT" \
        || fail "the carried features are not in 26.3's shape"
    say "data fidelity: carried content vs the 1.21.1 jar"
    RU_CONTENT="$CONTENT" python3 "$PORT/tools/verify_content.py" || fail "verify_content.py failed"
fi

SCRATCH=$(mktemp -d "$E2E_TMP/regions-unexplored-home.XXXXXX")
export HORIZON_HOME=$SCRATCH/game
export HORIZON_LAUNCHER_HOME=$SCRATCH/launcher
export XDG_DATA_HOME=$SCRATCH/data
export XDG_CONFIG_HOME=$SCRATCH/config
export HORIZON_NO_AUDIO=1
mkdir -p "$(dirname "$SOCK")"
rm -f "$SOCK"
cd "$SCRATCH"

ctl() { "$CTL" --socket "$SOCK" "$@"; }
end() { ctl command "execute in minecraft:the_end run $1"; }
block_state() { ctl block "$1" "$2" "$3" | jq -r '.state // .block // "unknown"'; }
prop() { echo "$1" | grep -o "$2=[a-z0-9_]*" | head -1 | cut -d= -f2 || true; }
assert_prop() {
    local state=$1 key=$2 want=$3 got
    got=$(prop "$state" "$key")
    [ "$got" = "$want" ] || fail "$state: $key is '$got', expected '$want'"
}
# Read a position back. The client's copy of a chunk can be overwritten by
# chunk data that arrives after a setblock, so on a mismatch the same block is
# set again (a server update the client then receives). A wrong block can never
# converge, so this only absorbs streaming lag.
readback() { # x y z id [state]
    local x=$1 y=$2 z=$3 id=$4 state=${5:-$4} st i
    for i in 1 2 3 4 5; do
        st=$(block_state "$x" "$y" "$z")
        case "$st" in "$id"*) echo "$st"; return 0 ;; esac
        ctl setblock "$x" "$y" "$z" "$state" >/dev/null 2>&1 || true
        ctl wait 5 >/dev/null
    done
    echo "$st"
}
place() { # x y z "id[props]"
    ctl setblock "$1" "$2" "$3" "$4" >/dev/null || fail "setblock $4 failed"
}

cleanup() {
    rc=$?
    ctl quit >/dev/null 2>&1 || true
    sleep 1
    rm -rf "$SCRATCH" || true
    echo "EXIT:$rc"
}
trap cleanup EXIT

say "launch (shared ${CTL%/horizon-ctl}, offscreen, creative, The End, --dev-mod content/carry)"
if ! "$CTL" --socket "$SOCK" launch \
    --game "$GAME" --world RegionsUnexploredE2E --seed 20261107 --creative --offscreen --wait \
    --game-dir "$SCRATCH/game" --resources "$RES" --dev-mod "$CONTENT" \
    > "$SCRATCH/launch.json" 2> "$SCRATCH/launch.err"; then
    # Keep the game's own reason in the log, then fail loudly: a server that
    # refuses a carried worldgen/advancement file never reaches the assertions.
    echo "launch reply: $(cat "$SCRATCH/launch.json" 2>/dev/null)" >&2
    grep -iE "invalid world generation|biome attributes|No key type in predicate|Couldn't parse data file|live features" \
        "$SCRATCH/game/logs/latest.log" >&2 || tail -25 "$SCRATCH/game/logs/latest.log" >&2 || true
    fail "the game did not launch: $(cat "$SCRATCH/launch.json" 2>/dev/null)"
fi
jq -c '{dimension, creative, ok: .launch.ok, game: .launch.game}' "$SCRATCH/launch.json"
ctl wait-ready 180 || fail "the game did not become ready"
if ctl logs --lines 6000 2>/dev/null | grep -q "content mods not loaded"; then
    ctl logs --lines 6000 | grep "content mods not loaded" >&2
    fail "the content mod did not load"
fi
echo "content mod loaded (no 'content mods not loaded')"

# The defect this leg exists for: at 0b14f8a the integrated server refuses the
# world on a 1.21.1 biome `carvers` map or advancement predicate, and silently
# drops a biome's 1.21.1 `effects`/`spawners`. Neither may appear in the log.
LOG=$(ctl logs --lines 8000 2>/dev/null)
grep -q "live features ready" <<<"$LOG" || fail "the log has no 'live features ready' line"
for bad in "invalid world generation field" "biome attributes" "No key type in predicate" \
           "Couldn't parse data file"; do
    if grep -qi "$bad" <<<"$LOG"; then
        grep -i "$bad" <<<"$LOG" >&2
        fail "the level opened with '$bad' in the log"
    fi
done
echo "the level opened: 'live features ready', no worldgen/advancement/attribute warning"

say "The End arena"
end "forceload add -16 -16 96 80"
end "tp @s 8.5 80 8.5"
ctl wait 40
end "fill -16 79 -16 96 79 80 minecraft:stone"
# Each fill layer is under the command's 32,768-block limit.
for y in $(seq 80 90); do end "fill -16 $y -16 96 $y 80 minecraft:air" >/dev/null; done
end "kill @e[type=minecraft:item]"
end "kill @e[type=minecraft:ender_dragon]"
end "kill @e[type=minecraft:end_crystal]"
end "difficulty peaceful"
end "gamerule spawn_mobs false"
for _ in $(seq 1 30); do
    [ "$(ctl state | jq -r '.dimension')" = minecraft:the_end ] && break
    ctl wait 10
done
[ "$(ctl state | jq -r '.dimension')" = minecraft:the_end ] \
    || fail "the player is in $(ctl state | jq -r '.dimension'), not The End"
ctl wait-ready 180 >/dev/null
ctl wait 40 >/dev/null
echo "player in the_end, chunks settled"

# ------------------------------------------------------------- content root
say "the content root: 71 mod biomes with their 26.3 attributes, features and tab"
MODROOT=$(ls -dt "$SCRATCH/game/.horizon-cache/mod-content"/*/ 2>/dev/null | head -1)
[ -n "$MODROOT" ] && [ -d "$MODROOT" ] || fail "no content root under .horizon-cache/mod-content/"
python3 - "$MODROOT" <<'PY'
import json, os, re, sys
root = sys.argv[1]
feats = json.load(open(os.path.join(root, "worldgen/features.json")))
placed = json.load(open(os.path.join(root, "worldgen/placed_features.json")))
biomes = json.load(open(os.path.join(root, "worldgen/biomes.json")))
ru_feats = [k for k in feats if k.startswith("regions_unexplored:")]
ru_placed = [k for k in placed if k.startswith("regions_unexplored:")]
ru_biomes = [k for k in biomes if k.startswith("regions_unexplored:")]
print(f"features bundle: {len(ru_feats)} regions_unexplored entries")
print(f"placed features bundle: {len(ru_placed)} regions_unexplored entries")
print(f"biomes bundle: {len(ru_biomes)} regions_unexplored entries")
# 26.3 reads `worldgen/feature/` (1.21.1's folder was `configured_feature`,
# which the content loader never looks at) and registers every carried id; the
# ones whose types 26.3 decodes then place (the per-family checks below).
if len(ru_feats) != 307:
    raise SystemExit(f"expected the 307 carried configured features in the "
                     f"registry, found {len(ru_feats)}")
if len(ru_placed) != 343:
    raise SystemExit(f"expected 343 carried placed features, found {len(ru_placed)}")
inert = []
for key in ru_placed:
    entry = json.loads(placed[key]) if isinstance(placed[key], str) else placed[key]
    if entry.get("feature") not in feats:
        inert.append(key)
print(f"placed features naming a registered configured feature: {len(ru_placed) - len(inert)}/{len(ru_placed)}")
if inert:
    raise SystemExit(f"{len(inert)} placed features name a feature outside the registry: {inert[:3]}")
if len(ru_biomes) != 71:
    raise SystemExit(f"expected the 71 carried biomes in the level's registry, found {len(ru_biomes)}")
# The bundle holds each biome's file text; parse it and check the 26.3 shape the
# engine read (a 1.21.1 `effects`/`spawners` would have been dropped silently).
with_sky = with_spawns = with_music = 0
for key in ru_biomes:
    biome = json.loads(biomes[key]) if isinstance(biomes[key], str) else biomes[key]
    name = key.split(":", 1)[1]
    if not isinstance(biome.get("carvers"), list):
        raise SystemExit(f"{name}: carvers is not a list")
    attributes = biome.get("attributes")
    if not isinstance(attributes, dict):
        raise SystemExit(f"{name}: no attributes map")
    spawns = attributes.get("minecraft:gameplay/natural_mob_spawns")
    if not isinstance(spawns, dict) or spawns.get("modifier") != "overlay":
        raise SystemExit(f"{name}: no natural_mob_spawns overlay")
    categories = spawns.get("argument", {}).get("spawns_by_category")
    if not isinstance(categories, dict) or not categories:
        raise SystemExit(f"{name}: natural_mob_spawns has no spawns_by_category")
    for entry in categories.get("monster", []):
        if "count" not in entry or "minCount" in entry:
            raise SystemExit(f"{name}: a monster spawner is not in the 26.3 count shape")
    if "minecraft:visual/sky_color" in attributes:
        if not re.fullmatch(r"#[0-9a-f]{6}", attributes["minecraft:visual/sky_color"]):
            raise SystemExit(f"{name}: sky_color is not #rrggbb")
        with_sky += 1
    if "minecraft:audio/background_music" in attributes:
        with_music += 1
    with_spawns += 1
    effects = biome.get("effects") or {}
    if not re.fullmatch(r"#[0-9a-f]{6}", effects.get("water_color", "")):
        raise SystemExit(f"{name}: effects.water_color is not #rrggbb")
    for legacy in ("sky_color", "fog_color", "water_fog_color", "music",
                   "mood_sound", "particle", "spawners", "spawn_costs",
                   "creature_spawn_probability"):
        if legacy in effects or legacy in biome:
            raise SystemExit(f"{name}: legacy {legacy} survived")
print(f"biome attributes: {with_spawns} with natural_mob_spawns, {with_sky} with a sky colour, "
      f"{with_music} with background music")
if with_spawns != 71 or with_sky != 71 or with_music != 71:
    raise SystemExit("some carried biomes lost their colours, music or spawns")
creative = json.load(open(os.path.join(root, "creative-inventory.json")))
pattern = re.compile(r'id:"(regions_unexplored:[^"]+)"')
seen = set()
for tab in creative.get("tabs", []):
    for stack in tab.get("items") or []:
        seen.update(pattern.findall(stack))
print(f"creative tab: {len(seen)} regions_unexplored items")
if len(seen) != 733:
    raise SystemExit(f"expected 733 items in the creative tab, found {len(seen)}")
states = json.load(open(os.path.join(root, "model-states.json")))
for block in ("regions_unexplored:willow_planks", "regions_unexplored:icicle",
              "regions_unexplored:blue_magnolia_flowers", "regions_unexplored:ashen_dirt"):
    if block not in states:
        raise SystemExit(f"{block} has no model-state row")
PY
echo "71/71 biomes registered with their 26.3 attributes; 307/307 configured features registered under worldgen/feature/ and 343 placed features name one; 733-item tab"

# --------------------------------------------------------------- all blocks
say "all ${#ALL[@]} carried ids bind their default state"
PER=25
for i in "${!ALL[@]}"; do
    x=$((2 + i % PER)); z=$((2 + i / PER))
    ctl setblock "$x" 80 "$z" "regions_unexplored:${ALL[$i]}" >/dev/null \
        || fail "setblock regions_unexplored:${ALL[$i]} failed"
done
ctl wait 20
for i in "${!ALL[@]}"; do
    x=$((2 + i % PER)); z=$((2 + i / PER))
    got=$(readback "$x" 80 "$z" "regions_unexplored:${ALL[$i]}")
    got=${got%%[*}
    [ "$got" = "regions_unexplored:${ALL[$i]}" ] \
        || fail "x=$x z=$z reads '$got', expected regions_unexplored:${ALL[$i]}"
done
echo "${#ALL[@]}/${#ALL[@]} block ids registered and their default state bound"

# ------------------------------------------------------------- state families
say "88 sign forms: rotation on standing signs, facing on wall signs"
i=0
for b in "${SIGN[@]}"; do
    place $((2 + i)) 81 44 "regions_unexplored:$b[rotation=$((i % 16)),waterlogged=false]"; i=$((i + 1))
done
for b in "${HANGING_SIGN[@]}"; do
    place $((2 + i)) 81 45 "regions_unexplored:$b[rotation=$((i % 16)),waterlogged=false]"; i=$((i + 1))
done
i=0
for b in "${WALL_SIGN[@]}"; do
    facing=$(echo "north east south west" | cut -d' ' -f$((i % 4 + 1)))
    place $((2 + i)) 81 46 "regions_unexplored:$b[facing=$facing,waterlogged=true]"; i=$((i + 1))
done
for b in "${WALL_HANGING_SIGN[@]}"; do
    facing=$(echo "north east south west" | cut -d' ' -f$((i % 4 + 1)))
    place $((2 + i)) 81 47 "regions_unexplored:$b[facing=$facing,waterlogged=true]"; i=$((i + 1))
done
ctl wait 10
i=0
for b in "${SIGN[@]}"; do
    assert_prop "$(readback $((2 + i)) 81 44 "regions_unexplored:$b" "regions_unexplored:$b[rotation=$((i % 16)),waterlogged=false]")" rotation "$((i % 16))"; i=$((i + 1))
done
for b in "${HANGING_SIGN[@]}"; do
    assert_prop "$(readback $((2 + i)) 81 45 "regions_unexplored:$b" "regions_unexplored:$b[rotation=$((i % 16)),waterlogged=false]")" rotation "$((i % 16))"; i=$((i + 1))
done
i=0
for b in "${WALL_SIGN[@]}"; do
    facing=$(echo "north east south west" | cut -d' ' -f$((i % 4 + 1)))
    s=$(readback $((2 + i)) 81 46 "regions_unexplored:$b" "regions_unexplored:$b[facing=$facing,waterlogged=true]")
    assert_prop "$s" facing "$facing"; assert_prop "$s" waterlogged true; i=$((i + 1))
done
for b in "${WALL_HANGING_SIGN[@]}"; do
    facing=$(echo "north east south west" | cut -d' ' -f$((i % 4 + 1)))
    s=$(readback $((2 + i)) 81 47 "regions_unexplored:$b" "regions_unexplored:$b[facing=$facing,waterlogged=true]")
    assert_prop "$s" facing "$facing"; assert_prop "$s" waterlogged true; i=$((i + 1))
done
echo "88/88 sign states bind (the carry's stone template had no rotation/facing at all)"

say "${#LEAVES[@]} leaves bind their distance/persistent state"
i=0
for b in "${LEAVES[@]}"; do
    place $((2 + i)) 81 50 "regions_unexplored:$b[distance=3,persistent=true,waterlogged=false]"; i=$((i + 1))
done
ctl wait 10
i=0
for b in "${LEAVES[@]}"; do
    s=$(readback $((2 + i)) 81 50 "regions_unexplored:$b")
    assert_prop "$s" persistent true
    # Vanilla LeavesBlock recomputes `distance` from the nearest log; with no
    # log beside these it becomes 7. That is the template's real leaf behaviour
    # (the raw carry's stone template had no such state at all).
    echo "$s" | grep -qE 'distance=[0-9]+' || fail "$s has no distance state"
    i=$((i + 1))
done
echo "${#LEAVES[@]}/${#LEAVES[@]} leaf states bind (distance recomputed to 7 with no log near, as vanilla leaves do)"

say "${#SAPLING[@]} saplings bind stage=1 (their own declared state)"
i=0
for b in "${SAPLING[@]}"; do
    place $((2 + i)) 81 51 "regions_unexplored:$b[stage=1]"; i=$((i + 1))
done
ctl wait 10
i=0
for b in "${SAPLING[@]}"; do
    assert_prop "$(readback $((2 + i)) 81 51 "regions_unexplored:$b" "regions_unexplored:$b[stage=1]")" stage 1; i=$((i + 1))
done
echo "${#SAPLING[@]}/${#SAPLING[@]} sapling stages bind"

say "${#MULTIFACE[@]} multiface flowers and ${#PETALS[@]} petal covers"
i=0
for b in "${MULTIFACE[@]}"; do
    place $((2 + i)) 81 52 "regions_unexplored:$b[north=true,east=true,waterlogged=true]"; i=$((i + 1))
done
i=0
for b in "${PETALS[@]}"; do
    place $((2 + i)) 81 53 "regions_unexplored:$b[facing=east,flower_amount=4]"; i=$((i + 1))
done
ctl wait 10
i=0
for b in "${MULTIFACE[@]}"; do
    s=$(readback $((2 + i)) 81 52 "regions_unexplored:$b" "regions_unexplored:$b[north=true,east=true,waterlogged=true]")
    assert_prop "$s" north true; assert_prop "$s" waterlogged true; i=$((i + 1))
done
i=0
for b in "${PETALS[@]}"; do
    s=$(readback $((2 + i)) 81 53 "regions_unexplored:$b" "regions_unexplored:$b[facing=east,flower_amount=4]")
    assert_prop "$s" facing east; assert_prop "$s" flower_amount 4; i=$((i + 1))
done
echo "${#MULTIFACE[@]} multiface + ${#PETALS[@]} petal covers bind (properties the raw carry left out)"

say "${#POINTED[@]} pointed blocks, ${#SNOWY[@]} snowy grass/podzol, ${#FARMLAND[@]} farmland"
i=0
for b in "${POINTED[@]}"; do
    place $((2 + i)) 81 54 "regions_unexplored:$b[thickness=tip,vertical_direction=up]"; i=$((i + 1))
done
i=0
for b in "${SNOWY[@]}"; do
    place $((2 + i)) 81 55 "regions_unexplored:$b[snowy=true]"; i=$((i + 1))
done
for b in "${FARMLAND[@]}"; do
    place $((2 + i)) 81 55 "regions_unexplored:$b[moisture=7]"; i=$((i + 1))
done
ctl wait 10
i=0
for b in "${POINTED[@]}"; do
    s=$(readback $((2 + i)) 81 54 "regions_unexplored:$b" "regions_unexplored:$b[thickness=tip,vertical_direction=up]")
    assert_prop "$s" thickness tip; assert_prop "$s" vertical_direction up; i=$((i + 1))
done
i=0
for b in "${SNOWY[@]}"; do
    assert_prop "$(readback $((2 + i)) 81 55 "regions_unexplored:$b" "regions_unexplored:$b[snowy=true]")" snowy true; i=$((i + 1))
done
for b in "${FARMLAND[@]}"; do
    fs=$(readback $((2 + i)) 81 55 "regions_unexplored:$b" "regions_unexplored:$b[moisture=7]")
    # Vanilla FarmBlock dries toward 0 without water beside it (7 -> 6 here),
    # as it does for a vanilla farmland; the moisture state itself binds.
    echo "$fs" | grep -qE 'moisture=[0-7]' || fail "$fs has no moisture state"
    i=$((i + 1))
done
echo "pointed/snowy/farmland states bind (farmland moisture dries as vanilla farmland does)"

say "the single-state blocks the raw carry left out"
i=0
check_state() { # "id[props]" key want
    local spec=$1 key=$2 want=$3 id=${1%%[*}
    place $((2 + i)) 81 57 "regions_unexplored:$spec"
    i=$((i + 1))
    local s
    s=$(readback $((1 + i)) 81 57 "regions_unexplored:$id" "regions_unexplored:$spec")
    assert_prop "$s" "$key" "$want"
}
SMOULDERING=true
[ "$NEGATIVE" = 1 ] && SMOULDERING=false
check_state "ashen_dirt[smouldering=true]" smouldering "$SMOULDERING"
check_state "bamboo_log[leaves=false]" leaves false
check_state "brimwood_log_magma[transition_block=true]" transition_block true
check_state "pine_log[is_stripped=true,transition_block=true]" is_stripped true
check_state "silver_birch_log[is_base=true]" is_base true
check_state "joshua_leaves[half=upper,natural=true]" half upper
check_state "dusktrap[half=upper,closed=true]" closed true
check_state "sandy_grass[is_red=true]" is_red true
check_state "sandy_tall_grass[half=upper,is_red=true]" is_red true
check_state "saguaro_cactus[cactus_shape=north_up]" cactus_shape north_up
check_state "hanging_prismarite[hanging_prismarite_shape=tip]" hanging_prismarite_shape tip
check_state "tall_hyacinth_stock[tall_hyacinth_stock_shape=base_tip]" tall_hyacinth_stock_shape base_tip
check_state "mycotoxic_mushrooms[facing=east,flower_amount=3]" flower_amount 3
check_state "blue_magnolia_flowers[north=true]" north true
echo "14/14 single-state blocks bind their patched states"

# ------------------------------------------------------------------- items
say "10 representative items give"
ctl command "gamemode creative @s" >/dev/null
ctl command "clear @s" >/dev/null
ITEMS=(
    regions_unexplored:ruby regions_unexplored:raw_meat regions_unexplored:cooked_meat
    regions_unexplored:salmonberry regions_unexplored:seeded_grass
    regions_unexplored:baobab_boat regions_unexplored:baobab_chest_boat
    regions_unexplored:willow_sign regions_unexplored:saguaro_cactus
    regions_unexplored:white_snowbelle
)
for item in "${ITEMS[@]}"; do
    ctl give "$item" 1 >/dev/null || fail "give $item failed"
done
ctl wait 3
for item in "${ITEMS[@]}"; do
    n=$(ctl inventory | jq -r --arg i "$item" '.counts[$i] // 0')
    [ "$n" -ge 1 ] || fail "$item did not reach the inventory (count $n)"
done
echo "all 10 give to the inventory"

# ----------------------------------------------------------------- recipes
say "craft in a real table: planks/tag, c:dyes, c:glass, the restored recipe"
end "setblock 40 80 60 minecraft:crafting_table"
end "tp @s 39.5 80 60.5"
ctl wait 10
python3 "$PORT/tools/craft_check.py" "$SOCK" "$CTL" 40 80 60 || fail "the crafting-table checks failed"

# ---------------------------------------------------------------- features
say "the converted features place: one per family, with a kept feature as the control"
end "fill 60 79 54 76 79 74 minecraft:grass_block"
end "fill 60 80 54 76 90 74 minecraft:air"
ctl wait 3
# The command itself works: a vanilla configured feature places.
ctl command "place feature minecraft:oak 62 80 62" >/dev/null \
    || fail "the vanilla oak control feature did not place"
ctl wait 10
control=$(ctl blocks 58 80 58 70 90 68)
control_logs=$(echo "$control" | jq -r '.counts["minecraft:oak_log"] // 0')
[ "$control_logs" -ge 1 ] || fail "the vanilla oak control placed no oak_log"
echo "control: /place feature minecraft:oak placed $control_logs oak_log"

# One feature per family the port converts. Each is placed at its own site on a
# floor it accepts, then the expected block is counted with `fill … replace`,
# which reports the number of blocks changed server-side. A feature that does
# not place leaves the count at 0, so every line is an assertion that can fail.
# The kept families (the mod's own Java feature types, `nether_forest_vegetation`,
# a non-vanilla multiface block) are the differential at the end.
end "forceload add 80 80 320 120" >/dev/null
ctl wait 20
feature_site() { # x z floor-block
    end "fill $(( $1 - 10 )) 79 $(( $2 - 10 )) $(( $1 + 10 )) 79 $(( $2 + 10 )) minecraft:stone"
    end "fill $(( $1 - 10 )) 80 $(( $2 - 10 )) $(( $1 + 10 )) 96 $(( $2 + 10 )) minecraft:air"
    end "fill $(( $1 - 10 )) 80 $(( $2 - 10 )) $(( $1 + 10 )) 82 $(( $2 + 10 )) $3"
    ctl wait 3
}
feature_check() { # x z configured-feature expected-block family [origin-y]
    local x=$1 z=$2 id=$3 want=$4 family=$5 y=${6:-83} reply got
    reply=$(ctl command "place feature regions_unexplored:$id $x $y $z" 2>&1 || true)
    echo "regions_unexplored:$id -> $(echo "$reply" | jq -r '.chat[0]' 2>/dev/null | head -c 70)"
    grep -q 'Placed' <<<"$reply" \
        || fail "$family: /place feature regions_unexplored:$id did not place: $reply"
    got=$(ctl command "fill $(( x - 10 )) 79 $(( z - 10 )) $(( x + 10 )) 96 $(( z + 10 )) minecraft:air replace $want" \
          | jq -r '.chat[0] // ""')
    echo "  $family: $want -> $got"
    grep -q 'Successfully filled' <<<"$got" \
        || fail "$family: $id placed no $want ($got)"
}
feature_site 100 100 minecraft:grass_block
feature_check 100 100 alpha_oak_tree regions_unexplored:alpha_log tree
feature_site 120 100 minecraft:grass_block
feature_check 120 100 patch_alpha_dandelion regions_unexplored:alpha_dandelion random_patch
feature_site 140 100 minecraft:grass_block
feature_check 140 100 corpse_flower regions_unexplored:corpse_flower flower
feature_site 160 100 minecraft:grass_block
feature_check 160 100 aster regions_unexplored:aster simple_block
feature_site 180 100 minecraft:dirt
feature_check 180 100 disk_clay minecraft:clay disk
feature_site 200 100 minecraft:grass_block
feature_check 200 100 giant_brown_mushroom minecraft:brown_mushroom_block huge_mushroom
feature_site 220 100 minecraft:stone
feature_check 220 100 ore_redstone_large minecraft:redstone_ore ore 81
feature_site 240 100 minecraft:dirt
feature_check 240 100 bamboo minecraft:bamboo bamboo
feature_site 260 100 minecraft:stone
feature_check 260 100 mineral_pool minecraft:calcite waterlogged_vegetation_patch
feature_site 280 100 minecraft:grass_block
feature_check 280 100 redwoods_rock minecraft:mossy_cobblestone block_blob
feature_site 300 100 minecraft:grass_block
feature_check 300 100 prairie_tree_mix minecraft:oak_log random_selector

# The differential: a feature whose type is the mod's own Java class never
# reaches the registry, so the same command fails. This is what the conversion
# bought — the converted ids above place, the kept ones do not.
kept_reply=$(ctl command "place feature regions_unexplored:ocean_rock 320 83 100" 2>&1 || true)
echo "regions_unexplored:ocean_rock (kept, Java feature type) -> $(echo "$kept_reply" | jq -r '.chat[0]' 2>/dev/null)"
grep -q 'Placed' <<<"$kept_reply" \
    && fail "a kept Java-type feature placed; the recorded gap is wrong"

# ------------------------------------------------------------------ biomes
say "biome command transcript: a RU biome id resolves, an unknown id is refused"
end_biome=$(ctl command "locate biome minecraft:the_end" 2>&1 || true)
ru_biome=$(ctl command "locate biome regions_unexplored:willow_forest" 2>&1 || true)
missing_biome=$(ctl command "locate biome regions_unexplored:not_a_biome" 2>&1 || true)
echo "minecraft:the_end -> $end_biome"
echo "regions_unexplored:willow_forest -> $ru_biome"
echo "regions_unexplored:not_a_biome -> $missing_biome"
grep -qi "the_end" <<<"$end_biome" || fail "the control biome lookup did not name minecraft:the_end"
# Registered but not generated here: TerraBlender's placement is Java and
# unported, so the id resolves in the registry and the search finds no cell.
grep -q 'Could not find a biome of type' <<<"$ru_biome" \
    && grep -q 'regions_unexplored:willow_forest' <<<"$ru_biome" \
    || fail "the carried RU biome id did not resolve in the registry: $ru_biome"
# The differential: an id that is not in the registry is refused by the lookup.
grep -q "Can't find element 'regions_unexplored:not_a_biome' of type 'minecraft:worldgen/biome'" <<<"$missing_biome" \
    || fail "an unknown biome id was not refused by the registry: $missing_biome"

# ---------------------------------------------------------------- controls
say "wrong-name controls fail"
if ctl give regions_unexplored:not_a_block 1 >/dev/null 2>&1; then
    fail "give regions_unexplored:not_a_block succeeded"
fi
ctl setblock 90 80 70 regions_unexplored:bogus_block >/dev/null 2>&1 || true
[ "$(block_state 90 80 70)" = "minecraft:air" ] || fail "regions_unexplored:bogus_block became a block"
echo "unknown block/item ids are refused"

echo "PASS: the level opens with 71/71 carried biomes registered and their 26.3 attributes (sky colour, background music, natural_mob_spawns) read, and a RU biome id resolves while an unknown id is refused; 844/844 block ids bind; 88 sign states, 27 leaves, 33 saplings, 4 multiface, 9 petal covers, 3 pointed, 10 snowy, 2 farmland and 14 single-state blocks bind their patched states; 10 items give; 4 recipes craft (incl. #c:yellow_dyes, #c:glass and a restored recipe) while their controls stay empty; the 307 carried configured features register and one per converted family places its block (tree, random_patch, flower, simple_block, disk, huge mushroom, ore, bamboo, waterlogged_vegetation_patch, block_blob, random_selector), the vanilla oak control places, and a kept Java-type feature does not; unknown ids are refused"

[ "$NEGATIVE" = 1 ] || exit 0
echo "NEGATIVE: the deliberately false smouldering assertion should have failed the run"
exit 1
