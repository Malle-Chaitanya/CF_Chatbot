#!/usr/bin/env python3
"""
Script to identify which team member emails are NOT being traced in Langfuse.

This helps diagnose:
1. Missing emails in TEAMS_STRUCTURE
2. Emails with different formats in traces vs config
3. Newly added teams with no traces
4. Duplicates across teams
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.teams import (
    validate_team_emails, 
    get_all_team_members_emails,
    get_all_email_to_team_mapping,
    TEAMS_STRUCTURE
)


def check_email_structure():
    """Check the email configuration in TEAMS_STRUCTURE."""
    print("=" * 80)
    print("TEAM EMAIL CONFIGURATION CHECK")
    print("=" * 80)
    
    diagnostics = validate_team_emails()
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total Teams: {diagnostics['total_teams']}")
    print(f"  Total Members: {diagnostics['total_members']}")
    print(f"  Total Leads: {diagnostics['total_leads']}")
    print(f"  Total Unique Emails: {diagnostics['email_count']}")
    
    # Check for issues
    if diagnostics['empty_emails']:
        print(f"\n⚠️  EMPTY EMAILS FOUND ({len(diagnostics['empty_emails'])}):")
        for item in diagnostics['empty_emails'][:5]:
            print(f"   - Team: {item['team']}, Type: {item['type']}, Name: {item.get('name', 'N/A')}")
        if len(diagnostics['empty_emails']) > 5:
            print(f"   ... and {len(diagnostics['empty_emails']) - 5} more")
    
    if diagnostics['duplicate_emails']:
        print(f"\n⚠️  DUPLICATE EMAILS ({len(diagnostics['duplicate_emails'])}):")
        for email, teams in list(diagnostics['duplicate_emails'].items())[:5]:
            print(f"   - {email}: {', '.join(teams)}")
        if len(diagnostics['duplicate_emails']) > 5:
            print(f"   ... and {len(diagnostics['duplicate_emails']) - 5} more")
    
    if diagnostics['teams_with_no_members']:
        print(f"\n⚠️  TEAMS WITH NO MEMBERS ({len(diagnostics['teams_with_no_members'])}):")
        for team in diagnostics['teams_with_no_members']:
            print(f"   - {team}")
    
    return diagnostics


def check_email_coverage():
    """Check email-to-team mapping coverage."""
    print("\n" + "=" * 80)
    print("EMAIL COVERAGE ANALYSIS")
    print("=" * 80)
    
    email_map = get_all_email_to_team_mapping()
    team_emails = get_all_team_members_emails()
    
    print(f"\n📊 EMAIL MAPPING:")
    print(f"  Unique Emails in Map: {len(email_map)}")
    print(f"  Total Team Entries: {sum(len(v) for v in team_emails.values())}")
    
    # Check each team
    print(f"\n📋 EMAILS BY TEAM:")
    for team_name in sorted(TEAMS_STRUCTURE.keys()):
        team_info = TEAMS_STRUCTURE[team_name]
        email_count = 0
        
        # Count lead
        if team_info.get("lead_email"):
            email_count += 1
        
        # Count members
        email_count += len(team_info.get("members", []))
        
        print(f"  {team_name}: {email_count} emails")


def suggest_fixes():
    """Suggest fixes for identified issues."""
    print("\n" + "=" * 80)
    print("TROUBLESHOOTING SUGGESTIONS")
    print("=" * 80)
    
    diagnostics = validate_team_emails()
    
    issues = []
    
    if diagnostics['empty_emails']:
        issues.append("✗ Empty emails found - Review TEAMS_STRUCTURE for null/empty email values")
    
    if diagnostics['duplicate_emails']:
        issues.append("✗ Duplicate emails across teams - Assign each person to ONE team")
    
    if diagnostics['teams_with_no_members']:
        issues.append("✗ Teams with no members - Either add members or remove empty teams")
    
    # Check if emails are in correct format
    email_map = get_all_email_to_team_mapping()
    cloudfuze_count = sum(1 for e in email_map.keys() if "@cloudfuze.com" in e)
    if cloudfuze_count < len(email_map) * 0.9:
        issues.append("⚠ Most emails should be @cloudfuze.com domain")
    
    if not issues:
        print("\n✅ NO ISSUES FOUND - Email structure looks good!")
    else:
        print("\n🔧 ISSUES TO FIX:")
        for issue in issues:
            print(f"  {issue}")


def get_trace_analysis_help():
    """Provide help for analyzing missing traces."""
    print("\n" + "=" * 80)
    print("DEBUGGING MISSING TRACES")
    print("=" * 80)
    
    print("""
When emails are not appearing in team analytics:

1️⃣  CHECK EMAIL FORMAT
   - Traces use metadata.user_email field
   - Compare format: 'First.Last@cloudfuze.com' vs config
   - Common issues: Case sensitivity, whitespace, typos

2️⃣  CHECK TEAM ASSIGNMENT
   - Email must exist in TEAMS_STRUCTURE
   - Run this script to validate: python scripts/check_email_tracing.py
   - Use diagnostics endpoint: GET /analytics/langfuse/teams/email-diagnostics

3️⃣  NEWLY ADDED TEAMS
   - After adding team to TEAMS_STRUCTURE, old traces won't be re-processed
   - Only NEW traces after team addition will be captured
   - To backfill: Export historical traces with matching emails

4️⃣  COMMON FIXES
   - Add missing emails to correct team in TEAMS_STRUCTURE
   - Fix email format mismatches
   - For new teams: Wait for users to ask questions, or test manually

5️⃣  CHECK BACKEND LOGS
   - Look for "[DEBUG] Trace with unassigned email:" messages
   - These show emails that don't match any team
   - Add these emails to appropriate team in TEAMS_STRUCTURE
    """)


if __name__ == "__main__":
    print("\n🔍 TEAM EMAIL TRACING DIAGNOSTICS\n")
    
    # Run all checks
    check_email_structure()
    check_email_coverage()
    suggest_fixes()
    get_trace_analysis_help()
    
    print("\n" + "=" * 80)
    print("For API diagnostics, visit: GET /analytics/langfuse/teams/email-diagnostics")
    print("=" * 80 + "\n")






