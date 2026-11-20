# Licence notice — `regions_unexplored` (Regions Unexplored)

This package carries content from **Regions Unexplored 0.5.9**
(`regions_unexplored-neoforge-1.21.1-0.5.9.jar`, mod id `regions_unexplored`),
authored by **Apollo** (Apollounknowndev).

## Upstream project

- Repository: <https://github.com/Apollounknowndev/RegionsUnexplored>
  (branch `21.1`, commit `ea78a0feb58434a2c7b8601f01037327cf2e3f54`, 2025-10-22)
- Modrinth project: <https://modrinth.com/mod/regions-unexplored> (`Tkikq67H`)

The repository and the Modrinth project's `source_url` both name
`Apollounknowndev/RegionsUnexplored`; the port's own repository
(`https://github.com/AdLf0208/regions_unexplored`) is where this port's source
lives and is **not** the upstream project.

## What the artefact declares — read from the files, not from a project page

| Evidence | Value |
|---|---|
| `META-INF/neoforge.mods.toml` → `license` | `ARR` — the NeoForge template line, never filled in |
| Upstream `LICENSE` (branch `21.1`) | the **MIT** text, `Copyright (c) 2026 Apollo` |
| Modrinth project `Tkikq67H` licence field | `MIT` |
| Jar contents | **no** `LICENSE`/`COPYING`/`NOTICE` file of its own |

So the code and assets are **MIT → licence rank 0 (permissive)**. The jar's
unfilled `ARR` line is a template artefact, not a grant that contradicts the
repository: the repository's `LICENSE` and Modrinth both say MIT, and the jar
ships no licence text of its own that could override them (ARCHITECTURE.md §8
reads a *specific file shipped in the jar* as the strongest evidence — there is
none here).

## What travels with this package

- `LICENSE` — the upstream MIT text, byte-identical to
  `https://github.com/Apollounknowndev/RegionsUnexplored/blob/21.1/LICENSE`
  (`Copyright (c) 2026 Apollo`). MIT requires the copyright and permission
  notice to travel with every copy or substantial portion of the software, and
  this package carries the mod's artwork and data, so the notice is inside the
  archive — the content loader ignores a root `LICENSE*` file.
- `LICENSE-NOTICE.md` — this file.
- `notes.md` (in the port, not in the archive) — provenance, the file
  inventory, and exactly what the port does and does not implement.

The JSON in this package is a clean-room content carry of the jar's data files
(upgraded to 26.3's shapes); no Java source is copied, and the jar itself is
evidence under `ports/_shared/carry-work/` — never committed, never shipped.

## Obligations that follow from MIT

1. Redistribution and modification are permitted; the copyright and permission
   notice travel with the package (this file and `LICENSE`).
2. The software is provided **as is**, without warranty; the licence's
   disclaimer applies unchanged.
3. The port is a **partial** implementation of 0.5.9 for Horizon/Minecraft
   26.3: the biomes, blocks, items, recipes and the features whose types 26.3
   decodes are carried; the mod's own Java feature types are not (see
   `notes.md`, "Worldgen verdict").
