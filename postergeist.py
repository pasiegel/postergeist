import os
import random
import argparse
import cv2
from PIL import Image, ImageTk, ImageFilter
import tkinter as tk
from screeninfo import get_monitors


# -----------------------------------------
# Postergeist Slideshow Class
# -----------------------------------------

class Postergeist:
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
        self.rotation = start_rotation
        self.index = 0
        self.after_id = None
        self.splash_text_id = None

        self.fade_duration = fade_duration
        self.fade_steps = 20

        self.canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        if self.files:
            self.shuffle_files()

        root.bind("<Escape>", lambda e: self.exit_slideshow())
        root.bind("<Right>", lambda e: self.next_slide(manual=True))
        root.bind("<Left>", lambda e: self.prev_slide())
        root.bind("<space>", lambda e: self.toggle_pause())
        root.bind("r", lambda e: self.rotate_poster())
        root.bind("<F5>", lambda e: self.refresh_files())

        if not self.files:
            self.root.after(100, self.show_splash)
        else:
            self.root.after(100, self.show_file)

    def load_files(self, folder):
        exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".mp4", ".mov", ".avi", ".mkv")
        try:
            return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]
        except FileNotFoundError:
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
        random.shuffle(self.files)
        self.index = random.randrange(len(self.files)) if self.files else 0

    def refresh_files(self):
        self.files = self.load_files(self.folder)
        if not self.files:
            self.show_splash()
        else:
            self.shuffle_files()
            self.show_file()

    def prepare_image_frame(self, img_to_process):
        screen_w = self.root.winfo_width()
        screen_h = self.root.winfo_height()

        is_portrait_rot = self.rotation in [90, 270]
        canvas_w = screen_h if is_portrait_rot else screen_w
        canvas_h = screen_w if is_portrait_rot else screen_h

        background = img_to_process.resize((canvas_w, canvas_h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))

        poster = img_to_process.copy()
        poster.thumbnail((canvas_w, canvas_h), Image.LANCZOS)
        poster_x = (canvas_w - poster.width) // 2
        poster_y = 0
        background.paste(poster, (poster_x, poster_y))

        if self.overlays:
            overlay_path = random.choice(self.overlays)
            try:
                with Image.open(overlay_path) as overlay_img:
                    overlay = overlay_img.copy()
                    overlay.thumbnail((canvas_w, canvas_h // 3), Image.LANCZOS)
                    overlay_x = (canvas_w - overlay.width) // 2
                    overlay_y = canvas_h - overlay.height
                    if overlay.mode in ("RGBA", "LA"):
                        background.paste(overlay, (overlay_x, overlay_y), overlay)
                    else:
                        background.paste(overlay, (overlay_x, overlay_y))
            except Exception as e:
                print(f"Error loading overlay {os.path.basename(overlay_path)}: {e}")

        if self.rotation != 0:
            final_img = background.rotate(self.rotation, expand=True)
        else:
            final_img = background

        return final_img

    def fade_to_image(self, new_img, old_img):
        if old_img is None or self.fade_duration == 0:
            self.tk_img = ImageTk.PhotoImage(new_img)
            self.canvas.delete("all")
            self.canvas.create_image(self.root.winfo_width() // 2, self.root.winfo_height() // 2, image=self.tk_img)
            return

        step_delay = self.fade_duration // self.fade_steps

        def do_step(step=0):
            if not self.running and step > 0: return
            alpha = step / self.fade_steps
            blended = Image.blend(old_img, new_img, alpha)
            self.tk_img = ImageTk.PhotoImage(blended)
            self.canvas.delete("all")
            self.canvas.create_image(self.root.winfo_width() // 2, self.root.winfo_height() // 2, image=self.tk_img)
            if step < self.fade_steps:
                self.root.after(step_delay, lambda: do_step(step + 1))

        do_step()

    def show_image(self, path):
        old_img = self.current_pil_img
        try:
            with Image.open(path) as img:
                img_rgb = img.convert("RGB")
                final_frame = self.prepare_image_frame(img_rgb)
                self.current_pil_img = final_frame
                self.fade_to_image(final_frame, old_img)
        except Exception as e:
            print(f"Error processing image '{os.path.basename(path)}': {e}. Skipping.")
            self.after_id = self.root.after(100, self.next_slide)
            return
        self.after_id = self.root.after(self.get_delay(), self.next_slide)

    def show_video(self, path):
        if self.video_capture: self.video_capture.release()
        self.video_capture = cv2.VideoCapture(path)
        if not self.video_capture.isOpened():
            print(f"Error opening video '{os.path.basename(path)}'. Skipping.")
            self.root.after(100, self.next_slide)
            return
        self.update_video_frame()

    def update_video_frame(self):
        if not self.running or not self.video_capture: return
        ret, frame = self.video_capture.read()
        if not ret:
            self.video_capture.release()
            self.video_capture = None
            self.after_id = self.root.after(self.get_delay(), self.next_slide)
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        final_frame = self.prepare_image_frame(img)
        self.current_pil_img = final_frame
        self.tk_img = ImageTk.PhotoImage(final_frame)
        self.canvas.delete("all")
        self.canvas.create_image(self.root.winfo_width() // 2, self.root.winfo_height() // 2, image=self.tk_img)
        self.root.after(self.FRAME_INTERVAL_MS, self.update_video_frame)

    def get_delay(self):
        if self.random_delay:
            return random.randint(60, 300) * 1000
        else:
            return self.delay * 1000

    def cancel_scheduled_next_slide(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def show_file(self):
        if self.splash_text_id:
            self.root.unbind("<Configure>")
            self.splash_text_id = None

        self.cancel_scheduled_next_slide()
        if not self.files:
            self.show_splash()
            return
        path = self.files[self.index]
        if path.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
            self.show_video(path)
        else:
            self.show_image(path)

    def next_slide(self, manual=False):
        if (not self.running and not manual) or not self.files: return
        self.index = (self.index + 1) % len(self.files)
        if self.index == 0: self.shuffle_files()
        self.show_file()

    def prev_slide(self):
        if not self.files: return
        self.index = (self.index - 1) % len(self.files)
        self.show_file()

    def toggle_pause(self):
        self.running = not self.running
        if self.running:
            self.next_slide(manual=True)
        else:
            self.cancel_scheduled_next_slide()

    def exit_slideshow(self):
        self.running = False
        if self.video_capture: self.video_capture.release()
        self.root.destroy()

    def rotate_poster(self):
        self.rotation = (self.rotation + 90) % 360
        self.show_file()

    def show_splash(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, w, h, fill="black")
        self.splash_text_id = self.canvas.create_text(
            w // 2, h // 2,
            text="Drop media into the 'posters' folder\n(Press F5 to refresh)",
            fill="white", font=("Helvetica", 32, "bold"), justify="center"
        )
        self.root.bind("<Configure>", self.on_resize_splash)

    def on_resize_splash(self, event):
        if self.splash_text_id:
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            self.canvas.coords(1, 0, 0, w, h)
            self.canvas.coords(self.splash_text_id, w // 2, h // 2)


# -----------------------------------------
# Main Execution
# -----------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Postergeist Slideshow")
    parser.add_argument("folder", nargs="?", default="posters", help="Folder with posters/videos")
    parser.add_argument("--overlays", default="overlays", help="Folder with overlay images")
    parser.add_argument("--delay", type=int, default=300, help="Delay between slides in seconds")
    parser.add_argument("--random-delay", action="store_true", help="Enable random delay between 1–5 minutes")
    parser.add_argument("--display", type=str, default="1", help="Which display to use (1, 2, 'all')")
    parser.add_argument("--windowed", action="store_true", help="Run in a window")
    parser.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270], help="Starting rotation")
    args = parser.parse_args()

    if not os.path.exists(args.folder):
        os.makedirs(args.folder)
        print(f"Created missing posters folder: {args.folder}")

    if not os.path.exists(args.overlays):
        os.makedirs(args.overlays)
        print(f"Created missing overlays folder: {args.overlays}")
    overlay_folder = args.overlays

    root = tk.Tk()
    root.title("Postergeist")

    monitors = get_monitors()
    if args.display == "all":
        w = sum(m.width for m in monitors)
        h = max(m.height for m in monitors)
        x = min(m.x for m in monitors)
        y = min(m.y for m in monitors)
        root.geometry(f"{w}x{h}+{x}+{y}")
    else:
        try:
            idx = int(args.display) - 1
            monitor = monitors[idx]
            root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        except (ValueError, IndexError):
            print("Invalid display, using primary.")
            monitor = monitors[0]
            root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")

    if not args.windowed:
        root.overrideredirect(True)
        root.config(cursor="none")

    Postergeist(root, args.folder, overlay_folder, args.delay, args.random_delay, args.rotate)
    root.mainloop()


if __name__ == "__main__":
    main()
