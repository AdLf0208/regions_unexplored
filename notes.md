# Regions Unexplored — port notes

Ported from **Regions Unexplored 0.5.9** (NeoForge 1.21.1, mod id
`regions_unexplored`) for Minecraft Java 26.3 on Horizon
**`1d63e0a5a37a7a708eb0b32b49bf0dfeb28ed8a9`** + horizon-mixins
`5a64af938ec86b00d53d16a408aabc0038fb3e57` (schema 6) for the carry, and on the
SDK pin **`0b14f8acfd97fa2c750e42795249dcc981178ca4`** for the delivered
package and its in-game leg. Content-only `.hmod`; no native module, no Rust, no
hooks.

**Class + tier:** `content` / `data` (source map `atm10-sources.csv:394`;
reviewed table `docs/modpacks/atm10-mods.csv:394`). The approach is the tier's
**carry-over** shape from `horizon/docs/modpacks.md`: the jar's `assets/` and
`data/` upgraded to 26.3, blocks declared from vanilla templates, behaviour the
carry cannot express recorded below. The mod is worldgen- and biome-heavy, so
the carry's worldgen limits are a large part of the verdict.

**Licence: MIT → rank 0 (permissive).** Modrinth (`Tkikq67H`) and the upstream
`LICENSE` both say MIT; the jar's `mods.toml` carries the template's unfilled
`license = "ARR"` line (recorded in `../_shared/carry-work/regions_unexplored/SOURCE.md`).
The port is **local-only until the maintainer approves publishing**
(ARCHITECTURE.md §8). Ported now because it is the next feasible rank-0
data-tier entry, dispatched explicitly by the orchestrator.

**Upstream project:** <https://github.com/Apollounknowndev/RegionsUnexplored>
(branch `21.1`, commit `ea78a0f`), Modrinth project `Tkikq67H`
(<https://modrinth.com/mod/regions-unexplored>). Both the repository and
Modrinth's `source_url` name that path; the port's own repository
(`https://github.com/AdLf0208/regions_unexplored`) is where **this port's**
source lives and is not upstream. The earlier notes named the same URL — the
package now states it too (`content/README.md`, `content/LICENSE-NOTICE.md`).

**The MIT notice ships inside the package (fixed 2026-11-20).** The jar ships
no `LICENSE`/`COPYING`/`NOTICE` of its own, and MIT requires the copyright and
permission notice to travel with every copy or substantial portion of the
software — this package carries the mod's artwork and data, so
`LICENSE` (the upstream MIT text, `Copyright (c) 2026 Apollo`),
`LICENSE-NOTICE.md` and `README.md` are added to the `.hmod` root by
`tools/notice.py` after the build (`cargo-horizon-mod` packs only the manifest,
`assets/` and `data/`), and the same three files sit in `content/` beside the
canonical copies.

## Provenance (no deviation)

The exact ATM10 jar: `regions_unexplored-neoforge-1.21.1-0.5.9.jar` —
5,365,182 bytes, SHA-1 `064c2da020731fadd07e095707320431df12288d` (**exact
match** to ATM10's `modrinthHash`), SHA-256
`6cad2d8438d6c2aa08dd8eb8c07d38fda1a685ad5a731c8a5814a0ebdaa2d31d`, 7,870
entries. Resolved from the pack's Crash Assistant export and downloaded from
Modrinth version `KrbwbPuJ`. Full evidence:
[`../_shared/carry-work/regions_unexplored/SOURCE.md`](../_shared/carry-work/regions_unexplored/SOURCE.md).

The jar's own census: 844 blockstates, 733 item models, 658 recipes, 790 loot
tables, 309 tag files, 723 worldgen files, 671 advancements, 2 damage types,
9 wolf variants (quarantined), 1,006 textures, 5 lang files, 345 classes,
2 mixin configs.

## Upstream analysis (analysis aid only)

Repo `https://github.com/Apollounknowndev/RegionsUnexplored`, branch `21.1`,
commit `ea78a0feb58434a2c7b8601f01037327cf2e3f54` (2025-10-22), MIT. Cloned
shallow to `/tmp/opencode/regions-unexplored-upstream` (deleted after the
notes). Files read for behaviour and registration, not translated:

- `registry/RUBlocks.java`, `registry/RUItems.java`,
  `registry/RUCreativeModeTabs.java`, `registry/RUCreativeModeTabsActual.java`;
- `block/plant/**` (grasses, saplings, shrubs, cactus), `block/other/{Icicle,DuskTrap}`,
  `block/state/properties/{HangingPrismariteShape,SaguaroCactusShape,TallHyacinthStockShape}`;
- `world/level/feature/tree/*` and `world/level/feature/*` (the mod's own
  `Feature` subclasses the check counts as 74 worldgen classes);
- `datagen`/generated worldgen JSON (the jar is the spec).

Behaviours extracted: one creative tab (`main`, title
`itemGroup.regions_unexplored.main`, icon `prismarite_cluster`), 22 wood sets
(planks, logs, leaves, saplings, signs, hanging signs, boats/chest boats),
six-sided multiface flowers, petal-style ground cover (`facing` +
`flower_amount`), pointed icicle/redstone (`thickness` + `vertical_direction`),
farmland/grass/podzol variants, custom cactus/shrub/strangle shapes, and the
biomes placed through **TerraBlender** (a required dependency; the jar ships no
`neoforge/biome_modifier` files).

## Carry verdict

Toolchain: `horizon-port-pack` (carried) and `cargo-horizon-mod` built from the
pin with `--locked --offline`, `CARGO_INCREMENTAL=0`, in build slot
`ru-1d63e0a`. Evidence:
[`../_shared/evidence/regions_unexplored/check-cli.txt`](../_shared/evidence/regions_unexplored/check-cli.txt),
[`carry-cli.txt`](../_shared/evidence/regions_unexplored/carry-cli.txt),
[`hmod-check.txt`](../_shared/evidence/regions_unexplored/hmod-check.txt).

`check <jar>` says **Partly. 805 blocks, 41 items port; not 39 blocks with no
vanilla block to copy (left out), 10 recipes for left-out blocks.** Its class
census names the code side: 105 blocks with behaviour, 3 with shapes of their
own, 1 item with behaviour, 2 entities (boats), 1 renderer, 74 worldgen
classes, 3 particles, 1 event, 11 mixins. That is the data tier's expected
shape: the behaviour is not carried.

`carry` reported:

| Item | Count / result |
|---|---|
| files copied | **7,323** |
| block declarations | **805** carried, **39 left out**, 0 differences |
| item definitions added | **733** (1.21.4 `items/` form) |
| recipes upgraded | **656** (0 kept); 646 registered, 10 unregistered for left-out blocks |
| loot tables upgraded | **790** (0 added) |
| advancements upgraded | **20** (671 carried) |
| worldgen | **723** files (71 biomes, 307 configured features, 343 placed features, 2 noise) |
| worldgen state rewrites | **433** block states (`{Name,Properties}` → `{id,properties}`) |
| outside | **14** files (9 wolf variants, 2 vanilla recipe overrides, 1 neoforge data map, 2 vanilla advancements) |

The raw carry has no NeoForge oracle, so it guesses each block's template from
the property names its **blockstate** lists. Regions Unexplored's blockstates
list only the default state for most wood sets, plants and signs, so the guess
fell back to `minecraft:stone` and lost `axis`, `snowy`, `stage`, `rotation`,
`facing`, `flower_amount`…; 39 blocks had a state no template has and were left
out. The port patches that (below): **844/844 blocks are declared**, with the
jar's own blockstate/models/textures/loot.

## Deliberate patches on top of the carry

`tools/gen_patches.py` reads the jar's blockstates and models and the **raw**
carry output (`../_shared/carry-work/regions_unexplored/work/mods/regions_unexplored/carry`)
and writes one complete declaration per changed block to
`content/patches/block/`. `content/patches/apply.sh` copies them over
`content/carry`, restores the 10 recipes, the creative tab, the convention
tags and two 26.3 model files. It is idempotent; 523 declarations are patched
and 321 kept from the carry.

What it fixes:

| Raw carry | Patch | Count |
|---|---|---|
| `stone` for every property-less block | `poppy` (cross plants/flowers), `short_grass` (tinted grass), `oak_planks`, `oak_leaves`, `oak_log`/`oak_wood` (axis), `oak_sapling`-shaped saplings with a declared `stage` | 405 stone templates reclassified |
| signs as `stone` (no rotation, no sign block entity) | `oak_sign` / `oak_wall_sign` / `oak_hanging_sign` / `oak_wall_hanging_sign` with `wall_block`, `item: false` on wall forms, `wood_type: regions_unexplored:<wood>` where the jar ships the editor texture | **88** (22 wood types x 4) |
| 39 blocks left out | declared from the jar's own states: snowy grass/podzol (`grass_block`/`podzol`), farmland, ashen dirt/grass (`smouldering`), bamboo/pine/silver-birch logs, multiface magnolia/hyacinth (`glow_lichen`), clover/coneflowers/leaf piles/`mycotoxic_mushrooms` (`pink_petals`), icicle/pointed redstone (`pointed_dripstone`), hanging prismarite and tall hyacinth stock (own shape enums), saguaro cactus (own shape enum), joshua leaves (`half`+`natural`), dusktrap, sandy grass/tall grass | **39** |
| 93 potted plants as `stone` | `minecraft:potted_poppy`, `item: false` | 93 |
| 10 recipes moved to `outside/` | restored (the result blocks are declared) | 10 |
| item-less blocks | `item: false` (152 blocks: potted, wall signs, technical) | 152 |
| `data/c/` tags absent at 26.3 | 16 `<colour>_dyes.json` + `glass.json` (the recipes name `#c:<colour>_dyes`, `#c:glass`) | 17 |
| `template_farmland` is not a 26.3 model | `peat/silt_farmland[_moist]` re-parented to `template_cube_bottom_top_indented` with 26.3's `bottom`/`side`/`top` slots | 4 models |
| creative tab was code | `data/regions_unexplored/horizon/creative_tab/main.json`, title `itemGroup.regions_unexplored.main`, icon `prismarite_cluster`, **733 items** | 1 |

## Worldgen verdict — corrected 2026-11-20: the features load and 136 of them place

**The earlier verdict ("26.3 cannot use the feature family") was wrong about the
cause, and the listing overstated what worked.** The port's own measurements at
`1d63e0a` and `0b14f8a` were right that **0** of the 307 configured features
reached the registry, but the reason was not the feature schema: **26.3 renamed
the registry folder.** 1.21.1 writes `data/<ns>/worldgen/configured_feature/`,
26.3 reads `data/<ns>/worldgen/feature/` (vanilla's own data, and
`horizon-client/src/mod_content.rs::worldgen_entry` reads
`data/<ns>/worldgen/feature/<name>.json` only). A carried `configured_feature/`
folder is never read at all — so no shape fix could have worked while the folder
name was wrong.

Both defects are fixed in the carry pipeline (`tools/upgrade_features.py`, run
by `content/patches/apply.sh` after a carry):

1. **The folder is moved** to `worldgen/feature/` (307 files), so the loader
   sees them.
2. **The configs are converted to 26.3's shapes**: the `config` wrapper is
   unwrapped; `simple_state_provider` becomes the bare state and
   `weighted_state_provider`/`noise_provider` become `minecraft:weighted`/
   `minecraft:noise`; the tree's `dirt_provider` becomes **`below_trunk_provider`**
   (`force_dirt` has no 26.3 field); `random_patch` and `flower` (82 features)
   become their inner configured feature plus `count(tries)` + a **trapezoid**
   offset + the patch's own placement on every reference — vanilla's own
   `patch_grass_normal.json` is exactly that shape; `forest_rock` becomes
   `block_blob` with vanilla's `forest_rock_can_place_on` tag; the huge
   mushrooms get the `can_place_on` predicate 26.3 requires; the disk's
   type-less rule-based provider is named; and `minecraft:patch_cactus` is
   renamed to 26.3's `minecraft:cactus` (26.3 kept `patch_cactus` as a *placed*
   feature, so the old id names no configured feature).

**Measured in game at `0b14f8a`:** 307/307 register, **136 place their block**
and **171 do not**. The 171 are the files whose whole type graph 26.3 does not
have: 154 use the mod's own Java feature types (`regions_unexplored:shrub`,
`…_tree`, `rock`, `vent`, …), 4 use `nether_forest_vegetation` (no 26.3
decoder; its 128-attempt spread is bonemeal-only and cannot be expressed), 2
trees carry mod decorators (`chance_willow_trunk_decorator`,
`willow_trunk_decorator`), 4 trees a mod foliage placer
(`sakura_foliage_placer`, `willow_foliage_placer`), 1 multiface feature is a
non-vanilla block (`regions_unexplored:hyacinth_flowers`; `vegetation.rs` only
decodes `glow_lichen`/`sculk_vein`), and the rest use
`randomized_int_state_provider`/`no_bonemeal_flower`, which 26.3 has no decoder
for. Those files keep their carried bytes, are refused by the feature registry
at placement time, and are the honest gap. The full per-file list is
[`../_shared/evidence/regions_unexplored/upgrade-features-report.log`](../_shared/evidence/regions_unexplored/upgrade-features-report.log),
the per-feature placement probe is
[`feature-placement-probe.log`](../_shared/evidence/regions_unexplored/feature-placement-probe.log).

**What still does not work: the biomes are not placed.** All 71 are registered
with their 26.3 `attributes` (colours, music, particles, `natural_mob_spawns`),
but TerraBlender's region placement is Java and unported, so
`/locate biome regions_unexplored:willow_forest` answers *"Could not find a
biome of type … within a reasonable distance"* and the 9
`regions_unexplored:has_wolf_variant/*` biome tags have no generated biome. The
features therefore appear through `/place feature`, not in generated terrain.
The 2 noise files are inert.

No structures, structure sets, template pools, processors, carvers, surface
rules or density functions exist in this jar, so none are missing from the
carry.

## Coverage — every family the jar ships, and what is proven

The parity rule's table. "Tested" names the `tools/e2e.sh` phase and the block
the run counts after `/place feature`; every count is asserted with
`fill … replace`, so a feature that does not place fails the run.

| jar family | count | status | evidence |
|---|---:|---|---|
| `tree` (25 converted) | 33 | **tested** — `alpha_oak_tree` places 5 `alpha_log` | e2e "converted features place" |
| `random_patch` (1.21.1) | 57 | **tested** — `patch_alpha_dandelion` places `alpha_dandelion` | e2e, same phase |
| `flower` (1.21.1) | 25 | **tested** — `corpse_flower` places `corpse_flower` | e2e, same phase |
| `simple_block` | 19 | **tested** — `aster` places `aster` | e2e, same phase |
| `disk` | 3 | **tested** — `disk_clay` places 29 `minecraft:clay` | e2e, same phase |
| huge mushrooms | 2 | **tested** — `giant_brown_mushroom` places 45 `brown_mushroom_block` | e2e, same phase |
| `ore` | 1 | **tested** — `ore_redstone_large` places 22 `redstone_ore` | e2e, same phase |
| `bamboo` | 1 | **tested** — `bamboo` places 14 `minecraft:bamboo` | e2e, same phase |
| `waterlogged_vegetation_patch` | 2 | **tested** — `mineral_pool` places 507 `calcite` | e2e, same phase |
| `forest_rock` (→ `block_blob`) | 1 | **tested** — `redwoods_rock` places 6 `mossy_cobblestone` | e2e, same phase |
| `random_selector` | 1 | **tested** — `prairie_tree_mix` places 29 `oak_log` | e2e, same phase |
| `multiface_growth` | 1 | **not ported** — the block is not a 26.3 `MultifaceSpreadeableBlock` | `feature-placement-probe.log` |
| `nether_forest_vegetation` | 4 | **not ported** — no 26.3 decoder | `feature-placement-probe.log` |
| the mod's own feature types | 154 | **not ported** — no Rust implementation in the pin | `feature-placement-probe.log` |
| mod decorators / foliage placers | 6 | **not ported** — inside the mod's own types | `feature-placement-probe.log` |
| biomes (registration) | 71 | **tested** — 71 registered with `attributes`; `/locate` resolves the id | e2e "content root" |
| biomes (generation) | 71 | **blocked(terrabender)** — TerraBlender's placement is Java | e2e `/locate` differential |


## Gaps and deviations

- **Worldgen** as above. At `0b14f8a` the 71 biomes **are registered** with
  their colours, sounds and spawns (the `attributes` map), but nothing places
  them: TerraBlender's region placement is Java and unported, so
  `/locate biome regions_unexplored:willow_forest` answers "Could not find a
  biome of type … within a reasonable distance" and the 9
  `regions_unexplored:has_wolf_variant/*` biome tags are in the bundle without a
  biome that generates. The 307 configured features register and **136 place
  their block**; the other 171 are the files whose types 26.3 does not decode
  (see the worldgen section and the coverage table), and the 2 noise files are
  inert.
- **Wolf variants** (9) are quarantined to `outside/data/minecraft/wolf_variant/`
  (another namespace; 1.21.1 registry, no 26.3 equivalent shipped).
- **Feature configs that 26.3 has no decoder for** stay as the 1.21.1 bytes:
  154 use the mod's own Java feature types, 4 `nether_forest_vegetation`, 6 a
  mod decorator/foliage placer, 1 a non-vanilla multiface block, and the rest a
  1.21.1-only provider/type (`randomized_int_state_provider`,
  `no_bonemeal_flower`). They register but are refused when placed; the list is
  in `upgrade-features-report.log`.
- **The 82 `random_patch`/`flower` features are re-expressed, not reproduced
  byte for byte.** 1.21.1 does the tries/spread inside the feature; 26.3 does it
  with placement modifiers, so the converted file is the inner feature and each
  reference gains `count(tries)` + a `trapezoid` offset. The offset is a
  trapezoid because `RandomPatchFeature` offsets with
  `nextInt(spread+1) - nextInt(spread+1)`, which is that distribution — the
  same shape vanilla's `patch_grass_normal.json` uses.
- **The neoforge compostables data map** and the jar's two vanilla recipe
  overrides (`minecraft:recipe/bamboo*`) are in `outside/` (other namespace;
  the content fence keeps them out).
- **Block behaviour is not carried** (data tier): 105 blocks with code
  behaviour — grass spreading/turning, sapling/tree growth, crop growth,
  smouldering, vines, cactus arms, ice/icicle formation, bonemeal — keep their
  template's behaviour only. Declared states bind, but e.g. a sapling does not
  grow (deliberately not `oak_sapling`, which would grow the wrong species).
- **Item components are not carried.** All 41 plain items are `stick`
  templates: `ruby`, meats/berries/fruit have no `food` component, the 22
  boat/chest-boat items cannot place or ride anything (the 2 boat entity types
  are among the 2 skipped entities), `seeded_grass`/`seeded_tall_grass` are
  plain items.
- **Block shapes** follow templates; `saguaro_cactus` (stone), `dusktrap`
  (tall grass) and hanging-prismarite arms use the template's collision/outline
  rather than upstream's custom shapes (3 blocks the check also lists).
- **Hardness/sounds/map colours** are the template's, not a NeoForge oracle's
  (no oracle at this pin). The family templates chosen (wood, leaves, plants,
  signs, farmland, grass) match the upstream material where the class was
  readable; 17 blocks remain `stone` (argillite/chalk/ash/cobalt-obsidian and
  the cube-shaped bioshroom/vent blocks) because the carry's guess is the
  closest sane template.
- **Upstream's own missing assets, carried faithfully, not invented:** the jar
  references 10 textures it does not ship (`regions_unexplored:item/{ruby,
  raw_meat,cooked_meat,brown_wall_mushroom,yellow_wall_bioshroom}`,
  `block/{seeded_grass,seeded_tall_grass_top,ashen_shrub_smouldering,bonsai_pot}`,
  `block/redwood_branch`) and the `blue_crystalite` model (only its blockstate
  exists). Those blocks/items show Horizon's missing model/texture. The jar's
  `en_us` also leaves 148 blocks and 13 items unnamed (wall signs, potted
  plants, five plain items); no names were invented.
- **`brown_wall_mushroom`, `pine_log_transition`, `saguaro_cactus_corner`,
  `yellow_wall_bioshroom`** are blocks with items but no lang key in the jar;
  they render under their raw key, exactly as the jars' data says.

## Verification

**Skills:** superpowers/using-superpowers,writing-plans,systematic-debugging,test-driven-development,verification-before-completion; BeautifulRust/rust-best-practices (read; no Rust written — the port is data)

Carried and packaged at pin `1d63e0a5a37a7a708eb0b32b49bf0dfeb28ed8a9`; the
in-game leg, the shape fix and the delivered package are at the SDK pin
`0b14f8acfd97fa2c750e42795249dcc981178ca4` (see *The 0b14f8a world-data shapes*
above). Tooling and the `.hmod` built through `ports/tools/build-slot.sh` with
`CARGO_INCREMENTAL=0`. Evidence:
[`../_shared/evidence/regions_unexplored/`](../_shared/evidence/regions_unexplored/).

| Check | Evidence |
|---|---|
| `horizon-port-pack check <jar>` | **Partly**: 805 blocks, 41 items, 646 recipes port; 39 blocks + 10 recipes left out; 105 behaviour blocks, 2 entities, 74 worldgen classes skipped (`check-cli.txt`, `check.json`) |
| `horizon-port-pack carry` | 7,323 files, 656 recipes, 790 loot, 733 item defs, **805 blocks (39 left out)**, 723 worldgen, 14 outside (`carry-cli.txt`, `carry-report.json`) |
| `tools/gen_patches.py` + `apply.sh` | **523 patched declarations**, 39 left-out blocks declared, 88 sign forms, 93 potted, 10 recipes restored, 17 `c:` tags, 4 farmland models, 1 tab, **71 biomes + 671 advancements + 307 features moved to `worldgen/feature/` and converted** (`gen-patches.log`) |
| `tools/verify_content.py` | **PASS**: 844 declarations = jar blockstates, 733 items, 656 recipes (results/ingredients/tags resolve), 790 loot, 5 lang files carried verbatim, every template checked against the prepared 26.3 tables, models/textures resolve except the jar's own 10 missing textures + 1 missing model, tags, 71 biomes + 307 + 343 + 2, 671 advancements, **every carried file in 26.3's shape**, 2 damage types, tab 733 (`verify-content.log`) |
| `tools/upgrade_shapes.py --check` | **OK 71 biomes + 671 advancements in 26.3 shape (jar cross-check green)**; red on the jar's bytes: 96 files, exit 1 (`upgrade-shapes-check.log`, `verify-shapes-red.log`) |
| `tools/upgrade_features.py --check` | **OK 307 configured features under `worldgen/feature/` (136 converted, 171 kept as carried), 343 placed features** (`upgrade-features-report.log`) |
| `python3 -m unittest test_upgrade_shapes` | **26 tests, OK** (`unit-tests.log`) |
| `python3 -m unittest test_upgrade_features` | **19 tests, OK** (`upgrade-features-unit-tests.log`); the same suite on a converter with the `below_trunk_provider` fix reverted: **2 failures + 1 error** (`upgrade-features-unit-tests-red.log`) |
| `cargo-horizon-mod build` ×2 + `tools/notice.py`, `cmp` | identical — **4,689,397 B**, SHA-256 `25a44d072cba73c1947aad4d181bcace57b6ec8e1587045582a9595c54f7ba5a`, **8,989 entries** (8,986 + LICENSE/LICENSE-NOTICE.md/README.md), no `Cargo.lock` (`hmod-build.txt`, `hmod-info.txt`) |
| `cargo-horizon-mod check` | `regions_unexplored 0.5.9 (mod, API 0.2, both)` … **no code: content only, nothing to run**, unsigned (`hmod-check.txt`) |
| `tools/e2e.sh` (default, `0b14f8a`) | **PASS + `EXIT:0`**; `e2e-default.log` / `../_shared/evidence/regions_unexplored-e2e/e2e-launcher.log` |
| `NEGATIVE=1 tools/e2e.sh` | **`FAIL:` + `EXIT:1`** at the deliberately false `ashen_dirt` smouldering assertion; `e2e-negative.log` |
| `tools/control_pre_fix.sh` | **`FAIL:` + `EXIT:1`**: the jar's 1.21.1 shapes reproduce `invalid world generation field: type`; `../_shared/evidence/regions_unexplored-e2e/e2e-control.log` |

The `0b14f8a` leg runs the **unmodified Nightly** at the pin
(`~/.cache/horizon-e2e/0b14f8a/control/`, `--dev-mod content/carry`): a
content-only port has no native module, so it skips the per-port game build. The
`1d63e0a` leg ran the shared unmodded game
(`ports/_shared/bin/horizon-1d63e0a5/`, `shared-bin.sh verify` green) and is kept
in `e2e-1d63e0a.log`.

Transcript at `1d63e0a` (abridged; the full log has every state read):

```
+ launch (shared …/horizon-1d63e0a5, offscreen, creative, The End, --dev-mod content/carry)
content mod loaded (no 'content mods not loaded')
content root: 307 configured + 343 placed features, 733 tab items, 0 mod biomes
844/844 block ids registered and their default state bound
88/88 sign states bind (rotation on standing/hanging, facing on wall forms)
27/27 leaf states bind (persistent=true; distance recomputed to 7 with no log near)
33/33 sapling stages bind (stage=1)
4 multiface + 9 petal covers bind (north/waterlogged, facing/flower_amount)
3 pointed + 10 snowy + 2 farmland states bind (farmland dries as vanilla farmland does)
14/14 single-state blocks bind (smouldering, leaves, transition_block, is_stripped, is_base,
  half/natural, closed, is_red, cactus_shape, shape enums, flower_amount)
10/10 representative items give
recipe PASS: willow planks via #regions_unexplored:willow_logs, #minecraft:planks + #c:yellow_dyes,
  #regions_unexplored:prismarite_crystals + #c:glass, and the restored magnolia recipe; controls empty
control: /place feature minecraft:oak placed 6 oak_log
regions_unexplored:alpha_oak_tree -> unexpected error; log: cannot be placed: invalid world
  generation field: trunk_provider  (gap confirmed)
regions_unexplored:willow_forest -> Can't find element … of type 'minecraft:worldgen/biome'
PASS: 844/844 block ids bind; 88 sign states, 27 leaves, 33 saplings, 4 multiface, 9 petal covers,
  3 pointed, 10 snowy, 2 farmland and 14 single-state blocks bind their patched states; 10 items
  give; 4 recipes craft while their controls stay empty; the content root holds 307 features +
  343 placed features and 733 tab items (that run predates the feature fix: it measured 0
  registered, the `configured_feature/` folder was not read); a RU biome id is not locatable;
  unknown ids are refused
```

`NEGATIVE=1` keeps the scenario and flips only the expected `ashen_dirt`
`smouldering` value:

```
FAIL: regions_unexplored:ashen_dirt[smouldering=true]: smouldering is 'true', expected 'false'
```

Transcript at `0b14f8a` (the delivered leg; abridged):

```
+ launch (Nightly 0b14f8a control game, offscreen, creative, The End, --dev-mod content/carry)
26.3 shapes: OK 71 biomes + 671 advancements in 26.3 shape (jar cross-check green)
content mod loaded (no 'content mods not loaded')
the level opened: 'live features ready', no worldgen/advancement/attribute warning
content root: 71 RU biomes (71 with natural_mob_spawns, 71 with a sky colour, 71 with background
  music), 307/307 configured features registered under worldgen/feature/, 343 placed features
  (342/343 naming a registered feature; `cactus_dense` names vanilla `minecraft:cactus`), 733 tab items
844/844 block ids bind; 88 sign states; 27 leaves; 33 saplings; 4 multiface + 9 petal covers;
  3 pointed + 10 snowy + 2 farmland; 14 single-state blocks
10 items give; 4 recipes craft (willow planks + tag, #c:yellow_dyes, #c:glass, the restored recipe)
control: /place feature minecraft:oak placed 4 oak_log
regions_unexplored:alpha_oak_tree -> Placed "regions_unexplored:alpha_oak_tree" at 100, 83, 100
  tree: regions_unexplored:alpha_log -> Successfully filled 5 block(s)
regions_unexplored:patch_alpha_dandelion -> Placed …   random_patch: alpha_dandelion -> 1 block
regions_unexplored:corpse_flower -> Placed …           flower: corpse_flower -> 1 block
regions_unexplored:aster -> Placed …                   simple_block: aster -> 1 block
regions_unexplored:disk_clay -> Placed …               disk: minecraft:clay -> 29 blocks
regions_unexplored:giant_brown_mushroom -> Placed …    huge_mushroom: brown_mushroom_block -> 45
regions_unexplored:ore_redstone_large -> Placed …      ore: minecraft:redstone_ore -> 22 blocks
regions_unexplored:bamboo -> Placed …                  bamboo: minecraft:bamboo -> 14 blocks
regions_unexplored:mineral_pool -> Placed …            waterlogged_vegetation_patch: calcite -> 507
regions_unexplored:redwoods_rock -> Placed …           block_blob: mossy_cobblestone -> 6 blocks
regions_unexplored:prairie_tree_mix -> Placed …        random_selector: minecraft:oak_log -> 29
regions_unexplored:ocean_rock (kept, Java feature type) -> Can't find element … in registry
minecraft:the_end -> The nearest minecraft:the_end is at [39, 80, 60] (0 blocks away)
regions_unexplored:willow_forest -> Could not find a biome of type … within a reasonable distance
regions_unexplored:not_a_biome -> Can't find element … of type 'minecraft:worldgen/biome'
PASS: … EXIT:0
```

Re-run:

```sh
# the delivered leg (SDK pin 0b14f8a): the Nightly's own unmodified game
CTL=$HOME/.cache/horizon-e2e/0b14f8a/control/horizon-ctl \
GAME=$HOME/.cache/horizon-e2e/0b14f8a/control/horizon-client \
RES=$HOME/.cache/horizon-e2e/root/data/horizon-launcher/versions/nightly-2026-11-18-0b14f8a/.local/horizon-client/26.3 \
ports/tools/build-slot.sh run --job ru-e2e --port ports/regions_unexplored --step e2e -- \
    bash ports/regions_unexplored/tools/e2e.sh                     # PASS + EXIT:0
NEGATIVE=1 … same command                                        # FAIL + EXIT:1
ports/tools/build-slot.sh run --job ru-control --port ports/regions_unexplored --step e2e -- \
    bash ports/regions_unexplored/tools/control_pre_fix.sh         # FAIL + EXIT:1
# the older shared-bin leg
eval "$(ports/tools/shared-bin.sh env)"
CTL=$CTL GAME=$GAME ports/regions_unexplored/tools/e2e.sh
```

## Loading the .hmod

At the SDK pin `0b14f8a` (the delivered package), with the Nightly's own
unmodified game:

```sh
CTL=$HOME/.cache/horizon-e2e/0b14f8a/control/horizon-ctl
GAME=$HOME/.cache/horizon-e2e/0b14f8a/control/horizon-client
RES=$HOME/.cache/horizon-e2e/root/data/horizon-launcher/versions/nightly-2026-11-18-0b14f8a/.local/horizon-client/26.3
$CTL --socket /tmp/opencode/regions-unexplored.sock launch \
    --game "$GAME" --world RegionsUnexplored --seed 20261107 --creative --offscreen --wait \
    --resources "$RES" --dev-mod ports/regions_unexplored/content/carry
```

At `1d63e0a` the shared unmodded game works the same way
(`eval "$(ports/tools/shared-bin.sh env)"` then `CTL=$CTL GAME=$GAME`).

The `.hmod` at `ports/regions_unexplored/regions_unexplored.hmod` is the same
content root (8,986 entries). `/mods` shows it; a world opened with it has all
844 blocks, 733 items, the creative tab and the 71 biomes with their colours and
spawns; the features remain the documented gap above.

## Gate at the SDK pin `0b14f8a` (2026-11-20) — green after the world-data fix

The first run at this pin was red (the level did not open); the defect, the fix
and the evidence are in *The 0b14f8a world-data shapes* below. Packaging and the
package checks were green throughout.

| Check | Result |
|---|---|
| `rm -f Cargo.lock`; `cargo test` / `clippy` / `fmt` | **n/a** — content-only port: no `Cargo.toml`, no `src/`; `python3 -m unittest test_upgrade_shapes` (**26 tests, OK**, `unit-tests.log`) and `test_upgrade_features` (**19 tests, OK**, `upgrade-features-unit-tests.log`) are the port's test suite |
| `cargo horizon-mod build` twice + `tools/notice.py`, `cmp` | **identical**, 4,689,397 B, SHA-256 `25a44d07…`; `unzip -l` has **no `Cargo.lock`** (8,989 entries) (`hmod-build.txt`) |
| `cargo horizon-mod check regions_unexplored.hmod` | `regions_unexplored 0.5.9 (mod, API 0.2, both)` … `no code: content only, nothing to run`, `CHECK_EXIT:0` (`sdk-check.log`) |
| `cargo horizon-mod fits regions_unexplored.hmod --build 0b14f8a` | *"is a content mod … `fits` doesn't apply."*, `FITS_EXIT:2` = the tool's not-applicable status (`sdk-fits.log`) |
| `python3 ports/tools/verify-sdk-package.py regions_unexplored` | **1/1** (package, content-only, check, fits, skills gate all `ok`) |
| `tools/upgrade_shapes.py --check` | **OK 71 biomes + 671 advancements in 26.3 shape (jar cross-check green)** (`upgrade-shapes-check.log`); red on the jar's 1.21.1 bytes, 96 files, exit 1 (`verify-shapes-red.log`) |
| `tools/verify_content.py` | **PASS**, including the 26.3 shape and feature checks (`verify-content.log`) |
| `tools/upgrade_features.py --check` | **OK 307 features under `worldgen/feature/` (136 converted, 171 kept)** (`upgrade-features-report.log`) |
| `tools/e2e.sh` at `0b14f8a` (control game, `--dev-mod content/carry`) | **PASS + `EXIT:0`** (`../_shared/evidence/regions_unexplored-e2e/e2e-launcher.log`, same bytes as `e2e-default.log`) |
| `NEGATIVE=1 tools/e2e.sh` | **`FAIL:` + `EXIT:1`** at the deliberately false `ashen_dirt` smouldering assertion (`e2e-negative.log`) |
| `tools/control_pre_fix.sh` (the jar's 1.21.1 shapes, same leg) | **`FAIL:` + `EXIT:1`**: 71 `biome attributes: attributes are not an object` warnings, then `invalid world generation field: type` and the game exits (`../_shared/evidence/regions_unexplored-e2e/e2e-control.log`) |
| `python3 ports/tools/check-e2e-logs.py regions_unexplored regions_unexplored-e2e --strict` | `logs=6 ok=6 missing-exit=0 bad-exit=0`, exit 0 |

The leg runs the **unmodified Nightly at `0b14f8a`**
(`~/.cache/horizon-e2e/0b14f8a/control/`) with that Nightly's prepared 26.3
resources; `launcher-game.sh build` refuses a content-only package (exit 5:
*"load it with `--dev-mod content` on a shared game"*,
`…-e2e/launcher-game-refusal.log`).

**Root cause (proved by the previous slice, fixed in this one).**
0b14f8a reads a mod's `worldgen/` and `advancement/` files and enforces the 26.3
shapes; 1d63e0a did not: the biome `carvers` step map (`carver/generation.rs:82`
→ `carver.rs:68` → *invalid world generation field: type*) and the 1.21.1
advancement predicate shape (*"No key type in predicate"*,
`registry_graph/fields.rs:95`). The conversion table, the tool, the tests and the
in-game evidence are in *The `0b14f8a` world-data shapes* below; the original
diagnosis is `../_shared/evidence/regions_unexplored/0b14f8a-defect.md`.

**Also measured at this pin** (the notes above are 1d63e0a facts): the 71 carried
biomes **are** parsed now, and their 26.3 colour/spawn data must move into the
`attributes` map (`minecraft:visual/*`, `minecraft:gameplay/natural_mob_spawns`)
or it is dropped. The feature family needed a second, separate fix — the folder
rename and the config shapes, in `tools/upgrade_features.py`; with it 307/307
features register and 136 place (see *Worldgen verdict* above).

## The `0b14f8a` world-data shapes — fixed 2026-11-20 (in-game leg green)

The port now converts the carried 1.21.1 world data in its **carry pipeline**,
not by hand: `tools/upgrade_shapes.py` (`--write` applies, `--check` re-derives
every file and compares it with the disk, plus a cross-check against the cached
jar), run as the last step of `content/patches/apply.sh` so a fresh
`horizon-port-pack carry` cannot undo it. `tools/verify_content.py` fails on an
unconverted file, and `tools/e2e.sh` runs `--check` before the game.

### The defect

```
[World initialization/WARN]: Horizon: live features unavailable: invalid world generation field: type
[Server thread/ERROR]: Horizon: integrated server: invalid world generation field: type
{"error":"game exited"}   EXIT:1
```

Two independent 1.21.1 shapes, both fatal at `0b14f8a`:

1. **Biome `carvers`** is the NeoForge step map (`{"air": […]}` in 66 biomes, a
   bare string in 4 nether biomes, `{}` in `redstone_abyss`) and 26.3 wants a
   flat list. `horizon-world`'s `worldgen/carver/generation.rs:82` `decode_set`
   treats a non-array as one inline carver, and `carver.rs:68` then reports the
   missing `type` (`worldgen.rs:103` renders it as
   `invalid world generation field: type`). Any single biome reproduced it.
2. **Advancement predicates** (`eternal_expedition`, `parent`, `pioneer`,
   `regions_explored`, `spelunker`) use `condition` (refused: *"No key type in
   predicate"*), un-namespaced predicate fields and the 1.21.1 one-element
   `conditions.player` list. 26.3 dispatches on `type`, namespaces the fields and
   takes an object (`registry_graph/fields.rs:95`; vanilla 26.3's own
   `adventure/adventuring_time.json` shows the shape).

### The conversions (each read from vanilla 26.3's prepared data, not guessed)

| 1.21.1 (carried) | 26.3 | Evidence |
|---|---|---|
| `carvers: {"air": [id…]}` / `{"air": id}` / `{}` | `carvers: [id…]` / `[id]` / `[]` | `plains.json` |
| `effects.sky_color`/`fog_color`/`water_fog_color` (int) | `attributes["minecraft:visual/sky_color"…]` as `#rrggbb` | `plains.json`, `swamp.json` |
| `effects.water_color`/`foliage_color`/`grass_color` (int) | kept in `effects`, as `#rrggbb` | `plains.json`, `swamp.json` |
| `effects.music` | `attributes["minecraft:audio/background_music"]["default"]` | `swamp.json` |
| `effects.mood_sound` / `ambient_sound` / `additions_sound` | `attributes["minecraft:audio/ambient_sounds"]` `mood` / `loop` / `additions` | `soul_sand_valley.json` |
| `effects.particle` (`{options, probability}`) | `attributes["minecraft:visual/ambient_particles"]` `{argument: [{particle, probability}], modifier: append}` | `soul_sand_valley.json` |
| `spawners` + `spawn_costs` | `attributes["minecraft:gameplay/natural_mob_spawns"]` `{argument: {spawn_costs, spawns_by_category}, modifier: overlay}`, `minCount`/`maxCount` → `count` (int, or `minecraft:uniform`), **empty categories kept** | `plains.json`, `soul_sand_valley.json`, `docs/datapack-upgrade.md:55` |
| `creature_spawn_probability` (≠ 0.1) | `attributes["minecraft:gameplay/creature_world_gen_spawn_probability"]` (left out at the 0.1 default) | `badlands.json`, `docs/datapack-upgrade.md:56` |
| criterion `conditions.player`/`entity` as a one-element list | the object | `adventuring_time.json` |
| predicate `condition` | `type` | `kill_a_mob.json`, `adventuring_time.json` |
| entity predicate `type`/`location`/`equipment` | `minecraft:entity_type`/`minecraft:location`/`minecraft:equipment` | same |
| `enter_block` criterion `conditions.block` | `conditions.blocks` (26.3 skips `block`, so the criterion matched *any* block entered) | `end/enter_end_gateway.json`; the pin's `horizon-port-pack/src/carry.rs:366` |

Every other key is preserved (ids, criterion names, parents, display,
requirements, `features`, climate). **No criterion, spawn category or colour was
dropped.** The tool refuses rather than guesses: an unverified predicate field,
a multi-entry `conditions` list, or `replace_current_music: true` is an error
with the file and reason.

### What the fix buys (measured in-game)

- The level opens (`Horizon: live features ready in …`, the probe measured
  244.7 ms), with no `invalid world generation field` and no `biome attributes`
  warning.
- **71/71 biomes are registered** and their attributes are read: 71 with
  `natural_mob_spawns` (`spawns_by_category`, `count`), 71 with a sky colour, 71
  with background music (the content-root check parses every one).
- `/locate biome regions_unexplored:willow_forest` →
  *"Could not find a biome of type … within a reasonable distance"* (registered;
  TerraBlender's placement is Java and unported), while
  `regions_unexplored:not_a_biome` → *"Can't find element … of type
  'minecraft:worldgen/biome'"* — the differential.
- The 307 configured features **register** under `worldgen/feature/` and **136
  place their block** (the per-family assertions in `tools/e2e.sh`); the other
  171 are the types 26.3 has no decoder for. `tools/upgrade_features.py` owns
  that fix and its `--check` runs in the e2e, so a re-carry cannot silently put
  the `configured_feature/` folder back.
- Controls: `NEGATIVE=1` flips the `ashen_dirt` assertion (`FAIL` + `EXIT:1`);
  `tools/control_pre_fix.sh` reverts the 742 files to the jar's bytes and the
  same leg reproduces the defect (`FAIL` + `EXIT:1`).

Deviations: `effects.music.replace_current_music` is dropped (26.3's
`background_music` has no such field; all 71 biomes set it `false`, which is
26.3's behaviour). The feature types 26.3 does not decode remain the recorded
gap (the coverage table above).
Worth an upstream report? No — the artefact is correct 1.21.1 data; 26.3 changed
the shapes and the folder name.

**A re-carry cannot undo it.** Simulated by writing the jar's 742 biome and
advancement files back into `content/carry` (the 1.21.1 bytes — what a carry
that skipped those upgrades leaves), then running
`content/patches/apply.sh`: `--check` is red on the re-carried tree (exit 1),
`apply.sh` converts, and all **8,987 content files** of `content/carry` are
**byte-identical** to the tree the package was built and the leg run from
(compared by sha256, including the 20 `enter_block` files). The conversion is
code, not a hand edit.

The same simulation for the **feature tree** (2026-11-20): the carried
`worldgen/configured_feature/` + `placed_feature/` folders were put back, the
tool's `--check` is red on them (exit 1: wrong folder, 1.21.1 configs), and
`--write` reproduces both delivered trees exactly — `diff -r` reports
`FEATURE_TREES_IDENTICAL` and `PLACED_TREES_IDENTICAL`
(`upgrade-features-recarry.log`).

The shape tests were written first (`tools/test_upgrade_shapes.py`, 26 cases)
and were red on the 1.21.1 content (the `PortContent` case and the `--check`
fixpoint) before the conversion was implemented; `verify-shapes-red.log` keeps
the red run against the jar's bytes (96 files, exit 1).

The feature conversion was driven by the game (the reviewer's finding, then a
load probe per candidate shape) and pinned by `tools/test_upgrade_features.py`
(19 cases) afterwards; the suite's fail-capability is proven the other way
round: on a copy of the converter with the `below_trunk_provider` mapping
reverted, **2 tests fail and 1 errors**
(`upgrade-features-unit-tests-red.log`). Its `--check` is also a fixpoint test —
`write_tree` twice changes 0 files (`test_a_second_run_changes_nothing`).

The package version stays **0.5.9**: it mirrors the upstream artefact
(`regions_unexplored-neoforge-1.21.1-0.5.9.jar`) and the port has no published
version record to supersede. The delivered bytes and SHA-256 changed and are
recorded above.

## Artifacts

- `ports/regions_unexplored/regions_unexplored.hmod` — **4,689,397 B**, SHA-256
  `25a44d072cba73c1947aad4d181bcace57b6ec8e1587045582a9595c54f7ba5a`, 8,989
  entries (8,986 content entries + `LICENSE`, `LICENSE-NOTICE.md`, `README.md`),
  `no code`. (The pre-fix package was 4,686,932 B, `f096d884…`; the package
  before the feature fix and the notice was 4,694,401 B, `1322d949…`.)
- `content/carry/` — the folder content mod (`horizon-mod.toml`, `assets/`,
  `data/`) that `--dev-mod` loads, beside `carry-report.json` and `outside/`
  (14 other-namespace files).
- `content/patches/` — `block/` (523 declarations), `tab/main.json`,
  `data/c/tags/item/` (17 tags), `assets/.../models/block/` (4 farmland models),
  `apply.sh` (runs `tools/upgrade_shapes.py` and `tools/upgrade_features.py`
  last, then copies the licence notice into `carry/`).
- `content/LICENSE`, `content/LICENSE-NOTICE.md`, `content/README.md` — the
  upstream MIT notice and the package's own docs; copied into `carry/` by
  `apply.sh` and injected into the built `.hmod` by `tools/notice.py`.
- `tools/` — `gen_patches.py` (regenerates the declarations from jar + raw
  carry), `upgrade_shapes.py` (the 26.3 world-data shapes, `--write`/`--check`),
  `upgrade_features.py` (the `worldgen/feature/` rename and the 26.3 feature
  shapes, `--write`/`--check`), `notice.py` (adds the licence notice to the
  built archive), `test_upgrade_features.py` (19 tests),
  `test_upgrade_shapes.py` (23 unit + fixpoint tests),
  `verify_content.py` (jar-vs-content, including the shapes),
  `craft_check.py` (the four recipes), `e2e.sh` (default, `NEGATIVE=1`,
  `CONTENT=`), `control_pre_fix.sh` (the counterfactual).
- `../_shared/carry-work/regions_unexplored/` — the jar, `SOURCE.md`,
  `work/` (inventory + carry), `check-out/`.
- `../_shared/evidence/regions_unexplored/` — `check-cli.txt`, `check.json`,
  `carry-cli.txt`, `carry-report.json`, `gen-patches.log`, `verify-content.log`,
  `upgrade-shapes-check.log`, `verify-shapes-red.log`, `unit-tests.log`,
  `hmod-build.txt`, `hmod-info.txt`, `hmod-check.txt`, `sdk-check.log`,
  `sdk-fits.log`, `e2e-default.log`, `e2e-negative.log`, `e2e-1d63e0a.log`,
  `feature-probe.log`, `feature-placement-probe.log`,
  `upgrade-features-report.log`, `upgrade-features-unit-tests.log`,
  `upgrade-features-unit-tests-red.log`, `0b14f8a-defect.md`,
  `0b14f8a-launch.log`, `0b14f8a-launch-gamelog.txt`;
  `../_shared/evidence/regions_unexplored-e2e/e2e-launcher.log` (PASS) and
  `e2e-control.log` (FAIL, the pre-fix shapes); the red pre-fix runs are kept in
  `…-e2e/before-fix/`.
