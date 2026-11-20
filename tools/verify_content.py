#!/usr/bin/env python3
"""Jar-vs-content fidelity check for ports/regions_unexplored.

Reads the exact ATM10 jar and the patched content root and asserts every count
and every reference the port claims: block declarations vs blockstates, models,
textures, item definitions, recipes and their tags/ingredients, loot tables,
lang keys, tags, worldgen files and the creative tab.

    python3 tools/verify_content.py
"""

from __future__ import annotations

import json
import os
import sys
import zipfile
from collections import Counter
from pathlib import Path

import upgrade_shapes

PORT = Path(__file__).resolve().parent.parent
CONTENT = Path(os.environ.get("RU_CONTENT", PORT / "content" / "carry"))
JAR = Path(
    os.environ.get(
        "RU_JAR",
        PORT.parent / "_shared" / "carry-work" / "regions_unexplored"
        / "regions_unexplored-neoforge-1.21.1-0.5.9.jar",
    )
)
PREPARED = Path(
    os.environ.get("HORIZON_RES", "/home/adlf/Desktop/horizon/.local/horizon-client/26.3")
)
MOD = "regions_unexplored"
errors: list[str] = []


def ok(msg: str) -> None:
    print(f"ok: {msg}")


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"FAIL: {msg}")


def check(cond: bool, msg: str) -> None:
    ok(msg) if cond else fail(msg)


def read(path: Path):
    return json.loads(path.read_text())


def main() -> int:
    z = zipfile.ZipFile(JAR)
    jar_blockstates = {
        n[len(f"assets/{MOD}/blockstates/"):-5]
        for n in z.namelist()
        if n.startswith(f"assets/{MOD}/blockstates/") and n.endswith(".json")
    }
    declares = {
        p.stem for p in (CONTENT / f"data/{MOD}/horizon/block").glob("*.json")
    }
    check(jar_blockstates == declares,
          f"blocks: {len(declares)} declarations, exactly the jar's {len(jar_blockstates)} blockstates")
    if jar_blockstates != declares:
        print("  missing:", sorted(jar_blockstates - declares)[:10])
        print("  extra:", sorted(declares - jar_blockstates)[:10])

    facts = read(PREPARED / "facts.json")["defaults"]
    decls = {
        n: read(CONTENT / f"data/{MOD}/horizon/block/{n}.json") for n in declares
    }
    bad_tpl = [n for n, d in decls.items() if d.get("template") not in facts]
    check(not bad_tpl, f"templates: every declaration names a prepared 26.3 block ({bad_tpl[:5]})")

    # item definitions and block items
    items = {
        p.stem for p in (CONTENT / f"assets/{MOD}/items").glob("*.json")
    }
    item_defs = {n: read(CONTENT / f"assets/{MOD}/items/{n}.json") for n in items}
    check(len(items) == 733, f"items: {len(items)} 26.3 item definitions (jar item models)")
    no_item = [n for n, d in decls.items() if d.get("item") is False]
    block_items = declares - {n for n in no_item}
    check(block_items | items == items and block_items <= items,
          f"items: {len(block_items)} block items, all defined; {len(no_item)} item-less blocks")

    # models and textures
    def model_path(ref: str) -> Path:
        ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)
        local = CONTENT / f"assets/{ns}/models/{path}.json"
        return local if local.exists() else PREPARED / f"assets/{ns}/models/{path}.json"

    def texture_exists(ref: str) -> bool:
        # An unqualified texture is minecraft's, as a ResourceLocation is.
        ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)
        return (CONTENT / f"assets/{ns}/textures/{path}.png").exists() or (
            PREPARED / f"assets/{ns}/textures/{path}.png"
        ).exists()

    missing_models: list[str] = []
    missing_textures: list[str] = []
    seen: set[str] = set()

    def walk_model(ref: str) -> None:
        if ref in seen:
            return
        seen.add(ref)
        path = model_path(ref)
        if not path.exists():
            missing_models.append(ref)
            return
        doc = read(path)
        parent = doc.get("parent")
        if parent and not parent.startswith("builtin/"):
            walk_model(parent if ":" in parent else f"minecraft:{parent}")
        for tex in doc.get("textures", {}).values():
            if isinstance(tex, str) and not tex.startswith("#"):
                if not texture_exists(tex):
                    missing_textures.append(tex)

    for n in declares:
        bs = read(CONTENT / f"assets/{MOD}/blockstates/{n}.json")
        refs: list[str] = []
        for v in bs.get("variants", {}).values():
            for x in v if isinstance(v, list) else [v]:
                refs.append(x["model"])
        for part in bs.get("multipart", []):
            refs.append(part["apply"]["model"])
        for ref in refs:
            walk_model(ref)
    for n, doc in item_defs.items():
        ref = doc.get("model", {}).get("model")
        if ref:
            walk_model(ref)
    # The jar itself omits two assets its own files name: the `blue_crystalite`
    # model (only its blockstate exists) and ten textures. The port carries the
    # jar faithfully and invents nothing, so these are the expected gaps.
    UPSTREAM_MISSING_MODELS = {f"{MOD}:block/blue_crystalite"}
    # The jar also names two more (`block/ashen_shrub_smouldering`,
    # `block/bonsai_pot`) in models no blockstate or item reaches.
    UPSTREAM_MISSING_TEXTURES = {
        "block/redwood_branch",
        f"{MOD}:block/seeded_grass",
        f"{MOD}:block/seeded_tall_grass_top",
        f"{MOD}:item/brown_wall_mushroom",
        f"{MOD}:item/cooked_meat",
        f"{MOD}:item/raw_meat",
        f"{MOD}:item/ruby",
        f"{MOD}:item/yellow_wall_bioshroom",
    }
    check(set(missing_models) == UPSTREAM_MISSING_MODELS,
          f"models: every model resolves except the jar's own missing "
          f"{sorted(UPSTREAM_MISSING_MODELS)} ({sorted(set(missing_models) - UPSTREAM_MISSING_MODELS)})")
    check(set(missing_textures) == UPSTREAM_MISSING_TEXTURES,
          f"textures: every texture resolves except the jar's own 10 missing ones "
          f"({sorted(set(missing_textures) - UPSTREAM_MISSING_TEXTURES)})")
    print(f"  gap: the jar references {len(UPSTREAM_MISSING_TEXTURES)} textures it does not ship "
          f"(and 2 more in unreachable models), and {len(UPSTREAM_MISSING_MODELS)} block model it "
          f"does not ship")

    # recipes
    recipes = {
        p.name: read(p) for p in (CONTENT / f"data/{MOD}/recipe").glob("*.json")
    }
    check(len(recipes) == 656, f"recipes: {len(recipes)} carried (656 = jar's 658 minus 2 vanilla overrides)")
    tag_dirs = [CONTENT / "data", PREPARED / "data"]

    def tag_file(tag: str) -> bool:
        ns, path = tag.split(":", 1) if ":" in tag else ("minecraft", tag)
        return any((d / ns / "tags" / "item" / f"{path}.json").exists() for d in tag_dirs)

    unregistered = []
    unknown_tags = []
    unknown_ingredients = []

    def ingredient(v, where):
        if isinstance(v, str):
            if v.startswith("#"):
                if not tag_file(v[1:]):
                    unknown_tags.append(f"{where}: {v}")
            elif v.split(":", 1)[0] == MOD:
                if v.split(":", 1)[1] not in items:
                    unknown_ingredients.append(f"{where}: {v}")
        elif isinstance(v, list):
            for x in v:
                ingredient(x, where)

    for name, r in recipes.items():
        res = r.get("result") or {}
        rid = res.get("id")
        if rid and rid.split(":", 1)[0] == MOD and rid.split(":", 1)[1] not in items:
            unregistered.append(f"{name}: {rid}")
        ingredient(r.get("ingredients"), name)
        for k, v in (r.get("key") or {}).items():
            ingredient(v, f"{name}:{k}")
    check(not unregistered, f"recipes: every result is a declared item ({unregistered[:5]})")
    check(not unknown_tags, f"recipes: every tag resolves (16 c:dyes + c:glass written) ({unknown_tags[:5]})")
    check(not unknown_ingredients, f"recipes: every mod ingredient is a declared item ({unknown_ingredients[:5]})")

    # loot tables
    loot = list((CONTENT / f"data/{MOD}/loot_table/blocks").glob("*.json"))
    check(len(loot) == 790, f"loot: {len(loot)} block loot tables (jar 790)")

    # lang
    lang = sorted((CONTENT / f"assets/{MOD}/lang").glob("*.json"))
    en = read(CONTENT / f"assets/{MOD}/lang/en_us.json")
    jar_en = json.loads(z.read(f"assets/{MOD}/lang/en_us.json"))
    check(len(lang) == 5, f"lang: {len(lang)} files ({', '.join(p.stem for p in lang)})")
    check(en == jar_en, f"lang: en_us carried verbatim ({len(en)} keys)")
    missing_names = [n for n in declares if f"block.{MOD}.{n}" not in en]
    missing_item_names = [
        n for n in items
        if f"item.{MOD}.{n}" not in en and f"block.{MOD}.{n}" not in en
    ]
    print(f"  gap: the jar's own en_us leaves {len(missing_names)} blocks and "
          f"{len(missing_item_names)} items unnamed (no key to carry; none invented): "
          f"{missing_item_names}")

    # tags: every regions_unexplored entry of a block/item tag is declared
    bad_entries = []
    for kind, known in (("block", declares), ("item", items)):
        for p in (CONTENT / f"data/{MOD}/tags/{kind}").rglob("*.json"):
            for v in read(p).get("values", []):
                v = v.get("id") if isinstance(v, dict) else v
                if not isinstance(v, str) or v.startswith("#"):
                    continue
                if v.split(":", 1)[0] == MOD and v.split(":", 1)[1] not in known:
                    bad_entries.append(f"{p.relative_to(CONTENT)}: {v}")
    check(not bad_entries, f"tags: every {MOD} block/item entry in the mod's tags is declared ({bad_entries[:5]})")

    # worldgen: file counts and feature types
    wg = CONTENT / f"data/{MOD}/worldgen"
    counts = {k: len(list((wg / k).glob("*.json"))) for k in (
        "biome", "configured_feature", "placed_feature", "noise",
    )}
    check(counts == {
        "biome": 71, "configured_feature": 307, "placed_feature": 343, "noise": 2,
    }, f"worldgen: {counts['biome']} biomes, {counts['configured_feature']} configured features, "
       f"{counts['placed_feature']} placed features, {counts['noise']} noise files")
    types = Counter(
        read(p).get("type") for p in (wg / "configured_feature").glob("*.json")
    )
    mod_types = sum(v for k, v in types.items() if k and k.startswith(f"{MOD}:"))
    check(len(types) == 82 and mod_types == 154,
          f"worldgen: {len(types)} configured-feature types, {mod_types} of them the mod's "
          f"Java types (carried as JSON; the game has no such feature type)")
    check(len(list((CONTENT / f"data/{MOD}/advancement").rglob("*.json"))) == 671,
          "advancements: 671 carried")
    # The shapes 0b14f8a enforces. A 1.21.1 biome `carvers` map or an
    # advancement `condition` predicate stops the level from opening, and a
    # 1.21.1 `effects`/`spawners` is silently dropped. tools/upgrade_shapes.py
    # owns the conversion, so a re-carry that writes the old bytes back fails
    # here, before the game refuses the world.
    shapes = upgrade_shapes.check_tree(CONTENT, biomes=71, advancements=671)
    if shapes:
        fail(f"26.3 shapes: {len(shapes)} carried file(s) not converted: {shapes[0]}")
    else:
        ok("26.3 shapes: 71 biomes (carvers list, attributes map) and 671 advancements "
           "(type-dispatched predicates)")
    check(len(list((CONTENT / f"data/{MOD}/damage_type").glob("*.json"))) == 2,
          "damage types: 2 carried")

    # creative tab
    tab = read(CONTENT / f"data/{MOD}/horizon/creative_tab/main.json")
    check(tab["title"] == "itemGroup.regions_unexplored.main"
          and tab["icon"] == f"{MOD}:prismarite_cluster"
          and len(tab["items"]) == len(items)
          and all(i.split(":", 1)[1] in items for i in tab["items"]),
          f"creative tab: {len(tab['items'])} items, title and prismarite icon")

    if errors:
        print(f"\nFAIL: {len(errors)} check(s) failed")
        return 1
    print("\nPASS: 844 blocks (all jar blockstates), 733 items, 656 recipes, 790 loot tables, "
          "5 lang files, tags resolve, models/textures resolve, 71 biomes + 307 configured "
          "+ 343 placed features + 2 noise files carried in 26.3's shapes (carvers list, "
          "attributes map, type-dispatched predicates), 671 advancements, 2 damage types, "
          "creative tab complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
