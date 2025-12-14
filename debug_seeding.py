import math

def next_power_of_two(n):
    return 1 if n == 0 else 2 ** math.ceil(math.log2(n))

# Test with 21 teams and 9 seeds
teams = [f"Team{i}" for i in range(1, 22)]
top_seeds = [f"Team{i}" for i in range(1, 10)]

total_teams = len(teams)
slots = next_power_of_two(total_teams)
num_byes = slots - total_teams
num_positions = slots // 2

print(f"Total teams: {total_teams}")
print(f"Slots: {slots}")
print(f"Num byes needed: {num_byes}")
print(f"Num positions: {num_positions}")
print(f"Top seeds: {top_seeds}")
print()

teams_set = set(teams)

# Allocate byes
bye_teams = []
for team in top_seeds:
    if len(bye_teams) < num_byes and team in teams_set:
        bye_teams.append(team)

# Fill remaining bye slots with random teams
for team in teams:
    if team not in bye_teams and len(bye_teams) < num_byes:
        bye_teams.append(team)

# Playing teams
playing_teams = []
for team in teams:
    if team not in bye_teams:
        playing_teams.append(team)

print(f"Bye teams ({len(bye_teams)}): {bye_teams}")
print(f"Playing teams ({len(playing_teams)}): {playing_teams}")
print()

# Seed info
seed_info = {}
for i, seed_name in enumerate(top_seeds):
    if seed_name in teams_set:
        seed_info[i + 1] = seed_name

print(f"Seed info: {seed_info}")
print()

# Seed positions for 32-slot bracket
seed_to_position = {
    2: 0, 15: 1,
    10: 2, 7: 3,
    6: 4, 11: 5,
    14: 6, 3: 7,
    4: 8, 13: 9,
    12: 10, 5: 11,
    8: 12, 9: 13,
    16: 14, 1: 15,
}

# Place seeds
first_round_entries = [None] * num_positions
used_teams = set()

print("Placing seeded teams:")
for seed_num, pos in seed_to_position.items():
    if seed_num in seed_info and pos < num_positions:
        seed_name = seed_info[seed_num]
        if seed_name in bye_teams:
            first_round_entries[pos] = (seed_name, None)
            print(f"  Position {pos}: {seed_name} (bye)")
        else:
            first_round_entries[pos] = seed_name
            print(f"  Position {pos}: {seed_name} (playing)")
        used_teams.add(seed_name)

print()
print(f"First round entries after seeding: {first_round_entries}")
print(f"Used teams: {used_teams}")
print()

# Remaining teams
remaining_playing = [t for t in playing_teams if t not in used_teams]
remaining_byes = [t for t in bye_teams if t not in used_teams]

print(f"Remaining byes ({len(remaining_byes)}): {remaining_byes}")
print(f"Remaining playing ({len(remaining_playing)}): {remaining_playing}")
print()

# Fill remaining positions
print("Filling remaining positions:")
bye_idx = 0
for pos in range(num_positions):
    if first_round_entries[pos] is None and bye_idx < len(remaining_byes):
        first_round_entries[pos] = (remaining_byes[bye_idx], None)
        print(f"  Position {pos}: {remaining_byes[bye_idx]} (bye)")
        bye_idx += 1

play_idx = 0
for pos in range(num_positions):
    if first_round_entries[pos] is None:
        if play_idx < len(remaining_playing):
            team1 = remaining_playing[play_idx]
            play_idx += 1
            
            team2 = None
            if play_idx < len(remaining_playing):
                team2 = remaining_playing[play_idx]
                play_idx += 1
            
            if team2:
                first_round_entries[pos] = (team1, team2)
                print(f"  Position {pos}: {team1} vs {team2}")
            else:
                first_round_entries[pos] = (team1, None)
                print(f"  Position {pos}: {team1} (bye)")

print()
print(f"Final entries before cleanup: {first_round_entries}")
print()

# Final conversion
final_entries = []
for entry in first_round_entries:
    if entry is None:
        continue
    elif isinstance(entry, tuple):
        final_entries.append(entry)
    else:
        final_entries.append((entry, None))

print(f"Final entries after cleanup: {final_entries}")
print(f"Total first-round entries: {len(final_entries)}")
