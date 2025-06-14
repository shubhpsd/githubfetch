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
import json        # For token storage and API responses
import shutil      # For checking if commands exist
import getpass     # For secure password/token input
import tempfile    # For temporary avatar storage
import textwrap    # For formatting text output nicely
import pathlib     # For cross-platform path handling
import subprocess  # For executing external commands like imgcat

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
    print(f"  • {color.color('reset', 'Avoid GitHub API rate limits')}")
    print(f"  • {color.color('reset', 'Access complete profile information')}")
    
    print(f"\n{color.color('green', 'How to create a token:')}")
    print(f"1. Visit {create_hyperlink('https://github.com/settings/tokens', color.color('light_blue', 'github.com/settings/tokens'))}")
    print(f"2. Click \"{color.color('yellow', 'Generate new token')}\" → \"{color.color('yellow', 'Generate new token (classic)')}\"")
    print(f"3. Enter a note like \"{color.color('reset', 'GitHubFetch')}\"")
    print(f"4. Select the \"{color.color('yellow', 'read:user')}\" scope (under \"user\")")
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
        lines.append(color.color('green', '-' * (len("Pinned Repositories:"))))
        # Add section for pinned repositories
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

def display_side_by_side(user_data, starred_count, pinned_repos):
    # Displays avatar on the left and user info on the right
    IMAGE_HEIGHT_CELLS = 15
    TEXT_GAP = 6
    
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
                
                info_lines = get_user_info_lines(user_data, starred_count, pinned_repos, available_text_width)
                
                sys.stdout.write(f"\x1b[{IMAGE_HEIGHT_CELLS}A")
                sys.stdout.write(f"\x1b[{text_start_column}C")
                for i, line in enumerate(info_lines):
                    print(line)
                    if i < len(info_lines) - 1:
                        sys.stdout.write(f"\x1b[{text_start_column}C")
                lines_to_move_down = max(0, IMAGE_HEIGHT_CELLS - len(info_lines))
                if lines_to_move_down > 0:
                    sys.stdout.write(f"\x1b[{lines_to_move_down}B")
                print()
                return
        except Exception as e:
            print(f"{color.color('red', f'Error displaying avatar: {e}')}", file=sys.stderr)
            # Continue to text-only fallback
    
    # Fallback to text-only display
    terminal_width = os.get_terminal_size().columns
    info_lines = get_user_info_lines(user_data, starred_count, pinned_repos, terminal_width - 10)
    
    print() # Add a bit of spacing
    for line in info_lines:
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
            print("  githubfetch <username>        (view a GitHub user profile)")
            print("  githubfetch --config          (set up/update GitHub token)")
            print("  githubfetch --reset-token     (delete and reconfigure token)")
            print("  githubfetch --help, -h        (display this help message)")
            
            print(f"\n{color.color('yellow', 'Examples:')}")
            print("  githubfetch shubhpsd          (view GitHub profile for shubhpsd)")
            print("  githubfetch --config          (configure your GitHub token)")
            sys.exit(0)
    
    # Make sure username to look up is provided
    if len(sys.argv) < 2:
        print("Usage: githubfetch <username>")
        print("Use " + color.color('yellow', "githubfetch --help") + " or " + color.color('yellow', "-h") + " for more information.")
        sys.exit(0)
    
    username = sys.argv[1]
    
    # Make GitHub token exists (or guide the user to set one up)
    ensure_github_token()
    
    try:
        # Fetch all GitHub data
        user_data = get_user_data(username)
        starred_count = get_starred_count(username)
        pinned_repos = fetch_pinned_repos(username)
        
        # Display the results in a nice format
        display_side_by_side(user_data, starred_count, pinned_repos)
    except Exception as e:
        # Handle errors gracefully
        print(f"{color.color('red', f'Error: {str(e)}')}", file=sys.stderr)
        sys.exit(1)


# This allows the script to be run directly or as a module
if __name__ == '__main__':
    main()