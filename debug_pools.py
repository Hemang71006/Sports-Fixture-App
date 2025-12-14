import math

def next_power_of_two(n):
    return 1 if n == 0 else 2 ** math.ceil(math.log2(n))

# Test with 64 teams (2 pools)
total_teams = 64
top_seeds = [f"Team{i}" for i in range(1, 17)]  # 16 seeds

print(f"Total teams: {total_teams}")
print(f"Top seeds: {top_seeds}")
print()

next_pow2 = next_power_of_two(total_teams)
num_pools = next_pow2 // 32
if num_pools == 0:
    num_pools = 1

print(f"Next power of 2: {next_pow2}")
print(f"Num pools: {num_pools}")
print()

# Define seed distribution for pools
if num_pools == 2:
    pool_seed_groups = [
        [2, 3, 6, 7, 10, 11, 14, 15],  # Pool A
        [1, 4, 5, 8, 9, 12, 13, 16],   # Pool B
    ]
elif num_pools == 4:
    pool_seed_groups = [
        [2, 7, 10, 15],   # Pool A
        [3, 6, 11, 14],   # Pool B
        [4, 5, 12, 13],   # Pool C
        [1, 8, 9, 16],    # Pool D
    ]

print("Pool seed groups:")
for i, seeds in enumerate(pool_seed_groups):
    print(f"  Pool {chr(65 + i)}: {seeds}")
print()

# Map seed numbers to team names
seed_info_global = {}
for i, seed_name in enumerate(top_seeds):
    seed_info_global[i + 1] = seed_name

print(f"Seed info global: {seed_info_global}")
print()

# Create teams list
teams = [f"T{i}" for i in range(1, total_teams + 1)]

# Divide teams into pools
teams_per_pool = total_teams // num_pools
remainder = total_teams % num_pools

pools = []
start_index = 0
for i in range(num_pools):
    pool_size = teams_per_pool
    if remainder > 0:
        pool_size += 1
        remainder -= 1

    pool_teams = teams[start_index : start_index + pool_size]
    pools.append(pool_teams)
    start_index += pool_size

print(f"Pools created:")
for i, pool in enumerate(pools):
    print(f"  Pool {chr(65 + i)}: {len(pool)} teams - {pool[:5]}... (first 5)")
print()

# Get seeds for each pool
print("Seeds for each pool:")
for i, pool in enumerate(pools):
    pool_seed_nums = pool_seed_groups[i] if i < len(pool_seed_groups) else []
    pool_seeds = [seed_info_global[seed_num] for seed_num in pool_seed_nums 
                  if seed_num in seed_info_global and seed_info_global[seed_num] in pool]
    
    print(f"  Pool {chr(65 + i)}: seed_nums={pool_seed_nums}")
    print(f"    Pool teams: {set(pool)}")
    print(f"    Matching seeds in pool: {pool_seeds}")
    print()
