#!/usr/bin/env python3
"""Craft Regions Unexplored recipes in a real crafting table.

Called by tools/e2e.sh with the open game's control socket. Uses the harness's
crafting grid (`ctl screen`: slots 100-108 row-major, result 200), gives the
ingredients, and asserts:

1. one `regions_unexplored:willow_log` -> four `willow_planks` (the shapeless
   recipe naming `#regions_unexplored:willow_logs`, so the carried item tag
   resolves); an oak log (a vanilla log, not in the tag) stays empty;
2. eight `minecraft:oak_planks` around one `minecraft:yellow_dye` -> eight
   `yellow_painted_planks` (the recipe names `#minecraft:planks` and the
   hand-written `#c:yellow_dyes`); a stick in the centre stays empty;
3. four `prismarite_crystals` around one `minecraft:glass` -> two `prismaglass`
   (the recipe names the carried `#regions_unexplored:prismarite_crystals` and
   the hand-written `#c:glass`); stone in the centre stays empty;
4. three `blue_magnolia_leaves` -> six `blue_magnolia_flowers`, a recipe the raw
   carry had moved to `outside/` because its result block was left out; two
   leaves stay empty.

The table is replaced before every case, so a failed case cannot leak into the
next grid. Exits 1 with the observed result on the first mismatch.
"""
import json
import subprocess
import sys

RING = [100, 101, 102, 103, 105, 106, 107, 108]
CROSS = [101, 103, 105, 107]
CENTRE = 104
TOP_ROW = [100, 101, 102]


def main():
    sock, ctl, x, y, z = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]

    def run(*args):
        out = subprocess.run([ctl, "--socket", sock, *args], text=True, capture_output=True)
        try:
            return json.loads(out.stdout)
        except json.JSONDecodeError:
            raise SystemExit(f"ctl {' '.join(args)}: {out.stdout}{out.stderr}")

    def wait(ticks=4):
        run("wait", str(ticks))

    def slots():
        screen = run("screen")
        if "slots" not in screen:
            raise SystemExit(f"no menu is open: {screen}")
        return screen["slots"]

    def find(item):
        for slot in slots():
            if slot.get("item") == item:
                return slot["slot"]
        raise SystemExit(f"missing ingredient {item} in the inventory")

    def open_table():
        wait()
        run("interact", x, y, z)
        wait(5)

    def result():
        stack = [s for s in slots() if s["slot"] == 200]
        if not stack or not stack[0].get("item"):
            return None
        return stack[0]

    def place(item, mode, targets):
        slot = find(item)
        run("click-slot", str(slot))
        wait(1)
        for target in targets:
            if mode == "right":
                run("click-slot", str(target), "right")
            else:
                run("click-slot", str(target))
            wait(1)
        run("click-slot", str(slot))
        wait(2)

    def setup(items):
        try:
            run("close")
        except SystemExit:
            pass
        wait(5)
        run("setblock", x, y, z, "minecraft:air")
        run("setblock", x, y, z, "minecraft:crafting_table")
        wait(2)
        run("command", f"tp @s {float(x) - 0.5} {y} {float(z) + 0.5}")
        wait(3)
        run("command", "clear @s")
        for item, count in items:
            run("give", item, str(count))
        wait(3)
        open_table()

    failures = []

    def check(label, items, placements, want_item, want_count, take=False):
        setup(items)
        for item, mode, targets in placements:
            place(item, mode, targets)
        got = result()
        print(f"{label} ->", json.dumps(got))
        if not got or got.get("item") != want_item or got.get("count") != want_count:
            failures.append(f"{label}: expected {want_count} {want_item}, got {got}")
            return None
        if take:
            run("click-slot", "200")
            wait(5)
            run("click-slot", "9")
            wait(3)
            made = run("inventory")["counts"].get(want_item, 0)
            if made < want_count:
                failures.append(
                    f"{label}: the crafted stack reached the inventory as {made}, not {want_count}"
                )
        return got

    def empty_control(label, items, placements):
        setup(items)
        for item, mode, targets in placements:
            place(item, mode, targets)
        got = result()
        print(f"{label} ->", json.dumps(got))
        if got is not None:
            failures.append(f"{label}: control crafted {got['item']}")

    # 1. Shapeless planks from the carried #regions_unexplored:willow_logs tag.
    check(
        "1 willow_log -> 4 willow_planks",
        [("regions_unexplored:willow_log", 1)],
        [("regions_unexplored:willow_log", "right", [100])],
        "regions_unexplored:willow_planks", 4, take=True,
    )
    empty_control(
        "stick control -> nothing",
        [("minecraft:stick", 1)],
        [("minecraft:stick", "right", [100])],
    )

    # 2. #minecraft:planks + #c:yellow_dyes.
    check(
        "8 oak_planks + yellow_dye -> 8 yellow_painted_planks",
        [("minecraft:oak_planks", 8), ("minecraft:yellow_dye", 1)],
        [("minecraft:oak_planks", "right", RING), ("minecraft:yellow_dye", "right", [CENTRE])],
        "regions_unexplored:yellow_painted_planks", 8,
    )
    empty_control(
        "8 oak_planks + stick -> nothing",
        [("minecraft:oak_planks", 8), ("minecraft:stick", 1)],
        [("minecraft:oak_planks", "right", RING), ("minecraft:stick", "right", [CENTRE])],
    )

    # 3. #regions_unexplored:prismarite_crystals + #c:glass.
    check(
        "4 prismarite_crystals + glass -> 2 prismaglass",
        [("regions_unexplored:prismarite_cluster", 4), ("minecraft:glass", 1)],
        [
            ("regions_unexplored:prismarite_cluster", "right", CROSS),
            ("minecraft:glass", "right", [CENTRE]),
        ],
        "regions_unexplored:prismaglass", 2,
    )
    empty_control(
        "4 prismarite_crystals + stone -> nothing",
        [("regions_unexplored:prismarite_cluster", 4), ("minecraft:stone", 1)],
        [
            ("regions_unexplored:prismarite_cluster", "right", CROSS),
            ("minecraft:stone", "right", [CENTRE]),
        ],
    )

    # 4. The restored recipe for a block the raw carry left out.
    check(
        "3 blue_magnolia_leaves -> 6 blue_magnolia_flowers",
        [("regions_unexplored:blue_magnolia_leaves", 3)],
        [("regions_unexplored:blue_magnolia_leaves", "right", TOP_ROW)],
        "regions_unexplored:blue_magnolia_flowers", 6,
    )
    empty_control(
        "2 blue_magnolia_leaves -> nothing",
        [("regions_unexplored:blue_magnolia_leaves", 2)],
        [("regions_unexplored:blue_magnolia_leaves", "right", TOP_ROW[:2])],
    )

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        raise SystemExit(1)
    print("recipe PASS: willow planks + tag, the c:dyes recipe, the c:glass recipe and "
          "the restored magnolia flower recipe craft; every control stays empty")


if __name__ == "__main__":
    main()
