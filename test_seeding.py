from app import generate_knockout

# Test with 21 teams and 4 seeds
teams = [str(i) for i in range(1, 22)]
top_seeds = ['1', '2', '3', '4']

result = generate_knockout(teams, top_seeds)

print('=== SEEDING TEST FOR 21 TEAMS ===')
print(f'Total matches in first round: {len(result[0])}\n')

# Find seed positions
seeds_found = {}
for idx, match in enumerate(result[0]):
    for s in ['1', '2', '3', '4']:
        if s in match:
            seeds_found[s] = idx

print('Seed positions:')
for seed, pos in sorted(seeds_found.items(), key=lambda x: int(x[0])):
    print(f'  Seed {seed}: Position {pos} - {result[0][pos]}')

print(f'\nTop half (0-15): Seeds {[s for s, p in seeds_found.items() if p <= 15]}')
print(f'Bottom half (16-31): Seeds {[s for s, p in seeds_found.items() if p >= 16]}')

print('\n=== VERIFICATION ===')
print(f'✓ Seed 2 and 3 in TOP half (semifinal): {seeds_found.get("2", -1) <= 15 and seeds_found.get("3", -1) <= 15}')
print(f'✓ Seed 1 and 4 in BOTTOM half (semifinal): {seeds_found.get("1", -1) >= 16 and seeds_found.get("4", -1) >= 16}')
print(f'✓ Seeds 3 and 4 in DIFFERENT halves: {(seeds_found.get("3", -1) <= 15) != (seeds_found.get("4", -1) <= 15)}')
