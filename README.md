<p align="center">
  <img src="https://i.imgur.com/YGI5vqk.png" alt="Postergeist Logo" width="250">
</p>
# Postergeist 👻

*Your personal, python-powered poster slideshow.*

---


[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Postergeist is a highly customizable, fullscreen slideshow application perfect for displaying your movie poster collection on a dedicated monitor or TV. It automatically creates blurred backgrounds and supports both images and videos. It's designed to be run from the command line and is ideal for a low-power, set-it-and-forget-it setup like a Raspberry Pi.

---

## Features

-   **Image & Video Support**: Displays a wide range of file types, including `.jpg`, `.png`, `.webp`, `.mp4`, `.mkv`, and more.
-   **Dynamic Backgrounds**: Automatically generates a blurred, fullscreen background from the current poster for a seamless look.
-   **Custom Overlays**: Add your own transparent `.png` overlays (like a "Now Showing" banner) that are randomly selected.
-   **Multi-Monitor Control**: Choose which display to run on, or span across all monitors.
-   **Flexible Timing**: Set a fixed delay between slides or use a random delay for a more natural feel.
-   **Full Keyboard Control**: Pause, play, skip, go back, rotate posters, and refresh the file list with simple hotkeys.
-   **Raspberry Pi Ready**: Lightweight and includes instructions for easy autostart on boot.

---

## Installation

These instructions are for a standard desktop (Windows, macOS, Linux). See the next section for Raspberry Pi-specific setup.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/pasiegel/postergeist.git](https://github.com/pasiegel/postergeist.git)
    cd postergeist
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    You will need a `requirements.txt` file with the necessary Python packages.
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If you don't have a `requirements.txt` file, you can install the packages manually: `pip install opencv-python Pillow screeninfo`)*

4.  **Create Folders:**
    Create a folder named `posters` in the project directory and add your image and video files. Optionally, create an `overlays` folder and add any `.png` overlays you'd like to use.

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

## Command-Line Parameters

You can customize the slideshow's behavior using the following command-line arguments.

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `folder` | `posters` | The path to the folder containing your image and video files. This is a positional argument. |
| `--overlays` | `overlays` | Specifies a folder with overlay images (e.g., `.png` files) to be randomly displayed on top of the media. |
| `--delay` | `300` | The delay in seconds between each slide. Defaults to 5 minutes. |
| `--random-delay`| `False` | When present, this flag overrides `--delay` and uses a random delay between 1 and 5 minutes for each slide. |
| `--display` | `1` | Selects which display monitor to use. Use `1` for the primary monitor, `2` for secondary, and so on. Use `all` to span the slideshow across all connected monitors. |
| `--windowed` | `False` | If included, the application will run in a standard resizable window instead of fullscreen mode. |
| `--rotate` | `0` | Sets an initial rotation angle for all media. Valid values are `0`, `90`, `180`, and `270`. |

---

## Raspberry Pi Kiosk Setup

To have Postergeist run automatically on a Raspberry Pi when it boots:

1.  **Follow steps 1, 3, and 4 from the installation section above.** A virtual environment is optional but still recommended on a Pi.

2.  **Install System Dependencies:**
    Ensure you have Python's Tkinter library installed, which is required for the GUI.
    ```bash
    sudo apt-get update
    sudo apt-get install python3-tk
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

## Usage

Run the script from the command line.

**Basic command:**
```bash
python postergeist.py
