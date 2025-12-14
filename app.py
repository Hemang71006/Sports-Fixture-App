from flask import Flask, render_template, request, redirect, url_for
import math
import random
import re
try:
    import PyPDF2
except Exception:
    PyPDF2 = None
try:
    import docx
except Exception:
    docx = None

app = Flask(__name__)

def next_power_of_two(n):
    return 1 if n == 0 else 2 ** math.ceil(math.log2(n))

def get_pool_seed_to_position(pool_seeds, slots, pool_type="A"):
    """
    Generate seed_to_position mapping for a pool based on LOCAL seed indices (1-N).
    Handles variable number of seeds (7, 8, etc.) by adjusting the seeding pattern.
    """
    seed_to_position = {}
    
    if slots == 32 and len(pool_seeds) >= 2:
        # Get the best and 2nd best seeds in this pool
        sorted_pool_seeds = sorted(pool_seeds, key=lambda x: int(x.replace('Team', '').replace('Seed', '').strip()))
        best_seed_num = int(sorted_pool_seeds[0].replace('Team', '').replace('Seed', '').strip())
        second_best_seed_num = int(sorted_pool_seeds[1].replace('Team', '').replace('Seed', '').strip())
        
        # Find LOCAL positions of these seeds
        best_seed_local = None
        second_best_seed_local = None
        for i, seed in enumerate(pool_seeds, 1):
            seed_num = int(seed.replace('Team', '').replace('Seed', '').strip())
            if seed_num == best_seed_num:
                best_seed_local = i
            elif seed_num == second_best_seed_num:
                second_best_seed_local = i
        
        if best_seed_local and second_best_seed_local:
            # For 4 pools: A/C place best on top, B/D place best on bottom
            if pool_type in ("A", "C"):
                # Best at position 0 (top), 2nd best at position 15 (bottom)
                top_local = best_seed_local
                bottom_local = second_best_seed_local
            else:  # "B" or "D"
                # 2nd best at position 0, Best at position 15
                top_local = second_best_seed_local
                bottom_local = best_seed_local
            
            # NCAA seeding pattern for 32-slot bracket
            seed_to_position = {
                top_local: 0,           # Strategic top → position 0
                bottom_local: 15,       # Strategic bottom → position 15
            }
            
            # Fill remaining seeds in NCAA pattern positions
            remaining_locals = [i for i in range(1, len(pool_seeds) + 1) if i != top_local and i != bottom_local]
            remaining_positions = [8, 7, 4, 11, 12, 3]  # NCAA pattern for remaining seeds
            for local_seed, position in zip(remaining_locals, remaining_positions):
                seed_to_position[local_seed] = position
                
    elif slots == 16 and len(pool_seeds) >= 2:
        sorted_pool_seeds = sorted(pool_seeds, key=lambda x: int(x.replace('Team', '').replace('Seed', '').strip()))
        best_seed_num = int(sorted_pool_seeds[0].replace('Team', '').replace('Seed', '').strip())
        second_best_seed_num = int(sorted_pool_seeds[1].replace('Team', '').replace('Seed', '').strip())
        
        best_seed_local = None
        second_best_seed_local = None
        for i, seed in enumerate(pool_seeds, 1):
            seed_num = int(seed.replace('Team', '').replace('Seed', '').strip())
            if seed_num == best_seed_num:
                best_seed_local = i
            elif seed_num == second_best_seed_num:
                second_seed_local = i
        
        if pool_type == "A":
            seed_to_position = {1: 0, 2: 7, 3: 4, 4: 3}
        else:
            seed_to_position = {2: 0, 1: 7, 3: 4, 4: 3}
            
    elif slots == 8 and len(pool_seeds) >= 2:
        if pool_type == "A":
            seed_to_position = {1: 0, 2: 3}
        else:
            seed_to_position = {2: 0, 1: 3}
    elif slots == 4 and len(pool_seeds) >= 2:
        if pool_type == "A":
            seed_to_position = {1: 0, 2: 1}
        else:
            seed_to_position = {2: 0, 1: 1}
    
    return seed_to_position




def generate_knockout(teams, top_seeds, preserve_order=False, pool_type=None):
    total_teams = len(teams)

    # Check if a single bracket is sufficient (32 teams or less)
    if total_teams <= 32:
        slots = next_power_of_two(total_teams)
        num_byes = slots - total_teams

        # Use sets for efficient lookup
        teams_set = set(teams)

        # Separate teams who get byes and those who will play
        bye_teams = []
        playing_teams = []

        # First, allocate byes to the highest-seeded teams
        for team in top_seeds:
            if len(bye_teams) < num_byes and team in teams_set:
                bye_teams.append(team)

        # If we still need more byes, add random teams from non-seeded teams
        if len(bye_teams) < num_byes:
            # Get all non-seeded teams
            non_seeded = [t for t in teams if t not in bye_teams]
            # Shuffle them to randomly select additional byes
            if not preserve_order:
                random.shuffle(non_seeded)
            # Add enough to reach num_byes
            for team in non_seeded:
                if len(bye_teams) < num_byes:
                    bye_teams.append(team)

        # Add remaining teams to playing teams list
        for team in teams:
            if team not in bye_teams:
                playing_teams.append(team)

        # Randomly shuffle the playing teams unless order is preserved
        if not preserve_order:
            random.shuffle(playing_teams)

        # Build seed_info dictionary
        seed_info = {}
        for i, seed_name in enumerate(top_seeds):
            if seed_name in teams_set:
                seed_info[i + 1] = seed_name
        
        # Create bracket: slots/2 positions (16 for 32-slot bracket)
        num_positions = slots // 2
        first_round_entries = [None] * num_positions
        
        # Seeding: define which POSITION (0-15 for 32 bracket) each seed goes to
        # Reverse NCAA seeding: Seed 2 at top, Seed 1 at bottom
        if pool_type:
            # Use pool-specific seeding
            seed_to_position = get_pool_seed_to_position(top_seeds, slots, pool_type)
        elif slots == 32:
            seed_to_position = {
                # Position 0-1: Seed 2 vs Seed 15
                2: 0,      # Seed 2
                15: 1,     # Seed 15
                
                # Position 2-3: Seed 7 vs Seed 10
                10: 2,     # Seed 10
                7: 3,      # Seed 7
                
                # Position 4-5: Seed 6 vs Seed 11
                6: 4,      # Seed 6
                11: 5,     # Seed 11
                
                # Position 6-7: Seed 3 vs Seed 14
                14: 6,     # Seed 14
                3: 7,      # Seed 3
                
                # Position 8-9: Seed 4 vs Seed 13
                4: 8,      # Seed 4
                13: 9,     # Seed 13
                
                # Position 10-11: Seed 5 vs Seed 12
                12: 10,    # Seed 12
                5: 11,     # Seed 5
                
                # Position 12-13: Seed 8 vs Seed 9
                8: 12,     # Seed 8
                9: 13,     # Seed 9
                
                # Position 14-15: Seed 1 vs Seed 16
                16: 14,    # Seed 16
                1: 15,     # Seed 1
            }
        elif slots == 16:
            seed_to_position = {
                # Top half (0-3): Seeds 2 and 3
                2: 0,      # Seed 2 at top
                3: 3,      # Seed 3 at bottom of top half
                6: 1,      # Seed 6
                7: 2,      # Seed 7
                10: 1,     11: 2,    14: 1,    15: 2,
                
                # Bottom half (4-7): Seeds 1 and 4
                1: 7,      # Seed 1 at bottom
                4: 4,      # Seed 4 at top of bottom half
                5: 5,      # Seed 5
                8: 6,      # Seed 8
                9: 4,      12: 6,    13: 5,    16: 6,
            }
        elif slots == 8:
            seed_to_position = {
                # Top half (0-1): Seeds 2 and 3
                2: 0,      # Seed 2
                3: 1,      # Seed 3
                6: 1,      7: 1,
                
                # Bottom half (2-3): Seeds 1 and 4
                1: 3,      # Seed 1
                4: 2,      # Seed 4
                5: 2,      8: 3,
            }
        elif slots == 4:
            seed_to_position = {
                2: 0,      1: 1,
            }
        else:
            seed_to_position = {}
        
        # Place seeds in their bracket positions
        used_teams = set()
        for seed_num, pos in seed_to_position.items():
            if seed_num in seed_info and pos < num_positions:
                seed_name = seed_info[seed_num]
                if seed_name in bye_teams:
                    first_round_entries[pos] = (seed_name, None)
                else:
                    first_round_entries[pos] = seed_name  # Placeholder
                used_teams.add(seed_name)
        
        # Fill remaining positions with other teams
        # We need to fill num_positions (16 for 32-bracket) with all teams
        
        remaining_playing = [t for t in playing_teams if t not in used_teams]
        remaining_byes = [t for t in bye_teams if t not in used_teams]
        
        # Place remaining byes in empty seed positions (where missing seeds would be)
        # Find which seed positions are empty
        empty_seed_positions = []
        for seed_num in range(1, 17):  # Seeds 1-16
            if seed_num in seed_to_position:
                pos = seed_to_position[seed_num]
                if first_round_entries[pos] is None:
                    empty_seed_positions.append(pos)
        
        # Place remaining byes in these empty seed positions
        bye_idx = 0
        for pos in empty_seed_positions:
            if bye_idx < len(remaining_byes):
                first_round_entries[pos] = (remaining_byes[bye_idx], None)
                bye_idx += 1
        
        # Place any leftover byes in remaining empty positions
        if bye_idx < len(remaining_byes):
            for pos in range(num_positions):
                if first_round_entries[pos] is None and bye_idx < len(remaining_byes):
                    first_round_entries[pos] = (remaining_byes[bye_idx], None)
                    bye_idx += 1
        
        # Place remaining playing teams in pairs in empty positions
        play_idx = 0
        for pos in range(num_positions):
            if first_round_entries[pos] is None:
                if play_idx < len(remaining_playing):
                    team1 = remaining_playing[play_idx]
                    play_idx += 1
                    
                    # Try to pair with next team
                    team2 = None
                    if play_idx < len(remaining_playing):
                        team2 = remaining_playing[play_idx]
                        play_idx += 1
                    
                    if team2:
                        first_round_entries[pos] = (team1, team2)
                    else:
                        first_round_entries[pos] = (team1, None)
        
        # Convert any remaining single team placeholders to byes
        final_entries = []
        for entry in first_round_entries:
            if entry is None:
                continue
            elif isinstance(entry, tuple):
                final_entries.append(entry)
            else:
                final_entries.append((entry, None))
        
        first_round_entries = final_entries
        
        # --- End of Seeding Logic ---

        rounds = [first_round_entries]

        # Generate subsequent rounds with explicit Winner-vs-Winner placeholders
        num_matches = len(first_round_entries)
        while num_matches > 1:
            # Each match produces one winner, so next round has half as many matches (ceil for odd)
            num_matches = (num_matches + 1) // 2
            next_round = [("Winner", "Winner") for _ in range(num_matches)]
            rounds.append(next_round)

        return rounds

    # If more than 32 teams, divide into pools
    next_pow2 = next_power_of_two(total_teams)

    # Determine number of pools
    num_pools = next_pow2 // 32
    if num_pools == 0:
        num_pools = 1

    # Define seed distribution for pools to ensure proper matchups
    # Seeds are distributed so that 1 and 2 only meet in finals
    # These are SEED POSITIONS (1-16), but we need to handle cases with fewer seeds
    num_seeds = len(top_seeds)
    
    if num_pools == 2:
        if num_seeds >= 8:
            # For 2 pools, support up to 32 seeds (16 per pool)
            # Pool A: Seeds 2,3,6,7,10,11,14,15,18,19,22,23,26,27,30,31
            # Pool B: Seeds 1,4,5,8,9,12,13,16,17,20,21,24,25,28,29,32
            pool_a_seeds = []
            pool_b_seeds = []
            
            # Pattern: Pool A gets 2,3,6,7 then 10,11,14,15 then 18,19,22,23 etc.
            # Pool B gets 1,4,5,8,9 then 12,13,16,17 then 20,21,24,25 etc.
            for block_start in range(1, 33, 8):  # 1, 9, 17, 25
                if block_start <= num_seeds:
                    # Pool B gets first seed of each block
                    pool_b_seeds.append(block_start)
                    # Pool A gets 2nd and 3rd
                    if block_start + 1 <= num_seeds:
                        pool_a_seeds.append(block_start + 1)
                    if block_start + 2 <= num_seeds:
                        pool_a_seeds.append(block_start + 2)
                    # Pool B gets 4th and 5th
                    if block_start + 3 <= num_seeds:
                        pool_b_seeds.append(block_start + 3)
                    if block_start + 4 <= num_seeds:
                        pool_b_seeds.append(block_start + 4)
                    # Pool A gets 6th and 7th
                    if block_start + 5 <= num_seeds:
                        pool_a_seeds.append(block_start + 5)
                    if block_start + 6 <= num_seeds:
                        pool_a_seeds.append(block_start + 6)
                    # Pool B gets 8th
                    if block_start + 7 <= num_seeds:
                        pool_b_seeds.append(block_start + 7)
            
            desired_pool_seeds = [pool_a_seeds, pool_b_seeds]
        else:
            # For fewer than 8 seeds, distribute evenly
            desired_pool_seeds = [[], []]
            for seed_pos in range(1, num_seeds + 1):
                pool_idx = (seed_pos - 1) % 2
                desired_pool_seeds[pool_idx].append(seed_pos)
    elif num_pools == 4:
        if num_seeds >= 8:
            # For 4 pools, support up to 32 seeds (8 per pool)
            # Pool A: 2,7,10,15,18,23,26,31
            # Pool B: 3,6,11,14,19,22,27,30
            # Pool C: 4,5,12,13,20,21,28,29
            # Pool D: 1,8,9,16,17,24,25,32
            pool_a_seeds = []
            pool_b_seeds = []
            pool_c_seeds = []
            pool_d_seeds = []
            
            for block_start in range(1, 33, 8):  # 1, 9, 17, 25
                if block_start <= num_seeds:
                    pool_d_seeds.append(block_start)
                if block_start + 1 <= num_seeds:
                    pool_a_seeds.append(block_start + 1)
                if block_start + 2 <= num_seeds:
                    pool_b_seeds.append(block_start + 2)
                if block_start + 3 <= num_seeds:
                    pool_c_seeds.append(block_start + 3)
                if block_start + 4 <= num_seeds:
                    pool_c_seeds.append(block_start + 4)
                if block_start + 5 <= num_seeds:
                    pool_b_seeds.append(block_start + 5)
                if block_start + 6 <= num_seeds:
                    pool_a_seeds.append(block_start + 6)
                if block_start + 7 <= num_seeds:
                    pool_d_seeds.append(block_start + 7)
            
            desired_pool_seeds = [pool_a_seeds, pool_b_seeds, pool_c_seeds, pool_d_seeds]
        else:
            # For fewer seeds, distribute evenly
            desired_pool_seeds = [[] for _ in range(4)]
            for seed_pos in range(1, num_seeds + 1):
                pool_idx = (seed_pos - 1) % 4
                desired_pool_seeds[pool_idx].append(seed_pos)
    else:
        # For other pool counts, use simple alternating distribution
        desired_pool_seeds = [[] for _ in range(num_pools)]
        for seed_pos in range(1, num_seeds + 1):
            pool_idx = (seed_pos - 1) % num_pools
            desired_pool_seeds[pool_idx].append(seed_pos)

    # Extract seeded teams for each pool by matching seed NUMBER (not position in list)
    pool_top_seeds = []
    
    # First, identify seed numbers in the team names
    seed_number_to_team = {}
    for seed_team in top_seeds:
        # Extract the number from team name (e.g., "Team5" -> 5, "Seed 3" -> 3, "1" -> 1)
        match = re.search(r'\d+', seed_team)
        if match:
            seed_num = int(match.group())
            seed_number_to_team[seed_num] = seed_team
    
    # Now distribute seeds to pools by their actual seed NUMBER
    for pool_idx in range(num_pools):
        pool_seeds = []
        for seed_pos in desired_pool_seeds[pool_idx]:
            # Find the team with this seed number
            if seed_pos in seed_number_to_team:
                pool_seeds.append(seed_number_to_team[seed_pos])
        pool_top_seeds.append(pool_seeds)

    # Divide teams as evenly as possible among pools
    # Distribute seeded teams first, then non-seeded teams
    teams_set = set(top_seeds)
    non_seeded_teams = [t for t in teams if t not in teams_set]
    
    if not preserve_order:
        random.shuffle(non_seeded_teams)

    pools = []
    non_seeded_idx = 0
    for i in range(num_pools):
        # Each pool gets its designated seeded teams
        pool_seeds = pool_top_seeds[i]
        
        # Calculate how many non-seeded teams this pool needs
        # Total teams per pool should be roughly equal
        teams_for_pool = []
        teams_for_pool.extend(pool_seeds)
        
        # Add non-seeded teams
        avg_non_seeded_per_pool = len(non_seeded_teams) // num_pools
        remainder_non_seeded = len(non_seeded_teams) % num_pools
        
        non_seeded_count = avg_non_seeded_per_pool
        if i < remainder_non_seeded:
            non_seeded_count += 1
        
        for _ in range(non_seeded_count):
            if non_seeded_idx < len(non_seeded_teams):
                teams_for_pool.append(non_seeded_teams[non_seeded_idx])
                non_seeded_idx += 1
        
        pools.append(teams_for_pool)

    # Generate brackets for each pool
    pool_brackets = []
    pool_champions = []
    
    for i, pool in enumerate(pools):
        # Seeds for this pool are already embedded in pool_top_seeds[i]
        pool_seeds = pool_top_seeds[i]
        
        # Determine pool type for seeding pattern
        if num_pools == 2:
            pool_type = "A" if i == 0 else "B"
        elif num_pools == 4:
            pool_type = chr(65 + i)  # "A", "B", "C", "D"
        else:
            pool_type = None
        
        bracket = generate_knockout(pool, pool_seeds, pool_type=pool_type)
        
        # Calculate byes for this pool
        pool_size = len(pool)
        slots = next_power_of_two(pool_size)
        num_byes = slots - pool_size
        
        pool_brackets.append(
            {
                "name": f"Pool {chr(65 + i)}",
                "bracket": bracket,
                "team_count": pool_size,
                "bye_count": num_byes,
            }
        )
        # Extract the champion from the final round (last team in the final match)
        if bracket and len(bracket) > 0:
            final_round = bracket[-1]
            if final_round and len(final_round) > 0:
                final_match = final_round[0]
                # The winner is represented as ("Winner", "Winner"), use pool name + champion
                champion_name = f"Pool {chr(65 + i)} Champion"
                pool_champions.append(champion_name)
    
    # Add champions bracket if there are multiple pools
    if len(pool_brackets) > 1:
        champions_bracket = generate_knockout(pool_champions, [])
        pool_brackets.append(
            {
                "name": "Pool Winners Playoff",
                "bracket": champions_bracket,
                "is_champions": True,
                "team_count": len(pool_champions),
                "bye_count": 0,
            }
        )
    
    return pool_brackets


def generate_round_robin(teams):
    num_teams = len(teams)
    if num_teams % 2:
        teams.append("BYE")
    n = len(teams)
    rounds = []
    
    # Generate all league matches
    for i in range(n - 1):
        matches = []
        for j in range(n // 2):
            t1, t2 = teams[j], teams[n - 1 - j]
            if t1 != "BYE" and t2 != "BYE":
                matches.append((t1, t2))
        teams.insert(1, teams.pop())
        rounds.append(matches)
        
    # Generate semi-finals and final based on top teams
    playoff_round = []
    
    # If 5 or more teams, generate semi-finals and a final
    if num_teams >= 5:
        semi_final_1 = ("1st Place", "4th Place")
        semi_final_2 = ("2nd Place", "3rd Place")
        playoff_round.append([semi_final_1, semi_final_2])
        final = ("SF1 Winner", "SF2 Winner")
        playoff_round.append([final])
    # If 4 or fewer teams, generate only a final
    elif num_teams >= 2:
        final = ("1st Place", "2nd Place")
        playoff_round.append([final])
    
    # Combine league matches and playoff rounds
    rounds.extend(playoff_round)
    
    return rounds


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        print("DEBUG: POST request received")
        print(f"DEBUG: Form data keys: {list(request.form.keys())}")
        
        # Determine teams based on whether the input came from 'num_teams' or the dynamic 'team' inputs
        if 'num_teams' in request.form and request.form["num_teams"]:
            num_teams = int(request.form["num_teams"])
            teams = [request.form.get(f"team{i}", f"Team{i}") for i in range(1, num_teams + 1)]
        else:
            # Handle list paste submissions (where num_teams is derived from the count of 'teamX' keys)
            teams = [request.form[key] for key in request.form if key.startswith('team')]
            num_teams = len(teams)
        
        print(f"DEBUG: Extracted {num_teams} teams: {teams}")
            
        top_seeds_raw = request.form.get("top_seeds", "")
        top_seeds = [x.strip() for x in top_seeds_raw.split(",") if x.strip()] if top_seeds_raw else []
        ttype = request.form["tournament_type"]
        tournament_name = request.form.get("tournament_name", "Tournament")

        print(f"DEBUG: Tournament type: {ttype}, name: {tournament_name}")
        print(f"DEBUG: Top seeds: {top_seeds}")

        fixtures = generate_knockout(teams, top_seeds) if ttype == "knockout" else generate_round_robin(teams)

        print(f"DEBUG: Generated fixtures, type: {type(fixtures)}")
        if isinstance(fixtures, list) and fixtures and isinstance(fixtures[0], dict):
            print("DEBUG: Returning pools template")
            return render_template("knockout_fixtures.html", pools=fixtures, ttype=ttype, tournament_name=tournament_name, background_class="bg-default")
        print("DEBUG: Returning regular fixtures template")
        if ttype == "knockout":
            return render_template("knockout_fixtures.html", fixtures_rounds=fixtures, ttype=ttype, tournament_name=tournament_name, background_class="bg-default")
        else:
            return render_template("round_robin_fixtures.html", fixtures_rounds=fixtures, ttype=ttype, tournament_name=tournament_name, background_class="bg-default")

    return render_template("index.html")

# New route to handle file uploads
@app.route("/upload", methods=["POST"])
def upload_teams():
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != "":
            teams_list = []
            if file.filename.endswith('.txt') or file.filename.endswith('.csv'):
                teams_list = [line.decode("utf-8").strip() for line in file.readlines()]
            elif file.filename.endswith('.pdf'):
                try:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        teams_list.extend(page.extract_text().splitlines())
                except Exception as e:
                    return f"Error reading PDF file: {e}"
            elif file.filename.endswith('.docx'):
                try:
                    doc = docx.Document(file)
                    for paragraph in doc.paragraphs:
                        teams_list.append(paragraph.text.strip())
                except Exception as e:
                    return f"Error reading DOCX file: {e}"
            
            teams = [team for team in teams_list if team]
            num_teams = len(teams)
            top_seeds_raw = request.form.get("top_seeds", "")
            top_seeds = [x.strip() for x in top_seeds_raw.split(",") if x.strip()] if top_seeds_raw else []
            ttype = request.form.get("tournament_type") or "knockout"
            tournament_name = request.form.get("tournament_name", "Tournament")

            fixtures = generate_knockout(teams, top_seeds) if ttype == "knockout" else generate_round_robin(teams)

            if ttype == "knockout":
                if isinstance(fixtures, list) and fixtures and isinstance(fixtures[0], dict):
                    return render_template("knockout_fixtures.html", pools=fixtures, ttype=ttype, tournament_name=tournament_name, background_class="bg-default")
                return render_template("knockout_fixtures.html", fixtures_rounds=fixtures, ttype=ttype, tournament_name=tournament_name, background_class="bg-default")
            else:
                return render_template("round_robin_fixtures.html", fixtures_rounds=fixtures, ttype=ttype, tournament_name=tournament_name, background_class="bg-default")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)






