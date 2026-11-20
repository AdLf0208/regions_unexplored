# Package receipt — regions_unexplored 0.5.9

This tag's archive is the file below. Earlier sections of `notes.md` and
`VALIDATION.md` describe earlier builds of this port; where a digest there differs,
**this receipt is the one that matches the release asset.**

| field | value |
|---|---|
| version | `0.5.9` |
| file | `regions_unexplored.hmod` |
| bytes | 4,689,397 |
| sha256 | `25a44d072cba73c1947aad4d181bcace57b6ec8e1587045582a9595c54f7ba5a` |
| source | this tag — the tree here is the source that produced the archive |
| game | 26.3 |
| package kind | content only — no `[native]` table, no code |

## Verification of these exact bytes

`check` exit 0 · `fits` exit 2 (a content package has nothing to fit) · `verify-sdk-package.py` 1/1 · content re-carry fixpoint (`--check` red, `--write` reproduces both trees identically) · launcher leg `PASS` + `EXIT:0`, `NEGATIVE=1` `EXIT:1`, pre-fix control `EXIT:1`, `check-e2e-logs --strict` 6/6
