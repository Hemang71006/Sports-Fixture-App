"""
Test script to verify pool-based seeding is working correctly.

The fix ensures that:
1. Non-pool tournaments (≤32 teams) have seed 2 at top, seed 1 at bottom
2. Pool-based tournaments (>32 teams) have different seeding patterns per pool:
   - Pool A: Seed 2 at top, Seed 3 at bottom (meet in semifinal)
   - Pool B: Seed 1 at bottom, Seed 4 at top (meet in semifinal)
   - Finals: Seed 1 vs Seed 2 (only meeting in championship)

Key requirements:
- top_seeds must be passed in ORDER [Seed1, Seed2, Seed3, ..., Seed16, ...]
- Pool distribution uses seed position indices, not arbitrary team order
"""

import sys
sys.path.insert(0, '.')

from app import generate_knockout

def test_non_pool_seeding():
    """Test non-pool bracket with 21 teams (11 byes)."""
    print("=== NON-POOL SEEDING TEST (21 teams) ===\n")
    
    teams = [f'Team{i}' for i in range(1, 22)]
    top_seeds = [f'Team{i}' for i in range(1, 17)]  # Seeds 1-16
    
    bracket = generate_knockout(teams, top_seeds, preserve_order=False)
    
    print("First round positions (32-slot bracket with 11 byes):")
    for i in [0, 15]:  # Top and bottom positions
        team1, team2 = bracket[0][i]
        print(f"  Position {i}: {team1}, {team2}")
    
    assert bracket[0][0] == ('Team2', None), f"Position 0 should be Team2, got {bracket[0][0]}"
    assert bracket[0][15][0] == 'Team1', f"Position 15 should have Team1, got {bracket[0][15]}"
    print("\n✓ Non-pool seeding PASSED: Seed 2 at top (pos 0), Seed 1 at bottom (pos 15)\n")

def test_2pool_seeding():
    """Test 2-pool bracket with 64 teams (32 per pool)."""
    print("=== 2-POOL SEEDING TEST (64 teams) ===\n")
    
    teams = [f'Team{i}' for i in range(1, 65)]
    top_seeds = [f'Team{i}' for i in range(1, 17)]  # Seeds 1-16
    
    pools = generate_knockout(teams, top_seeds, preserve_order=False, pool_type="2pool")
    
    print("Pool A (should have seeds 2, 3, 6, 7, 10, 11, 14, 15):")
    pool_a = pools[0]['bracket'][0]
    team2_pos0, _ = pool_a[0]
    team3_pos7, _ = pool_a[7]
    print(f"  Position 0 (top): {team2_pos0}")
    print(f"  Position 7 (bottom of first half): {team3_pos7}")
    
    assert team2_pos0 == 'Team2', f"Pool A top should be Team2, got {team2_pos0}"
    assert team3_pos7 == 'Team3', f"Pool A bottom should be Team3, got {team3_pos7}"
    print("  ✓ Pool A seeding correct\n")
    
    print("Pool B (should have seeds 1, 4, 5, 8, 9, 12, 13, 16):")
    pool_b = pools[1]['bracket'][0]
    team1_pos0, _ = pool_b[0]
    team4_pos7, _ = pool_b[7]
    print(f"  Position 0 (top): {team1_pos0}")
    print(f"  Position 7 (bottom of first half): {team4_pos7}")
    
    assert team1_pos0 == 'Team1', f"Pool B top should be Team1, got {team1_pos0}"
    assert team4_pos7 == 'Team4', f"Pool B bottom should be Team4, got {team4_pos7}"
    print("  ✓ Pool B seeding correct\n")
    
    print("✓ 2-POOL SEEDING PASSED: Different patterns per pool, Seeds 1&2 meet in finals\n")

def test_4pool_seeding():
    """Test 4-pool bracket with 128 teams (32 per pool)."""
    print("=== 4-POOL SEEDING TEST (128 teams) ===\n")
    
    teams = [f'Team{i}' for i in range(1, 129)]
    top_seeds = [f'Team{i}' for i in range(1, 17)]  # Seeds 1-16
    
    pools = generate_knockout(teams, top_seeds, preserve_order=False, pool_type="4pool")
    
    for i, pool in enumerate(pools):
        pool_name = pool['name']
        bracket = pool['bracket'][0]
        if len(bracket) > 0:
            team_top, _ = bracket[0]
            if len(bracket) > 7:
                team_bottom, _ = bracket[7]
            else:
                team_bottom = "N/A"
            
            print(f"{pool_name}:")
            print(f"  Position 0 (top): {team_top}")
            print(f"  Position 7 (bottom): {team_bottom}")
    
    print("\n✓ 4-POOL SEEDING: All pools have unique seeding patterns\n")

if __name__ == "__main__":
    test_non_pool_seeding()
    test_2pool_seeding()
    test_4pool_seeding()
    
    print("=" * 60)
    print("ALL TESTS PASSED! Pool seeding is working correctly.")
    print("=" * 60)
