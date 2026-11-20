#!/usr/bin/env python3
"""Tests for `tools/upgrade_shapes.py` — the 1.21.1 → 26.3 shape fixes.

Every expected value here is taken from vanilla 26.3's own prepared data
(`data/minecraft/worldgen/biome/*.json`, `data/minecraft/advancement/**`) and
from the engine's predicate validator, never from the tool's implementation:

* `plains.json` has `"carvers": ["minecraft:cave", ...]` (a list) and colours
  as `#rrggbb`;
* `swamp.json` keeps `foliage_color`/`grass_color` in `effects` and carries the
  music in `attributes["minecraft:audio/background_music"]["default"]`;
* `soul_sand_valley.json` carries `minecraft:visual/ambient_particles`
  (`{argument, modifier: append}`), `minecraft:audio/ambient_sounds`
  (`{loop, mood, additions}`) and `minecraft:gameplay/natural_mob_spawns`
  (`{argument: {spawn_costs, spawns_by_category}, modifier: overlay}`) with
  `count` as an int or a `minecraft:uniform` provider;
* `badlands.json` has `minecraft:gameplay/creature_world_gen_spawn_probability`
  as a plain number;
* `adventure/adventuring_time.json` has
  `{"conditions": {"player": {"type": "minecraft:entity_properties", ...,
  "predicate": {"minecraft:location": ...}}}}`.

Run: `python3 -m unittest discover -s ports/regions_unexplored/tools -p 'test_*.py'`
"""

from __future__ import annotations

import copy
import json
import pathlib
import tempfile
import unittest

import upgrade_shapes as up


def legacy_biome() -> dict:
    """The shape Regions Unexplored's 1.21.1 jar ships (alpha_grove, trimmed)."""
    return {
        "carvers": {"air": ["minecraft:cave", "minecraft:canyon"]},
        "creature_spawn_probability": 0.03,
        "downfall": 0.6,
        "effects": {
            "additions_sound": {
                "sound": "minecraft:ambient.cave.additions",
                "tick_chance": 0.0111,
            },
            "ambient_sound": "minecraft:ambient.cave",
            "fog_color": 0xC0D8FF,
            "foliage_color": 0x6A7039,
            "grass_color": 0x91BD59,
            "mood_sound": {
                "block_search_extent": 8,
                "offset": 2.0,
                "sound": "minecraft:ambient.cave",
                "tick_delay": 6000,
            },
            "music": {
                "max_delay": 24000,
                "min_delay": 12000,
                "replace_current_music": False,
                "sound": "minecraft:music.overworld.forest",
            },
            "particle": {"options": {"type": "minecraft:ash"}, "probability": 0.05},
            "sky_color": 0x78A7FF,
            "water_color": 0x3F76E4,
            "water_fog_color": 0x050533,
        },
        "features": [[], ["minecraft:lake_lava_surface"]],
        "has_precipitation": True,
        "spawn_costs": {},
        "spawners": {
            "creature": [
                {"maxCount": 4, "minCount": 4, "type": "minecraft:cow", "weight": 8}
            ],
            "misc": [],
            "monster": [
                {"maxCount": 4, "minCount": 1, "type": "minecraft:zombie", "weight": 95}
            ],
        },
        "temperature": 0.7,
    }


def legacy_advancement() -> dict:
    return {
        "criteria": {
            "alpha_grove": {
                "conditions": {
                    "player": [
                        {
                            "condition": "minecraft:entity_properties",
                            "entity": "this",
                            "predicate": {
                                "location": {
                                    "biomes": "regions_unexplored:alpha_grove"
                                }
                            },
                        }
                    ]
                },
                "trigger": "minecraft:location",
            }
        },
        "display": {"title": {"translate": "advancement.ru.alpha_grove"}},
        "parent": "regions_unexplored:parent",
    }


class BiomeShape(unittest.TestCase):
    def test_carvers_map_becomes_a_flat_list(self):
        self.assertEqual(
            up.convert_biome(legacy_biome())["carvers"],
            ["minecraft:cave", "minecraft:canyon"],
        )

    def test_carvers_bare_string_becomes_a_one_element_list(self):
        biome = legacy_biome()
        biome["carvers"] = {"air": "minecraft:nether_cave"}
        self.assertEqual(
            up.convert_biome(biome)["carvers"], ["minecraft:nether_cave"]
        )

    def test_carvers_empty_map_becomes_an_empty_list(self):
        biome = legacy_biome()
        biome["carvers"] = {}
        self.assertEqual(up.convert_biome(biome)["carvers"], [])

    def test_visual_colours_move_to_attributes_as_hex(self):
        attributes = up.convert_biome(legacy_biome())["attributes"]
        self.assertEqual(attributes["minecraft:visual/sky_color"], "#78a7ff")
        self.assertEqual(attributes["minecraft:visual/fog_color"], "#c0d8ff")
        self.assertEqual(attributes["minecraft:visual/water_fog_color"], "#050533")

    def test_effects_keeps_water_and_tint_colours_as_hex(self):
        effects = up.convert_biome(legacy_biome())["effects"]
        self.assertEqual(effects["water_color"], "#3f76e4")
        self.assertEqual(effects["foliage_color"], "#6a7039")
        self.assertEqual(effects["grass_color"], "#91bd59")
        for legacy in ("sky_color", "fog_color", "water_fog_color", "music",
                       "mood_sound", "particle"):
            self.assertNotIn(legacy, effects)

    def test_music_mood_and_ambient_sounds_move_to_audio_attributes(self):
        attributes = up.convert_biome(legacy_biome())["attributes"]
        self.assertEqual(
            attributes["minecraft:audio/background_music"],
            {
                "default": {
                    "max_delay": 24000,
                    "min_delay": 12000,
                    "sound": "minecraft:music.overworld.forest",
                }
            },
        )
        sounds = attributes["minecraft:audio/ambient_sounds"]
        self.assertEqual(
            sounds["mood"],
            {
                "block_search_extent": 8,
                "offset": 2.0,
                "sound": "minecraft:ambient.cave",
                "tick_delay": 6000,
            },
        )
        self.assertEqual(sounds["loop"], "minecraft:ambient.cave")
        self.assertEqual(
            sounds["additions"],
            {"sound": "minecraft:ambient.cave.additions", "tick_chance": 0.0111},
        )

    def test_particle_moves_to_the_ambient_particles_attribute(self):
        self.assertEqual(
            up.convert_biome(legacy_biome())["attributes"][
                "minecraft:visual/ambient_particles"
            ],
            {
                "argument": [
                    {"particle": {"type": "minecraft:ash"}, "probability": 0.05}
                ],
                "modifier": "append",
            },
        )

    def test_spawners_become_natural_mob_spawns_with_counts(self):
        attribute = up.convert_biome(legacy_biome())["attributes"][
            "minecraft:gameplay/natural_mob_spawns"
        ]
        self.assertEqual(attribute["modifier"], "overlay")
        self.assertEqual(attribute["argument"]["spawn_costs"], {})
        self.assertEqual(
            attribute["argument"]["spawns_by_category"],
            {
                "creature": [
                    {"type": "minecraft:cow", "weight": 8, "count": 4}
                ],
                "misc": [],
                "monster": [
                    {
                        "type": "minecraft:zombie",
                        "weight": 95,
                        "count": {
                            "type": "minecraft:uniform",
                            "min_inclusive": 1,
                            "max_inclusive": 4,
                        },
                    }
                ],
            },
        )

    def test_creature_spawn_probability_becomes_an_attribute(self):
        attributes = up.convert_biome(legacy_biome())["attributes"]
        self.assertEqual(
            attributes["minecraft:gameplay/creature_world_gen_spawn_probability"],
            0.03,
        )

    def test_default_creature_spawn_probability_is_left_out(self):
        biome = legacy_biome()
        biome["creature_spawn_probability"] = 0.1
        attributes = up.convert_biome(biome)["attributes"]
        self.assertNotIn(
            "minecraft:gameplay/creature_world_gen_spawn_probability", attributes
        )

    def test_legacy_keys_are_gone(self):
        converted = up.convert_biome(legacy_biome())
        for legacy in ("spawners", "spawn_costs", "creature_spawn_probability"):
            self.assertNotIn(legacy, converted)
        self.assertEqual(converted["temperature"], 0.7)
        self.assertEqual(converted["has_precipitation"], True)
        self.assertEqual(converted["features"], [[], ["minecraft:lake_lava_surface"]])

    def test_conversion_is_idempotent(self):
        once = up.convert_biome(legacy_biome())
        self.assertEqual(up.convert_biome(copy.deepcopy(once)), once)

    def test_unconverted_biome_is_not_equal_to_its_conversion(self):
        # The fixpoint test `--check` relies on: a 1.21.1 file differs from the
        # 26.3 form, so the check can tell them apart.
        self.assertNotEqual(up.convert_biome(legacy_biome()), legacy_biome())


class AdvancementShape(unittest.TestCase):
    def test_condition_becomes_type_and_the_player_list_an_object(self):
        self.assertEqual(
            up.convert_advancement(legacy_advancement())["criteria"]["alpha_grove"],
            {
                "conditions": {
                    "player": {
                        "type": "minecraft:entity_properties",
                        "entity": "this",
                        "predicate": {
                            "minecraft:location": {
                                "biomes": "regions_unexplored:alpha_grove"
                            }
                        },
                    }
                },
                "trigger": "minecraft:location",
            },
        )

    def test_entity_slot_is_unwrapped_too(self):
        data = {
            "criteria": {
                "killed": {
                    "conditions": {
                        "entity": [
                            {
                                "condition": "minecraft:entity_properties",
                                "entity": "this",
                                "predicate": {"type": "minecraft:zombie"},
                            }
                        ]
                    },
                    "trigger": "minecraft:player_killed_entity",
                }
            }
        }
        entry = up.convert_advancement(data)["criteria"]["killed"]["conditions"]["entity"]
        self.assertEqual(entry["type"], "minecraft:entity_properties")
        self.assertEqual(entry["predicate"], {"minecraft:entity_type": "minecraft:zombie"})

    def test_a_multi_entry_condition_list_is_refused(self):
        data = legacy_advancement()
        data["criteria"]["alpha_grove"]["conditions"]["player"].append(
            {"condition": "minecraft:tick"}
        )
        with self.assertRaises(ValueError):
            up.convert_advancement(data)

    def test_an_unverified_predicate_field_is_refused(self):
        data = legacy_advancement()
        data["criteria"]["alpha_grove"]["conditions"]["player"][0]["predicate"] = {
            "invented_field": 1
        }
        with self.assertRaises(ValueError):
            up.convert_advancement(data)

    def test_conversion_is_idempotent_and_keeps_everything_else(self):
        once = up.convert_advancement(legacy_advancement())
        self.assertEqual(up.convert_advancement(copy.deepcopy(once)), once)
        self.assertEqual(once["display"], legacy_advancement()["display"])
        self.assertEqual(once["parent"], "regions_unexplored:parent")

    def test_advancement_without_predicates_is_unchanged(self):
        data = {"criteria": {"slept": {"trigger": "minecraft:slept_in_bed"}}}
        self.assertEqual(up.convert_advancement(data), data)


class EnterBlockShape(unittest.TestCase):
    """26.3 reads an `enter_block` criterion's block as `blocks`.

    The pin's own carry says why (`horizon-port-pack/src/carry.rs:366`): 26.3
    skips the old `block` field, so the criterion matched *any* block the player
    entered — Regions Unexplored's "Downer" on the first dive. Vanilla 26.3's
    `end/enter_end_gateway.json` shows the shape.
    """

    def test_enter_block_names_its_blocks(self):
        data = {
            "criteria": {
                "dive": {
                    "trigger": "minecraft:enter_block",
                    "conditions": {"block": "regions_unexplored:dorcel"},
                }
            }
        }
        self.assertEqual(
            up.convert_advancement(data)["criteria"]["dive"]["conditions"],
            {"blocks": "regions_unexplored:dorcel"},
        )

    def test_enter_block_keeps_an_existing_blocks_field(self):
        data = {
            "criteria": {
                "swim": {
                    "trigger": "minecraft:enter_block",
                    "conditions": {"blocks": "minecraft:water"},
                }
            }
        }
        self.assertEqual(up.convert_advancement(data), data)

    def test_other_triggers_keep_their_block_field(self):
        data = {
            "criteria": {
                "mined": {
                    "trigger": "minecraft:item_used_on_block",
                    "conditions": {"block": "minecraft:stone"},
                }
            }
        }
        self.assertEqual(up.convert_advancement(data), data)


class CheckTree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.biomes = self.root / "data" / up.NS / "worldgen" / "biome"
        self.advancements = self.root / "data" / up.NS / "advancement"
        self.biomes.mkdir(parents=True)
        self.advancements.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path: pathlib.Path, data: dict) -> None:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def test_check_names_every_unconverted_file(self):
        self.write(self.biomes / "alpha_grove.json", legacy_biome())
        self.write(self.advancements / "regions_explored.json", legacy_advancement())
        problems = up.check_tree(self.root)
        self.assertEqual(len(problems), 2, problems)
        joined = "\n".join(problems)
        self.assertIn("worldgen/biome/alpha_grove.json", joined)
        self.assertIn("advancement/regions_explored.json", joined)

    def test_check_is_green_after_write(self):
        self.write(self.biomes / "alpha_grove.json", legacy_biome())
        self.write(self.advancements / "regions_explored.json", legacy_advancement())
        counts = up.write_tree(self.root)
        self.assertEqual(counts, {"biomes": 1, "advancements": 1})
        self.assertEqual(up.check_tree(self.root), [])

    def test_check_counts_the_expected_files(self):
        self.write(self.biomes / "alpha_grove.json", up.convert_biome(legacy_biome()))
        self.write(self.advancements / "regions_explored.json",
                   up.convert_advancement(legacy_advancement()))
        problems = up.check_tree(self.root, biomes=71, advancements=671)
        self.assertTrue(any("71" in p for p in problems), problems)
        self.assertTrue(any("671" in p for p in problems), problems)


class PortContent(unittest.TestCase):
    """The delivered content must be in the 26.3 shape (the defect's regression)."""

    def test_port_content_is_converted(self):
        problems = up.check_tree(up.CONTENT, biomes=71, advancements=671)
        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
