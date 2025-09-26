import os
import random
import argparse
import cv2
from PIL import Image, ImageTk, ImageFilter, ImageSequence
import tkinter as tk
from screeninfo import get_monitors


# -----------------------------------------
# Postergeist Slideshow Class
# -----------------------------------------

class Postergeist:
    FRAME_INTERVAL_MS = 1000 // 30

    def __init__(self, root, folder, overlay_folder, delay, random_delay, start_rotation, fade_duration=1000,
                 fade_height=20, performance_mode=False):
        self.root = root
        self.folder = folder
        self.overlay_folder = overlay_folder
        self.delay = delay
        self.random_delay = random_delay
        self.fade_height_percent = fade_height
        self.performance_mode = performance_mode

        self.files = self.load_files(folder)
        self.overlays = self.load_overlays(overlay_folder)

        self.running = True
        self.video_capture = None
        self.tk_img = None

        # --- State Management ---
        self.current_pil_img_no_overlay = None
        self.current_pil_img_final = None
        self.rotation = start_rotation
        self.index = 0
        self.suppress_overlay = False
        self.cached_video_background = None

        # --- Job Scheduling IDs ---
        self.slideshow_job = None
        self.overlay_job = None

        # --- Overlay Animation State ---
        self.active_overlay_path = None
        self.active_overlay_frames = []
        self.active_overlay_index = 0
        self.active_overlay_duration = 100

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
        file_list = []
        try:
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(exts):
                        file_list.append(os.path.join(root, f))
            return file_list
        except FileNotFoundError:
            return []

    def load_overlays(self, overlay_folder):
        exts = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".apng")
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

    def prepare_base_frame(self, img_to_process, is_video=False):
        screen_w = self.root.winfo_width()
        screen_h = self.root.winfo_height()
        is_portrait_rot = self.rotation in [90, 270]
        canvas_w = screen_h if is_portrait_rot else screen_w
        canvas_h = screen_w if is_portrait_rot else screen_h

        if is_video and self.cached_video_background:
            background = self.cached_video_background.copy()
        else:
            background = img_to_process.resize((canvas_w, canvas_h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
            if is_video:
                self.cached_video_background = background.copy()

        poster = img_to_process.copy()
        poster.thumbnail((canvas_w, canvas_h), Image.LANCZOS)
        p_w, p_h = poster.size

        if p_h >= canvas_h * 0.99:
            self.suppress_overlay = True
        else:
            self.suppress_overlay = False
            if not self.performance_mode:
                glow = poster.filter(ImageFilter.GaussianBlur(25))
                glow_x = (canvas_w - p_w) // 2
                glow_y = 5
                background.paste(glow, (glow_x, glow_y), glow)

        poster_x = (canvas_w - p_w) // 2
        poster_y = 0
        background.paste(poster, (poster_x, poster_y), poster)
        self.current_pil_img_no_overlay = background

    def _update_canvas(self):
        if not self.current_pil_img_no_overlay:
            return
        img_with_overlay = self.current_pil_img_no_overlay.copy()
        if self.active_overlay_path and not self.suppress_overlay:
            try:
                overlay_img = None
                if self.active_overlay_frames:
                    overlay_img = self.active_overlay_frames[self.active_overlay_index]
                else:
                    overlay_img = Image.open(self.active_overlay_path)
                canvas_w = img_with_overlay.width
                canvas_h = img_with_overlay.height
                overlay = overlay_img.copy()
                overlay.thumbnail((canvas_w, canvas_h // 3), Image.LANCZOS)
                overlay_x = (canvas_w - overlay.width) // 2
                overlay_y = canvas_h - overlay.height
                if overlay.mode in ("RGBA", "LA"):
                    img_with_overlay.paste(overlay, (overlay_x, overlay_y), overlay)
                else:
                    img_with_overlay.paste(overlay, (overlay_x, overlay_y))
            except Exception as e:
                print(f"Error processing overlay {os.path.basename(self.active_overlay_path)}: {e}")
                self.active_overlay_path = None

        if self.rotation != 0:
            final_img = img_with_overlay.rotate(self.rotation, expand=True)
        else:
            final_img = img_with_overlay
        self.current_pil_img_final = final_img
        self.tk_img = ImageTk.PhotoImage(final_img)
        self.canvas.delete("all")
        self.canvas.create_image(self.root.winfo_width() // 2, self.root.winfo_height() // 2, image=self.tk_img)

    def fade_to_new_slide(self, new_base_img):
        old_final_img = self.current_pil_img_final
        self.current_pil_img_no_overlay = new_base_img
        self._update_canvas()
        new_final_img = self.current_pil_img_final
        if old_final_img is None or self.fade_duration == 0:
            return
        step_delay = self.fade_duration // self.fade_steps

        def do_step(step=0):
            if not self.running and step > 0: return
            alpha = step / self.fade_steps
            blended = Image.blend(old_final_img, new_final_img, alpha)
            self.tk_img = ImageTk.PhotoImage(blended)
            self.canvas.delete("all")
            self.canvas.create_image(self.root.winfo_width() // 2, self.root.winfo_height() // 2, image=self.tk_img)
            if step < self.fade_steps:
                self.root.after(step_delay, lambda: do_step(step + 1))

        do_step()

    def _select_new_overlay(self, media_path):
        self.active_overlay_path = None
        self.active_overlay_frames = []
        self.active_overlay_index = 0
        tagged_overlay_found = False

        folder_name = os.path.basename(os.path.dirname(media_path))

        if '_' in folder_name:
            tag = folder_name.rsplit('_', 1)[-1]
            for overlay_file_path in self.overlays:
                overlay_filename_no_ext = os.path.splitext(os.path.basename(overlay_file_path))[0]
                if overlay_filename_no_ext == tag:
                    self.active_overlay_path = overlay_file_path
                    tagged_overlay_found = True
                    break

        if not tagged_overlay_found and self.overlays:
            self.active_overlay_path = random.choice(self.overlays)

        if self.active_overlay_path and self.active_overlay_path.lower().endswith((".gif", ".apng")):
            try:
                with Image.open(self.active_overlay_path) as img:
                    self.active_overlay_duration = img.info.get('duration', 100)
                    self.active_overlay_frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
            except Exception as e:
                print(f"Error loading animated overlay {os.path.basename(self.active_overlay_path)}: {e}")
                self.active_overlay_path = None

    def show_image(self, path):
        self.cached_video_background = None
        self._select_new_overlay(path)
        try:
            with Image.open(path) as img:
                img_rgba = img.convert("RGBA")
                self.prepare_base_frame(img_rgba, is_video=False)
                self.fade_to_new_slide(self.current_pil_img_no_overlay)
        except Exception as e:
            print(f"Error processing image '{os.path.basename(path)}': {e}. Skipping.")
            self.slideshow_job = self.root.after(100, self.next_slide)
            return
        if self.active_overlay_frames:
            self._animate_overlay()
        self.slideshow_job = self.root.after(self.get_delay(), self.next_slide)

    def show_video(self, path):
        self.cached_video_background = None
        if self.video_capture: self.video_capture.release()
        self.video_capture = cv2.VideoCapture(path)
        if not self.video_capture.isOpened():
            print(f"Error opening video '{os.path.basename(path)}'. Skipping.")
            self.root.after(100, self.next_slide)
            return

        vid_w = self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        vid_h = self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        screen_w = self.root.winfo_width()
        screen_h = self.root.winfo_height()
        if vid_w < screen_w * 0.95 or vid_h < screen_h * 0.95:
            self._select_new_overlay(path)
        else:
            self.active_overlay_path = None
            self.active_overlay_frames = []
        if self.active_overlay_frames:
            self._animate_overlay()
        self.update_video_frame()

    def update_video_frame(self):
        if not self.running or not self.video_capture: return
        ret, frame = self.video_capture.read()
        if not ret:
            self.video_capture.release()
            self.video_capture = None
            self.slideshow_job = self.root.after(self.get_delay(), self.next_slide)
            return
        frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(frame_rgba)
        self.prepare_base_frame(img, is_video=True)
        self._update_canvas()
        self.root.after(self.FRAME_INTERVAL_MS, self.update_video_frame)

    def _animate_overlay(self):
        if not self.running or not self.active_overlay_frames: return
        self.active_overlay_index = (self.active_overlay_index + 1) % len(self.active_overlay_frames)
        self._update_canvas()
        self.overlay_job = self.root.after(self.active_overlay_duration, self._animate_overlay)

    def get_delay(self):
        if self.random_delay:
            return random.randint(60, 300) * 1000
        else:
            return self.delay * 1000

    def cancel_scheduled_jobs(self):
        if self.slideshow_job:
            self.root.after_cancel(self.slideshow_job)
        if self.overlay_job:
            self.root.after_cancel(self.overlay_job)
        self.slideshow_job = None
        self.overlay_job = None

    def show_file(self):
        self.cancel_scheduled_jobs()
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
            self.cancel_scheduled_jobs()
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None

    def exit_slideshow(self):
        self.running = False
        if self.video_capture: self.video_capture.release()
        self.root.destroy()

    def rotate_poster(self):
        self.rotation = (self.rotation + 90) % 360
        self.cached_video_background = None
        if self.video_capture and self.video_capture.isOpened():
            self.show_file()
        else:
            if self.files:
                self.show_image(self.files[self.index])

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
    parser.add_argument("--overlays", default="overlays", help="Folder with overlay images/gifs/apngs")
    parser.add_argument("--delay", type=int, default=300, help="Delay between slides in seconds")
    parser.add_argument("--random-delay", action="store_true", help="Enable random delay between 1–5 minutes")
    parser.add_argument("--display", type=str, default="1", help="Which display to use (1, 2, 'all')")
    parser.add_argument("--windowed", action="store_true", help="Run in a window")
    parser.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270], help="Starting rotation")
    parser.add_argument("--fade-height", type=int, default=20,
                        help="Fade height at bottom of poster as a percentage (e.g., 20)")
    parser.add_argument("--performance-mode", action="store_true",
                        help="Disable intensive effects like glow for better performance")
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

    Postergeist(root, args.folder, overlay_folder, args.delay, args.random_delay, args.rotate,
                fade_height=args.fade_height, performance_mode=args.performance_mode)
    root.mainloop()


if __name__ == "__main__":
    main()
