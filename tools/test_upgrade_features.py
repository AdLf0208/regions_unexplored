#!/usr/bin/env python3
"""Tests for `tools/upgrade_features.py` — the 1.21.1 → 26.3 feature shapes.

Every expected value is taken from vanilla 26.3's own prepared data
(`.../26.3/data/minecraft/worldgen/{feature,block_state_provider}/`) and from
the pin's decoder (`horizon-world/src/worldgen/{feature_graph,state_provider,
tree,simple_block,disk,value_provider,placement,block_predicate}.rs`), never
from the tool's implementation:

* `oak.json` — `{"type": "minecraft:tree", "below_trunk_provider": …,
  "trunk_provider": {"id": "minecraft:oak_log", …}}`: no `config` wrapper, a
  bare state as the provider, `below_trunk_provider` instead of `dirt_provider`;
* `crimson_forest_vegetation.json` — `minecraft:weighted` with `data`/`weight`
  entries and `to_place` at the root of a `simple_block`;
* `patch_grass_normal.json` — `count` then a `trapezoid` offset, the shape
  1.21.1's `random_patch` tries/spread becomes;
* `forest_rock.json` — `block_blob` with the `forest_rock_can_place_on` tag;
* `huge_brown_mushroom.json` — `cap_provider`/`stem_provider` plus the
  required `can_place_on` predicate;
* `flower_plain.json` — a `simple_block` whose `to_place` is a named provider;
* `glow_lichen.json` — `multiface_growth` for `minecraft:glow_lichen` only.

Run: `python3 -m unittest discover -s ports/regions_unexplored/tools -p 'test_*.py'`
"""

from __future__ import annotations

import copy
import json
import pathlib
import tempfile
import unittest

import upgrade_features as uf


def tree_feature() -> dict:
    """`alpha_oak_tree.json` as the 1.21.1 jar ships it (trimmed)."""
    return {
        "config": {
            "decorators": [],
            "dirt_provider": {
                "state": {"id": "minecraft:dirt"},
                "type": "minecraft:simple_state_provider",
            },
            "foliage_placer": {
                "height": 3, "offset": 0, "radius": 2,
                "type": "minecraft:blob_foliage_placer",
            },
            "foliage_provider": {
                "state": {"id": "regions_unexplored:alpha_leaves"},
                "type": "minecraft:simple_state_provider",
            },
            "force_dirt": False,
            "ignore_vines": True,
            "minimum_size": {
                "limit": 1, "lower_size": 0,
                "type": "minecraft:two_layers_feature_size", "upper_size": 1,
            },
            "trunk_placer": {
                "base_height": 4, "height_rand_a": 2, "height_rand_b": 0,
                "type": "minecraft:straight_trunk_placer",
            },
            "trunk_provider": {
                "state": {"id": "regions_unexplored:alpha_log"},
                "type": "minecraft:simple_state_provider",
            },
        },
        "type": "minecraft:tree",
    }


def patch_feature() -> dict:
    """`patch_alpha_dandelion.json` (a 1.21.1 `flower`)."""
    return {
        "config": {
            "feature": {
                "feature": {
                    "config": {
                        "to_place": {
                            "state": {"id": "regions_unexplored:alpha_dandelion"},
                            "type": "minecraft:simple_state_provider",
                        }
                    },
                    "type": "minecraft:simple_block",
                },
                "placement": [{
                    "predicate": {"blocks": "minecraft:air",
                                  "type": "minecraft:matching_blocks"},
                    "type": "minecraft:block_predicate_filter",
                }],
            },
            "tries": 96,
            "xz_spread": 6,
            "y_spread": 2,
        },
        "type": "minecraft:flower",
    }


class TreeShape(unittest.TestCase):
    def test_config_is_unwrapped_and_providers_are_states(self):
        converted, modifiers = uf._feature(tree_feature(), {})
        self.assertEqual(modifiers, [])
        self.assertNotIn("config", converted)
        self.assertEqual(converted["type"], "minecraft:tree")
        self.assertEqual(converted["trunk_provider"],
                         {"id": "regions_unexplored:alpha_log"})
        self.assertEqual(converted["foliage_provider"],
                         {"id": "regions_unexplored:alpha_leaves"})

    def test_dirt_provider_becomes_below_trunk_provider(self):
        converted, _ = uf._feature(tree_feature(), {})
        self.assertEqual(converted["below_trunk_provider"], {"id": "minecraft:dirt"})
        self.assertNotIn("dirt_provider", converted)
        # 1.21.1 `force_dirt` has no 26.3 field; the decoder never reads it.
        self.assertNotIn("force_dirt", converted)

    def test_the_pin_requires_below_trunk_provider(self):
        # `tree.rs::TreeFeature::decode` requires it, so dropping it is a bug.
        converted, _ = uf._feature(tree_feature(), {})
        self.assertIn("below_trunk_provider", converted)

    def test_a_mod_foliage_placer_keeps_the_file(self):
        doc = tree_feature()
        doc["config"]["foliage_placer"]["type"] = \
            "regions_unexplored:sakura_foliage_placer"
        with self.assertRaises(uf.Unsupported):
            uf._feature(doc, {})


class PatchShape(unittest.TestCase):
    def test_a_patch_becomes_its_inner_feature(self):
        converted, modifiers = uf._feature(patch_feature(), {})
        self.assertEqual(converted["type"], "minecraft:simple_block")
        self.assertEqual(converted["to_place"], {"id": "regions_unexplored:alpha_dandelion"})
        # count(tries) + the offset + the patch's own placement
        self.assertEqual(modifiers[0], {"type": "minecraft:count", "count": 96})
        offset = modifiers[1]
        self.assertEqual(offset["type"], "minecraft:offset")
        self.assertEqual(offset["x"],
                         {"type": "minecraft:trapezoid", "min": -6, "max": 6,
                          "plateau": 0})
        self.assertEqual(offset["y"],
                         {"type": "minecraft:trapezoid", "min": -2, "max": 2,
                          "plateau": 0})
        self.assertEqual(modifiers[2]["type"], "minecraft:block_predicate_filter")

    def test_a_reference_to_a_patch_gets_the_modifiers_appended(self):
        placed = {"feature": "regions_unexplored:patch_alpha_dandelion",
                  "placement": [{"type": "minecraft:in_square"}]}
        patches = {"regions_unexplored:patch_alpha_dandelion": [{"type": "minecraft:count",
                                                                 "count": 96}]}
        converted = uf._placed(placed, patches)
        self.assertEqual([m["type"] for m in converted["placement"]],
                         ["minecraft:in_square", "minecraft:count"])

    def test_vanilla_patch_cactus_is_renamed_to_cactus(self):
        # 26.3 keeps `patch_cactus` as a *placed* feature, so the old id names
        # no configured feature; vanilla's own `cactus.json` is the successor.
        converted = uf._placed({"feature": "minecraft:patch_cactus",
                                "placement": []}, {})
        self.assertEqual(converted["feature"], "minecraft:cactus")


class ProviderShape(unittest.TestCase):
    def test_weighted_state_provider_becomes_weighted(self):
        provider = uf._provider({
            "type": "minecraft:weighted_state_provider",
            "entries": [{"data": {"id": "minecraft:crimson_roots"}, "weight": 87}],
        })
        self.assertEqual(provider, {
            "type": "minecraft:weighted",
            "entries": [{"data": {"id": "minecraft:crimson_roots"}, "weight": 87}],
        })

    def test_a_rule_based_provider_without_a_type_is_named(self):
        # 1.21.1's rule-based provider carries no `type` (the jar's disks).
        provider = uf._provider({
            "fallback": {"state": {"id": "minecraft:clay"},
                         "type": "minecraft:simple_state_provider"},
            "rules": [],
        })
        self.assertEqual(provider["type"], "minecraft:rule_based")
        self.assertEqual(provider["fallback"], {"id": "minecraft:clay"})

    def test_single_octave_noise_is_renamed_and_reshaped(self):
        provider = uf._provider({
            "type": "minecraft:noise_provider",
            "noise": {"amplitudes": [1.0], "firstOctave": 0},
            "scale": 0.075, "seed": 2345,
            "states": [{"id": "regions_unexplored:poppy_bush"}],
        })
        self.assertEqual(provider["type"], "minecraft:noise")
        self.assertEqual(provider["noise"], {"base_octave": 0, "base_amplitude": 1.0})

    def test_multi_octave_noise_is_refused(self):
        with self.assertRaises(uf.Unsupported):
            uf._provider({
                "type": "minecraft:noise_provider",
                "noise": {"amplitudes": [1.0, 0.5], "firstOctave": -1},
                "scale": 1.0, "seed": 1, "states": [{"id": "minecraft:stone"}],
            })


class RetiredTypes(unittest.TestCase):
    def test_forest_rock_becomes_a_block_blob(self):
        converted, modifiers = uf._feature({
            "config": {"state": {"id": "minecraft:mossy_cobblestone"}},
            "type": "minecraft:forest_rock",
        }, {})
        self.assertEqual(modifiers, [])
        self.assertEqual(converted["type"], "minecraft:block_blob")
        self.assertEqual(converted["can_place_on"],
                         {"type": "minecraft:matching_block_tag",
                          "tag": "minecraft:forest_rock_can_place_on"})

    def test_nether_forest_vegetation_is_kept(self):
        with self.assertRaises(uf.Unsupported):
            uf._feature({
                "config": {"spread_width": 3, "spread_height": 1,
                           "state_provider": {"type": "minecraft:weighted_state_provider",
                                              "entries": []}},
                "type": "minecraft:nether_forest_vegetation",
            }, {})

    def test_a_mod_feature_type_is_kept(self):
        with self.assertRaises(uf.Unsupported):
            uf._feature({"config": {}, "type": "regions_unexplored:shrub"}, {})


class MushroomAndMultiface(unittest.TestCase):
    def test_huge_mushroom_gets_the_required_can_place_on(self):
        converted, _ = uf._feature({
            "config": {
                "cap_provider": {"state": {"id": "minecraft:brown_mushroom_block"},
                                 "type": "minecraft:simple_state_provider"},
                "foliage_radius": 3,
                "stem_provider": {"state": {"id": "minecraft:mushroom_stem"},
                                  "type": "minecraft:simple_state_provider"},
            },
            "type": "minecraft:huge_brown_mushroom",
        }, {})
        self.assertEqual(converted["can_place_on"]["tag"],
                         "minecraft:huge_brown_mushroom_can_place_on")
        self.assertEqual(converted["cap_provider"]["id"], "minecraft:brown_mushroom_block")

    def test_a_non_vanilla_multiface_block_is_kept(self):
        # `vegetation.rs` only decodes glow_lichen and sculk_vein.
        with self.assertRaises(uf.Unsupported):
            uf._feature({
                "config": {"block": "regions_unexplored:hyacinth_flowers",
                           "can_be_placed_on": ["minecraft:stone"]},
                "type": "minecraft:multiface_growth",
            }, {})


class FolderAndTree(unittest.TestCase):
    def test_the_carried_folder_is_moved_to_feature(self):
        # 26.3's content loader reads `worldgen/feature/` only
        # (`mod_content.rs::worldgen_entry`), so `configured_feature/` is dead.
        with tempfile.TemporaryDirectory() as tmp:
            content = pathlib.Path(tmp)
            base = content / "data" / "regions_unexplored" / "worldgen"
            (base / "configured_feature").mkdir(parents=True)
            (base / "placed_feature").mkdir()
            (base / "configured_feature" / "alpha_oak_tree.json").write_text(
                json.dumps(tree_feature()), encoding="utf-8")
            (base / "placed_feature" / "alpha_oak_tree.json").write_text(
                json.dumps({"feature": "regions_unexplored:alpha_oak_tree",
                            "placement": []}), encoding="utf-8")
            changed = uf.write_tree(content)
            self.assertEqual(changed["renamed"], 1)
            self.assertFalse((base / "configured_feature").exists())
            converted = json.loads(
                (base / "feature" / "alpha_oak_tree.json").read_text(encoding="utf-8"))
            self.assertIn("below_trunk_provider", converted)
            self.assertEqual(uf.check_tree(content), [])

    def test_a_second_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = pathlib.Path(tmp)
            base = content / "data" / "regions_unexplored" / "worldgen"
            (base / "configured_feature").mkdir(parents=True)
            (base / "placed_feature").mkdir()
            for name, doc in (("patch_alpha_dandelion", patch_feature()),
                              ("alpha_oak_tree", tree_feature())):
                (base / "configured_feature" / f"{name}.json").write_text(
                    json.dumps(doc), encoding="utf-8")
            (base / "placed_feature" / "patch_alpha_dandelion.json").write_text(
                json.dumps({"feature": "regions_unexplored:patch_alpha_dandelion",
                            "placement": [{"type": "minecraft:in_square"}]}),
                encoding="utf-8")
            first = uf.write_tree(content)
            second = uf.write_tree(content)
            self.assertEqual(first["configured_feature"], 2)
            self.assertEqual(second["configured_feature"], 0)
            self.assertEqual(second["placed_feature"], 0)
            placed = json.loads((base / "placed_feature" / "patch_alpha_dandelion.json")
                                .read_text(encoding="utf-8"))
            self.assertEqual(placed["placement"][0]["type"], "minecraft:in_square")
            self.assertEqual(placed["placement"][1]["type"], "minecraft:count")
            self.assertEqual(placed["placement"][1]["count"], 96)

    def test_a_kept_file_keeps_its_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = pathlib.Path(tmp)
            base = content / "data" / "regions_unexplored" / "worldgen"
            (base / "configured_feature").mkdir(parents=True)
            (base / "placed_feature").mkdir()
            text = '{"config": {}, "type": "regions_unexplored:shrub"}'
            (base / "configured_feature" / "shrub.json").write_text(text, encoding="utf-8")
            uf.write_tree(content)
            self.assertEqual((base / "feature" / "shrub.json").read_text(encoding="utf-8"),
                             text)


if __name__ == "__main__":
    unittest.main()
