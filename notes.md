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

## Worldgen verdict (the family that 26.3 cannot use)

**Corrected 2026-11-20 at the SDK pin `0b14f8a`.** The three limits below are the
`1d63e0a` measurements. At `0b14f8a` the **71 biomes are read and registered**
(their colours, sounds and spawns now live in the 26.3 `attributes` map — see
*The 0b14f8a world-data shapes* below), and the 307 configured features are
**refused at load** instead of failing at `/place` (0 of them reach the
registry; the 343 placed features are kept and every one names a dropped
feature). Limits 2–3 therefore still hold, with a different observable.

The jar's worldgen is carried **as data**, but at the `1d63e0a` pin the game did
not process it. Three independent limits, each verified in-game or in the
content root:

1. **Biomes are not read from mods.** `mod_content` merges only biome
   *modifiers* into the prepared `worldgen/biomes.json`; the 71 carried
   `worldgen/biome/*.json` files are overlaid but never registered. The content
   root's `worldgen/biomes.json` contains **0** `regions_unexplored:` keys, and
   `/locate biome regions_unexplored:willow_forest` answers
   `Can't find element … of type 'minecraft:worldgen/biome'`. TerraBlender's
   region placement is Java and unported.
2. **The carried feature configs are 1.21.1 shapes 26.3 rejects.** 26.3's
   `minecraft:tree` requires `below_trunk_provider` and flat state providers
   (`{id, properties}`); the carry leaves `dirt_provider` and wrapped
   `simple_state_provider` objects. `minecraft:simple_block` rejects the
   wrapped `to_place` provider. The game logs
   `feature regions_unexplored:alpha_oak_tree cannot be placed: invalid world
   generation field: trunk_provider` (and `to_place` for `barrel_cactus`)
   while a vanilla `minecraft:oak` control places. See
   [`../_shared/evidence/regions_unexplored/feature-probe.log`](../_shared/evidence/regions_unexplored/feature-probe.log).
3. **Feature types.** 57 configured features use `minecraft:random_patch` and
   25 `minecraft:flower`, which are not feature types in 26.3; 154 of the 307
   use the mod's own Java types (`regions_unexplored:shrub`, `*_tree`,
   `rock`, `vent`, `ivy`, …), which have no Rust implementation. The remaining
   vanilla-typed ones (`tree`, `simple_block`, `disk`, `multiface_growth`,
   huge mushrooms, selectors, waterlogged patches) still hit limit 2.

Consequence: the features/placed features are present in the content root's
bundles (307 / 343 entries) but generate nothing and cannot be placed. The
port does **not** rewrite 307 configs by hand — that is a carry/engine feature,
not a content edit, and the 1.21.1→26.3 feature-schema migration is not
mechanical (`random_patch`/`flower` have no 26.3 equivalent). This is the
"whole worldgen family cannot be expressed" case the brief allows; the rest of
the mod is kept.

No structures, structure sets, template pools, processors, carvers, surface
rules or density functions exist in this jar, so none are missing from the
carry.

## Gaps and deviations

- **Worldgen** as above. At `0b14f8a` the 71 biomes **are registered** with
  their colours, sounds and spawns (the `attributes` map), but nothing places
  them: TerraBlender's region placement is Java and unported, so
  `/locate biome regions_unexplored:willow_forest` answers "Could not find a
  biome of type … within a reasonable distance" and the 9
  `regions_unexplored:has_wolf_variant/*` biome tags are in the bundle without a
  biome that generates. The 307 configured features are refused at load (0
  registered), the 343 placed features are kept and every one names a dropped
  feature, and the 2 noise files are inert.
- **Wolf variants** (9) are quarantined to `outside/data/minecraft/wolf_variant/`
  (another namespace; 1.21.1 registry, no 26.3 equivalent shipped).
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
| `tools/gen_patches.py` + `apply.sh` | **523 patched declarations**, 39 left-out blocks declared, 88 sign forms, 93 potted, 10 recipes restored, 17 `c:` tags, 4 farmland models, 1 tab, **71 biomes + 671 advancements converted to 26.3 shapes** (`gen-patches.log`) |
| `tools/verify_content.py` | **PASS**: 844 declarations = jar blockstates, 733 items, 656 recipes (results/ingredients/tags resolve), 790 loot, 5 lang files carried verbatim, every template checked against the prepared 26.3 tables, models/textures resolve except the jar's own 10 missing textures + 1 missing model, tags, 71 biomes + 307 + 343 + 2, 671 advancements, **every carried file in 26.3's shape**, 2 damage types, tab 733 (`verify-content.log`) |
| `tools/upgrade_shapes.py --check` | **OK 71 biomes + 671 advancements in 26.3 shape (jar cross-check green)**; red on the jar's bytes: 96 files, exit 1 (`upgrade-shapes-check.log`, `verify-shapes-red.log`) |
| `python3 -m unittest test_upgrade_shapes` | **26 tests, OK** (`unit-tests.log`) |
| `cargo-horizon-mod build` ×2, `cmp` | identical — **4,694,401 B**, SHA-256 `1322d94974581955b38030988e19d580b923489f7b24f6f4ffd5e710f96ac29b`, **8,986 entries**, no `Cargo.lock` (`hmod-build.txt`, `hmod-info.txt`) |
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
  343 placed features and 733 tab items but 0 mod biomes, and the game rejects the carried
  features' 1.21.1 configs while the vanilla oak control places; a RU biome id is not locatable;
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
  music), 0 of the 307 configured features registered, 343 placed features (343 naming a dropped
  feature), 733 tab items
844/844 block ids bind; 88 sign states; 27 leaves; 33 saplings; 4 multiface + 9 petal covers;
  3 pointed + 10 snowy + 2 farmland; 14 single-state blocks
10 items give; 4 recipes craft (willow planks + tag, #c:yellow_dyes, #c:glass, the restored recipe)
control: /place feature minecraft:oak placed 4 oak_log
regions_unexplored:alpha_oak_tree -> Can't find element … in registry 'minecraft:worldgen/feature'
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
| `rm -f Cargo.lock`; `cargo test` / `clippy` / `fmt` | **n/a** — content-only port: no `Cargo.toml`, no `src/`; `python3 -m unittest test_upgrade_shapes` is the port's test suite (**26 tests, OK**, `unit-tests.log`) |
| `cargo horizon-mod build` twice, `cmp` | **identical**, 4,694,401 B, SHA-256 `1322d949…`; `unzip -l` has **no `Cargo.lock`** (8,986 entries) (`hmod-build.txt`) |
| `cargo horizon-mod check regions_unexplored.hmod` | `regions_unexplored 0.5.9 (mod, API 0.2, both)` … `no code: content only, nothing to run`, `CHECK_EXIT:0` (`sdk-check.log`) |
| `cargo horizon-mod fits regions_unexplored.hmod --build 0b14f8a` | *"is a content mod … `fits` doesn't apply."*, `FITS_EXIT:2` = the tool's not-applicable status (`sdk-fits.log`) |
| `python3 ports/tools/verify-sdk-package.py regions_unexplored` | **1/1** (package, content-only, check, fits, skills gate all `ok`) |
| `tools/upgrade_shapes.py --check` | **OK 71 biomes + 671 advancements in 26.3 shape (jar cross-check green)** (`upgrade-shapes-check.log`); red on the jar's 1.21.1 bytes, 96 files, exit 1 (`verify-shapes-red.log`) |
| `tools/verify_content.py` | **PASS**, including the 26.3 shape check (`verify-content.log`) |
| `tools/e2e.sh` at `0b14f8a` (control game, `--dev-mod content/carry`) | **PASS + `EXIT:0`** (`../_shared/evidence/regions_unexplored-e2e/e2e-launcher.log`, same bytes as `e2e-default.log`) |
| `NEGATIVE=1 tools/e2e.sh` | **`FAIL:` + `EXIT:1`** at the deliberately false `ashen_dirt` smouldering assertion (`e2e-negative.log`) |
| `tools/control_pre_fix.sh` (the jar's 1.21.1 shapes, same leg) | **`FAIL:` + `EXIT:1`**: 71 `biome attributes: attributes are not an object` warnings, then `invalid world generation field: type` and the game exits (`../_shared/evidence/regions_unexplored-e2e/e2e-control.log`) |
| `python3 ports/tools/check-e2e-logs.py regions_unexplored regions_unexplored-e2e --strict` | `logs=5 ok=5 missing-exit=0 bad-exit=0`, exit 0 |

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
biomes **are** parsed now, their 26.3 colour/spawn data must move into the
`attributes` map (`minecraft:visual/*`, `minecraft:gameplay/natural_mob_spawns`)
or it is dropped, and the feature-config rejection moved from `/place` to load:
0 of the 307 configured features reach the registry, while the 343 placed
features are kept and name dropped features.

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
- The 307 configured features are **refused at load** (0 registered; the old
  `place`-time `trunk_provider` rejection is gone) and the 343 placed features
  are kept, all naming a dropped feature. Recorded as the gap it is.
- Controls: `NEGATIVE=1` flips the `ashen_dirt` assertion (`FAIL` + `EXIT:1`);
  `tools/control_pre_fix.sh` reverts the 742 files to the jar's bytes and the
  same leg reproduces the defect (`FAIL` + `EXIT:1`).

Deviations: `effects.music.replace_current_music` is dropped (26.3's
`background_music` has no such field; all 71 biomes set it `false`, which is
26.3's behaviour). Feature configs and feature types remain the recorded gap.
Worth an upstream report? No — the artefact is correct 1.21.1 data; 26.3 changed
the shapes.

**A re-carry cannot undo it.** Simulated by writing the jar's 742 biome and
advancement files back into `content/carry` (the 1.21.1 bytes — what a carry
that skipped those upgrades leaves), then running
`content/patches/apply.sh`: `--check` is red on the re-carried tree (exit 1),
`apply.sh` converts, and all **8,987 files** of `content/carry` are
**byte-identical** to the tree the package was built and the leg run from
(compared by sha256, including the 20 `enter_block` files). The conversion is
code, not a hand edit.

The tests were written first (`tools/test_upgrade_shapes.py`, 26 cases) and were
red on the 1.21.1 content (the `PortContent` case and the `--check` fixpoint)
before the conversion was implemented; `verify-shapes-red.log` keeps the red
run against the jar's bytes (96 files, exit 1).

The package version stays **0.5.9**: it mirrors the upstream artefact
(`regions_unexplored-neoforge-1.21.1-0.5.9.jar`) and the port has no published
version record to supersede. The delivered bytes and SHA-256 changed and are
recorded above.

## Artifacts

- `ports/regions_unexplored/regions_unexplored.hmod` — **4,694,401 B**, SHA-256
  `1322d94974581955b38030988e19d580b923489f7b24f6f4ffd5e710f96ac29b`, 8,986
  entries, `no code`. (The pre-fix package was 4,686,932 B, `f096d884…`.)
- `content/carry/` — the folder content mod (`horizon-mod.toml`, `assets/`,
  `data/`) that `--dev-mod` loads, beside `carry-report.json` and `outside/`
  (14 other-namespace files).
- `content/patches/` — `block/` (523 declarations), `tab/main.json`,
  `data/c/tags/item/` (17 tags), `assets/.../models/block/` (4 farmland models),
  `apply.sh` (runs `tools/upgrade_shapes.py --write` + `--check` last).
- `tools/` — `gen_patches.py` (regenerates the declarations from jar + raw
  carry), `upgrade_shapes.py` (the 26.3 world-data shapes, `--write`/`--check`),
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
  `feature-probe.log`, `0b14f8a-defect.md`, `0b14f8a-launch.log`,
  `0b14f8a-launch-gamelog.txt`;
  `../_shared/evidence/regions_unexplored-e2e/e2e-launcher.log` (PASS) and
  `e2e-control.log` (FAIL, the pre-fix shapes); the red pre-fix runs are kept in
  `…-e2e/before-fix/`.
