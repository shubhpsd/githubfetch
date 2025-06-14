#!/usr/bin/env python3

#######################################################
#  GitHub Fetch - Display GitHub profiles in terminal
#  Created by: Shubham Prasad
#  This project helped me learn:
#  - API Integration with GitHub
#  - Terminal UI techniques
#  - Python package management
#  - User configuration handling
#######################################################

# Core Python libraries
import os          # For environment variables and terminal size
import sys         # For command-line arguments and stdout manipulation
import json        # For token storage
import shutil      # For checking if commands exist
import getpass     # For secure password/token input
import tempfile    # For temporary avatar storage
import textwrap    # For formatting text output nicely
import pathlib     # For cross-platform path handling
import subprocess  # For executing external commands like imgcat
import datetime    # For date handling in contribution heatmap
import calendar    # For month names in contribution heatmap

# Third-party libraries (need to be installed)
import requests    # For making HTTP requests to GitHub API
from PIL import Image  # For image processing
from io import BytesIO  # For handling image data without files

##### -> UTILITY CLASSES AND FUNCTIONS

class Color:
    """
    A utility class for adding colors to terminal output.
    Usage:
        print(color.color('green', 'This text will be green'))
    """
    def __init__(self):
        # ANSI color codes for different colors
        self.red = "\x1b[38;5;1m"
        self.green = "\x1b[38;5;149m"
        self.yellow = "\x1b[38;5;11m"
        self.light_blue = "\x1b[38;5;45m"
        self.light_red = "\x1b[38;5;9m"
        self.orange = "\x1b[38;5;208m"
        self.blue = "\x1b[38;5;21m"
        self.reset = "\x1b[00m"  # This resets the color back to default
        
    def color(self, color_name, text):
        # Apply color to text and reset afterward
        return f"{getattr(self, color_name, self.reset)}{text}{self.reset}"

# Create a global color instance for use throughout the app
color = Color()

def create_hyperlink(url, text):
    # Creates a clickable hyperlink in compatible terminals
    return f"\x1b]8;;{url}\a{text}\x1b]8;;\a"


##### -> TOKEN AND CONFIG MANAGEMENT

def get_config_dir():
    # Creates and returns the configuration directory (.config/githubfetch)
    config_dir = os.path.join(pathlib.Path.home(), ".config", "githubfetch")
    os.makedirs(config_dir, exist_ok=True)  # Create directory if it doesn't exist
    return config_dir

def get_token_path():
    # Returns the path to the token storage file
    return os.path.join(get_config_dir(), "token.json")

def load_token():
    # Loads the GitHub token from the config file
    token_path = get_token_path()
    if os.path.exists(token_path):
        try:
            with open(token_path, "r") as f:
                data = json.load(f)
                return data.get("github_token")
        except Exception:
            # Handle any errors (corrupted file, etc.)
            return None
    return None

def save_token(token):
    # Saves the GitHub token to a file with secure permissions
    token_path = get_token_path()
    with open(token_path, "w") as f:
        json.dump({"github_token": token}, f)
    
    # Set file permissions to be readable only by the user (important for security!)
    os.chmod(token_path, 0o600)

def validate_github_token(token):
    # Tests if a GitHub token is valid by making an API request
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # The /user endpoint is perfect for validation as it requires authentication
        # and returns information about the authenticated user
        response = requests.get("https://api.github.com/user", headers=headers)
        
        if response.status_code == 200:
            print(f"{color.color('green', '✓')} Token validated successfully!")
            user_data = response.json()
            username = user_data.get('login')
            
            # Check for needed scopes
            scopes = response.headers.get('X-OAuth-Scopes', '')
            print(f"{color.color('yellow', 'Token scopes:')} {color.color('reset', scopes or 'None')}")
            
            if 'read:user' not in scopes and 'user' not in scopes:
                print(f"{color.color('yellow', 'Warning:')} Token may not have the required 'read:user' scope.")
                print(f"{color.color('yellow', 'Some features like contribution heatmaps may not work properly.')}")
            
            print(f"{color.color('green', 'Welcome,')} {color.color('yellow', username)}!")
            return True
        elif response.status_code == 401:
            # 401 means unauthorized/failure
            print(f"{color.color('red', '✗')} Invalid token: Authentication failed.")
            return False
        else:
            # Other status codes might indicate rate limiting or 
            # repeated requests or other issues so try again later
            print(f"{color.color('red', '✗')} API request failed: {response.status_code}")
            return False
    except Exception as e:
        # Handle network errors, etc.
        print(f"{color.color('red', f'Error validating token: {str(e)}')}")
        return False


        
def setup_github_token():
    """Interactive setup for GitHub token."""
    print(f"{color.color('green', '┌───────────────────────────────────────────┐')}")
    print(f"{color.color('green', '│           GitHub Token Setup              │')}")
    print(f"{color.color('green', '└───────────────────────────────────────────┘')}")
    print(f"\n{color.color('yellow', 'GitHubFetch needs a GitHub personal access token to:')}")
    print(f"  • {color.color('reset', 'View your pinned repositories')}")
    print(f"  • {color.color('reset', 'Access contribution data for heatmaps')}")
    print(f"  • {color.color('reset', 'Avoid GitHub API rate limits')}")
    print(f"  • {color.color('reset', 'Access complete profile information')}")
    
    print(f"\n{color.color('green', 'How to create a token:')}")
    print(f"1. Visit {create_hyperlink('https://github.com/settings/tokens', color.color('light_blue', 'github.com/settings/tokens'))}")
    print(f"2. Click \"{color.color('yellow', 'Generate new token')}\" → \"{color.color('yellow', 'Generate new token (classic)')}\"")
    print(f"3. Enter a note like \"{color.color('reset', 'GitHubFetch')}\"")
    print(f"4. Select the \"{color.color('yellow', 'read:user')}\" scope (under \"user\")")
    print(f"   {color.color('yellow', '(This scope is REQUIRED for heatmap and pinned repositories!)')}")
    print(f"5. Click \"{color.color('green', 'Generate token')}\" at the bottom")
    print(f"6. Copy the token and paste it below")
    
    print(f"\n{color.color('yellow', 'Enter your GitHub token')} {color.color('reset', '(input is hidden for security)')}{color.color('yellow', ':')}")
    token = getpass.getpass("")
    
    if not token.strip():
        print(f"{color.color('red', 'No token provided. Some features may not work properly.')}")
        return None
    
    # Validate token format
    if not token.startswith(("ghp_", "github_pat_")):
        print(f"{color.color('yellow', 'Warning: Token format looks unusual. Tokens usually start with ghp_ or github_pat_.')}")
        proceed = input(f"{color.color('green', 'Continue anyway? [y/N]: ')}").lower()
        if not proceed.startswith("y"):
            print(f"{color.color('red', 'Setup cancelled. Some features may not work properly.')}")
            return None
    
    # Validate the token before saving
    print(f"{color.color('yellow', 'Validating token...')}")
    os.environ["GITHUB_TOKEN"] = token
    valid = validate_github_token(token)
    
    if valid:
        # Save the token
        save_token(token)
        print(f"{color.color('green', '✓')} Token saved successfully!")
        
        return token
    else:
        print(f"{color.color('red', 'Token validation failed.')}")
        print(f"{color.color('yellow', 'Please check your token and try again.')}")
        retry = input(f"{color.color('green', 'Try again? [Y/n]: ')}").lower()
        
        if not retry or retry.startswith("y"):
            print("\n") # Add some spacing
            return setup_github_token() # Try again
        else:
            return None

def reset_github_token():
    """Reset the saved GitHub token and prompt for a new one."""
    token_path = get_token_path()
    
    # Check if token exists
    if os.path.exists(token_path):
        try:
            os.remove(token_path)
            print(f"{color.color('green', '✓')} Previous token deleted.")
        except Exception as e:
            print(f"{color.color('red', f'Error deleting token: {str(e)}')}")
    
    # Clear the environment variable if set
    if "GITHUB_TOKEN" in os.environ:
        os.environ.pop("GITHUB_TOKEN")
        print(f"{color.color('green', '✓')} Token cleared from environment.")
    
    # Set up a new token
    return setup_github_token()

def ensure_github_token():
    """Ensures a GitHub token is available, prompting the user if needed."""
    # First check environment variable
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    
    # Then check saved token
    token = load_token()
    if token:
        os.environ["GITHUB_TOKEN"] = token
        return token
    
    # No token found, ask user to set up
    print(f"{color.color('yellow', 'No GitHub token found.')}")
    print(f"To access all features, including pinned repositories, a token is needed.")
    setup = input(f"{color.color('green', 'Set up a GitHub token now? [Y/n]: ')}").lower()
    
    if not setup or setup.startswith("y"):
        return setup_github_token()
    
    print(f"{color.color('yellow', 'Running with limited functionality (no pinned repos).')}")
    return None

##### -> GITHUB API INTEGRATION

def get_headers():
    # Prepares authorization headers for GitHub API requests
    # Try environment variable first (takes precedence if set)
    token = os.getenv("GITHUB_TOKEN")
    
    # If not in environment, try our saved token
    if not token:
        token = load_token()
        if token:
            # Set it in environment for this session
            os.environ["GITHUB_TOKEN"] = token
            
    # Return headers with token if we have one, empty dict otherwise
    return {"Authorization": f"Bearer {token}"} if token else {}

def get_user_data(username):
    # Fetches a user's profile data from the GitHub API
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()  # This will raise an exception if request failed
    return response.json()

def get_starred_count(username):
    # Counts how many repositories a user has starred
    url = f"https://api.github.com/users/{username}/starred"
    response = requests.get(url, headers=get_headers())
    return len(response.json()) if response.ok else 0

def fetch_contributions_data(username):
    """Fetch contribution data for creating a heatmap.
    
    Note: This uses GraphQL API which requires a token.
    """
    headers = get_headers()
    if not headers.get("Authorization"):
        print(color.color("yellow", "Warning: GitHub token not set. Cannot fetch contribution data."), file=sys.stderr)
        return None
    
    # Get today's date and date from a year ago
    try:
        today = datetime.datetime.utcnow()  # Use UTC time
        one_year_ago = today - datetime.timedelta(days=365)
        
        # Format dates for GraphQL query (GitHub requires ISO-8601 format with time in UTC)
        from_date = one_year_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
        to_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        print(color.color("red", f"Error formatting dates: {str(e)}"), file=sys.stderr)
        return None
        
    print(color.color("yellow", f"Fetching contributions for {username} from {from_date} to {to_date}..."))
    
    # Build the GraphQL query for contributions
    graphql_query = {
        "query": """
            query($login: String!, $from: DateTime!, $to: DateTime!) {
                user(login: $login) {
                    name
                    contributionsCollection(from: $from, to: $to) {
                        contributionCalendar {
                            totalContributions
                            weeks {
                                firstDay
                                contributionDays {
                                    date
                                    contributionCount
                                    color
                                }
                            }
                        }
                    }
                }
            }
        """,
        "variables": {
            "login": username,
            "from": from_date,
            "to": to_date
        }
    }
    
    # Make the POST request to the GraphQL API
    try:
        print(color.color("yellow", "Sending GraphQL request to GitHub API..."))
        response = requests.post("https://api.github.com/graphql", json=graphql_query, headers=headers)
        
        # Handle errors gracefully
        if not response.ok:
            print(color.color("red", f"API Error: {response.status_code}"), file=sys.stderr)
            print(color.color("red", f"Response: {response.text}"), file=sys.stderr)
            return None
        
        # Print response for debugging
        response_data = response.json()
        if "errors" in response_data:
            print(color.color("red", "GraphQL errors:"), file=sys.stderr)
            for error in response_data["errors"]:
                print(color.color("red", f"  - {error.get('message', 'Unknown error')}"), file=sys.stderr)
            return None
        
        # Return the contribution data
        data = response_data.get("data", {})
        
        # Check if we got the expected data structure
        user_data = data.get("user", {})
        if not user_data:
            print(color.color("red", f"Could not find user data for '{username}'"), file=sys.stderr)
            print(color.color("yellow", f"Response data: {data}"), file=sys.stderr)
            return None
        
        contributions_collection = user_data.get("contributionsCollection", {})
        if not contributions_collection:
            print(color.color("red", "No contributions collection data returned"), file=sys.stderr)
            print(color.color("yellow", f"User data: {user_data}"), file=sys.stderr) 
            return None
        
        contribution_calendar = contributions_collection.get("contributionCalendar", {})
        if not contribution_calendar:
            print(color.color("red", "No contribution calendar data returned"), file=sys.stderr)
            print(color.color("yellow", f"Contributions collection: {contributions_collection}"), file=sys.stderr)
            return None
        
        total = contribution_calendar.get('totalContributions', 0)
        weeks = contribution_calendar.get('weeks', [])
        print(color.color("green", f"Successfully fetched {total} contributions across {len(weeks)} weeks"))
        
        return contribution_calendar
        
    except Exception as e:
        print(color.color("red", f"Error fetching contribution data: {str(e)}"), file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None

def get_contributions_heatmap_lines(username, contributions_data, text_width):
    """Prepare formatted text lines for the contributions heatmap display."""
    # Start with an empty array - no initial lines
    lines = []
    
    if not contributions_data:
        return [
            color.color("red", "No contribution data available."),
            color.color("yellow", "Please check if:"),
            color.color("yellow", "  1. Your GitHub token is valid (try 'githubfetch --reset-token')"),
            color.color("yellow", "  2. The username exists on GitHub"),
            color.color("yellow", "  3. The user has public contribution activity")
        ]
    
    total_contributions = contributions_data.get("totalContributions", 0)
    weeks = contributions_data.get("weeks", [])
    
    if total_contributions == 0 or not weeks:
        return [color.color("yellow", f"No contributions found for user '{username}' in the past year.")]
    
    # Terminal ANSI color blocks for heatmap (from light to dark)
    # Using the color class for better terminal compatibility with more distinct levels
    contribution_blocks = [
        color.color("reset", "·"),            # No contributions
        color.color("light_green", "▪"),      # Level 1 (light)
        color.color("green", "▪"),           # Level 2
        color.color("green", "■"),           # Level 3
        color.color("dark_green", "■")       # Level 4 (dark)
    ]
    
    # Add dark green color if it doesn't exist
    if not hasattr(color, "dark_green"):
        color.dark_green = "\x1b[38;5;22m"
    
    # Add light green color if it doesn't exist
    if not hasattr(color, "light_green"):
        color.light_green = "\x1b[38;5;118m"
    
    # Calculate the range for color selection
    # Flatten the contribution days
    all_days = []
    for week in weeks:
        for day in week.get("contributionDays", []):
            all_days.append(day.get("contributionCount", 0))
    
    # Skip if no days data
    if not all_days:
        return [color.color("yellow", f"No contribution data found for '{username}' in the past year.")]
    
    # Calculate quartiles for color distribution
    max_contributions = max(all_days) if all_days else 0
    q1 = max(1, max_contributions // 4)
    q2 = max(2, max_contributions // 2)
    q3 = max(3, 3 * max_contributions // 4)
    
    # Dictionary to map month numbers to shortened names
    month_names = {i: calendar.month_abbr[i] for i in range(1, 13)}
    current_month = None
    month_labels = []
    
    lines.append(f"{color.color('green', 'Contributions:')} {color.color('yellow', str(total_contributions))}")
    
    # Prepare data structure for horizontal heatmap (days as rows, weeks as columns)
    # Initialize a 2D array to hold contribution data [day_of_week][week]
    horizontal_data = [[] for _ in range(7)]  # 7 days in a week
    month_positions = []  # Store (week_idx, month) for month labels
    
    # Process weeks data to organize into horizontal format
    for week_idx, week in enumerate(weeks):
        # Extract month from first day of week for month labels
        for day in week.get("contributionDays", []):
            date_parts = day.get("date", "").split("-")
            if len(date_parts) == 3:
                month_num = int(date_parts[1])
                if month_num != current_month:
                    current_month = month_num
                    month_labels.append((week_idx, month_names[month_num]))
            break
        
        # Create a lookup dict for days keyed by weekday (0=Sunday, 6=Saturday)
        day_lookup = {}
        for day in week.get("contributionDays", []):
            date_str = day.get("date", "")
            if date_str:
                try:
                    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    weekday = date_obj.weekday()
                    # Convert to Sunday=0 format
                    weekday = (weekday + 1) % 7
                    day_lookup[weekday] = day
                except Exception:
                    # If parsing fails, skip this day
                    continue
        
        # Add contribution data for each day in this week
        for day_idx in range(7):  # Sunday to Saturday
            if day_idx in day_lookup:
                day = day_lookup[day_idx]
                count = day.get("contributionCount", 0)
                # Select appropriate block based on count
                if count == 0:
                    block = contribution_blocks[0]
                elif count <= q1:
                    block = contribution_blocks[1]
                elif count <= q2:
                    block = contribution_blocks[2]
                elif count <= q3:
                    block = contribution_blocks[3]
                else:
                    block = contribution_blocks[4]
            else:
                block = " "  # Empty space for days not in the week
            
            # Add to our horizontal data structure
            horizontal_data[day_idx].append(block)
        
    # Create the month labels row
    if month_labels:
        month_header = "   "  # Space for day labels
        last_pos = -3  # Start position for first month
        
        for week_idx, month_name in month_labels:
            # Add spaces between month labels
            spaces = week_idx - last_pos - 1
            month_header += " " * (spaces * 2)  # 2 spaces per week
            month_header += color.color("light_blue", month_name[:3])
            last_pos = week_idx + len(month_name[:3]) // 2
        
        lines.append(month_header)
    
    # Day labels for the new horizontal format
    day_labels = [
        color.color("yellow", "S"),  # Sunday
        color.color("yellow", "M"),  # Monday
        color.color("yellow", "T"),  # Tuesday
        color.color("yellow", "W"),  # Wednesday
        color.color("yellow", "T"),  # Thursday
        color.color("yellow", "F"),  # Friday
        color.color("yellow", "S")   # Saturday
    ]
    
    # Create each row (day of week)
    for day_idx in range(7):
        row = f"{day_labels[day_idx]} "  # Day label at the beginning of the row
        
        # Add all weeks for this day
        for week_idx, block in enumerate(horizontal_data[day_idx]):
            row += block
            # Add space between weeks
            if week_idx < len(horizontal_data[day_idx]) - 1:
                row += " "
        
        lines.append(row)
    
    # Add legend at the bottom - no extra line
    legend = (f"{contribution_blocks[0]}None {contribution_blocks[1]}Few "
              f"{contribution_blocks[2]}Some {contribution_blocks[3]}Many "
              f"{contribution_blocks[4]}Lots")
    lines.append(legend)
    
    return lines

def fetch_pinned_repos(username):
    # Fetches a user's pinned repositories using GitHub's GraphQL API
    # GraphQL API requires authentication
    headers = get_headers()
    if not headers.get("Authorization"):
        print(color.color("yellow", "Warning: GitHub token not set. Cannot fetch pinned repos."), file=sys.stderr)
        return []
    
    # Build the GraphQL query - this gets exactly the fields we need
    # I spent a lot of time in GitHub's GraphQL Explorer to get this right
    graphql_query = {
        "query": """
            query($login: String!) {
                user(login: $login) {
                    pinnedItems(first: 6, types: [REPOSITORY]) {
                        nodes {
                            ... on Repository {
                                name
                                description
                                owner { login }
                                stargazerCount
                                forkCount
                                primaryLanguage { name, color }
                            }
                        }
                    }
                }
            }
        """,
        "variables": {"login": username}
    }
    
    # Make the POST request to the GraphQL API
    response = requests.post("https://api.github.com/graphql", json=graphql_query, headers=headers)
    
    # Handle errors gracefully
    if not response.ok:
        return []
        
    # Navigate through the response structure to get the pinned repos
    data = response.json().get("data", {})
    return data.get("user", {}).get("pinnedItems", {}).get("nodes", [])

# Note: These functions are no longer used - we're using the GraphQL API now
# Keeping function shells for backwards compatibility

def fetch_contribution_heatmap(username):
    """Legacy function stub - no longer used"""
    return []

def parse_heatmap_data(events):
    """Legacy function stub - no longer used"""
    contribution_days = {}
    
    for event in events:
        if event.get("type") == "PushEvent":
            # Only count actual pushes, not other event types
            for commit in event.get("payload", {}).get("commits", []):
                # Each commit corresponds to a contribution
                commit_time = commit.get("timestamp")
                if commit_time:
                    # Convert to date string
                    date_str = commit_time.split("T")[0]
                    contribution_days[date_str] = contribution_days.get(date_str, 0) + 1
    
    return contribution_days

def generate_heatmap(contribution_days):
    """Legacy function stub - no longer used"""
    # Return empty string for backwards compatibility
    return ""

def trim_trailing_empty_lines(lines):
    """Remove trailing empty lines from an array of strings."""
    if not lines:
        return lines
    
    # Find the index of the last non-empty line
    last_non_empty = len(lines) - 1
    while last_non_empty >= 0 and not lines[last_non_empty].strip():
        last_non_empty -= 1
    
    # Return the array up to and including the last non-empty line
    return lines[:last_non_empty + 1]

##### -> MAIN DISPLAY AND UI FUNCTIONS

def get_user_info_lines(data, starred_count, pinned_repos, text_width):
    # Prepares formatted text lines for display
    username = data.get('login')
    info = {
        "Website": data.get('blog') or 'N/A', "Repos": data.get('public_repos'), "Bio": data.get('bio') or 'N/A',
        "From": data.get('location') or 'Not Provided', "Followers": data.get('followers'), "Following": data.get('following'), "Starred": starred_count
    }
    max_label_len = max(len(label) for label in info.keys())
    lines = []
    
    profile_url = f"https://github.com/{username}"
    display_title = f"{color.color('green', username)}{color.color('reset', '@')}{color.color('green', 'github')}"
    title = create_hyperlink(profile_url, display_title)
    lines.append(title)
    lines.append(color.color('green', '-' * (len(username) + 7)))

    for label, value in info.items():
        formatted_label = f"{color.color('yellow', f'{label}:'.ljust(max_label_len + 2))}"
        if label == "Website" and value and value != 'N/A':
            schemed_url = value if value.startswith(('http://', 'https://')) else f'https://{value}'
            wrapped_value = textwrap.wrap(value, width=text_width)
            linked_display_text = create_hyperlink(schemed_url, wrapped_value[0])
            lines.append(f"{formatted_label}{color.color('reset', linked_display_text)}")
            for line in wrapped_value[1:]:
                lines.append(f"{' ' * (max_label_len + 2)}{color.color('reset', line)}")
        elif label == "Bio" and value != 'N/A':
            wrapped_value = textwrap.wrap(str(value), width=text_width)
            lines.append(f"{formatted_label}{color.color('reset', wrapped_value[0])}")
            for line in wrapped_value[1:]:
                lines.append(f"{' ' * (max_label_len + 2)}{color.color('reset', line)}")
        else:
            lines.append(f"{formatted_label}{color.color('reset', str(value))}")
    
    if pinned_repos:
        # Add section for pinned repositories - made more compact
        lines.append(color.color('green', "Pinned Repositories:"))
        for repo in pinned_repos:
            lang_color_name = 'green' if repo.get('primaryLanguage') else 'reset'
            lang_dot = color.color(lang_color_name, "●")
            
            repo_owner = repo.get('owner', {}).get('login', username)
            repo_url = f"https://github.com/{repo_owner}/{repo['name']}"
            repo_name_text = color.color('orange', repo['name'])
            repo_name = create_hyperlink(repo_url, repo_name_text)
            
            stars = color.color('yellow', f"★ {repo['stargazerCount']}")
            forks = color.color('light_blue', f"⑂ {repo['forkCount']}")
            
            lines.append(f" {lang_dot} {repo_name} ({stars} / {forks})")
            
            raw_description = repo.get('description')
            if raw_description:
                wrapped_description = textwrap.wrap(raw_description, width=text_width - 3)
                for line in wrapped_description:
                    lines.append(f"   {color.color('reset', line)}")
    
    return lines

def display_side_by_side(user_data, starred_count=None, pinned_repos=None, contributions_data=None):
    # Displays avatar on the left and user info on the right
    IMAGE_HEIGHT_CELLS = 15
    TEXT_GAP = 6
    
    username = user_data.get('login')
    # Determine content to display (pinned repos or contributions heatmap)
    show_heatmap = contributions_data is not None
    
    # Check for imgcat installation before attempting to display image
    imgcat_path = check_imgcat_installed()
    
    if imgcat_path:
        # We can display the image
        avatar_url = user_data.get('avatar_url')
        try:
            response = requests.get(avatar_url)
            response.raise_for_status()
            image_data = response.content
            img = Image.open(BytesIO(image_data))
            width_px, height_px = img.size
            aspect_ratio = width_px / height_px
            image_width_cells = int(IMAGE_HEIGHT_CELLS * aspect_ratio * 2.0)
            
            terminal_width = os.get_terminal_size().columns
            text_start_column = image_width_cells + TEXT_GAP
            available_text_width = terminal_width - text_start_column

            with tempfile.NamedTemporaryFile(suffix=".png") as temp_image:
                temp_image.write(image_data)
                temp_image.flush()
                
                # If imgcat_path is True, imgcat is in PATH. Otherwise it contains the path
                imgcat_cmd = "imgcat" if imgcat_path is True else imgcat_path
                
                # Try to detect which imgcat version we're dealing with by checking help output
                try:
                    help_output = subprocess.run([imgcat_cmd, "--help"], capture_output=True, text=True).stdout.lower()
                    
                    # The pip-installed version uses --height instead of -H
                    if "--height" in help_output:
                        subprocess.run([imgcat_cmd, "--height", str(IMAGE_HEIGHT_CELLS), temp_image.name], check=True)
                    else:
                        # Assume it's the iterm2 bundled imgcat or similar that uses -H
                        subprocess.run([imgcat_cmd, "-H", str(IMAGE_HEIGHT_CELLS), temp_image.name], check=True)
                except Exception:
                    # If we can't determine the version, try the pip version first, then fall back
                    try:
                        subprocess.run([imgcat_cmd, "--height", str(IMAGE_HEIGHT_CELLS), temp_image.name], check=True)
                    except Exception:
                        subprocess.run([imgcat_cmd, temp_image.name], check=True)
                
                # Get user info lines
                user_info_lines = get_user_info_lines(user_data, starred_count or 0, 
                                                    [] if show_heatmap else (pinned_repos or []), 
                                                    available_text_width)
                
                # Get contribution heatmap lines if showing heatmap
                if show_heatmap:
                    # Remove any trailing empty lines from user info
                    user_info_lines = trim_trailing_empty_lines(user_info_lines)
                    heatmap_lines = get_contributions_heatmap_lines(username, contributions_data, available_text_width)
                    # Direct combine with no spacing
                    display_lines = user_info_lines + heatmap_lines
                else:
                    display_lines = user_info_lines
                
                # Display the lines next to the image
                sys.stdout.write(f"\x1b[{IMAGE_HEIGHT_CELLS}A")
                sys.stdout.write(f"\x1b[{text_start_column}C")
                for i, line in enumerate(display_lines):
                    print(line)
                    if i < len(display_lines) - 1:
                        sys.stdout.write(f"\x1b[{text_start_column}C")
                
                # Move down if needed
                lines_to_move_down = max(0, IMAGE_HEIGHT_CELLS - len(display_lines))
                if lines_to_move_down > 0:
                    sys.stdout.write(f"\x1b[{lines_to_move_down}B")
                print()
                return
        except Exception as e:
            print(f"{color.color('red', f'Error displaying avatar: {e}')}", file=sys.stderr)
            # Continue to text-only fallback
    
    # Fallback to text-only display
    terminal_width = os.get_terminal_size().columns
    
    # Get user info lines
    user_info_lines = get_user_info_lines(user_data, starred_count or 0, 
                                        [] if show_heatmap else (pinned_repos or []), 
                                        terminal_width - 10)
    
    # Get contribution heatmap lines if showing heatmap
    if show_heatmap:
        # Remove any trailing empty lines from user info
        user_info_lines = trim_trailing_empty_lines(user_info_lines)
        heatmap_lines = get_contributions_heatmap_lines(username, contributions_data, terminal_width - 10)
        # Direct combine with no spacing
        display_lines = user_info_lines + heatmap_lines
    else:
        display_lines = user_info_lines
    
    print() # Add a bit of spacing
    for line in display_lines:
        print(f"  {line}")
    print()

# Check if imgcat is installed
##### -> DEPENDENCY MANAGEMENT

def check_imgcat_installed():
    # Checks if imgcat is installed and offers to install it if not
    if shutil.which("imgcat"):
        return True
    
    print(f"{color.color('yellow', 'The imgcat command is not installed.')}")
    print(f"{color.color('yellow', 'This tool is required to display GitHub profile images in the terminal.')}")
    
    install = input(f"{color.color('green', 'Would you like to install imgcat now? [Y/n]: ')}").lower()
    
    if not install or install.startswith("y"):
        try:
            print(f"{color.color('green', 'Installing imgcat...')}")
            # Try to install with pip first
            subprocess.run([sys.executable, "-m", "pip", "install", "imgcat"], 
                          check=True, capture_output=True)
            
            # Verify installation
            if shutil.which("imgcat"):
                print(f"{color.color('green', '✓')} imgcat installed successfully!")
                return True
            else:
                # If installation succeeded but command not found, it might be in a path not in PATH
                pip_path = shutil.which("pip") or shutil.which("pip3")
                if pip_path:
                    pip_dir = os.path.dirname(pip_path)
                    imgcat_path = os.path.join(pip_dir, "imgcat")
                    if os.path.exists(imgcat_path):
                        print(f"{color.color('yellow', f'imgcat installed at {imgcat_path} but not in PATH.')}")
                        return imgcat_path
                        
                # Could consider creating a symbolic link to imgcat in a directory that is in PATH
                print(f"{color.color('yellow', 'Could not verify imgcat installation.')}")
            
        except Exception as e:
            print(f"{color.color('red', f'Failed to install imgcat: {str(e)}')}")
            print(f"{color.color('yellow', 'You can install it manually with: pip install imgcat')}")
    
    print(f"{color.color('yellow', 'Continuing without profile images.')}")
    return False

##### -> MAIN PROGRAM FLOW

# Define the main function to be used as the entry point for the package
def main():
    """
    Main entry point for GitHubFetch
    
    Program flow:
    1. Check for required dependencies
    2. Handle special commands (--config, --reset-token, --help)
    3. Verify if there is GitHub username to look up
    4. Ensure GitHub token is available
    5. Fetch user data and display it in the terminal
    """
    # First check for dependencies
    check_imgcat_installed()
    
    # Handle flags usage for config or help
    if len(sys.argv) > 1:
        if sys.argv[1] == '--config':
            setup_github_token()
            sys.exit(0)
        elif sys.argv[1] == '--reset-token':
            reset_github_token()
            sys.exit(0)
        elif sys.argv[1] in ['--help', '-h']:
            print(color.color('green', "┌───────── GitHubFetch ────────────┐"))
            print(color.color('green', "│") + " A terminal GitHub profile viewer " + color.color('green', "│"))
            print(color.color('green', "└──────────────────────────────────┘"))
            print("Usage:")
            print("  githubfetch <username>          (view a GitHub user profile)")
            print("  githubfetch <username> --heatmap (view GitHub contributions heatmap)")
            print("  githubfetch --config            (set up/update GitHub token)")
            print("  githubfetch --reset-token       (delete and reconfigure token)")
            print("  githubfetch --help, -h          (display this help message)")
            
            print(f"\n{color.color('yellow', 'Examples:')}")
            print("  githubfetch shubhpsd            (view GitHub profile for shubhpsd)")
            print("  githubfetch shubhpsd --heatmap  (view contribution heatmap for shubhpsd)")
            print("  githubfetch --config            (configure your GitHub token)")
            sys.exit(0)
    
    # Make sure username to look up is provided
    if len(sys.argv) < 2:
        print("Usage: githubfetch <username>")
        print("Use " + color.color('yellow', "githubfetch --help") + " or " + color.color('yellow', "-h") + " for more information.")
        sys.exit(0)
    
    # Check for command flags
    args = sys.argv[1:]
    show_heatmap = '--heatmap' in args
    
    # Extract the username (first non-flag argument)
    username = None
    for arg in args:
        if not arg.startswith('--'):
            username = arg
            break
    
    if not username:
        print(f"{color.color('red', 'Error: No username provided.')}")
        print("Usage: githubfetch <username> [--heatmap]")
        print("Use " + color.color('yellow', "githubfetch --help") + " for more information.")
        sys.exit(1)
    
    # Make GitHub token exists (or guide the user to set one up)
    ensure_github_token()
    
    try:
        # Fetch user data
        user_data = get_user_data(username)
        
        # Always fetch user data for display
        starred_count = get_starred_count(username)
            
        if show_heatmap:
            # Fetch contributions data for heatmap display
            contributions_data = fetch_contributions_data(username)
            # Display profile with heatmap
            display_side_by_side(user_data, starred_count, None, contributions_data)
        else:
            # Display standard profile with pinned repos
            pinned_repos = fetch_pinned_repos(username)
            display_side_by_side(user_data, starred_count, pinned_repos)
    except Exception as e:
        # Handle errors gracefully
        print(f"{color.color('red', f'Error: {str(e)}')}", file=sys.stderr)
        sys.exit(1)
