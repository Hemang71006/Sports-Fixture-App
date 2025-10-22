from flask import Flask, render_template, request, redirect, url_for
import math
import random
import PyPDF2
import docx

app = Flask(__name__)

def next_power_of_two(n):
    return 1 if n == 0 else 2 ** math.ceil(math.log2(n))

def generate_knockout(teams, top_seeds):
    total_teams = len(teams)
    
    # Check if a single bracket is sufficient (32 teams or less)
    if total_teams <= 32:
        slots = next_power_of_two(total_teams)
        num_byes = slots - total_teams

        # Use sets for efficient lookup
        teams_set = set(teams)
        
        # Separate teams who get byes and those who will play in the first round
        bye_teams = []
        first_round_participants = []
        
        # First, allocate byes to the highest-seeded teams
        for team in top_seeds:
            if len(bye_teams) < num_byes and team in teams_set:
                bye_teams.append(team)

        # Add any remaining teams to the participants list
        for team in teams:
            if team not in bye_teams:
                first_round_participants.append(team)

        # Randomly shuffle the participants who will actually play
        random.shuffle(first_round_participants)

        # Combine byes and participants for the final first round order
        first_round_entries = []
        
        # Pair up the participants
        for i in range(0, len(first_round_participants), 2):
            if i + 1 < len(first_round_participants):
                first_round_entries.append((first_round_participants[i], first_round_participants[i+1]))
            else:
                # If an odd team is left, give it a bye
                bye_teams.append(first_round_participants[i])
                
        # Add the bye teams to the list of matches as a team with a "None" opponent
        for team in bye_teams:
            first_round_entries.append((team, None))
            
        # --- Seeding Logic for Top Four Teams ---
        # Find the matches containing the top four seeds
        seed_matches = {i+1: None for i in range(len(top_seeds))}
        
        for i, seed_name in enumerate(top_seeds):
            for match in first_round_entries:
                if seed_name in match:
                    seed_matches[i+1] = match
                    break
        
        # Place #2 seed's match at the top
        if seed_matches.get(2):
            seed2_match = seed_matches[2]
            seed2_index = first_round_entries.index(seed2_match)
            first_round_entries[0], first_round_entries[seed2_index] = first_round_entries[seed2_index], first_round_entries[0]

        # Place #1 seed's match at the bottom
        if seed_matches.get(1):
            seed1_match = seed_matches[1]
            seed1_index = first_round_entries.index(seed1_match) # Re-find index in case of a swap
            last_index = len(first_round_entries) - 1
            first_round_entries[last_index], first_round_entries[seed1_index] = first_round_entries[seed1_index], first_round_entries[last_index]

        # Place #4 seed's match at the top of the bottom half (index len/2)
        if seed_matches.get(4):
            seed4_match = seed_matches[4]
            seed4_index = first_round_entries.index(seed4_match)
            halfway_index = len(first_round_entries) // 2
            first_round_entries[halfway_index], first_round_entries[seed4_index] = first_round_entries[seed4_index], first_round_entries[halfway_index]

        # Place #3 seed's match at the bottom of the top half (index len/2 - 1)
        if seed_matches.get(3):
            seed3_match = seed_matches[3]
            seed3_index = first_round_entries.index(seed3_match)
            halfway_index = len(first_round_entries) // 2
            first_round_entries[halfway_index - 1], first_round_entries[seed3_index] = first_round_entries[seed3_index], first_round_entries[halfway_index - 1]


        # --- End of Seeding Logic ---

        rounds = [first_round_entries]

        # Generate subsequent rounds with placeholder names
        current_round_size = math.ceil(len(first_round_entries) / 2)
        while current_round_size >= 1:
            rounds.append([("Winner", "Winner")] * current_round_size)
            current_round_size //= 2
        
        return rounds

    else: # If more than 32 teams, divide into pools
        # Find the next power of two for the total number of teams
        next_pow2 = next_power_of_two(total_teams)
        
        # Determine number of pools
        num_pools = (next_pow2 // 32)
        if num_pools == 0:
            num_pools = 1
        
        # Divide teams as evenly as possible among pools
        teams_per_pool = total_teams // num_pools
        remainder = total_teams % num_pools
        
        random.shuffle(teams)
        
        pools = []
        start_index = 0
        for i in range(num_pools):
            pool_size = teams_per_pool
            if remainder > 0:
                pool_size += 1
                remainder -= 1
            
            pool_teams = teams[start_index:start_index + pool_size]
            pools.append(pool_teams)
            start_index += pool_size
        
        # Generate brackets for each pool
        pool_brackets = []
        for i, pool in enumerate(pools):
            pool_brackets.append({
                "name": f"Pool {chr(65 + i)}",
                "bracket": generate_knockout(pool, top_seeds)
            })
            
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
        # Determine teams based on whether the input came from 'num_teams' or the dynamic 'team' inputs
        if 'num_teams' in request.form and request.form["num_teams"]:
            num_teams = int(request.form["num_teams"])
            teams = [request.form.get(f"team{i}", f"Team{i}") for i in range(1, num_teams + 1)]
        else:
            # Handle list paste submissions (where num_teams is derived from the count of 'teamX' keys)
            teams = [request.form[key] for key in request.form if key.startswith('team')]
            num_teams = len(teams)
            
        top_seeds_raw = request.form.get("top_seeds", "")
        top_seeds = [x.strip() for x in top_seeds_raw.split(",") if x.strip()] if top_seeds_raw else []
        ttype = request.form["tournament_type"]
        tournament_name = request.form.get("tournament_name", "Tournament")

        fixtures = generate_knockout(teams, top_seeds) if ttype == "knockout" else generate_round_robin(teams)
        
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
                return render_template("knockout_fixtures.html", fixtures_rounds=fixtures, ttype=ttype, tournament_name=tournament_name, background_class="bg-default")
            else:
                return render_template("round_robin_fixtures.html", fixtures_rounds=fixtures, ttype=ttype, tournament_name=tournament_name, background_class="bg-default")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)






