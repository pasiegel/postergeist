<p align="center">
  <img src="https://i.imgur.com/YGI5vqk.png" alt="Postergeist Logo" width="250">
</p>
# Postergeist 👻 v1.4.0

*Your personal, python-powered poster slideshow.*

---

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Postergeist is a highly customizable, fullscreen slideshow application perfect for displaying your movie poster collection on a dedicated monitor or TV. It automatically creates blurred backgrounds, supports both images and videos, and can now be themed using folder-based tags. It's designed to be run from the command line and is ideal for a low-power, set-it-and-forget-it setup like a Raspberry Pi.

---

## Features

-   **Image & Video Support**: Displays a wide range of file types, including `.jpg`, `.png`, `.webp`, `.mp4`, `.mkv`, and more.
-   **Recursive Scanning** 🆕: Automatically finds media in all subdirectories of your main `posters` folder.
-   **Themed Overlays** 🆕: Assign specific overlays to different folders using a simple `_tag` naming convention.
-   **Dynamic Backgrounds**: Automatically generates a blurred, fullscreen background from the current poster for a seamless look.
-   **Animated Overlays**: Add your own transparent `.png`, animated `.gif`, or `.apng` overlays that are randomly selected or assigned via tags.
-   **Multi-Monitor Control**: Choose which display to run on, or span across all monitors.
-   **Flexible Timing**: Set a fixed delay between slides or use a random delay. Now includes an option to limit video playback time.
-   **Full Keyboard Control**: Pause, play, skip, go back, rotate posters, and refresh the file list with simple hotkeys.
-   **Performance Mode**: Toggle effects like glow blur for smoother playback on low-powered devices.
-   **Raspberry Pi Ready**: Lightweight and includes instructions for easy autostart on boot.

---

## ✨ Themed Overlays (Folder Tags)

You can now assign specific overlays to entire folders of media, allowing you to create different themes for your collection (e.g., a VHS effect for horror movies, a retro TV frame for 80s sci-fi).

The logic is simple: **Folder Name** + **\_** + **Tag**.

1.  **Organize Your Media**: Inside your main `posters` folder, create subfolders for different categories (e.g., `Horror`, `SciFi`).
2.  **Add a Tag**: Rename the subfolder by appending an underscore and a tag name. For example, `Horror` becomes `Horror_vhs`. The tag here is `vhs`.
3.  **Create a Matching Overlay**: In your `overlays` folder, add an image or GIF whose filename (without the extension) exactly matches the tag. For the `_vhs` tag, you would create `vhs.png` or `vhs.gif`.

The script will automatically apply the correct overlay. If a folder has no tag, it will use a random overlay as a fallback.

### Example Structure
-   `postergeist/`
    -   `posters/`
        -   `Horror_vhs/` (This folder uses the **`vhs`** tag)
            -   `movie1.mp4`
            -   `movie2.jpg`
        -   `SciFi_80s/` (This folder uses the **`80s`** tag)
            -   `movie3.mkv`
            -   `movie4.png`
    -   `overlays/`
        -   `vhs.png` (Matches the `_vhs` tag)
        -   `80s.gif` (Matches the `_80s` tag)
        -   `random_overlay.apng` (Fallback for untagged folders)
    -   `postergeist.py`

---

## Installation

These instructions are for a standard desktop (Windows, macOS, Linux). See the platform-specific sections for Raspberry Pi, macOS, Arch Linux, and Debian/Ubuntu setup.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/pasiegel/postergeist.git](https://github.com/pasiegel/postergeist.git)
    cd postergeist
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    You will need a `requirements.txt` file with the necessary Python packages.
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If you don't have a `requirements.txt` file, you can install the packages manually: `pip install opencv-python Pillow screeninfo`)*

4.  **Create Folders:**
    Create a folder named `posters` in the project directory and add your image/video files (or subfolders). Optionally, create an `overlays` folder and add any `.png`, `.gif`, or `.apng` overlays.

---

## ⌨️ Keyboard Controls

Control the slideshow while it is running with these keyboard shortcuts.

| Key | Action |
| :--- | :--- |
| `Right Arrow` | Manually advance to the **next** slide. |
| `Left Arrow` | Go back to the **previous** slide. |
| `Spacebar` | **Pause** or **resume** the automatic slideshow. |
| `r` | **Rotate** the current image or video 90 degrees clockwise. |
| `F5` | **Refresh** the file list from the source folder(s) without restarting. |
| `Esc` | **Exit** the slideshow. |

---

## 🆕 What’s New in v1.4
- **Themed Overlays**: Assign specific overlays to media folders using a `FolderName_tag` naming convention.
- **Subdirectory Scanning**: The slideshow now automatically finds and includes media from all subfolders.
- **Video Time Limit** (`--max-video-time`): A new option to ensure videos don't exceed the slide delay, cutting them off if they are too long. This creates a more consistent, TV-like channel surfing experience.
- **Animated Overlays**: Now supports `.gif` and `.apng` overlays in addition to static images.  
- **Performance Mode** (`--performance-mode`): Disable glow blur and other intensive effects for smoother playback on low-powered hardware.  
- **Fade Height Control** (`--fade-height`): Adjust the faded bottom section of posters as a percentage (default `20`).  
- **Improved Overlay Behavior**: Overlays are suppressed when posters/videos nearly fill the entire screen.  
- **Cached Video Backgrounds**: Faster performance by caching blurred video backgrounds.
  
---

## Command-Line Parameters

You can customize the slideshow's behavior using the following command-line arguments.

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `folder` | `posters` | The path to the folder containing your image and video files. This is a positional argument. |
| `--overlays` | `overlays` | Specifies a folder with overlay images (`.png`, `.jpg`, `.gif`, `.apng`). |
| `--delay` | `300` | The delay in seconds between each slide. Defaults to 5 minutes. |
| `--random-delay`| `False` | When present, this flag overrides `--delay` and uses a random delay between 1 and 5 minutes for each slide. |
| `--max-video-time` 🆕 | `False` | Limits video playback to the `--delay` duration. If a video is longer than the delay, it will be cut short. |
| `--display` | `1` | Selects which display monitor to use. Use `1` for the primary monitor, `2` for secondary, and so on. Use `all` to span the slideshow across all connected monitors. |
| `--windowed` | `False` | If included, the application will run in a standard resizable window instead of fullscreen mode. |
| `--rotate` | `0` | Sets an initial rotation angle for all media. Valid values are `0`, `90`, `180`, and `270`. |
| `--fade-height` | `20` | Sets the fade height at the bottom of posters as a percentage. |
| `--performance-mode` | `False` | Disables glow and other intensive effects for better performance. |

---

## Raspberry Pi Kiosk Setup

To have Postergeist run automatically on a Raspberry Pi when it boots:

1.  **Follow steps 1, 3, and 4 from the installation section above.** A virtual environment is optional but still recommended on a Pi.

2.  **Install System Dependencies:**
    Ensure you have Python's Tkinter library installed, which is required for the GUI.
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-tk python3-pil python3-pil.imagetk python3-opencv python3-screeninfo
    ```

3.  **Set up Autostart:**
    We will create a `.desktop` file that tells the OS to launch the script on startup.

    -   Create the autostart directory if it doesn't exist:
        ```bash
        mkdir -p /home/pi/.config/autostart
        ```
    -   Create a new desktop entry file:
        ```bash
        nano /home/pi/.config/autostart/postergeist.desktop
        ```
    -   Paste the following content into the file. **Important:** You must change the `path/to/postergeist` to the actual full path where you cloned the repository (e.g., `/home/pi/postergeist`).

        ```ini
        [Desktop Entry]
        Type=Application
        Name=Postergeist
        Exec=python /path/to/postergeist/postergeist.py
        ```

    -   Save the file by pressing `Ctrl+X`, then `Y`, then `Enter`.

4.  **Reboot:**
    ```bash
    sudo reboot
    ```
    After rebooting, the slideshow should start automatically in fullscreen.

---

## macOS Kiosk Setup

To have Postergeist run automatically when you log in on macOS:

1.  **Install Homebrew**: If you don't have it, install the Homebrew package manager.
    ```bash
    /bin/bash -c "$(curl -fsSL [https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh](https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh))"
    ```

2.  **Install Dependencies**: Use Homebrew to install the necessary libraries.
    ```bash
    brew install python-tk opencv
    ```

3.  **Follow the main installation steps 1-4**: Clone the repository, create a virtual environment, and install the Python packages from `requirements.txt`.

4.  **Set up Autostart with `launchd`**: We will create a `.plist` file to tell macOS to launch the script on login.

    -   Create the `LaunchAgents` directory if it doesn't exist:
        ```bash
        mkdir -p ~/Library/LaunchAgents
        ```
    -   Create a new property list file:
        ```bash
        nano ~/Library/LaunchAgents/com.user.postergeist.plist
        ```
    -   Paste the following XML into the file. **Important**: You must change the path `/path/to/postergeist/postergeist.py` to the **actual full path** where you cloned the repository.

        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "[http://www.apple.com/DTDs/PropertyList-1.0.dtd](http://www.apple.com/DTDs/PropertyList-1.0.dtd)">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>com.user.postergeist</string>
            <key>ProgramArguments</key>
            <array>
                <string>/usr/bin/python3</string>
                <string>/path/to/postergeist/postergeist.py</string>
            </array>
            <key>RunAtLoad</key>
            <true/>
        </dict>
        </plist>
        ```

    -   Save the file by pressing `Ctrl+X`, then `Y`, then `Enter`.

5.  **Log Out and Log In**: The script will now start automatically the next time you log into your Mac user account.

---

## Arch Linux Global Install

You can make `postergeist` available as a global command on Arch Linux by using the provided installation script. This script will install dependencies, make the Python script executable, and copy it to a directory in your system's PATH.

1.  **Save the Install Script**: Create a new file named `install-arch.sh` and paste the contents below into it. Make sure it's in the same directory as your `postergeist.py` script.

2.  **Make the Script Executable**:
    ```bash
    chmod +x install-arch.sh
    ```

3.  **Run with Sudo**:
    ```bash
    sudo ./install-arch.sh
    ```

### Install Script (`install-arch.sh`)
```bash
#!/bin/bash
# A script to install the Postergeist slideshow globally on Arch Linux

# --- Configuration ---
PYTHON_SCRIPT="postergeist.py"
INSTALL_NAME="postergeist"
INSTALL_DIR="/usr/local/bin"

# --- Main Script ---
# Check for root privileges
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'." 1>&2
    exit 1
fi

echo "--- Postergeist Global Installer for Arch Linux ---"

# 1. Install dependencies with pacman
echo "Updating package database and installing dependencies..."
pacman -Syu --noconfirm --needed python python-pillow python-opencv tk python-screeninfo
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies with pacman." >&2
    exit 1
fi
echo "✅ Dependencies installed successfully."
echo

# 2. Prepare the Python script
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: The script '$PYTHON_SCRIPT' was not found in the current directory." >&2
    exit 1
fi

if ! grep -q "^#!" "$PYTHON_SCRIPT"; then
    echo "Adding shebang '#!/usr/bin/env python3' to '$PYTHON_SCRIPT'..."
    sed -i '1s,^,#!/usr/bin/env python3\n,' "$PYTHON_SCRIPT"
fi
chmod +x "$PYTHON_SCRIPT"
echo "✅ Python script is now executable."
echo

# 3. Install the script to the system PATH
echo "Installing '$PYTHON_SCRIPT' to '$INSTALL_DIR/$INSTALL_NAME'..."
cp "$PYTHON_SCRIPT" "$INSTALL_DIR/$INSTALL_NAME"
if [ $? -ne 0 ]; then
    echo "Error: Failed to copy the script to '$INSTALL_DIR'." >&2
    exit 1
fi
echo "✅ Installation complete."
echo

# --- Final Instructions ---
echo "You can now run the slideshow from anywhere in your terminal by typing:"
echo "$> $INSTALL_NAME [options] /path/to/your/images"
echo
echo "To see all available options, run:"
echo "$> $INSTALL_NAME --help"
echo
