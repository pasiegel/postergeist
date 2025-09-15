import os
import random
import argparse
import cv2
from PIL import Image, ImageTk, ImageFilter, UnidentifiedImageError
import tkinter as tk
from screeninfo import get_monitors


# -----------------------------------------
# Poster Slideshow with Overlays
# -----------------------------------------

class PosterSlideshow:
    # --- Class constant for video frame rate ---
    FRAME_INTERVAL_MS = 1000 // 30  # Approx 30 FPS

    def __init__(self, root, folder, overlay_folder, delay, random_delay, start_rotation, fade_duration=1000):
        self.root = root
        self.folder = folder
        self.overlay_folder = overlay_folder
        self.delay = delay
        self.random_delay = random_delay

        self.files = self.load_files(folder)
        self.overlays = self.load_overlays(overlay_folder)

        self.running = True
        self.video_capture = None
        self.tk_img = None
        self.current_pil_img = None
        self.rotation = start_rotation % 360
        self.index = 0

        # fade settings
        self.fade_duration = fade_duration  # in ms
        self.fade_steps = 20  # number of blend steps

        self.canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        if self.files:
            self.shuffle_files()

        # keyboard controls
        root.bind("<Escape>", lambda e: self.exit_slideshow())
        root.bind("<Right>", lambda e: self.next_slide(manual=True))
        root.bind("<Left>", lambda e: self.prev_slide())
        root.bind("<space>", lambda e: self.toggle_pause())
        root.bind("r", lambda e: self.rotate_poster())
        root.bind("<F5>", lambda e: self.refresh_files())

        if not self.files:
            self.show_splash()
        else:
            # FIX: Delay the first call to allow the main window to be drawn first
            self.root.after(100, self.show_file)

    # -----------------------------------------
    # File loading
    # -----------------------------------------

    def load_files(self, folder):
        exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif",
                ".mp4", ".mov", ".avi", ".mkv")
        try:
            return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]
        except FileNotFoundError:
            print(f"Error: Main folder not found at '{folder}'")
            return []

    def load_overlays(self, overlay_folder):
        exts = (".png", ".jpg", ".jpeg", ".webp")
        overlays = []
        if overlay_folder and os.path.exists(overlay_folder):
            for f in os.listdir(overlay_folder):
                if f.lower().endswith(exts):
                    overlays.append(os.path.join(overlay_folder, f))
        return overlays

    def shuffle_files(self):
        random.seed()
        random.shuffle(self.files)
        self.index = random.randrange(len(self.files)) if self.files else 0

    def refresh_files(self):
        print("Refreshing file list...")
        self.files = self.load_files(self.folder)
        if not self.files:
            self.show_splash()
        else:
            self.shuffle_files()
            self.show_file()

    # -----------------------------------------
    # Image/Video display
    # -----------------------------------------

    def prepare_blurred_background(self, img):
        screen_w = self.root.winfo_width()
        screen_h = self.root.winfo_height()

        if screen_w < 2 or screen_h < 2:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()

        ratio = screen_w / img.width
        new_h = int(img.height * ratio)
        poster_resized = img.resize((screen_w, new_h), Image.LANCZOS)

        if new_h >= screen_h:
            final_poster = poster_resized.crop((0, 0, screen_w, screen_h))
            if self.rotation != 0:
                return final_poster.rotate(self.rotation, expand=True, resample=Image.BICUBIC)
            return final_poster

        bg = img.resize((screen_w, screen_h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))

        if self.rotation != 0:
            poster_resized = poster_resized.rotate(self.rotation, expand=True, resample=Image.BICUBIC)

        composited_layer = Image.new("RGBA", (screen_w, screen_h), (0, 0, 0, 0))

        px = (screen_w - poster_resized.width) // 2
        py = 0
        composited_layer.paste(poster_resized, (px, py))

        if self.overlays:
            overlay_path = random.choice(self.overlays)
            overlay = Image.open(overlay_path).convert("RGBA")
            overlay_resized = overlay.resize((screen_w, int(overlay.height * screen_w / overlay.width)), Image.LANCZOS)

            if self.rotation != 0:
                overlay_resized = overlay_resized.rotate(self.rotation, expand=True, resample=Image.BICUBIC)

            ox = (screen_w - overlay_resized.width) // 2
            oy = screen_h - overlay_resized.height
            composited_layer.paste(overlay_resized, (ox, oy), overlay_resized)

        bg.paste(composited_layer, (0, 0), composited_layer)
        return bg

    def fade_to_image(self, new_img, old_img):
        if old_img is None:
            self.tk_img = ImageTk.PhotoImage(new_img)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
            return

        step_delay = self.fade_duration // self.fade_steps

        def do_step(step=0):
            if not self.running and step > 0: return
            alpha = step / self.fade_steps
            blended = Image.blend(old_img, new_img, alpha)
            self.tk_img = ImageTk.PhotoImage(blended)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
            if step < self.fade_steps:
                self.root.after(step_delay, lambda: do_step(step + 1))

        do_step()

    def show_image(self, path):
        old_img = self.current_pil_img

        try:
            img = Image.open(path).convert("RGB")
            img = self.prepare_blurred_background(img)
            self.current_pil_img = img
            self.fade_to_image(img, old_img)
        except FileNotFoundError:
            print(f"Image Error: File not found at '{path}'. Skipping.")
            self.root.after(100, self.next_slide)
            return
        except UnidentifiedImageError:
            print(
                f"Image Error: Cannot identify or open image file '{os.path.basename(path)}'. It may be corrupt. Skipping.")
            self.root.after(100, self.next_slide)
            return
        except ValueError as e:
            print(f"Image Error: A value error occurred with '{os.path.basename(path)}' ({e}). Skipping.")
            self.root.after(100, self.next_slide)
            return
        except Exception as e:
            print(f"An unexpected error occurred with '{os.path.basename(path)}': {e}. Skipping.")
            self.root.after(100, self.next_slide)
            return

        delay = self.get_delay()
        self.root.after(delay, self.next_slide)

    def show_video(self, path):
        if self.video_capture:
            self.video_capture.release()
        self.video_capture = cv2.VideoCapture(path)
        if not self.video_capture.isOpened():
            print(f"Video Error: Could not open or read video file '{os.path.basename(path)}'. Skipping.")
            self.root.after(100, self.next_slide)
            return
        self.update_video_frame()

    def update_video_frame(self):
        if not self.running or not hasattr(self, 'video_capture') or not self.video_capture:
            return

        ret, frame = self.video_capture.read()
        if not ret:
            self.video_capture.release()
            self.video_capture = None
            delay = self.get_delay()
            self.root.after(delay, self.next_slide)
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)

        processed_img = self.prepare_blurred_background(img)
        self.current_pil_img = processed_img
        self.tk_img = ImageTk.PhotoImage(processed_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")

        self.root.after(self.FRAME_INTERVAL_MS, self.update_video_frame)

    # -----------------------------------------
    # Slideshow navigation
    # -----------------------------------------

    def get_delay(self):
        if self.random_delay:
            return random.randint(60, 300) * 1000
        else:
            return self.delay * 1000

    def show_file(self):
        if not self.files:
            self.show_splash()
            return

        path = self.files[self.index]
        if path.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
            self.show_video(path)
        else:
            self.show_image(path)

    def next_slide(self, manual=False):
        if (not self.running and not manual) or not self.files:
            return

        self.index = (self.index + 1) % len(self.files)
        if self.index == 0:
            self.shuffle_files()
        self.show_file()

    def prev_slide(self):
        if not self.files: return
        self.index = (self.index - 1) % len(self.files)
        self.show_file()

    def toggle_pause(self):
        self.running = not self.running
        print("Slideshow Paused" if not self.running else "Slideshow Resumed")
        if self.running:
            self.next_slide(manual=True)

    def exit_slideshow(self):
        self.running = False
        if self.video_capture:
            self.video_capture.release()
        self.root.destroy()

    def rotate_poster(self):
        self.rotation = (self.rotation + 90) % 360
        self.show_file()

    # -----------------------------------------
    # Splash screen
    # -----------------------------------------

    def show_splash(self):
        self.canvas.delete("all")
        screen_w = self.root.winfo_width() or self.root.winfo_screenwidth()
        screen_h = self.root.winfo_height() or self.root.winfo_screenheight()
        self.canvas.create_rectangle(0, 0, screen_w, screen_h, fill="black")
        self.canvas.create_text(
            screen_w // 2,
            screen_h // 2,
            text="Drop posters or videos into the 'posters' folder\n(Press F5 to refresh)",
            fill="white",
            font=("Helvetica", 32, "bold"),
            justify="center",
        )
        self.root.after(5000, self.refresh_files)


# -----------------------------------------
# Main
# -----------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Movie Poster Slideshow")
    parser.add_argument("folder", nargs="?", default="posters",
                        help="Folder with posters/videos (default: posters)")
    parser.add_argument("--overlays", default="overlays",
                        help="Folder with overlay images (default: overlays, ignored if missing)")
    # TYPO FIX: Removed extra hyphen from 'add_-argument'
    parser.add_argument("--delay", type=int, default=300,
                        help="Delay between slides in seconds (default 300s = 5min)")
    parser.add_argument("--random-delay", action="store_true",
                        help="Enable random delay between 1–5 minutes")
    parser.add_argument("--display", type=str, default="1",
                        help="Which display to use (1=primary, 2=secondary, 'all'=span)")
    parser.add_argument("--windowed", action="store_true",
                        help="Run in a resizable window instead of fullscreen")
    parser.add_argument("--rotate", type=int, default=0,
                        help="Starting rotation angle in degrees (0, 90, 180, 270)")
    args = parser.parse_args()

    if not os.path.exists(args.folder):
        os.makedirs(args.folder)
        print(f"Created missing posters folder: {args.folder}")

    overlay_folder = args.overlays if os.path.exists(args.overlays) else None

    root = tk.Tk()
    root.title("Poster Slideshow")
    monitors = get_monitors()

    if args.display == "all":
        total_w = sum(m.width for m in monitors)
        max_h = max(m.height for m in monitors)
        min_x = min(m.x for m in monitors)
        min_y = min(m.y for m in monitors)
        root.geometry(f"{total_w}x{max_h}+{min_x}+{min_y}")
    else:
        try:
            idx = int(args.display) - 1
            if not (0 <= idx < len(monitors)):
                raise ValueError
        except (ValueError, IndexError):
            print(f"Invalid display '{args.display}', defaulting to primary monitor (1).")
            idx = 0
        monitor = monitors[idx]
        root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")

    if not args.windowed:
        root.overrideredirect(True)
        root.config(cursor="none")

    PosterSlideshow(root, args.folder, overlay_folder,
                    args.delay, args.random_delay, args.rotate)
    root.mainloop()


if __name__ == "__main__":
    main()