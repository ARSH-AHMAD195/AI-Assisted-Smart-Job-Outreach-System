import os
import csv
import re

def clean_company_name(name: str) -> str:
    name = name.lower().strip()
    # Remove common suffixes and punctuation
    suffixes = [
        "technologies", "technology", "solutions", "software", "services", "labs",
        "inc.", "inc", "ltd.", "ltd", "pvt.", "pvt", "co.", "co", "gmbh", "limited",
        "corp.", "corp", "corporation", "india"
    ]
    for s in suffixes:
        name = re.sub(r'\b' + re.escape(s) + r'\b', '', name)
    # Remove all non-alphanumeric characters
    return "".join(filter(str.isalnum, name))

def test_match(target_name: str):
    csv_path = "/home/om/dev/minor1/backend/hr_contacts.csv"
    target_clean = clean_company_name(target_name)
    matches = []
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_company = row.get("Company", "")
            csv_clean = clean_company_name(csv_company)
            
            # Match if either is empty (skip) or if they are equal after cleaning
            if not target_clean or not csv_clean:
                continue
                
            if target_clean == csv_clean:
                matches.append(row)
            elif len(target_clean) > 3 and target_clean in csv_clean:
                matches.append(row)
            elif len(csv_clean) > 3 and csv_clean in target_clean:
                matches.append(row)
                
    print(f"Target: '{target_name}' (cleaned: '{target_clean}')")
    print(f"Matches found: {len(matches)}")
    for m in matches[:5]:
        print(f"  - {m['Name']} ({m['Email']}) at {m['Company']} [{m['Title']}]")
    print("-" * 50)

if __name__ == "__main__":
    test_match("SourceFuse")
    test_match("Estuate")
    test_match("Windmill")
    test_match("Perennial Systems")
