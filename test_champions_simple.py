#!/usr/bin/env python
"""Test script to verify the champions bracket feature works correctly"""

from app import app
import sys

def test_pool_tournament():
    """Test that pool tournaments with champions bracket are generated correctly"""
    with app.test_client() as client:
        # Test with 36 teams (should create pools + champions bracket)
        form_data = {
            'tournament_name': 'Test Pool Tournament',
            'num_teams': '36',
            'tournament_type': 'knockout'
        }
        # Add team names
        for i in range(1, 37):
            form_data[f'team{i}'] = f'Team {i}'
        
        response = client.post('/', data=form_data, follow_redirects=True)
        
        if response.status_code != 200:
            print(f"ERROR: Expected 200 but got {response.status_code}")
            return False
        
        html = response.get_data(as_text=True)
        
        # Check for pool elements
        required_elements = [
            'Pool A Champion',
            'Pool B Champion',
            'Pool Winners Playoff',
            'Tournament Champion',
            'bracket-champions',
            'bracket-wrapper-champions',
            'connectors-champions',
        ]
        
        for element in required_elements:
            if element not in html:
                print(f"ERROR: Missing expected element: {element}")
                return False
        
        print("[OK] Pool tournament test passed")
        
        # Test with single bracket (8 teams)
        form_data = {
            'tournament_name': 'Test Single Bracket',
            'num_teams': '8',
            'tournament_type': 'knockout'
        }
        # Add team names
        for i in range(1, 9):
            form_data[f'team{i}'] = f'Team {i}'
        
        response = client.post('/', data=form_data, follow_redirects=True)
        
        if response.status_code != 200:
            print(f"ERROR: Expected 200 but got {response.status_code}")
            return False
        
        html = response.get_data(as_text=True)
        
        # For single bracket, should NOT have champions bracket
        # Check for pool-specific elements in the actual content (not JavaScript)
        has_pools = 'Pool A Champion' in html or 'Pool A' in html
        # Check for the actual div element, not just the string in JavaScript
        import re
        has_champions_bracket_div = bool(re.search(r'<div[^>]*id="bracket-champions"', html))
        
        if has_pools or has_champions_bracket_div:
            print(f"ERROR: Single bracket should NOT have Champions Bracket section")
            print(f"  has_pools: {has_pools}")
            print(f"  has_champions_bracket_div: {has_champions_bracket_div}")
            return False
        
        # But should have regular champion card
        if 'Champion' not in html:
            print(f"ERROR: Should have Champion card in single bracket")
            return False
        
        print("[OK] Single bracket test passed")
        
        return True

if __name__ == '__main__':
    print("Testing champions bracket feature...")
    print("-" * 50)
    
    try:
        if test_pool_tournament():
            print("-" * 50)
            print("[OK] All tests passed!")
            sys.exit(0)
        else:
            print("-" * 50)
            print("[FAIL] Tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
