#!/usr/bin/env python3
"""Generate block declarations for the regions_unexplored carry.

The raw carry has no NeoForge oracle: it guesses a block's template from the
property names *its blockstate lists*. Many Regions Unexplored blockstates list
only their default state (`"variants": {"": ...}`), so the guess loses states
the Java class has (wood planks, leaves, saplings, signs...) and falls back to
`minecraft:stone`; 39 blocks have properties no template in the carry's table
has and are left out entirely.

This script reads the jar's blockstates and models and writes one complete
declaration per block that the raw carry got wrong, to `content/patches/block/`.
It invents no assets: every declaration names a vanilla template and, where the
block has a state of its own, declares it; the jar's blockstate, models,
textures and loot table stay the block's own.

Idempotent. Run from the port directory:

    python3 tools/gen_patches.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

PORT = Path(__file__).resolve().parent.parent
# The *raw* carry output: the patched port content must not become the next
# run's baseline, or re-running would find nothing to patch.
CARRY = Path(
    os.environ.get(
        "RU_CARRY",
        PORT.parent / "_shared" / "carry-work" / "regions_unexplored"
        / "work" / "mods" / "regions_unexplored" / "carry",
    )
)
PATCHES = PORT / "content" / "patches"
JAR = Path(
    os.environ.get(
        "RU_JAR",
        PORT.parent / "_shared" / "carry-work" / "regions_unexplored"
        / "regions_unexplored-neoforge-1.21.1-0.5.9.jar",
    )
)
MOD = "regions_unexplored"

# Blocks the raw carry could not place, with the template and declared states
# read from the upstream classes (analysis) and the jar's own blockstates.
SPECIAL: dict[str, dict] = {
    # Snowy grass/podzol blocks: `minecraft:grass_block`'s `snowy`, kept.
    **{
        n: {"template": "minecraft:grass_block"}
        for n in (
            "alpha_grass_block",
            "argillite_grass_block",
            "chalk_grass_block",
            "deepslate_grass_block",
            "peat_grass_block",
            "silt_grass_block",
            "stone_grass_block",
        )
    },
    "peat_podzol": {"template": "minecraft:podzol"},
    "silt_podzol": {"template": "minecraft:podzol"},
    "peat_farmland": {"template": "minecraft:farmland"},
    "silt_farmland": {"template": "minecraft:farmland"},
    # AshenDirtBlock/AshenGrassBlock: `smouldering`, light 7 when true.
    "ashen_dirt": {
        "template": "minecraft:dirt",
        "state": {"smouldering": {"type": "boolean"}},
        "default": {"smouldering": "false"},
        "random_ticks": False,
    },
    "ashen_grass": {
        "template": "minecraft:grass_block",
        "state": {"smouldering": {"type": "boolean"}},
        "default": {"smouldering": "false"},
    },
    # Rotated pillars with the mod's extra states.
    "bamboo_log": {
        "template": "minecraft:bamboo_block",
        "state": {"leaves": {"type": "boolean"}},
        "default": {"leaves": "true"},
    },
    "brimwood_log_magma": {
        "template": "minecraft:magma_block",
        "state": {"transition_block": {"type": "boolean"}},
        "default": {"transition_block": "false"},
    },
    "pine_log": {
        "template": "minecraft:oak_log",
        "state": {
            "is_stripped": {"type": "boolean"},
            "transition_block": {"type": "boolean"},
        },
        "default": {"is_stripped": "false", "transition_block": "false"},
    },
    "silver_birch_log": {
        "template": "minecraft:oak_log",
        "state": {"is_base": {"type": "boolean"}},
        "default": {"is_base": "false"},
    },
    # Multiface flowers (six sides, like glow lichen); do not spread.
    **{
        n: {"template": "minecraft:glow_lichen", "random_ticks": False}
        for n in (
            "blue_magnolia_flowers",
            "pink_magnolia_flowers",
            "white_magnolia_flowers",
            "hyacinth_flowers",
        )
    },
    # `facing` + `flower_amount` ground cover: pink petals' own state set.
    **{
        n: {"template": "minecraft:pink_petals"}
        for n in (
            "clover",
            "enchanted_birch_leaf_pile",
            "maple_leaf_pile",
            "mycotoxic_mushrooms",
            "orange_coneflower",
            "orange_maple_leaf_pile",
            "purple_coneflower",
            "red_maple_leaf_pile",
            "silver_birch_leaf_pile",
        )
    },
    # Pointed blocks: pointed dripstone has exactly thickness+vertical_direction.
    "icicle": {"template": "minecraft:pointed_dripstone"},
    "pointed_redstone": {"template": "minecraft:pointed_dripstone"},
    "hanging_prismarite": {
        "template": "minecraft:pointed_dripstone",
        "state": {
            "hanging_prismarite_shape": {
                "type": "enum",
                "values": ["column", "frustum", "tip"],
            }
        },
        "default": {"hanging_prismarite_shape": "column"},
        "random_ticks": False,
    },
    "tall_hyacinth_stock": {
        "template": "minecraft:short_grass",
        "state": {
            "tall_hyacinth_stock_shape": {
                "type": "enum",
                "values": [
                    "middle",
                    "frustum",
                    "tip",
                    "base",
                    "base_frustum",
                    "base_tip",
                ],
            }
        },
        "default": {"tall_hyacinth_stock_shape": "middle"},
    },
    "saguaro_cactus": {
        "template": "minecraft:stone",
        "state": {"cactus_shape": {"type": "enum", "values": []}},  # values read
        "default": {"cactus_shape": "up_down"},
    },
    "joshua_leaves": {
        "template": "minecraft:oak_leaves",
        "state": {
            "half": {"type": "enum", "values": ["lower", "upper"]},
            "natural": {"type": "boolean"},
        },
        "default": {"half": "lower", "natural": "false"},
    },
    "sandy_grass": {
        "template": "minecraft:short_grass",
        "state": {"is_red": {"type": "boolean"}},
        "default": {"is_red": "false"},
    },
    "sandy_tall_grass": {
        "template": "minecraft:tall_grass",
        "state": {"is_red": {"type": "boolean"}},
        "default": {"is_red": "false"},
    },
    "dusktrap": {
        "template": "minecraft:tall_grass",
        "state": {"closed": {"type": "boolean"}},
        "default": {"closed": "false"},
    },
}

# Wrong guesses the name alone settles (each is the vanilla block the upstream
# class copies or the nearest same-material vanilla block).
NAMED: dict[str, str] = {
    "ash": "minecraft:sand",
    "volcanic_ash": "minecraft:sand",
    "mossy_stone": "minecraft:mossy_cobblestone",
    "overgrown_bone_block": "minecraft:bone_block",
    "raw_redstone_block": "minecraft:redstone_block",
    "cobalt_obsidian": "minecraft:obsidian",
    "peat_dirt": "minecraft:dirt",
    "silt_dirt": "minecraft:dirt",
    "peat_coarse_dirt": "minecraft:coarse_dirt",
    "silt_coarse_dirt": "minecraft:coarse_dirt",
    "peat_mud": "minecraft:mud",
    "silt_mud": "minecraft:mud",
    "mycotoxic_moss": "minecraft:moss_block",
    "brimsprout_nylium": "minecraft:crimson_nylium",
    "cobalt_nylium": "minecraft:crimson_nylium",
    "glistering_nylium": "minecraft:crimson_nylium",
    "viridescent_nylium": "minecraft:crimson_nylium",
    "deepslate_viridescent_nylium": "minecraft:crimson_nylium",
    "glowing_blue_bioshroom_block": "minecraft:shroomlight",
    "glowing_green_bioshroom_block": "minecraft:shroomlight",
    "glowing_pink_bioshroom_block": "minecraft:shroomlight",
    "glowing_yellow_bioshroom_block": "minecraft:shroomlight",
    "prismaglass": "minecraft:glass",
    "prismoss": "minecraft:moss_block",
    "deepslate_prismoss": "minecraft:moss_block",
    "peat_dirt_path": "minecraft:dirt_path",
    "silt_dirt_path": "minecraft:dirt_path",
    "hyacinth_lamp": "minecraft:shroomlight",
    "duckweed": "minecraft:lily_pad",
    "flowering_lily_pad": "minecraft:lily_pad",
    "glistering_fern": "minecraft:fern",
    "prismarite_cluster": "minecraft:amethyst_cluster",
    "dropleaf": "minecraft:poppy",
    "dropleaf_plant": "minecraft:poppy",
    "glistering_ivy": "minecraft:poppy",
    "hanging_earlight": "minecraft:poppy",
    "hanging_earlight_plant": "minecraft:poppy",
    "hyacinth_bloom": "minecraft:poppy",
    "blackstone_cluster": "minecraft:stone",
}

PLANT_TEMPLATES = {
    "minecraft:block/cross": "minecraft:poppy",
    "block/cross": "minecraft:poppy",
    "minecraft:block/tinted_cross": "minecraft:short_grass",
    "block/tinted_cross": "minecraft:short_grass",
}

SIGN_SUFFIXES = (
    "_wall_hanging_sign",
    "_hanging_sign",
    "_wall_sign",
    "_sign",
)


def read_json(z: zipfile.ZipFile, name: str):
    return json.loads(z.read(name))


def first_model(blockstate: dict) -> str | None:
    for v in blockstate.get("variants", {}).values():
        if isinstance(v, list):
            v = v[0]
        return v.get("model")
    for part in blockstate.get("multipart", []):
        return part.get("apply", {}).get("model")
    return None


def state_values(blockstate: dict, prop: str) -> list[str]:
    out: set[str] = set()

    def add(cond):
        if not isinstance(cond, dict):
            return
        v = cond.get(prop)
        if isinstance(v, str):
            out.update(x.lstrip("!") for x in v.split("|"))

    for key in blockstate.get("variants", {}):
        for pair in key.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                if k == prop:
                    out.add(v)
    for part in blockstate.get("multipart", []):
        when = part.get("when", {})
        add(when)
        for k in ("OR", "AND"):
            for c in when.get(k, []) if isinstance(when.get(k), list) else []:
                add(c)
    return sorted(out)


def main() -> int:
    if not JAR.is_file():
        print(f"jar not found: {JAR}", file=sys.stderr)
        return 1
    z = zipfile.ZipFile(JAR)
    blockstates = {
        n[len(f"assets/{MOD}/blockstates/"):-5]: read_json(z, n)
        for n in z.namelist()
        if n.startswith(f"assets/{MOD}/blockstates/") and n.endswith(".json")
    }
    item_defs = {
        n[len(f"assets/{MOD}/items/"):-5]
        for n in z.namelist()
        if n.startswith(f"assets/{MOD}/items/") and n.endswith(".json")
    }
    # The carry already wrote 26.3 item definitions for the jar's item models.
    item_defs |= {
        n[:-5]
        for n in os.listdir(CARRY / f"assets/{MOD}/items")
        if n.endswith(".json")
    }
    hanging_textures = {
        n[len(f"assets/{MOD}/textures/gui/hanging_signs/"):-4]
        for n in z.namelist()
        if n.startswith(f"assets/{MOD}/textures/gui/hanging_signs/")
        and n.endswith(".png")
    }
    carried = {
        p.stem: json.loads(p.read_text())
        for p in (CARRY / f"data/{MOD}/horizon/block").glob("*.json")
    }

    out: dict[str, dict] = {}
    why: dict[str, str] = {}

    def model_parent(name: str) -> str | None:
        model = first_model(blockstates[name])
        if not model:
            return None
        ns, path = model.split(":", 1) if ":" in model else ("minecraft", model)
        if ns != MOD:
            return None
        file = CARRY / f"assets/{MOD}/models/{path}.json"
        if not file.exists():
            return None
        return json.loads(file.read_text()).get("parent")

    for name in sorted(blockstates):
        bs = blockstates[name]
        decl: dict | None = None
        reason = ""

        if name in SPECIAL:
            spec = SPECIAL[name]
            decl = {"template": spec["template"]}
            state = dict(spec.get("state", {}))
            if "cactus_shape" in state and not state["cactus_shape"]["values"]:
                state["cactus_shape"]["values"] = state_values(bs, "cactus_shape")
            if state:
                decl["state_properties"] = state
            if spec.get("default"):
                decl["default_state"] = spec["default"]
            if spec.get("random_ticks") is False:
                decl.setdefault("properties", {})["random_ticks"] = False
            reason = "left out by the carry (own state set)"
        else:
            for suffix in SIGN_SUFFIXES:
                if name.endswith(suffix):
                    wood = name[: -len(suffix)]
                    if suffix == "_wall_hanging_sign":
                        decl = {
                            "template": "minecraft:oak_wall_hanging_sign",
                            "item": False,
                        }
                    elif suffix == "_hanging_sign":
                        decl = {
                            "template": "minecraft:oak_hanging_sign",
                            "wall_block": f"{MOD}:{wood}_wall_hanging_sign",
                        }
                        if wood in hanging_textures:
                            decl["wood_type"] = f"{MOD}:{wood}"
                    elif suffix == "_wall_sign":
                        decl = {"template": "minecraft:oak_wall_sign", "item": False}
                    else:
                        decl = {
                            "template": "minecraft:oak_sign",
                            "wall_block": f"{MOD}:{wood}_wall_sign",
                        }
                    reason = "sign: template's rotation and block entity"
                    break

        if decl is None and (name.startswith("potted_") or model_parent(name) in (
            "block/flower_pot_cross",
            f"{MOD}:block/coneflower_pot",
        )):
            decl = {"template": "minecraft:potted_poppy", "item": False}
            reason = "potted plant"

        parent = model_parent(name)
        if decl is None and (parent == "block/leaves" or parent == "block/leaves_all"):
            decl = {"template": "minecraft:oak_leaves"}
            reason = "leaves: distance/persistent preserved"
        if decl is None and name in NAMED:
            decl = {"template": NAMED[name]}
            reason = "name -> vanilla block"
        if decl is None and name.endswith("_planks"):
            decl = {"template": "minecraft:oak_planks"}
            reason = "planks: wood, not stone"
        if decl is None and name.endswith(("_log", "_stem", "_hyphae")):
            decl = {"template": "minecraft:oak_log"}
            reason = "pillar: axis preserved"
        if decl is None and name.endswith("_wood"):
            decl = {"template": "minecraft:oak_wood"}
            reason = "pillar: axis preserved"
        if decl is None and name.endswith("_sapling"):
            decl = {
                "template": "minecraft:poppy",
                "state_properties": {"stage": {"type": "enum", "values": ["0", "1"]}},
                "default_state": {"stage": "0"},
            }
            reason = "sapling: stage declared, no wrong-species growth"
        if decl is None and parent in PLANT_TEMPLATES:
            decl = {"template": PLANT_TEMPLATES[parent]}
            reason = "plant: cross shape instead of a cube"

        if decl is None:
            # The carry's own guess stands unless a name rule above improves it.
            if name in carried:
                decl = dict(carried[name])
            else:
                print(f"unclassified block with no carry declaration: {name}",
                      file=sys.stderr)
                return 1

        # A block with no 26.3 item definition has no item (potted plants, wall
        # signs, technical blocks): the carry never wrote one for them.
        if name not in item_defs and "item" not in decl:
            decl["item"] = False

        before = carried.get(name)
        if before != decl:
            out[name] = decl
            why[name] = reason or "template corrected"
        carried.pop(name, None)

    if carried:
        print(f"carry has blocks the jar does not: {sorted(carried)}", file=sys.stderr)
        return 1

    if PATCHES.joinpath("block").exists():
        shutil.rmtree(PATCHES / "block")
    (PATCHES / "block").mkdir(parents=True, exist_ok=True)
    for name, decl in sorted(out.items()):
        (PATCHES / "block" / f"{name}.json").write_text(
            json.dumps(decl, indent=2) + "\n"
        )

    # The Java tab (`RUCreativeModeTabs.MAIN`) lists every item the mod has;
    # the icon is RUBlocks.PRISMARITE_CLUSTER.
    (PATCHES / "tab").mkdir(parents=True, exist_ok=True)
    (PATCHES / "tab" / "main.json").write_text(
        json.dumps(
            {
                "title": "itemGroup.regions_unexplored.main",
                "icon": f"{MOD}:prismarite_cluster",
                "items": [f"{MOD}:{n}" for n in sorted(item_defs)],
            },
            indent=2,
        )
        + "\n"
    )

    # NeoForge's convention tags the recipes name but the jar does not ship.
    # 26.3 has no `c:` tags, and an unknown tag makes a recipe load but never
    # match (carry-pipeline pitfall 6). Colours are the 16 vanilla dyes; `c:glass`
    # is the glass blocks a stained-glass recipe replaces.
    dyes = [
        "white", "orange", "magenta", "light_blue", "yellow", "lime", "pink",
        "gray", "light_gray", "cyan", "purple", "blue", "brown", "green", "red",
        "black",
    ]
    tags = PATCHES / "data" / "c" / "tags" / "item"
    tags.mkdir(parents=True, exist_ok=True)
    # The recipe names `#c:<colour>_dyes`, so the tag id is `c:<colour>_dyes`
    # and its file is fixed by that id, as Minecraft's tag loader maps it.
    for colour in dyes:
        (tags / f"{colour}_dyes.json").write_text(
            json.dumps({"values": [f"minecraft:{colour}_dye"]}, indent=2) + "\n"
        )
    glass = ["minecraft:glass", "minecraft:tinted_glass"] + [
        f"minecraft:{c}_stained_glass" for c in dyes
    ]
    (tags / "glass.json").write_text(
        json.dumps({"values": glass}, indent=2) + "\n"
    )

    # 26.3 renamed vanilla's `template_farmland` to
    # `template_cube_bottom_top_indented` and its `dirt` texture slot to
    # `bottom`/`side`. The jar's two farmland models still name the 1.21.1
    # parent, which does not exist at 26.3.
    models = PATCHES / "assets" / MOD / "models" / "block"
    models.mkdir(parents=True, exist_ok=True)
    for name, wood in (
        ("peat_farmland", "peat"),
        ("peat_farmland_moist", "peat"),
        ("silt_farmland", "silt"),
        ("silt_farmland_moist", "silt"),
    ):
        (models / f"{name}.json").write_text(
            json.dumps(
                {
                    "parent": "minecraft:block/template_cube_bottom_top_indented",
                    "textures": {
                        "bottom": f"{MOD}:block/{wood}_dirt",
                        "side": f"{MOD}:block/{wood}_dirt",
                        "top": f"{MOD}:block/{name}",
                    },
                },
                indent=2,
            )
            + "\n"
        )

    print(f"jar blockstates: {len(blockstates)}")
    print(f"carry declarations: {len(out)} patched, "
          f"{len(blockstates) - len(out)} kept from the carry")
    left_out = [n for n in blockstates if n in SPECIAL]
    print(f"declared from the left-out 39: {len(left_out)}")
    for name in left_out:
        print(f"  {name}: {out.get(name, {}).get('template')}")
    # every declaration must name a block the prepared tables have
    facts = json.loads(
        (Path("/home/adlf/Desktop/horizon/.local/horizon-client/26.3")
         / "facts.json").read_text()
    )["defaults"]
    missing = sorted(
        {d["template"] for d in out.values()} - set(facts)
    )
    if missing:
        print(f"templates the prepared tables lack: {missing}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
