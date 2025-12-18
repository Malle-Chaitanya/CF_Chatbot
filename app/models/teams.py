# -*- coding: utf-8 -*-
"""
Team structure and member mapping for CloudFuze analytics.
"""

from typing import List, Dict, Any

# Define all teams with their leads and members
TEAMS_STRUCTURE = {
    "Content": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Santosh Chintalapelli", "email": "santosh@cloudfuze.com"},
            {"name": "Akhila Aenkoju", "email": "akhila.aenkoju@cloudfuze.com"},
            {"name": "Shaikh Adnan", "email": "adnan@cloudfuze.com"},
            {"name": "Mayank Jain", "email": "mayank@cloudfuze.com"},
            {"name": "Amuda Shivakumar", "email": "shiva.amuda@cloudfuze.com"},
            {"name": "Praveen Vancharla", "email": "praveen.v@cloudfuze.com"},
            {"name": "Naved", "email": "naved.osama@cloudfuze.com"},
            {"name": "Srinu G", "email": "srinu.gudimitla@cloudfuze.com"},
            {"name": "Ravi Srivastava", "email": "ravi.srivastava@cloudfuze.com"},
            {"name": "Vishal Kumar", "email": "vishal.kumar@cloudfuze.com"},
            {"name": "Jaswanth Adari", "email": "jaswanth.adari@cloudfuze.com"},
        ],
        "color": "#3B82F6",  # Blue
        "description": "Content Development"
    },
    "M7 (Content)": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Adi Nandyala", "email": "adi.nandyala@cloudfuze.com"},
            {"name": "Pranavi", "email": "pranavi@cloudfuze.com"},
        ],
        "color": "#3B82F6",  # Blue
        "description": "Content Team - M7"
    },
    "Messaging & Email": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Ankit Mishra", "email": "ankit@cloudfuze.com"},
            {"name": "Bhagya", "email": "bhagyashri.deokar@cloudfuze.com"},
            {"name": "Abhinandan Kumar", "email": "abhinandan.kumar@cloudfuze.com"},
            {"name": "Shivam Singh", "email": "shivam.singh@cloudfuze.com"},
            {"name": "Pragati Pandey", "email": "pragati.pandey@cloudfuze.com"},
            {"name": "Sai Raj", "email": "sairaj.kanigicharla@cloudfuze.com"},
            {"name": "Anantha Lakshmi", "email": "lakshmi.adabala@cloudfuze.com"},
            {"name": "Vamsi Malla", "email": "vamsi.malla@cloudfuze.com"},
            {"name": "Hemadasu Kantam", "email": "hemadasu.kantam@cloudfuze.com"},
            {"name": "Akib Mohd", "email": "akib.mohd@cloudfuze.com"},
        ],
        "color": "#10B981",  # Green
        "description": "Messaging & Email"
    },
    "CF Manage": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Ravi Achakka Chandra", "email": "ravic@cloudfuze.com"},
            {"name": "Suraj Kumar", "email": "suraj.kumar@cloudfuze.com"},
            {"name": "Roopa Yerrabothu", "email": "roopa.yerrabothu@cloudfuze.com"},
            {"name": "Phani R", "email": "phani.ryali@cloudfuze.com"},
            {"name": "Prakash S", "email": "prakash.singampalli@cloudfuze.com"},
            {"name": "Giridhar Kolavasi", "email": "giridhar.kolavasi@cloudfuze.com"},
        ],
        "color": "#F59E0B",  # Amber
        "description": "CF Manage"
    },
    "QA": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Kamal Basha", "email": "kamal.basha@cloudfuze.com"},
            {"name": "Soumya G", "email": "soumya.gande@cloudfuze.com"},
            {"name": "Soniya P", "email": "soniya.paladugula@cloudfuze.com"},
            {"name": "Asma Karim", "email": "asma.karim@cloudfuze.com"},
            {"name": "Kiran Ummenthala", "email": "kiran.ummenthala@cloudfuze.com"},
            {"name": "Bhuvana Mosra", "email": "bhuvana.mosra@cloudfuze.com"},
            {"name": "Ganesh Guda", "email": "ganesh.guda@cloudfuze.com"},
            {"name": "Sadia Shaik", "email": "sadia.shaik@cloudfuze.com"},
            {"name": "Nagalakshmi Mangina", "email": "nagalakshmi.mangina@cloudfuze.com"},
        ],
        "color": "#EF4444",  # Red
        "description": "QA"
    },
    "Neutara Labs": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Ravi Poli", "email": "ravi.poli@cloudfuze.com"},
            {"name": "Bharath Tummaganti", "email": "bharath.tummaganti@cloudfuze.com"},
            {"name": "Satya Pinniti", "email": "satya.pinniti@cloudfuze.com"},
            {"name": "Bhanu Srikakulam", "email": "bhanu.srikakulam@cloudfuze.com"},
            {"name": "Sruthi Chimata", "email": "sruthi.chimata@cloudfuze.com"},
            {"name": "Jyoshitha Dhannapaneni", "email": "jyoshitha.dhannapaneni@cloudfuze.com"},
            {"name": "Tharun P", "email": "Tharun.Pothi@cloudfuze.com"},
            {"name": "Abhilasha K", "email": "Abhilasha.Kandakatla@cloudfuze.com"},
            {"name": "Anush Dasari", "email": "anush.dasari@cloudfuze.com"},
            {"name": "Suditya Nimmala", "email": "suditya.nimmala@cloudfuze.com"},
            {"name": "laxman kadari", "email": "laxman.kadari@cloudfuze.com"},
            {"name": "chaitanya malle", "email": "chaitanya.malle@cloudfuze.com"},
        ],
        "color": "#8B5CF6",  # Purple
        "description": "Neutara Labs"
    },
    "Infra": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Pavan Bhagavathula", "email": "pavan@cloudfuze.com"},
            {"name": "Gururaj Bhimrao", "email": "gururaj.bhimrao@cloudfuze.com"},
            {"name": "Nageshkumar Mhetre", "email": "nageshkumar.mhetre@cloudfuze.com"},
            {"name": "Hymavathi Irla", "email": "hymavathi@cloudfuze.com"},
            {"name": "Bala Raviteja", "email": "bala.raviteja@cloudfuze.com"},
            {"name": "Sravani Avagadda", "email": "avagadda.sravani@cloudfuze.com"},
        ],
        "color": "#EC4899",  # Pink
        "description": "Infra"
    },
    "Marketing": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Arun Jyothi", "email": "jyothi@cloudfuze.com"},
            {"name": "Hari Rowlo", "email": "hari.rowlo@cloudfuze.com"},
            {"name": "Srikanth Tammali", "email": "srikanth.tammali@cloudfuze.com"},
            {"name": "Venkata Rahul", "email": "venkata.rahul@cloudfuze.com"},
            {"name": "Nirosh Reddy", "email": "nirosh.reddy@cloudfuze.com"},
            {"name": "Ashu Tiwary", "email": "ashu.tiwary@cloudfuze.com"},
            {"name": "Aayushi", "email": "aayushi@cloudfuze.com"},
            {"name": "Bhavani Asok", "email": "bhavani.asok@cloudfuze.com"},
            {"name": "Pankaj Rai", "email": "pankaj.rai@cloudfuze.com"},
            {"name": "Rashmi Ramesh", "email": "rashmi.ramesh@cloudfuze.com"},
            {"name": "Narayana Reddy", "email": "narayana.reddy@cloudfuze.com"},
        ],
        "color": "#06B6D4",  # Cyan
        "description": "Marketing"
    },
    "Pre-Sales": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Nivas", "email": "nivas@cloudfuze.com"},
            {"name": "Sonali Lunia", "email": "sonali.lunia@cloudfuze.com"},
            {"name": "Vimalesh T", "email": "vimalesh.t@cloudfuze.com"},
        ],
        "color": "#14B8A6",  # Teal
        "description": "Pre-Sales"
    },
    "M1": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Nikhil Patel", "email": "nikhil@cloudfuze.com"},
            {"name": "Arshiya Syed", "email": "arshiya.syed@cloudfuze.com"},
            {"name": "Harsha Thakre", "email": "harsha.thakre@cloudfuze.com"},
            {"name": "Mallesh Pothina", "email": "mallesh.pothina@cloudfuze.com"},
            {"name": "Harshith Kaduluri", "email": "harshith.kaduluri@cloudfuze.com"},
        ],
        "color": "#A78BFA",  # Light Purple
        "description": "M1"
    },
    "M2": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Maheswari Aram", "email": "maheswari.aram@cloudfuze.com"},
            {"name": "Tejaswini Sivakumaram", "email": "sivakumaram.tejaswini@cloudfuze.com"},
            {"name": "Ishwar Yadav", "email": "ishwar.yadav@cloudfuze.com"},
            {"name": "Siva Kota", "email": "siva.kota@cloudfuze.com"},
            {"name": "Vineetha Yenti", "email": "vineetha.yenti@cloudfuze.com"},
            {"name": "Ravi Hemanth", "email": "ravi.hemanth@cloudfuze.com"},
        ],
        "color": "#F97316",  # Orange
        "description": "M2"
    },
    "M3": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Lakshmi Prasanna", "email": "lakshmi.prasanna@cloudfuze.com"},
            {"name": "Meena Lakshmi Triveni", "email": "meena.lakshmi@cloudfuze.com"},
            {"name": "Swaroop", "email": "swaroop@cloudfuze.com"},
            {"name": "Lakshma Reddy", "email": "lakshma.reddy@cloudfuze.com"},
            {"name": "Davidraj Dumpala", "email": "davidraj.dumpala@cloudfuze.com"},
            {"name": "Srinadh Pala", "email": "srinadh.pala@cloudfuze.com"},
        ],
        "color": "#06C6D4",  # Cyan
        "description": "M3"
    },
    "M4": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Neelima Krotta", "email": "neelima.krotta@cloudfuze.com"},
            {"name": "Nandini Tirumalasetti", "email": "nandini.tirumalasetti@cloudfuze.com"},
            {"name": "Manisha Verma", "email": "manisha.verma@cloudfuze.com"},
            {"name": "Sriram Ramakrishnan", "email": "sriram.ramakrishnan@cloudfuze.com"},
            {"name": "Ganesh Kondameedi", "email": "ganesh.kondameedi@cloudfuze.com"},
            {"name": "Vishnu Gundu", "email": "vishnu.gundu@cloudfuze.com"},
        ],
        "color": "#7C3AED",  # Violet
        "description": "M4"
    },
    "M4 (M+E)": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Ajay Singh", "email": "ajay.singh@cloudfuze.com"},
            {"name": "Aanchal Tyagi", "email": "aanchal.tyagi@cloudfuze.com"},
            {"name": "Akshay Raina", "email": "akshay.raina@cloudfuze.com"},
            {"name": "Dipali", "email": "dipali@cloudfuze.com"},
            {"name": "Habeebunnisa Begum", "email": "habeebunnisa.begum@cloudfuze.com"},
        ],
        "color": "#7C3AED",  # Violet
        "description": "M4 (Messaging + Email)"
    },
    "M6 (M+E)": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Abhishek Sakala", "email": "abhishek.sakala@cloudfuze.com"},
            {"name": "Pallavi K", "email": "pallavi.kosuvaripalli@cloudfuze.com"},
            {"name": "Arun Kandula", "email": "arun@cloudfuze.com"},
            {"name": "Manoj Bathula", "email": "manoj.bathula@cloudfuze.com"},
            {"name": "Sai Pedaparti", "email": "sai.pedaparti@cloudfuze.com"},
        ],
        "color": "#10B981",  # Green
        "description": "M6 (Messaging + Email)"
    },
    "M5": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Abhishikth Yenugula", "email": "abhishikth.yenugula@cloudfuze.com"},
            {"name": "Ranadeep Muddam", "email": "ranadeep.muddam@cloudfuze.com"},
            {"name": "Amulya Anapuram", "email": "amulya.anapuram@cloudfuze.com"},
            {"name": "Vijendar Burgula", "email": "vijendar.burgula@cloudfuze.com"},
        ],
        "color": "#EC4899",  # Pink
        "description": "M5"
    },
    "BD": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Karthik Brahmakal", "email": "karthik.brahmakal@cloudfuze.com"},
            {"name": "Pruthvi Raygol", "email": "pruthvi.raygol@cloudfuze.com"},
            {"name": "Vijay Kumar", "email": "vijay.kumar@cloudfuze.com"},
            {"name": "Craig Fernandez", "email": "craig.fernandez@cloudfuze.com"},
            {"name": "Rebecca Valentina", "email": "rebecca.valentina@cloudfuze.com"},
            {"name": "Sushmitha Esther", "email": "sushmitha.esther@cloudfuze.com"},
            {"name": "Hrushikesh Sholapure", "email": "hrushikesh.sholapure@cloudfuze.com"},
            {"name": "Preethi John", "email": "preethi.john@cloudfuze.com"},
            {"name": "Kevin Anto", "email": "kevin.anto@cloudfuze.com"},
        ],
        "color": "#06B6D4",  # Cyan
        "description": "Business Development"
    },
    "Sales Ops": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Rahul Gowda", "email": "rahul.gowda@cloudfuze.com"},
            {"name": "Sakshi Priya", "email": "sakshi.priya@cloudfuze.com"},
            {"name": "Raya Durai", "email": "raya.durai@cloudfuze.com"},
            {"name": "Varsha Nallashami", "email": "varsha.nallashami@cloudfuze.com"},
            {"name": "Sanjana Khanapur", "email": "sanjana.khanapur@cloudfuze.com"},
        ],
        "color": "#8B5CF6",  # Purple
        "description": "Sales Operations"
    },
    "Sales [SMB]": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Chitradip Saha", "email": "chitradip.saha@cloudfuze.com"},
            {"name": "Royston Aden", "email": "Royston.Aden@cloudfuze.com"},
            {"name": "Deepak R J", "email": "Deepak.Rj@cloudfuze.com"},
            {"name": "Vicky Cariappa", "email": "vicky.cariappa@cloudfuze.com"},
            {"name": "Yogesh Vig", "email": "Yogesh.vig@cloudfuze.com"},
            {"name": "Kartik Kashyap", "email": "Kartik.Kashyap@cloudfuze.com"},
            {"name": "Kritika Gupta", "email": "Kritika.Gupta@cloudfuze.com"},
        ],
        "color": "#F59E0B",  # Amber
        "description": "Sales [SMB]"
    },
    "Sales [ENT]": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Anthony Raymond", "email": "anthony@cloudfuze.com"},
            {"name": "Lukas Bohlander", "email": "lukas.bohlander@cloudfuze.com"},
            {"name": "Charles Stiltner", "email": "charles.stiltner@cloudfuze.com"},
        ],
        "color": "#EF4444",  # Red
        "description": "Sales [Enterprise]"
    },
    "Sales [AM]": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Lawrence Lewis", "email": "lawrence.lewis@cloudfuze.com"},
            {"name": "Nikitha Shekher", "email": "nikita.shekher@cloudfuze.com"},
            {"name": "Joy Prakash", "email": "joy.prakash@cloudfuze.com"},
            {"name": "Jalsha Chakma", "email": "jalsha.chakma@cloudfuze.com"},
            {"name": "Vivin Joseph", "email": "vivin.joseph@cloudfuze.com"},
            {"name": "Bhima Raju", "email": "bhimaraju.patsamatla@cloudfuze.com"},
            {"name": "Garima Patel", "email": "garima.patel@cloudfuze.com"},
        ],
        "color": "#10B981",  # Green
        "description": "Sales [Account Management]"
    },
    "HR": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Gopi Krishna", "email": "gopi@cloudfuze.com"},
            {"name": "Vipra Mishra", "email": "vipra.mishra@cloudfuze.com"},
            {"name": "Sujana Manapuram", "email": "sujana.manapuram@cloudfuze.com"},
            {"name": "Madhuri Yeleswarapu", "email": "madhuri.yeleswarapu@cloudfuze.com"},
            {"name": "Pooja Parmar", "email": "pooja.parmar@cloudfuze.com"},
        ],
        "color": "#3B82F6",  # Blue
        "description": "Human Resources"
    },
    "Manager": {
        "lead": None,
        "lead_email": None,
        "members": [
            {"name": "Raghavan Krishnan", "email": "raghavan.krishnan@cloudfuze.com"},
        ],
        "color": "#64748B",  # Slate Gray
        "description": "Manager"
    },
}


def get_all_teams() -> Dict[str, dict]:
    """Get all teams."""
    return TEAMS_STRUCTURE


def get_team_by_name(team_name: str) -> dict:
    """Get a specific team by name."""
    return TEAMS_STRUCTURE.get(team_name)


def get_team_by_member_email(email: str) -> str:
    """Find which team a member belongs to by email.
    
    This function handles:
    - Direct email matches (exact email in team)
    - Case-insensitive matching
    - Whitespace normalization
    - Returns "Unassigned" if not found
    """
    if not email:
        return "Unassigned"
    
    email_lower = str(email).lower().strip()
    
    # First pass: Direct email match (most efficient)
    for team_name, team_info in TEAMS_STRUCTURE.items():
        # Check if it's the lead
        lead_email = team_info.get("lead_email")
        if lead_email and str(lead_email).lower().strip() == email_lower:
            return team_name
        
        # Check if it's a member
        for member in team_info.get("members", []):
            member_email = member.get("email", "").lower().strip()
            if member_email == email_lower:
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


# Email exclusion list for analytics - MANAGED VIA FRONTEND TOGGLE
# This is now handled by frontend admin controls, not hardcoded here
ANALYTICS_EXCLUSION_LIST = set()  # Empty by default - all emails included


def is_email_excluded(email: str, exclusion_list: set = None) -> bool:
    """
    Check if email should be excluded from analytics.
    Now accepts dynamic exclusion list from frontend.
    
    Args:
        email: Email to check
        exclusion_list: Optional set of emails to exclude (from frontend)
    
    Returns:
        True if email should be excluded, False otherwise
    """
    if not email or not exclusion_list:
        return False
    return email.lower().strip() in exclusion_list


def get_exclusion_list() -> set:
    """Get the list of excluded emails."""
    return ANALYTICS_EXCLUSION_LIST.copy()


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


def get_all_email_to_team_mapping() -> Dict[str, str]:
    """Get a flat mapping of all emails to their teams.
    
    This creates a dictionary for fast O(1) lookups instead of O(n) iteration.
    Useful for batch processing and analytics.
    
    Returns:
    {
        "email@domain.com": "Team Name",
        ...
    }
    """
    mapping = {}
    
    for team_name, team_info in TEAMS_STRUCTURE.items():
        # Add lead
        if team_info.get("lead_email"):
            email_lower = team_info["lead_email"].lower().strip()
            if email_lower:
                mapping[email_lower] = team_name
        
        # Add members
        for member in team_info.get("members", []):
            email = member.get("email", "").lower().strip()
            if email:
                mapping[email] = team_name
    
    return mapping


def validate_team_emails() -> Dict[str, Any]:
    """Validate team email structure and return diagnostic information.
    
    This function checks:
    - Empty emails
    - Duplicate emails across teams
    - Invalid email format
    - Missing team members
    
    Returns diagnostic data for debugging.
    """
    diagnostics = {
        "total_teams": len(TEAMS_STRUCTURE),
        "total_members": 0,
        "total_leads": 0,
        "empty_emails": [],
        "duplicate_emails": {},
        "invalid_emails": [],
        "teams_with_no_members": [],
        "email_count": 0
    }
    
    email_to_teams = {}  # Track which teams have each email
    
    for team_name, team_info in TEAMS_STRUCTURE.items():
        # Check lead
        if team_info.get("lead_email"):
            lead_email = team_info.get("lead_email", "").lower().strip()
            diagnostics["total_leads"] += 1
            
            if not lead_email:
                diagnostics["empty_emails"].append({
                    "team": team_name,
                    "type": "lead",
                    "value": team_info.get("lead_email")
                })
            else:
                diagnostics["email_count"] += 1
                if lead_email not in email_to_teams:
                    email_to_teams[lead_email] = []
                email_to_teams[lead_email].append(team_name)
        
        # Check members
        members = team_info.get("members", [])
        diagnostics["total_members"] += len(members)
        
        if not members:
            diagnostics["teams_with_no_members"].append(team_name)
        
        for member in members:
            member_email = member.get("email", "").lower().strip()
            
            if not member_email:
                diagnostics["empty_emails"].append({
                    "team": team_name,
                    "type": "member",
                    "name": member.get("name"),
                    "value": member.get("email")
                })
            else:
                diagnostics["email_count"] += 1
                if member_email not in email_to_teams:
                    email_to_teams[member_email] = []
                email_to_teams[member_email].append(team_name)
    
    # Find duplicates (same email in multiple teams)
    for email, teams in email_to_teams.items():
        if len(teams) > 1:
            diagnostics["duplicate_emails"][email] = teams
    
    return diagnostics
