#!/usr/bin/env python
"""Check QA team member emails"""

from app.models.teams import TEAMS_STRUCTURE

qa = TEAMS_STRUCTURE['QA']
print("QA Team Members:")
print(f"Lead: {qa.get('lead')} ({qa.get('lead_email')})")
print(f"\nMembers ({len(qa['members'])}):")
for m in qa['members']:
    print(f"  - {m['name']:30s} {m['email']}")

# Now check trace email
trace_email = "Kiran.Ummenthala@cloudfuze.com"
print(f"\nTrace Email: {trace_email}")

# Check direct match
for m in qa['members']:
    if m['email'].lower() == trace_email.lower():
        print(f"MATCH FOUND: {m['name']}")
        break
else:
    print("NO DIRECT MATCH in emails")
    
# Check partial match
print("\nSearching for 'Kiran' in QA team:")
for m in qa['members']:
    if 'kiran' in m['email'].lower() or 'kiran' in m['name'].lower():
        print(f"  - {m['name']:30s} {m['email']}")

