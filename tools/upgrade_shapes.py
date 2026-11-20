#!/usr/bin/env python3
"""Put the carried world data into the shapes Minecraft 26.3 reads.

The 1.21.1 jar's `worldgen/biome/*.json` and `advancement/*.json` are carried
verbatim (the biomes byte for byte; the advancements with the carry's own
`conditions.block` → `conditions.blocks` upgrade). 26.3 reads two different
shapes, and at the SDK pin `0b14f8a` the integrated server refuses the world
when it meets the old ones:

* **biome `carvers`** — 1.21.1's NeoForge step map (`{"air": [...]}`, and a bare
  string in four nether biomes) is a flat list in 26.3 (`plains.json`:
  `["minecraft:cave", "minecraft:cave_extra_underground", "minecraft:canyon"]`).
  `horizon-world`'s `carver/generation.rs::decode_set` treats a non-array as one
  inline carver, and `carver.rs::from_json` then reports the missing `type`:
  *"invalid world generation field: type"*.
* **biome colours, sounds, particles and spawns** — 26.3 keeps only the tint
  colours in `effects` (`water_color`, `foliage_color`, `grass_color`,
  `dry_foliage_color`, `grass_color_modifier`) and moves everything else into
  the `attributes` map: `minecraft:visual/{sky_color,fog_color,water_fog_color,
  ambient_particles}`, `minecraft:audio/{background_music,ambient_sounds}` and
  `minecraft:gameplay/{natural_mob_spawns,creature_world_gen_spawn_probability}`.
  1.21.1's `spawners`/`spawn_costs` become one `natural_mob_spawns` overlay whose
  entries carry `count` (an int, or a `minecraft:uniform` provider) instead of
  `minCount`/`maxCount`. A file without the map parses, but its colours and
  spawns are silently dropped (*"biome attributes: attributes are not an
  object"*).
* **advancement predicates** — 26.3 dispatches predicates on `type` (the
  1.21.1 `condition` key is refused: *"No key type in predicate"*), namespaces
  the entity predicate's fields (`location` → `minecraft:location`), and wants
  `conditions.player`/`conditions.entity` as an object, not the 1.21.1
  one-element list. The engine's validator says so at `0b14f8a`
  (`game/administration/functions/registry_graph/fields.rs`: *"26.3 predicates
  dispatch on `type`. The old `condition: reference`/`name` shape is a codec
  failure"*), and vanilla 26.3's own `adventure/adventuring_time.json` shows the
  shape.

Every expected shape is read from vanilla 26.3's prepared data (the authority),
not guessed. `--check` re-derives every carried file and compares it with what
is on disk, so a re-carry (which writes the 1.21.1 bytes again) cannot undo the
conversion unnoticed; `--write` applies it. `content/patches/apply.sh` runs
`--write` as the last carry step, and `tools/e2e.sh` runs `--check` first.

Deviations, recorded in `notes.md`: `effects.music.replace_current_music` is
dropped (26.3's `background_music` has no such field; the jar sets it `false`
in all 71 biomes, which is 26.3's behaviour), and a `true` value is refused
rather than silently dropped.
"""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "carry"
NS = "regions_unexplored"

#: The cached ATM10 jar, the artefact every carried file comes from.
DEFAULT_JAR = (
    ROOT.parent / "_shared/carry-work" / NS
    / "regions_unexplored-neoforge-1.21.1-0.5.9.jar"
)

#: 1.21.1 `effects` colour keys 26.3 keeps in `effects`, as `#rrggbb`.
TINT_COLOURS = ("water_color", "foliage_color", "grass_color", "dry_foliage_color")
#: 1.21.1 `effects` colour keys 26.3 moved into the attributes map.
VISUAL_COLOURS = {
    "sky_color": "minecraft:visual/sky_color",
    "fog_color": "minecraft:visual/fog_color",
    "water_fog_color": "minecraft:visual/water_fog_color",
}
#: 26.3's default `creature_spawn_probability`; left out at that value.
DEFAULT_CREATURE_PROBABILITY = 0.1
#: 1.21.1 `EntityPredicate` fields 26.3 namespaced, verified against vanilla
#: 26.3's own advancements (`kill_a_mob.json`, `adventuring_time.json`).
PREDICATE_FIELDS = {
    "type": "minecraft:entity_type",
    "location": "minecraft:location",
    "equipment": "minecraft:equipment",
}


class ShapeError(ValueError):
    """A carried value 26.3 cannot express; the tool refuses rather than guess."""


def hex_colour(value, where: str) -> str:
    """1.21.1's integer colour as 26.3's `#rrggbb` (an existing string passes)."""
    if isinstance(value, str):
        if not value.startswith("#") or len(value) != 7:
            raise ShapeError(f"{where}: {value!r} is not a #rrggbb colour")
        return value.lower()
    if isinstance(value, bool) or not isinstance(value, int):
        raise ShapeError(f"{where}: {value!r} is not an integer colour")
    return f"#{value & 0xFFFFFF:06x}"


def spawn_count(entry: dict, where: str):
    """1.21.1 `minCount`/`maxCount` as 26.3's `count` (an int or a uniform provider)."""
    if "count" in entry:  # already converted
        return entry["count"]
    low, high = entry.get("minCount"), entry.get("maxCount")
    if not isinstance(low, int) or not isinstance(high, int):
        raise ShapeError(f"{where}: spawner {entry.get('type')!r} has no minCount/maxCount")
    if low == high:
        return low
    return {"type": "minecraft:uniform", "min_inclusive": low, "max_inclusive": high}


def flatten_carvers(carvers, where: str) -> list[str]:
    """1.21.1's step map (or a bare string) as 26.3's flat list."""
    if isinstance(carvers, list):
        return list(carvers)
    if isinstance(carvers, str):
        return [carvers]
    if not isinstance(carvers, dict):
        raise ShapeError(f"{where}: carvers is {type(carvers).__name__}, not a map or list")
    flat: list[str] = []
    for step, value in carvers.items():
        if isinstance(value, str):
            flat.append(value)
        elif isinstance(value, list):
            flat.extend(value)
        else:
            raise ShapeError(f"{where}: carvers[{step}] is {type(value).__name__}")
    return flat


def natural_mob_spawns(spawners: dict, spawn_costs: dict, where: str) -> dict:
    """1.21.1 `spawners`/`spawn_costs` as 26.3's `natural_mob_spawns` overlay.

    Empty categories are kept: they are what stops the dimension's defaults
    from filling them (`docs/datapack-upgrade.md`).
    """
    by_category: dict[str, list] = {}
    for category, entries in spawners.items():
        converted = []
        for entry in entries:
            if not isinstance(entry, dict) or "type" not in entry:
                raise ShapeError(f"{where}: spawners[{category}] entry has no type")
            item = {"type": entry["type"], "weight": entry.get("weight", 1)}
            item["count"] = spawn_count(entry, f"{where}: spawners[{category}]")
            converted.append(item)
        by_category[category] = converted
    return {
        "argument": {"spawn_costs": spawn_costs, "spawns_by_category": by_category},
        "modifier": "overlay",
    }


def convert_biome(data: dict) -> dict:
    """A carried 1.21.1 biome in the shape 26.3 reads (idempotent)."""
    source = copy.deepcopy(data)
    attributes = dict(source.get("attributes") or {})
    where = "biome"

    if "carvers" in source:
        source["carvers"] = flatten_carvers(source["carvers"], where)

    if "spawners" in source or "spawn_costs" in source:
        attributes["minecraft:gameplay/natural_mob_spawns"] = natural_mob_spawns(
            source.pop("spawners", {}) or {}, source.pop("spawn_costs", {}) or {}, where
        )

    if "creature_spawn_probability" in source:
        probability = source.pop("creature_spawn_probability")
        if probability != DEFAULT_CREATURE_PROBABILITY:
            attributes[
                "minecraft:gameplay/creature_world_gen_spawn_probability"
            ] = probability

    effects = source.get("effects")
    if isinstance(effects, dict):
        kept: dict = {}
        for key, value in effects.items():
            if key in TINT_COLOURS:
                kept[key] = hex_colour(value, f"effects.{key}")
            elif key == "grass_color_modifier":
                kept[key] = value
            elif key in VISUAL_COLOURS:
                attributes[VISUAL_COLOURS[key]] = hex_colour(value, f"effects.{key}")
            elif key == "music":
                if value.get("replace_current_music"):
                    raise ShapeError(
                        "effects.music.replace_current_music is true; 26.3's "
                        "background_music has no such field"
                    )
                kept_music = {
                    key2: value[key2]
                    for key2 in ("max_delay", "min_delay", "sound")
                    if key2 in value
                }
                attributes["minecraft:audio/background_music"] = {"default": kept_music}
            elif key == "mood_sound":
                sounds = attributes.setdefault("minecraft:audio/ambient_sounds", {})
                sounds["mood"] = dict(value)
            elif key == "ambient_sound":
                sounds = attributes.setdefault("minecraft:audio/ambient_sounds", {})
                sounds["loop"] = value
            elif key == "additions_sound":
                sounds = attributes.setdefault("minecraft:audio/ambient_sounds", {})
                sounds["additions"] = dict(value)
            elif key == "particle":
                attributes["minecraft:visual/ambient_particles"] = {
                    "argument": [
                        {
                            "particle": value.get("options", {}),
                            "probability": value.get("probability", 0),
                        }
                    ],
                    "modifier": "append",
                }
            else:
                raise ShapeError(f"effects.{key} has no known 26.3 home")
        source["effects"] = kept

    if attributes:
        source["attributes"] = attributes
    return source


def convert_predicate(entry: dict, where: str) -> dict:
    """One 1.21.1 predicate as 26.3's `type`-dispatched form."""
    if not isinstance(entry, dict):
        raise ShapeError(f"{where}: predicate is {type(entry).__name__}, not an object")
    converted = copy.deepcopy(entry)
    if "condition" in converted:
        kind = converted.pop("condition")
        if "type" in converted and converted["type"] != kind:
            raise ShapeError(f"{where}: both condition {kind!r} and type {converted['type']!r}")
        converted = {"type": kind, **converted}
    kind = converted.get("type")
    if not isinstance(kind, str) or not kind:
        raise ShapeError(f"{where}: no `type` key; 26.3 refuses it with 'No key type in predicate'")
    predicate = converted.get("predicate")
    if kind == "minecraft:entity_properties" and isinstance(predicate, dict):
        namespaced: dict = {}
        for key, value in predicate.items():
            if key.startswith("minecraft:"):
                namespaced[key] = value
                continue
            if key not in PREDICATE_FIELDS:
                raise ShapeError(
                    f"{where}: predicate field {key!r} has no verified 26.3 name; read "
                    "vanilla 26.3's own data before carrying it"
                )
            namespaced[PREDICATE_FIELDS[key]] = value
        converted["predicate"] = namespaced
    return converted


def convert_advancement(data: dict) -> dict:
    """A carried 1.21.1 advancement in the shape 26.3 reads (idempotent)."""
    converted = copy.deepcopy(data)
    for name, criterion in (converted.get("criteria") or {}).items():
        conditions = criterion.get("conditions")
        if not isinstance(conditions, dict):
            continue
        # 26.3 reads an `enter_block` criterion's block as `blocks`; it skips the
        # old `block` field, which made the criterion match any block entered
        # (`horizon-port-pack/src/carry.rs:366`, vanilla `end/enter_end_gateway`).
        if criterion.get("trigger") in ("minecraft:enter_block", "enter_block"):
            if "blocks" not in conditions and "block" in conditions:
                conditions["blocks"] = conditions.pop("block")
        for slot in ("player", "entity"):
            if slot not in conditions:
                continue
            value = conditions[slot]
            where = f"criteria[{name}].conditions.{slot}"
            if isinstance(value, list):
                if len(value) != 1:
                    raise ShapeError(
                        f"{where}: {len(value)} predicates in a list; 26.3 takes one object"
                    )
                value = value[0]
            conditions[slot] = convert_predicate(value, where)
    return converted


def legacy_reasons(data: dict) -> list[str]:
    """Why a carried biome is not yet in 26.3's shape (empty when it is)."""
    reasons = []
    carvers = data.get("carvers")
    if isinstance(carvers, dict) or isinstance(carvers, str):
        reasons.append("carvers is a step map/string, 26.3 wants a list")
    if not isinstance(data.get("attributes"), dict):
        reasons.append("no attributes map (colours, sounds and spawns would be dropped)")
    for key in ("spawners", "spawn_costs", "creature_spawn_probability"):
        if key in data:
            reasons.append(f"{key} is the 1.21.1 shape")
    effects = data.get("effects")
    if isinstance(effects, dict):
        for key in ("sky_color", "fog_color", "water_fog_color", "music",
                    "mood_sound", "ambient_sound", "additions_sound", "particle"):
            if key in effects:
                reasons.append(f"effects.{key} is the 1.21.1 shape")
    return reasons


def advancement_reasons(data: dict) -> list[str]:
    """Why a carried advancement is not yet in 26.3's shape (empty when it is)."""
    reasons = []
    for name, criterion in (data.get("criteria") or {}).items():
        conditions = criterion.get("conditions")
        if not isinstance(conditions, dict):
            continue
        if criterion.get("trigger") in ("minecraft:enter_block", "enter_block") \
                and "block" in conditions and "blocks" not in conditions:
            reasons.append(f"criteria[{name}] names its block as `block`, 26.3 reads `blocks`")
        for slot in ("player", "entity"):
            if slot not in conditions:
                continue
            value = conditions[slot]
            where = f"criteria[{name}].conditions.{slot}"
            if isinstance(value, list):
                reasons.append(f"{where} is a list, 26.3 wants an object")
                continue
            if isinstance(value, dict) and "condition" in value:
                reasons.append(f"{where} dispatches on `condition`, 26.3 on `type`")
    return reasons


def carried(content: pathlib.Path, kind: str) -> list[pathlib.Path]:
    """The carried files of one registry, sorted."""
    base = content / "data" / NS / ("worldgen/biome" if kind == "biomes" else "advancement")
    return sorted(base.rglob("*.json"))


def check_tree(content: pathlib.Path, *, biomes=None, advancements=None,
               jar: pathlib.Path | None = None) -> list[str]:
    """Every carried file must already be what the conversion produces.

    `biomes`/`advancements` are the expected file counts (a re-carry that loses
    files is a problem too). `jar`, when given, also re-derives each biome from
    the artefact and compares it with the converted file on disk.
    """
    problems: list[str] = []
    jar_biomes = None
    if jar is not None and pathlib.Path(jar).is_file():
        with zipfile.ZipFile(jar) as archive:
            jar_biomes = {
                name.rsplit("/", 1)[-1]: json.loads(archive.read(name))
                for name in archive.namelist()
                if name.startswith(f"data/{NS}/worldgen/biome/") and name.endswith(".json")
            }
    elif jar is not None:
        problems.append(f"{jar}: not found, so the artefact cross-check did not run")

    files = carried(content, "biomes")
    if biomes is not None and len(files) != biomes:
        problems.append(f"biomes: expected {biomes} files, found {len(files)}")
    for path in files:
        rel = path.relative_to(content).as_posix()
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            expected = convert_biome(data)
        except ShapeError as error:
            problems.append(f"{rel}: {error}")
            continue
        if expected != data:
            reasons = legacy_reasons(data) or ["differs from the 26.3 form"]
            problems.append(f"{rel}: {'; '.join(reasons)}")
        if jar_biomes is not None:
            source = jar_biomes.get(path.name)
            if source is None:
                problems.append(f"{rel}: no such biome in the jar")
            elif convert_biome(source) != expected:
                problems.append(f"{rel}: does not match the jar's biome after conversion")

    files = carried(content, "advancements")
    if advancements is not None and len(files) != advancements:
        problems.append(f"advancements: expected {advancements} files, found {len(files)}")
    for path in files:
        rel = path.relative_to(content).as_posix()
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            expected = convert_advancement(data)
        except ShapeError as error:
            problems.append(f"{rel}: {error}")
            continue
        if expected != data:
            reasons = advancement_reasons(data) or ["differs from the 26.3 form"]
            problems.append(f"{rel}: {'; '.join(reasons)}")
    return problems


def write_tree(content: pathlib.Path) -> dict[str, int]:
    """Apply the conversion in place; return how many files of each kind changed."""
    changed = {"biomes": 0, "advancements": 0}
    for kind, convert in (("biomes", convert_biome), ("advancements", convert_advancement)):
        for path in carried(content, kind):
            data = json.loads(path.read_text(encoding="utf-8"))
            converted = convert(data)
            if converted != data:
                path.write_text(
                    json.dumps(converted, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                changed[kind] += 1
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Put the carried world data into Minecraft 26.3's shapes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="verify every carried file; exit 1 on any problem")
    mode.add_argument("--write", action="store_true", help="convert the carried files in place")
    parser.add_argument("--content", type=pathlib.Path, default=CONTENT)
    parser.add_argument("--jar", type=pathlib.Path, default=DEFAULT_JAR,
                        help="the cached jar, for the biome cross-check")
    parser.add_argument("--no-jar", action="store_true", help="skip the artefact cross-check")
    parser.add_argument("--biomes", type=int, default=71)
    parser.add_argument("--advancements", type=int, default=671)
    args = parser.parse_args(argv)

    if not args.content.is_dir():
        print(f"{args.content} is not a content tree", file=sys.stderr)
        return 2
    if args.write:
        changed = write_tree(args.content)
        print(f"converted {changed['biomes']} biomes, {changed['advancements']} advancements")
    problems = check_tree(
        args.content,
        biomes=args.biomes,
        advancements=args.advancements,
        jar=None if args.no_jar else args.jar,
    )
    for line in problems:
        print(line, file=sys.stderr)
    if problems:
        print(f"FAIL: {len(problems)} carried file(s) are not in 26.3's shape", file=sys.stderr)
        return 1
    biomes = len(carried(args.content, "biomes"))
    advancements = len(carried(args.content, "advancements"))
    jar_note = "jar cross-check green" if not args.no_jar else "jar cross-check skipped"
    print(f"OK {biomes} biomes + {advancements} advancements in 26.3 shape ({jar_note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
