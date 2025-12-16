# -*- coding: utf-8 -*-
"""
Team structure and member mapping for CloudFuze analytics.
"""

from typing import List, Dict

# Define all teams with their leads and members
TEAMS_STRUCTURE = {
    "Content": {
        "lead": "Santosh Chintalapelli",
        "lead_email": "santosh.chintalapelli@cloudfuze.com",
        "members": [
            {"name": "Akhila", "email": "akhila@cloudfuze.com"},
            {"name": "Mayank Jain", "email": "mayank.jain@cloudfuze.com"},
            {"name": "Amuda Shivakumar", "email": "amuda.shivakumar@cloudfuze.com"},
            {"name": "Praveen Vancharla", "email": "praveen.vancharla@cloudfuze.com"},
            {"name": "Naved", "email": "naved@cloudfuze.com"},
            {"name": "Srinu", "email": "srinu@cloudfuze.com"},
            {"name": "Ravi Srivatsava", "email": "ravi.srivatsava@cloudfuze.com"},
            {"name": "Vishal", "email": "vishal@cloudfuze.com"},
            {"name": "Jaswanth", "email": "jaswanth@cloudfuze.com"},
        ],
        "color": "#3B82F6",  # Blue
        "description": "Organization-Wide Teams"
    },
    "Messaging & Email": {
        "lead": "Ankit Mishra",
        "lead_email": "ankit.mishra@cloudfuze.com",
        "members": [
            {"name": "Bhagya", "email": "bhagya@cloudfuze.com"},
            {"name": "Abhinandan Kumar", "email": "abhinandan.kumar@cloudfuze.com"},
            {"name": "Shivam", "email": "shivam@cloudfuze.com"},
            {"name": "Pragati", "email": "pragati@cloudfuze.com"},
            {"name": "Sai Raj", "email": "sai.raj@cloudfuze.com"},
            {"name": "Anantha Lakshmi", "email": "anantha.lakshmi@cloudfuze.com"},
            {"name": "Vamsi", "email": "vamsi@cloudfuze.com"},
            {"name": "Hemadasu", "email": "hemadasu.kantam@cloudfuze.com"},
            {"name": "Akib", "email": "akib@cloudfuze.com"},
        ],
        "color": "#10B981",  # Green
        "description": "Messaging & Email"
    },
    "CF Manage": {
        "lead": "Ravi Achakka Chandra",
        "lead_email": "ravi.chandra@cloudfuze.com",
        "members": [
            {"name": "Suraj Kumar", "email": "suraj.kumar@cloudfuze.com"},
            {"name": "Roopa", "email": "roopa@cloudfuze.com"},
            {"name": "Phani", "email": "phani@cloudfuze.com"},
            {"name": "Prakash", "email": "prakash@cloudfuze.com"},
            {"name": "Giridhar", "email": "giridhar@cloudfuze.com"},
        ],
        "color": "#F59E0B",  # Amber
        "description": "CF Manage"
    },
    "QA": {
        "lead": "Kamal Basha",
        "lead_email": "kamal.basha@cloudfuze.com",
        "members": [
            {"name": "Soumya", "email": "soumya@cloudfuze.com"},
            {"name": "Soniya", "email": "soniya@cloudfuze.com"},
            {"name": "Asma", "email": "asma@cloudfuze.com"},
            {"name": "Kiran Ummenthala", "email": "kiran.ummenthala@cloudfuze.com"},
            {"name": "Bhavani Nimmala", "email": "bhavani.nimmala@cloudfuze.com"},
            {"name": "Ganesh R", "email": "ganesh.r@cloudfuze.com"},
            {"name": "Bhuvana", "email": "bhuvana@cloudfuze.com"},
            {"name": "Ganesh G", "email": "ganesh.g@cloudfuze.com"},
            {"name": "Sadia", "email": "sadia@cloudfuze.com"},
            {"name": "Nagalakshmi", "email": "nagalakshmi.mangina@cloudfuze.com"},
        ],
        "color": "#EF4444",  # Red
        "description": "QA"
    },
    "Neutara Labs": {
        "lead": "Ravi Poli",
        "lead_email": "ravi.poli@cloudfuze.com",
        "members": [
            {"name": "Bharath", "email": "bharath.tummaganti@cloudfuze.com"},
            {"name": "Satya", "email": "satya@cloudfuze.com"},
            {"name": "Bhanu", "email": "bhanu.srikakulam@cloudfuze.com"},
            {"name": "Sruthi", "email": "sruthi@cloudfuze.com"},
            {"name": "Jyoshitha", "email": "jyoshitha@cloudfuze.com"},
            {"name": "Tharun", "email": "tharun.pothi@cloudfuze.com"},
            {"name": "Abhilasha", "email": "abhilasha.kandakatla@cloudfuze.com"},
            {"name": "Anush", "email": "anush.dasari@cloudfuze.com"},
        ],
        "color": "#8B5CF6",  # Purple
        "description": "Neutara Labs"
    },
    "Infra": {
        "lead": "Pavan Bhagavathula",
        "lead_email": "pavan.bhagavathula@cloudfuze.com",
        "members": [
            {"name": "Gururaj", "email": "gururaj@cloudfuze.com"},
            {"name": "Nagesh", "email": "nagesh@cloudfuze.com"},
            {"name": "Hymavathi", "email": "hymavathi@cloudfuze.com"},
            {"name": "Bala Ravi Teja", "email": "bala.ravi.teja@cloudfuze.com"},
            {"name": "Sravani Avagadda", "email": "sravani.avagadda@cloudfuze.com"},
        ],
        "color": "#EC4899",  # Pink
        "description": "Infra"
    },
    "Pre-Sales": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Nivas", "email": "nivas@cloudfuze.com"},
            {"name": "Sonali", "email": "sonali@cloudfuze.com"},
            {"name": "Vimalesh", "email": "vimalesh@cloudfuze.com"},
            {"name": "Vignesh", "email": "vignesh@cloudfuze.com"},
        ],
        "color": "#06B6D4",  # Cyan
        "description": "Pre-Sales"
    },
    "Sales Ops": {
        "lead": "Rahul Gowda",
        "lead_email": "rahul.gowda@cloudfuze.com",
        "members": [
            {"name": "Sakshi Priya", "email": "sakshi.priya@cloudfuze.com"},
            {"name": "Raya Durai", "email": "raya.durai@cloudfuze.com"},
            {"name": "Varsha", "email": "varsha@cloudfuze.com"},
            {"name": "Sanjana Khanapur", "email": "sanjana.khanapur@cloudfuze.com"},
        ],
        "color": "#14B8A6",  # Teal
        "description": "Sales Ops"
    },
}


def get_all_teams() -> Dict[str, dict]:
    """Get all teams."""
    return TEAMS_STRUCTURE


def get_team_by_name(team_name: str) -> dict:
    """Get a specific team by name."""
    return TEAMS_STRUCTURE.get(team_name)


def get_team_by_member_email(email: str) -> str:
    """Find which team a member belongs to by email."""
    email_lower = email.lower()
    
    for team_name, team_info in TEAMS_STRUCTURE.items():
        # Check if it's the lead
        if team_info.get("lead_email", "").lower() == email_lower:
            return team_name
        
        # Check if it's a member
        for member in team_info.get("members", []):
            if member.get("email", "").lower() == email_lower:
                return team_name
    
    return "Unassigned"


def get_all_team_members_emails() -> Dict[str, List[str]]:
    """Get all emails organized by team."""
    result = {}
    
    for team_name, team_info in TEAMS_STRUCTURE.items():
        emails = []
        
        # Add lead
        if team_info.get("lead_email"):
            emails.append(team_info["lead_email"].lower())
        
        # Add members
        for member in team_info.get("members", []):
            emails.append(member.get("email", "").lower())
        
        result[team_name] = emails
    
    return result


def get_team_member_count(team_name: str) -> int:
    """Get total members in a team (including lead)."""
    team = TEAMS_STRUCTURE.get(team_name)
    if not team:
        return 0
    
    count = len(team.get("members", []))
    if team.get("lead_email"):
        count += 1
    
    return count


def get_team_color(team_name: str) -> str:
    """Get the color code for a team."""
    team = TEAMS_STRUCTURE.get(team_name)
    return team.get("color", "#6B7280") if team else "#6B7280"


def normalize_email(email: str) -> str:
    """Normalize email for matching."""
    return email.lower().strip()


def get_team_by_member_name(member_name: str) -> str:
    """Find which team a member belongs to by name."""
    if not member_name:
        return "Unassigned"
    
    member_lower = member_name.lower().strip()
    
    for team_name, team_info in TEAMS_STRUCTURE.items():
        # Check if it's the lead
        if team_info.get("lead", "").lower() == member_lower:
            return team_name
        
        # Check if it's a member
        for member in team_info.get("members", []):
            if member.get("name", "").lower() == member_lower:
                return team_name
    
    return "Unassigned"


# Legacy format support for backward compatibility
TEAMS = {}
for team_name, team_info in TEAMS_STRUCTURE.items():
    TEAMS[team_name] = {
        "Lead": team_info.get("lead"),
        "Members": [m.get("name") for m in team_info.get("members", [])]
    }


def get_team_for_member(member_name: str) -> str:
    """Legacy function - find team for member by name."""
    return get_team_by_member_name(member_name)

