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
   pip install requests pillow
   ```

3. Make sure the [imgcat](https://github.com/danielgatis/imgcat) tool is installed for displaying images in the terminal:

   ```bash
   pip install imgcat
   ```

4. Install the script to your system:

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
githubfetch shubhamprasad
```

## Environment Variables

To view pinned repositories, you'll need to set up a GitHub token:

```bash
export GITHUB_TOKEN=your_github_token
```

For permanent configuration, add this line to your `.zshrc` file:

```bash
echo 'export GITHUB_TOKEN=your_github_token' >> ~/.zshrc
source ~/.zshrc
```

You can create a personal access token in your [GitHub Developer Settings](https://github.com/settings/tokens).

## Requirements

A terminal that supports ANSI escape codes and images (like iTerm2)
