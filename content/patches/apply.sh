#!/usr/bin/env bash
# Re-apply the hand patches after a fresh `horizon-port-pack carry` (it deletes
# and rewrites carry/). Run from ports/regions_unexplored/content.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. The 26.3 block declarations. The raw carry (no NeoForge oracle) guesses a
#    template from the state names a blockstate lists. Regions Unexplored's
#    blockstates list only the default state for the wood sets, plants and
#    signs, so the guess fell back to stone and lost `axis`, `snowy`, `stage`,
#    `rotation`, `flower_amount`...; 39 blocks had no vanilla template at all
#    and were left out. tools/gen_patches.py writes one complete declaration
#    per changed block from the jar's blockstates/models and the vanilla block
#    each upstream class copies.
python3 ../tools/gen_patches.py
cp patches/block/*.json carry/data/regions_unexplored/horizon/block/

# 2. The Java creative tab (`RUCreativeModeTabs.MAIN`) is code; mirror it as
#    26.3 data, icon PRISMARITE_CLUSTER, every item the mod has.
mkdir -p carry/data/regions_unexplored/horizon/creative_tab
cp patches/tab/main.json carry/data/regions_unexplored/horizon/creative_tab/main.json

# 2b. The NeoForge convention tags the recipes name (16 dye colours, c:glass);
#     26.3 ships no c: tags and an unknown tag never matches.
mkdir -p carry/data/c/tags/item
cp -a patches/data/c/tags/item/. carry/data/c/tags/item/

# 2c. The 26.3 farmland model: the jar's parent `template_farmland` was renamed.
mkdir -p carry/assets/regions_unexplored/models/block
cp -a patches/assets/regions_unexplored/models/block/. carry/assets/regions_unexplored/models/block/

# 3. The carry moves a recipe to `outside/` when its result is a block it left
#    out. Those 39 blocks are declared by patch 1, so their 10 recipes come
#    back (already upgraded to 26.3 by the carry).
restored=0
for f in carry/../outside/data/regions_unexplored/recipe/*.json; do
    [ -e "$f" ] || continue
    cp "$f" carry/data/regions_unexplored/recipe/
    restored=$((restored + 1))
done
[ "$restored" -eq 10 ] || {
    echo "expected 10 restored recipes, restored $restored" >&2
    exit 1
}

# 4. The 26.3 world data shapes. A fresh carry copies the jar's
#    `worldgen/biome/*.json` verbatim (1.21.1 `carvers` step map, `effects`,
#    `spawners`) and the advancements with the 1.21.1 predicate shape
#    (`condition`, un-namespaced fields, a one-element `conditions.player`
#    list). At the SDK pin 0b14f8a the integrated server refuses the world on
#    both ("invalid world generation field: type", "No key type in predicate"),
#    and a biome's 1.21.1 colours/spawns would be dropped silently.
#    tools/upgrade_shapes.py applies the conversion and proves every file.
python3 ../tools/upgrade_shapes.py --write
python3 ../tools/upgrade_shapes.py --check

# 4b. The 26.3 feature shapes, and the folder 26.3 reads them from. 1.21.1
#     names the registry folder `configured_feature`; 26.3 renamed it to
#     `feature`, and the content loader only reads `worldgen/feature/`
#     (`horizon-client/src/mod_content.rs::worldgen_entry`), so a carried
#     folder is never read at all. tools/upgrade_features.py moves the 307
#     files and converts the ones whose types 26.3 has a decoder for (the
#     tree's `dirt_provider` -> `below_trunk_provider`, the state providers,
#     `random_patch`/`flower` -> their inner feature + placement, ...); the
#     rest keep their carried bytes and are the recorded gap.
python3 ../tools/upgrade_features.py --write
python3 ../tools/upgrade_features.py --check

# 5. The upstream MIT notice travels inside the archive: the content loader
#    ignores a root LICENSE*, and MIT requires the copyright and permission
#    notice with every copy of the artwork and data this package carries.
cp LICENSE LICENSE-NOTICE.md README.md carry/
echo "patches applied: $(ls patches/block | wc -l) block declarations, 1 creative tab, 10 restored recipes," \
     "$(ls carry/data/regions_unexplored/worldgen/biome | wc -l) biomes + 671 advancements +" \
     "$(ls carry/data/regions_unexplored/worldgen/feature | wc -l) features in 26.3 shapes"
