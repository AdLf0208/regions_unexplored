# Regions Unexplored for Horizon

A content port of **Regions Unexplored 0.5.9** (`regions_unexplored`, MIT) to
Minecraft Java **26.3** on Horizon's SDK `0b14f8acfd97fa2c750e42795249dcc981178ca4`
(package format 6, `api = "0.2"`).

- Upstream: <https://github.com/Apollounknowndev/RegionsUnexplored>
  (branch `21.1`, commit `ea78a0f`), Modrinth `Tkikq67H`, MIT —
  see `LICENSE` and `LICENSE-NOTICE.md` in this package.
- This port's source: <https://github.com/AdLf0208/regions_unexplored>.

## What this package is

844 block declarations (the jar's 844 blockstates), 733 item definitions, 656
recipes, 790 loot tables, 5 lang files, the mod's tags and its creative tab, all
upgraded to 26.3's formats — plus the world data:

- **71 biomes**, registered, with their colours, sounds, particles and spawns in
  26.3's `attributes` map;
- **307 configured features** in `worldgen/feature/` and **343 placed
  features**, all registered.

## What actually works, measured in game

- **136 of the 307 configured features place their block.** They are the ones
  whose whole type graph exists in 26.3: `tree`, `simple_block` (which is what
  1.21.1's `random_patch` and `flower` became), `disk`, huge mushrooms, `ore`,
  `bamboo`, `vegetation_patch`, `block_blob` (1.21.1's `forest_rock`) and the
  selectors. One feature per family is asserted in game by the port's e2e
  (`tools/e2e.sh`), counting the placed blocks with `fill … replace`.
- **171 do not.** 154 of them are the mod's own Java feature types
  (`regions_unexplored:shrub`, `…_tree`, `rock`, `vent`, …) and 17 are 1.21.1
  types with no 26.3 decoder (`nether_forest_vegetation`, a non-vanilla
  multiface block, `randomized_int_state_provider`, two mod foliage placers and
  two mod tree decorators). They keep their carried bytes and are refused by
  the feature registry at placement time.
- **The biomes are registered but nothing places them.** TerraBlender's region
  placement is Java and unported, so `/locate biome
  regions_unexplored:willow_forest` answers "Could not find a biome of type …
  within a reasonable distance" — the id resolves, the biome just does not
  generate. The features therefore only appear through `/place feature`, not in
  generated terrain.

## What is not carried

Block and item behaviour (data tier): 105 blocks with code behaviour keep their
template's behaviour only, item components are not carried, and the 9 wolf
variants are quarantined (another namespace, no 26.3 equivalent). `notes.md` in
the port lists every gap.
