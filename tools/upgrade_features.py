#!/usr/bin/env python3
"""Put the carried configured and placed features into Minecraft 26.3's shapes.

The 1.21.1 jar's `worldgen/configured_feature/*.json` and
`worldgen/placed_feature/*.json` are carried verbatim, and at the SDK pin
`0b14f8a` the game refuses every one of the 307 configured features at load:
the decoder is `horizon-world/src/worldgen/feature_graph.rs`, and its shapes
differ from 1.21.1's in five ways, all read from the pin's source and from
vanilla 26.3's own prepared data (`.../26.3/data/minecraft/worldgen/`), never
guessed:

* **the `config` wrapper is gone** — 1.21.1 nests the config under `config`,
  26.3 spreads it at the root (`oak.json`: `{"type": "minecraft:tree",
  "trunk_provider": …}`).
* **state providers were renamed** — 1.21.1's
  `minecraft:simple_state_provider` is a bare block state in 26.3 (`"id"` or
  `{id, properties}`), `minecraft:weighted_state_provider` is
  `minecraft:weighted` (`crimson_forest_vegetation.json`), and
  `minecraft:noise_provider` is `minecraft:noise` (`state_provider.rs`).
* **the tree's dirt provider moved** — 1.21.1 `dirt_provider` is 26.3's
  `below_trunk_provider`, and `force_dirt` has no 26.3 field (`oak.json`,
  `tree.rs::TreeFeature::decode` reads `below_trunk_provider`).
* **`random_patch` and `flower` are not feature types any more** — 26.3 has no
  such decoder arm. Their work (tries, xz/y spread) is placement now:
  vanilla's `patch_grass_normal.json` is `count` + `trapezoid` offset, and
  1.21.1's `RandomPatchFeature`/`FlowerFeature` offset with
  `nextInt(spread+1) - nextInt(spread+1)` — a trapezoid, not a uniform. So the
  patch's inner configured feature becomes the file, and every reference to it
  gets `count(tries)` + `offset(trapezoid)` + the patch's own placement
  appended (vanilla's order: the outer placement first, then the patch).
* **`nether_forest_vegetation` and `forest_rock` were retired** — 26.3's
  `forest_rock.json` is `block_blob` with the `forest_rock_can_place_on` tag;
  `nether_forest_vegetation` has no equivalent (its 128-attempt spread and
  bonemeal-only use cannot be expressed), so those four files stay as carried
  and are recorded as the gap they are.

A feature is converted only when **every** type inside it is one 26.3 knows
(`FEATURE_TYPES`, the placer/decorator/size/int-provider/placement/predicate
sets below). The mod's own Java types (`regions_unexplored:shrub`,
`…_tree`, `regions_unexplored:sakura_foliage_placer`, …) and the 1.21.1-only
shapes that have no 26.3 equivalent (`randomized_int_state_provider`,
`weighted_list`, `random_offset`, multi-octave noise) make a file
*unconvertible*: it is left byte-identical and reported, so the loader keeps
dropping exactly what the game cannot express instead of the port inventing a
different feature.

`--check` re-derives every file and compares it with the disk (a re-carry that
writes the 1.21.1 bytes again is caught); `--write` applies it.
`content/patches/apply.sh` runs `--write` after the carry, and `tools/e2e.sh`
runs `--check` before the game.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "carry"
NS = "regions_unexplored"

#: Every feature type the pin's `feature_graph.rs` decodes.
FEATURE_TYPES = frozenset({
    "minecraft:no_op", "minecraft:template", "minecraft:fossil",
    "minecraft:freeze_top_layer", "minecraft:delta_feature", "minecraft:bamboo",
    "minecraft:netherrack_replace_blobs", "minecraft:speleothem",
    "minecraft:chorus_plant", "minecraft:bonus_chest", "minecraft:end_gateway",
    "minecraft:end_podium", "minecraft:spike", "minecraft:blue_ice",
    "minecraft:underwater_magma", "minecraft:vines", "minecraft:spring_feature",
    "minecraft:block_blob", "minecraft:disk", "minecraft:block_pile",
    "minecraft:random_neighbor_spread", "minecraft:single_block_pillar",
    "minecraft:block_column", "minecraft:simple_block", "minecraft:fill_layer",
    "minecraft:replace_single_block", "minecraft:ore", "minecraft:scattered_ore",
    "minecraft:vegetation_patch", "minecraft:waterlogged_vegetation_patch",
    "minecraft:root_system", "minecraft:coral_tree", "minecraft:coral_claw",
    "minecraft:huge_red_mushroom", "minecraft:huge_brown_mushroom",
    "minecraft:lake", "minecraft:monster_room", "minecraft:geode",
    "minecraft:speleothem_cluster", "minecraft:large_dripstone",
    "minecraft:projected_random_patchy_square", "minecraft:stepped_column_cluster",
    "minecraft:end_spike", "minecraft:sculk_patch", "minecraft:huge_fungus",
    "minecraft:iceberg", "minecraft:multiface_growth", "minecraft:tree",
    "minecraft:fallen_tree", "minecraft:weighted_random_selector",
    "minecraft:sequence", "minecraft:overlay", "minecraft:simple_random_selector",
    "minecraft:random_boolean_selector", "minecraft:random_selector",
})

#: The feature types this converter knows how to bring over. Everything else
#: (including 1.21.1-only types) keeps its carried bytes.
CONVERTIBLE = frozenset({
    "minecraft:tree", "minecraft:simple_block", "minecraft:disk",
    "minecraft:multiface_growth", "minecraft:huge_red_mushroom",
    "minecraft:huge_brown_mushroom", "minecraft:vegetation_patch",
    "minecraft:waterlogged_vegetation_patch", "minecraft:ore",
    "minecraft:bamboo", "minecraft:simple_random_selector",
    "minecraft:random_selector", "minecraft:sequence", "minecraft:overlay",
    "minecraft:weighted_random_selector", "minecraft:random_boolean_selector",
    "minecraft:block_column", "minecraft:block_blob",
})

#: 1.21.1 feature types whose 26.3 form is a different type.
RETIRED = {
    # 1.21.1 `random_patch`/`flower` -> the inner feature + placement modifiers
    "minecraft:random_patch": "patch",
    "minecraft:flower": "patch",
    # 26.3's `forest_rock` is a `block_blob` with the vanilla place-on tag
    "minecraft:forest_rock": "block_blob",
    # no 26.3 equivalent: a 128-attempt spread used by bonemeal only
    "minecraft:nether_forest_vegetation": "unsupported",
}

#: State-provider types 26.3 decodes (`state_provider.rs`).
PROVIDER_TYPES = frozenset({
    "minecraft:rule_based", "minecraft:noise", "minecraft:noise_threshold",
    "minecraft:dual_noise", "minecraft:simple", "minecraft:weighted",
    "minecraft:random_block", "minecraft:rotated", "minecraft:randomized_int",
})
TRUNK_PLACERS = frozenset({
    "minecraft:straight_trunk_placer", "minecraft:forking_trunk_placer",
    "minecraft:giant_trunk_placer", "minecraft:mega_jungle_trunk_placer",
    "minecraft:dark_oak_trunk_placer", "minecraft:fancy_trunk_placer",
    "minecraft:bending_trunk_placer", "minecraft:upwards_branching_trunk_placer",
    "minecraft:cherry_trunk_placer", "minecraft:poplar_trunk_placer",
})
FOLIAGE_PLACERS = frozenset({
    "minecraft:blob_foliage_placer", "minecraft:fancy_foliage_placer",
    "minecraft:bush_foliage_placer", "minecraft:jungle_foliage_placer",
    "minecraft:acacia_foliage_placer", "minecraft:dark_oak_foliage_placer",
    "minecraft:spruce_foliage_placer", "minecraft:pine_foliage_placer",
    "minecraft:mega_pine_foliage_placer", "minecraft:random_spread_foliage_placer",
    "minecraft:cherry_foliage_placer", "minecraft:poplar_foliage_placer",
})
DECORATORS = frozenset({
    "minecraft:trunk_vine", "minecraft:leave_vine", "minecraft:cocoa",
    "minecraft:beehive", "minecraft:creaking_heart", "minecraft:shelf_mushroom",
    "minecraft:alter_ground", "minecraft:attached_to_leaves",
    "minecraft:attached_to_logs", "minecraft:pale_moss",
    "minecraft:place_on_ground",
})
SIZE_TYPES = frozenset({
    "minecraft:two_layers_feature_size", "minecraft:three_layers_feature_size",
})
INT_PROVIDERS = frozenset({
    "minecraft:constant", "minecraft:uniform", "minecraft:trapezoid",
    "minecraft:clamped_normal", "minecraft:biased_to_bottom",
    "minecraft:very_biased_to_bottom", "minecraft:clamped",
    "minecraft:weighted_list",
})
PLACEMENT_TYPES = frozenset({
    "minecraft:biome", "minecraft:block_predicate_filter",
    "minecraft:environment_scan", "minecraft:heightmap",
    "minecraft:surface_relative_threshold_filter",
    "minecraft:surface_water_depth_filter", "minecraft:noise_based_count",
    "minecraft:noise_threshold_count", "minecraft:count_on_every_layer",
    "minecraft:count", "minecraft:in_square", "minecraft:cuboid",
    "minecraft:offset", "minecraft:height_range", "minecraft:rarity_filter",
    "minecraft:random_chance", "minecraft:fixed_placement",
    "minecraft:randomly_selected",
})
PREDICATE_TYPES = frozenset({
    "minecraft:would_survive", "minecraft:has_sturdy_face", "minecraft:solid",
    "minecraft:replaceable", "minecraft:unobstructed", "minecraft:matching_biomes",
    "minecraft:matching_fluids", "minecraft:matching_blocks",
    "minecraft:matching_block_tag", "minecraft:height_range",
    "minecraft:volume_match", "minecraft:true", "minecraft:not",
    "minecraft:all_of", "minecraft:any_of", "minecraft:inside_world_bounds",
})
#: 1.21.1 names the ore target predicate `predicate_type`; 26.3 keeps that key
#: in its own `ore_*.json`, so it is accepted unchanged.
PREDICATE_ALIASES = frozenset({"minecraft:tag_match"})
#: Vanilla configured features 26.3 renamed. `random_patch` and `flower` were
#: retired, so their configs became `simple_block` features with a new name:
#: 1.21.1's `minecraft:patch_cactus` is 26.3's `minecraft:cactus` (26.3 keeps a
#: *placed* feature called `patch_cactus`, which is not a configured feature, so
#: a reference to the old id resolves to nothing).
VANILLA_FEATURE_RENAMES = {"minecraft:patch_cactus": "minecraft:cactus"}

#: Vanilla 26.3's `forest_rock.json` uses this tag for the retired 1.21.1 type.
FOREST_ROCK_TAG = "minecraft:forest_rock_can_place_on"

ALL_KNOWN = (
    FEATURE_TYPES | PROVIDER_TYPES | TRUNK_PLACERS | FOLIAGE_PLACERS
    | DECORATORS | SIZE_TYPES | INT_PROVIDERS | PLACEMENT_TYPES | PREDICATE_TYPES
)


class Unsupported(Exception):
    """The file cannot be expressed as a 26.3 feature; keep the carried bytes."""


def _provider(node):
    """One 1.21.1 block-state provider in 26.3's shape."""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        raise Unsupported("state provider is neither a state nor an object")
    kind = node.get("type")
    if kind is None and "rules" in node:
        # 1.21.1's rule-based provider carries no `type`; 26.3 names it.
        kind = "minecraft:rule_based"
    if kind == "minecraft:simple_state_provider":
        return node["state"]
    if kind == "minecraft:weighted_state_provider":
        return {
            "type": "minecraft:weighted",
            "entries": [
                {"data": entry["data"], "weight": entry["weight"]}
                for entry in node["entries"]
            ],
        }
    if kind == "minecraft:noise_provider":
        return {
            "type": "minecraft:noise",
            "noise": _noise(node["noise"]),
            "scale": node["scale"],
            "seed": node["seed"],
            "states": node["states"],
        }
    if kind == "minecraft:rule_based":
        out = {"type": "minecraft:rule_based", "rules": []}
        if "fallback" in node:
            out["fallback"] = _provider(node["fallback"])
        for rule in node["rules"]:
            out["rules"].append(
                {"if_true": rule["if_true"], "then": _provider(rule["then"])}
            )
        return out
    if kind in ("minecraft:simple", "minecraft:weighted", "minecraft:noise",
                "minecraft:noise_threshold", "minecraft:dual_noise",
                "minecraft:random_block", "minecraft:rotated"):
        return node
    raise Unsupported(f"state provider {kind!r} has no 26.3 form")


def _noise(node):
    """1.21.1 `{firstOctave, amplitudes}` -> 26.3 `{base_octave, …}`."""
    if not isinstance(node, dict):
        raise Unsupported("noise spec is not an object")
    if "base_octave" in node:
        return node
    amplitudes = node.get("amplitudes")
    if not isinstance(amplitudes, list) or len(amplitudes) != 1:
        raise Unsupported("multi-octave noise has no single-amplitude 26.3 form")
    return {"base_octave": node["firstOctave"], "base_amplitude": amplitudes[0]}


def _count(tries):
    return {"type": "minecraft:count", "count": tries}


def _offset(spread, height):
    """1.21.1 `RandomPatchFeature` offsets with `nextInt(n+1) - nextInt(n+1)`.

    That is a triangle, which 26.3 spells `trapezoid` with a zero plateau —
    the same shape vanilla's own `patch_grass_normal.json` uses.
    """
    def axis(value):
        return {"type": "minecraft:trapezoid", "min": -value, "max": value, "plateau": 0}

    return {"type": "minecraft:offset", "x": axis(spread), "y": axis(height),
            "z": axis(spread)}


def _placed(node, patches):
    """A placed feature (inline or a file body) in 26.3's shape."""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        raise Unsupported("placed feature is not an object")
    placement = list(node.get("placement") or [])
    feature = node["feature"]
    if isinstance(feature, str):
        feature = VANILLA_FEATURE_RENAMES.get(feature, feature)
        if feature in patches:
            placement = placement + patches[feature]
        return {"feature": feature, "placement": placement}
    converted, modifiers = _feature(feature, patches)
    return {"feature": converted, "placement": placement + modifiers}


def _feature(doc, patches):
    """A configured feature in 26.3's shape, plus modifiers for its references."""
    if not isinstance(doc, dict):
        raise Unsupported("configured feature is not an object")
    kind = doc.get("type")
    if kind in RETIRED:
        return _retired(doc, patches)
    if kind not in CONVERTIBLE:
        raise Unsupported(f"feature type {kind!r} has no 26.3 decoder")
    config = doc.get("config")
    if config is None:
        # Already in 26.3's shape (a re-run, or a file this tool wrote earlier).
        _validate(doc)
        return doc, []
    if not isinstance(config, dict):
        raise Unsupported("configured feature has no config object")
    out = {"type": kind}
    out.update(config)
    if kind == "minecraft:tree":
        out["trunk_provider"] = _provider(config["trunk_provider"])
        out["foliage_provider"] = _provider(config["foliage_provider"])
        # 1.21.1's `dirt_provider` + `force_dirt` is 26.3's `below_trunk_provider`.
        out["below_trunk_provider"] = _provider(config["dirt_provider"])
        out.pop("dirt_provider", None)
        out.pop("force_dirt", None)
    elif kind == "minecraft:simple_block":
        out["to_place"] = _provider(config["to_place"])
    elif kind == "minecraft:disk":
        out["state_provider"] = _provider(config["state_provider"])
    elif kind in ("minecraft:huge_red_mushroom", "minecraft:huge_brown_mushroom"):
        out["cap_provider"] = _provider(config["cap_provider"])
        out["stem_provider"] = _provider(config["stem_provider"])
        # 26.3 requires the place-on predicate 1.21.1 did not carry; vanilla's
        # own `huge_*_mushroom.json` names this tag.
        out["can_place_on"] = {
            "type": "minecraft:matching_block_tag",
            "tag": f"minecraft:huge_{kind.removeprefix('minecraft:huge_').removesuffix('_mushroom')}"
                   f"_mushroom_can_place_on",
        }
    elif kind == "minecraft:multiface_growth":
        # The 26.3 decoder only knows the two `MultifaceSpreadeableBlock`
        # subclasses (`vegetation.rs`), so another mod's multiface block has no
        # 26.3 feature.
        if config.get("block") not in ("minecraft:glow_lichen", "minecraft:sculk_vein"):
            raise Unsupported(f"multiface block {config.get('block')!r} is not a "
                              "26.3 MultifaceSpreadeableBlock")
    elif kind in ("minecraft:vegetation_patch", "minecraft:waterlogged_vegetation_patch"):
        out["ground_state"] = _provider(config["ground_state"])
        out["vegetation_feature"] = _placed(config["vegetation_feature"], patches)
    elif kind == "minecraft:block_column":
        out["layers"] = [
            {**layer, "provider": _provider(layer["provider"])}
            for layer in config["layers"]
        ]
    elif kind in ("minecraft:simple_random_selector", "minecraft:sequence",
                  "minecraft:overlay"):
        out["features"] = [_placed(entry, patches) for entry in config["features"]]
    elif kind == "minecraft:random_selector":
        out["default"] = _placed(config["default"], patches)
        out["features"] = [
            {"chance": entry["chance"], "feature": _placed(entry["feature"], patches)}
            for entry in config["features"]
        ]
    elif kind == "minecraft:weighted_random_selector":
        out["features"] = [
            {"data": _placed(entry["data"], patches), "weight": entry["weight"]}
            for entry in config["features"]
        ]
    elif kind == "minecraft:random_boolean_selector":
        out["feature_false"] = _placed(config["feature_false"], patches)
        out["feature_true"] = _placed(config["feature_true"], patches)
    _validate(out)
    return out, []


def _retired(doc, patches):
    kind = doc["type"]
    form = RETIRED[kind]
    if form == "unsupported":
        raise Unsupported(f"{kind} has no 26.3 decoder")
    config = doc["config"]
    if form == "block_blob":
        out = {
            "type": "minecraft:block_blob",
            "state": config["state"],
            "can_place_on": {"type": "minecraft:matching_block_tag",
                             "tag": FOREST_ROCK_TAG},
        }
        _validate(out)
        return out, []
    # `patch`: the inner placed feature becomes the file, and its tries/spread
    # become placement modifiers on every reference.
    inner = config["feature"]
    if not isinstance(inner, dict):
        raise Unsupported("a patch's inner feature is a reference, not an inline feature")
    converted, modifiers = _feature(inner["feature"], patches)
    modifiers = (
        [_count(config["tries"]), _offset(config["xz_spread"], config["y_spread"])]
        + list(inner.get("placement") or [])
        + modifiers
    )
    return converted, modifiers


def _validate(doc):
    """Refuse any document that still names a type 26.3 does not decode."""
    stack = [doc]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "type" and isinstance(value, str) and value not in ALL_KNOWN:
                    raise Unsupported(f"26.3 has no decoder for {value!r}")
                if key == "predicate_type" and isinstance(value, str) \
                        and value not in PREDICATE_ALIASES:
                    raise Unsupported(f"26.3 has no predicate {value!r}")
                stack.append(value)
        elif isinstance(node, list):
            stack.extend(node)


def _feature_dirs(content: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """The carried folder and 26.3's folder for configured features.

    1.21.1 names the registry folder `configured_feature`; 26.3 renamed it to
    `feature` (`.../26.3/data/minecraft/worldgen/feature/`), and the content
    loader's `worldgen_entry` reads `data/<ns>/worldgen/feature/<name>.json`
    only (`horizon-client/src/mod_content.rs`). A carried `configured_feature`
    folder is therefore never read at all — that was the real reason 0 of the
    307 features reached the registry, on top of the shape differences.
    """
    base = content / "data" / NS / "worldgen"
    return base / "configured_feature", base / "feature"


def _carried_dir(content: pathlib.Path) -> pathlib.Path:
    """Where the files are now: the carried folder if it still exists."""
    carried, converted = _feature_dirs(content)
    return carried if carried.is_dir() else converted


def plan(content: pathlib.Path) -> tuple[dict, dict, dict]:
    """Convert the tree in memory.

    Returns `(configured, placed, kept)`:
    * `configured` — file name -> the document 26.3 should hold (every file)
    * `placed` — file name -> the document 26.3 should hold (every file)
    * `kept` — file name -> the reason it stays as carried
    """
    base = content / "data" / NS / "worldgen"
    files = sorted(_carried_dir(content).glob("*.json"))
    # Phase 1: convert each file and collect the modifiers every reference to a
    # `random_patch`/`flower` must carry. Phase 2 re-runs the same conversion
    # with the complete reference table, so a placed feature may name a patch
    # defined later in the directory.
    patches: dict[str, list] = {}
    for _ in (0, 1):
        configured: dict[str, dict] = {}
        kept: dict[str, str] = {}
        found: dict[str, list] = {}
        for path in files:
            doc = json.loads(path.read_text(encoding="utf-8"))
            try:
                converted, modifiers = _feature(doc, patches)
            except Unsupported as error:
                kept[path.name] = str(error)
                configured[path.name] = doc
                continue
            configured[path.name] = converted
            if modifiers:
                found[f"{NS}:{path.stem}"] = modifiers
        patches = found
    placed: dict[str, dict] = {}
    for path in sorted((base / "placed_feature").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        placed[path.name] = _placed(doc, patches)
    return configured, placed, kept


def check_tree(content: pathlib.Path, *, configured_count=None,
               placed_count=None) -> list[str]:
    """Every carried feature must already be what the conversion produces."""
    problems: list[str] = []
    base = content / "data" / NS / "worldgen"
    carried, converted_dir = _feature_dirs(content)
    if carried.is_dir():
        problems.append("worldgen/configured_feature: 26.3 reads worldgen/feature; "
                        "the carried folder was not renamed")
    files = sorted(_carried_dir(content).glob("*.json"))
    if configured_count is not None and len(files) != configured_count:
        problems.append(f"configured features: expected {configured_count} files, "
                        f"found {len(files)}")
    files = sorted((base / "placed_feature").glob("*.json"))
    if placed_count is not None and len(files) != placed_count:
        problems.append(f"placed features: expected {placed_count} files, found {len(files)}")
    expected_cf, expected_pf, _kept = plan(content)
    for name, expected in expected_cf.items():
        path = _carried_dir(content) / name
        if json.loads(path.read_text(encoding="utf-8")) != expected:
            problems.append(f"worldgen/feature/{name}: not in 26.3's shape")
    for name, expected in expected_pf.items():
        path = base / "placed_feature" / name
        if json.loads(path.read_text(encoding="utf-8")) != expected:
            problems.append(f"worldgen/placed_feature/{name}: not in 26.3's shape")
    return problems


def write_tree(content: pathlib.Path) -> dict[str, int]:
    """Apply the conversion and the folder rename in place."""
    base = content / "data" / NS / "worldgen"
    carried, target = _feature_dirs(content)
    source = _carried_dir(content)
    configured, placed, _kept = plan(content)
    changed = {"configured_feature": 0, "placed_feature": 0, "renamed": 0}
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        doc = json.loads(text)
        converted = configured[path.name]
        out = target / path.name
        if converted != doc:
            changed["configured_feature"] += 1
            text = json.dumps(converted, indent=2, sort_keys=True) + "\n"
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            out.write_text(text, encoding="utf-8")
        if carried.is_dir():
            changed["renamed"] += 1
    if carried.is_dir():
        for path in sorted(carried.glob("*.json")):
            path.unlink()
        carried.rmdir()
    for name, converted in placed.items():
        path = base / "placed_feature" / name
        text = path.read_text(encoding="utf-8")
        if converted != json.loads(text):
            changed["placed_feature"] += 1
            path.write_text(json.dumps(converted, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Put the carried worldgen features into Minecraft 26.3's shapes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="verify every carried feature; exit 1 on any problem")
    mode.add_argument("--write", action="store_true",
                      help="convert the carried features in place")
    parser.add_argument("--content", type=pathlib.Path, default=CONTENT)
    parser.add_argument("--report", action="store_true",
                        help="print the per-file verdicts and the counts")
    args = parser.parse_args(argv)

    if args.write:
        changed = write_tree(args.content)
        _, _, kept = plan(args.content)
        print(f"converted {changed['configured_feature']} configured features "
              f"(moved {changed['renamed']} files to worldgen/feature/) and "
              f"{changed['placed_feature']} placed features; "
              f"{len(kept)} configured features stay as carried")
    problems = check_tree(args.content, configured_count=307, placed_count=343)
    if args.report:
        _, _, kept = plan(args.content)
        for name, reason in sorted(kept.items()):
            print(f"kept  {name}: {reason}")
    if problems:
        for problem in problems:
            print(f"FAIL  {problem}", file=sys.stderr)
        return 1
    if args.check:
        _, _, kept = plan(args.content)
        print(f"OK    307 configured features in 26.3's shape under worldgen/feature/ "
              f"({307 - len(kept)} converted, {len(kept)} kept as carried), "
              f"343 placed features")
    return 0


if __name__ == "__main__":
    sys.exit(main())
