# GitHubFetch

A terminal-based GitHub profile viewer written in Python. View GitHub profiles right in your terminal with style!

![GitHubFetch Demo Screenshot](demo-screenshot.png)

## About

GitHubFetch is a command-line tool I created as a side project. It displays GitHub user profiles in a terminal with a nice layout inspired by system fetch tools like neofetch and fastfetch.

## Features

- 🖼️ Shows user's avatar in the terminal (using imgcat)
- 👤 Displays basic profile information (bio, location, follower count, etc.)
- 🔗 Creates clickable links to profiles and websites
- ⭐ Shows starred repositories count
- 📌 Lists pinned repositories with stars and forks
- 🎨 Uses color-coding to make information easier to read
- 📏 Automatically adjusts to your terminal size

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/shubhamprasad/githubfetch.git
   ```

2. Install dependencies:

   ```bash
   pip install requests pillow imgcat
   ```

   Note: The script will automatically check for and offer to install the `imgcat` dependency on first run if it's missing.

3. Install the script to your system:

   ```bash
   # Install to system directory (requires sudo)
   sudo cp githubfetch /usr/local/bin/githubfetch
   sudo chmod +x /usr/local/bin/githubfetch
   ```

Alternatively, if you've already downloaded the script to the mentioned folder:

   ```bash
   chmod +x /usr/local/bin/githubfetch
   ```

1. Install the required dependencies:

   ```bash
   pip install requests pillow imgcat
   ```

## Usage

```bash
githubfetch <username>
```

For example:

```bash
githubfetch shubhpsd
```

## GitHub Token Setup

To view pinned repositories and avoid API rate limits, GitHubFetch needs a GitHub personal access token.

The first time you run the tool, it will guide you through setting up your token:

1. It will prompt you to create a token at [GitHub Developer Settings](https://github.com/settings/tokens)
2. After entering your token, it's securely saved for future use

If you need to update or reconfigure your token later:

```bash
githubfetch --config
```

Your token needs only the `read:user` scope to work properly.

## Requirements

A terminal that supports ANSI escape codes and images (like iTerm2)
