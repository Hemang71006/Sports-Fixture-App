from flask import Flask, render_template, request, redirect, url_for
import math
import random
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


def generate_knockout(teams, top_seeds, preserve_order=False):
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
        if slots == 32:
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

    # Divide teams as evenly as possible among pools
    teams_per_pool = total_teams // num_pools
    remainder = total_teams % num_pools

    if not preserve_order:
        random.shuffle(teams)

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

    # Generate brackets for each pool
    pool_brackets = []
    pool_champions = []
    
    for i, pool in enumerate(pools):
        bracket = generate_knockout(pool, top_seeds)
        
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






