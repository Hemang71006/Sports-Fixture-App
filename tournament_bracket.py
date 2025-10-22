
import math
from typing import List

# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------

def next_power_of_two(x: int) -> int:
    return 1 << (x - 1).bit_length()

def seeding_map(n: int) -> List[int]:
    """
    Return a list of bracket positions (1-indexed) for
    seeds 1..n in classic order:
      seed1 bottom, seed2 top, seed3 bottom of top half,
      seed4 top of bottom half, etc.
    """
    if n == 1:
        return [1]
    half = n // 2
    top = seeding_map(half)
    bottom = seeding_map(half)
    return [p for p in top] + [p + half for p in bottom]

def arrange_teams(total: int, seeds: List[str], others: List[str]) -> List[str]:
    """
    Place teams and BYEs so that:
      * seed 1 is at bottom,
      * seed 2 is at top,
      * BYEs are assigned to the *lowest seeds*.
    """
    slots = next_power_of_two(total)
    mapping = seeding_map(slots)          # visual position for each seed number
    seed_count = total
    bye_count = slots - total

    # full list of team names in seed order
    allteams = list(seeds) + list(others)
    while len(allteams) < total:
        allteams.append(f"Team{len(allteams)+1}")

    # seed numbers that should become BYEs: the lowest-priority ones
    bye_seeds = set(range(seed_count - bye_count + 1, seed_count + 1))

    placed = [""] * slots
    for seed_num in range(1, slots + 1):
        pos = mapping[seed_num - 1] - 1
        if seed_num <= seed_count:
            if seed_num in bye_seeds:
                placed[pos] = "BYE"
            else:
                placed[pos] = allteams[seed_num - 1]
        else:
            placed[pos] = "BYE"
    return placed

def make_pairs(lst: List[str]) -> List[List[str]]:
    return [[lst[i], lst[i + 1]] for i in range(0, len(lst), 2)]

def print_bracket(teams: List[str]) -> None:
    rounds, current = [], teams
    while len(current) > 1:
        rounds.append(make_pairs(current))
        current = ["Winner"] * (len(current) // 2)

    gap_sizes = [8 * (2 ** i) for i in range(len(rounds))]
    columns = []
    for matches, gap in zip(rounds, gap_sizes):
        lines = []
        for a, b in matches:
            lines += [a.ljust(gap) + "┐",
                      b.ljust(gap) + "┘",
                      ""]
        columns.append(lines)

    max_rows = max(len(c) for c in columns)
    for c in columns:
        c.extend([""] * (max_rows - len(c)))

    for row in zip(*columns):
        print("  ".join(row).rstrip())

# -----------------------------------------------------------
# Main
# -----------------------------------------------------------

def main():
    total = int(input("Enter number of teams: ").strip())
    seeds = [s.strip() for s in input(
        "Enter top seeded team names in rank order (comma separated): "
    ).split(",") if s.strip()]
    others = [o.strip() for o in input(
        "Enter remaining team names (comma separated) or leave blank: "
    ).split(",") if o.strip()]

    print("\n======= TOURNAMENT BRACKET =======\n")
    bracket = arrange_teams(total, seeds, others)
    print_bracket(bracket)
    print("\n==================================")

if __name__ == "__main__":
    main()




