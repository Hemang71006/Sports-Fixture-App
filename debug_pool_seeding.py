import math

def next_power_of_two(n):
    return 1 if n == 0 else 2 ** math.ceil(math.log2(n))

def get_pool_seed_to_position(pool_seeds, slots, pool_type="A"):
    """
    Generate seed_to_position mapping for a pool based on its seeds.
    pool_type: "A" (seeds 2,3,6,7...) or "B" (seeds 1,4,5,8...)
    """
    seed_to_position = {}
    
    # For now, return standard mapping based on how many seeds we have
    if slots == 32 and len(pool_seeds) >= 8:
        if pool_type == "A":
            # Pool A: Seeds 2, 3, 6, 7, 10, 11, 14, 15 - Seed 2 at top, Seed 3 at bottom
            seed_to_position = {
                2: 0,      # Seed 2
                15: 1,     # Seed 15
                10: 2,     # Seed 10
                7: 3,      # Seed 7
                6: 4,      # Seed 6
                11: 5,     # Seed 11
                14: 6,     # Seed 14
                3: 7,      # Seed 3
                4: 8, 13: 9, 12: 10, 5: 11, 8: 12, 9: 13, 16: 14, 1: 15
            }
        else:  # pool_type == "B"
            # Pool B: Seeds 1, 4, 5, 8, 9, 12, 13, 16 - Seed 1 at bottom, Seed 4 at top
            seed_to_position = {
                2: 0, 15: 1, 10: 2, 7: 3, 6: 4, 11: 5, 14: 6, 3: 7,
                4: 8, 13: 9, 12: 10, 5: 11, 8: 12, 9: 13, 16: 14, 1: 15
            }
    
    return seed_to_position

# Test with Pool A seeds
pool_a_seeds = ["Team2", "Team3", "Team6", "Team7", "Team10", "Team11", "Team14", "Team15"]
slots = 32

print("Pool A (8 seeds):")
print(f"  Seeds: {pool_a_seeds}")
s2p_a = get_pool_seed_to_position(pool_a_seeds, slots, "A")
print(f"  seed_to_position: {s2p_a}")
print()

# Test with Pool B seeds
pool_b_seeds = ["Team1", "Team4", "Team5", "Team8", "Team9", "Team12", "Team13", "Team16"]
print("Pool B (8 seeds):")
print(f"  Seeds: {pool_b_seeds}")
s2p_b = get_pool_seed_to_position(pool_b_seeds, slots, "B")
print(f"  seed_to_position: {s2p_b}")
print()

# Check if seeds are the same
print("Issue: Both pools have the same seed_to_position mapping!")
print(f"Pool A == Pool B: {s2p_a == s2p_b}")
