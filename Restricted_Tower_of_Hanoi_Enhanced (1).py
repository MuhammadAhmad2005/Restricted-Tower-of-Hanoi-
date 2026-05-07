import tkinter as tk
from tkinter import ttk
import json
import os
import math
import threading
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ─── Try to import sound libraries (optional) ───────────────────────────────
try:
    import winsound
    SOUND_BACKEND = "winsound"
except ImportError:
    try:
        import pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        SOUND_BACKEND = "pygame"
    except ImportError:
        SOUND_BACKEND = None

# ════════════════════════════════════════════════════════════════════════════
#  SOUND ENGINE
# ════════════════════════════════════════════════════════════════════════════
class SoundEngine:
    """Cross-platform sound: generates tones via pygame or winsound."""

    def __init__(self):
        self.enabled = True
        self._lock = threading.Lock()

    def _play_pygame(self, freq, duration_ms, volume=0.6):
        try:
            import pygame, numpy as np
            sr = 44100
            n  = int(sr * duration_ms / 1000)
            t  = np.linspace(0, duration_ms / 1000, n, False)
            wave = (np.sin(2 * np.pi * freq * t) * 32767 * volume).astype(np.int16)
            # Fade out last 20 %
            fade = int(n * 0.2)
            wave[-fade:] = (wave[-fade:] * np.linspace(1, 0, fade)).astype(np.int16)
            sound = pygame.sndarray.make_sound(wave)
            sound.play()
        except Exception:
            pass

    def _beep_thread(self, freq, duration_ms):
        if SOUND_BACKEND == "winsound":
            try:
                winsound.Beep(max(37, min(32767, freq)), duration_ms)
            except Exception:
                pass
        elif SOUND_BACKEND == "pygame":
            self._play_pygame(freq, duration_ms)

    def play(self, kind):
        if not self.enabled:
            return
        configs = {
            "move":    (520, 80),
            "invalid": (220, 180),
            "undo":    (400, 100),
            "hint":    (660, 120),
            "win":     (880, 400),
            "solve":   (600, 60),
        }
        freq, dur = configs.get(kind, (440, 100))
        t = threading.Thread(target=self._beep_thread, args=(freq, dur), daemon=True)
        t.start()


sound = SoundEngine()

# ════════════════════════════════════════════════════════════════════════════
#  DATA HANDLING
# ════════════════════════════════════════════════════════════════════════════
RECORDS_FILE = "records.json"

def load_records():
    default_data = {
        "3": {"name": "-", "moves": 999, "time": 0},
        "4": {"name": "-", "moves": 999, "time": 0},
        "5": {"name": "-", "moves": 999, "time": 0},
        "6": {"name": "-", "moves": 999, "time": 0}
    }
    if os.path.exists(RECORDS_FILE):
        try:
            with open(RECORDS_FILE, "r") as f:
                data = json.load(f)
                if not isinstance(data, dict) or "3" not in data:
                    return default_data
                return data
        except (json.JSONDecodeError, ValueError, TypeError):
            return default_data
    return default_data

def save_record(name, moves, time_val, level):
    records = load_records()
    lvl_str = str(level)
    if moves < records[lvl_str].get("moves", 999):
        records[lvl_str] = {"name": name, "moves": moves, "time": time_val}
        with open(RECORDS_FILE, "w") as f:
            json.dump(records, f)
        return True
    return False

# ════════════════════════════════════════════════════════════════════════════
#  RESTRICTED HANOI SOLVER  (generates optimal move sequence)
# ════════════════════════════════════════════════════════════════════════════
def restricted_hanoi_moves(n, src, mid, dst, moves_list):
    """
    Recursively generate the optimal move list for Restricted Tower of Hanoi.
    Rules: S↔M and M↔D only — no direct S↔D.
    """
    if n == 0:
        return
    restricted_hanoi_moves(n - 1, src, dst, mid, moves_list)   # n-1 disks: src→mid  (via dst)
    moves_list.append((src, mid))                               # move disk n: src→mid
    restricted_hanoi_moves(n - 1, dst, src, mid, moves_list)   # n-1 disks: dst→mid  (via src)  -- wait: wrong
    moves_list.append((mid, dst))                               # move disk n: mid→dst
    restricted_hanoi_moves(n - 1, src, dst, mid, moves_list)   # n-1 disks: src→mid  (via dst)  -- wait

# Correct recursive algorithm for Restricted Hanoi (Frame-Stewart-like):
def solve_restricted(n, src, mid, dst, moves_list):
    """
    Restricted Hanoi: only S↔M and M↔D moves allowed.
    To move n disks from src to dst via mid (mandatory):
      1. Move top n-1 from src to dst (using mid)
      2. Move disk n from src to mid
      3. Move top n-1 from dst to src (using mid)
      4. Move disk n from mid to dst
      5. Move top n-1 from src to dst (using mid)
    """
    if n == 0:
        return
    solve_restricted(n - 1, src, mid, dst, moves_list)
    moves_list.append((src, mid))
    solve_restricted(n - 1, dst, mid, src, moves_list)
    moves_list.append((mid, dst))
    solve_restricted(n - 1, src, mid, dst, moves_list)

# ════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ════════════════════════════════════════════════════════════════════════════
class HanoiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Restricted Tower of Hanoi — Enhanced")
        self.root.geometry("700x650")
        self.root.resizable(False, False)

        self.container = tk.Frame(root, bg="#f0f0f0")
        self.container.pack(fill="both", expand=True)

        self.bg_images = {}
        self.load_images()
        self.show_main_menu()

    def load_images(self):
        for img_name in ["background.png", "background1.png", "background2.png"]:
            if os.path.exists(img_name) and PIL_AVAILABLE:
                try:
                    img = Image.open(img_name)
                    if img_name == "background2.png":
                        img = img.resize((600, 400), Image.Resampling.LANCZOS)
                    else:
                        img = img.resize((700, 650), Image.Resampling.LANCZOS)
                    self.bg_images[img_name] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Error loading {img_name}: {e}")

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def set_menu_background(self, img_name):
        self.clear_container()
        self.canvas = tk.Canvas(self.container, width=700, height=650, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        if img_name in self.bg_images:
            self.canvas.create_image(0, 0, image=self.bg_images[img_name], anchor="nw")
        else:
            self.canvas.configure(bg="#2c3e50")
        return self.canvas

    # ── MAIN MENU ─────────────────────────────────────────────────────────
    def show_main_menu(self):
        canvas = self.set_menu_background("background.png")
        canvas.create_text(350, 110, text="Restricted Tower of Hanoi",
                           font=("Helvetica", 24, "bold"), fill="white" if "background.png" not in self.bg_images else "black")

        style = {"width": 20, "font": ("Helvetica", 12), "pady": 8, "bg": "#e1e1e1", "relief": "raised"}
        canvas.create_window(350, 260, window=tk.Button(self.container, text="Start Game",   **style, command=self.show_difficulty_menu))
        canvas.create_window(350, 320, window=tk.Button(self.container, text="View Records", **style, command=self.show_records))
        canvas.create_window(350, 380, window=tk.Button(self.container, text="Quit",         **style, command=self.root.destroy))

        # Sound toggle on main menu
        snd_frame = tk.Frame(self.container, bg="#e1e1e1", relief="flat")
        snd_lbl = tk.Label(snd_frame, text="🔊 Sound:", font=("Helvetica", 10), bg="#e1e1e1")
        snd_lbl.pack(side=tk.LEFT, padx=4)
        self._snd_var = tk.BooleanVar(value=sound.enabled)
        snd_chk = tk.Checkbutton(snd_frame, variable=self._snd_var, bg="#e1e1e1",
                                  command=lambda: setattr(sound, "enabled", self._snd_var.get()))
        snd_chk.pack(side=tk.LEFT)
        canvas.create_window(350, 440, window=snd_frame)

    # ── RECORDS ───────────────────────────────────────────────────────────
    def show_records(self):
        win = tk.Toplevel(self.root)
        win.title("High Scores")
        win.geometry("500x350")
        win.configure(bg="#f0f0f0")
        tk.Label(win, text="Leaderboard", font=("Helvetica", 16, "bold"), bg="#f0f0f0").pack(pady=15)

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 10), rowheight=25)
        tree = ttk.Treeview(win, columns=("Level", "Name", "Moves", "Time"), show="headings")
        for col in ["Level", "Name", "Moves", "Time"]:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        records = load_records()
        for lvl in ["3", "4", "5", "6"]:
            r = records.get(lvl, {"name": "-", "moves": 999, "time": 0})
            tree.insert("", "end", values=(lvl, r["name"], r["moves"], f"{r['time']}s"))
        tk.Button(win, text="Close", command=win.destroy).pack(pady=15)

    # ── DIFFICULTY MENU ───────────────────────────────────────────────────
    def show_difficulty_menu(self):
        canvas = self.set_menu_background("background1.png")
        canvas.create_text(350, 80, text="Select Difficulty", font=("Helvetica", 20, "bold"), fill="black")

        f = tk.Frame(self.container, bg="#f0f0f0")
        tk.Label(f, text="Enter Player Name:", bg="#f0f0f0").pack()
        self.name_entry = tk.Entry(f, font=("Helvetica", 12), width=20)
        self.name_entry.insert(0, "Player")
        self.name_entry.pack(pady=5)
        canvas.create_window(350, 150, window=f)

        grid_frame = tk.Frame(self.container, bg="#f0f0f0")
        level_colors = ["#4A90E2", "#7ED321", "#F5A623", "#D0021B"]
        opt_moves    = [26, 80, 242, 728]
        for i, level in enumerate(range(3, 7)):
            inner = tk.Frame(grid_frame, bg="#f0f0f0")
            tk.Button(inner, text=f"Level {level}", bg=level_colors[i], fg="white",
                      font=("Helvetica", 12, "bold"), width=10, height=2,
                      command=lambda l=level: self.start_game(self.name_entry.get(), l)
                      ).pack()
            tk.Label(inner, text=f"Optimal: {opt_moves[i]} moves",
                     font=("Helvetica", 8), bg="#f0f0f0", fg="#555").pack()
            inner.grid(row=i // 2, column=i % 2, padx=10, pady=8)
        canvas.create_window(350, 310, window=grid_frame)

        canvas.create_window(350, 460, window=tk.Button(self.container, text="Back",
                              font=("Helvetica", 10), command=self.show_main_menu))

    def start_game(self, name, diff):
        self.clear_container()
        GameInterface(self.container, self, diff, name if name.strip() else "Player")


# ════════════════════════════════════════════════════════════════════════════
#  GAME INTERFACE
# ════════════════════════════════════════════════════════════════════════════
class GameInterface:
    DISK_H   = 20
    DISK_GAP = 5
    BASE_Y   = 310          # top of base platform
    ROD_TOP  = 100

    def __init__(self, parent, app, n, player_name):
        self.parent      = parent
        self.app         = app
        self.n           = n
        self.player_name = player_name
        self.move_count  = 0
        self.time_elapsed = 0
        self.paused      = False
        self.game_over   = False

        self.towers   = {"S": list(range(n, 0, -1)), "M": [], "D": []}
        self.tower_x  = {"S": 100, "M": 300, "D": 500}
        self.tower_lbl = {"S": "Source", "M": "Middle", "D": "Destination"}

        self.disk_colors = ["#90EE90", "#00FF7F", "#D8BFD8", "#FFD700", "#FF69B4", "#87CEFA"]
        self.disk_items  = {}
        self.drag_data   = {"item": None, "x": 0, "y": 0, "tower": None, "disk": None}

        # ── NEW: history stack for Undo ─────────────────────────────
        self.history = []           # list of (towers_snapshot, move_count)

        # ── NEW: hint / auto-solve state ────────────────────────────
        self.hint_highlight  = None   # canvas item id of hint glow
        self._optimal_moves  = []     # full optimal move sequence from current state
        self._solve_running  = False
        self._solve_after_id = None

        # ── NEW: animation state ─────────────────────────────────────
        self._anim_running   = False

        self._build_ui()
        self.draw()
        self.tick()

    # ── UI CONSTRUCTION ───────────────────────────────────────────────────
    def _build_ui(self):
        # Canvas
        self.canvas = tk.Canvas(self.parent, width=600, height=400, highlightthickness=0, bg="#aed6f1")
        self.canvas.pack(pady=(10, 2))
        if "background2.png" in self.app.bg_images:
            self.canvas.create_image(0, 0, image=self.app.bg_images["background2.png"], anchor="nw")

        # Info bar
        self.info_label = tk.Label(self.parent,
            text=f"Player: {self.player_name} | Moves: 0 | Time: 0s | Optimal: {3**self.n - 1}",
            font=("Helvetica", 10), bg="#f0f0f0")
        self.info_label.pack()

        # Status
        self.status_label = tk.Label(self.parent, text="", fg="red",
                                     font=("Helvetica", 10, "bold"), bg="#f0f0f0")
        self.status_label.pack(pady=2)

        # ── Button row 1: game controls ──────────────────────────────
        row1 = tk.Frame(self.parent, bg="#f0f0f0")
        row1.pack(pady=2)

        self.pause_btn = tk.Button(row1, text="⏸ Pause", width=10,
                                   font=("Helvetica", 10), command=self.toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, padx=4)

        self.undo_btn = tk.Button(row1, text="↩ Undo", width=10,
                                  font=("Helvetica", 10), bg="#f39c12", fg="white",
                                  command=self.undo_move)
        self.undo_btn.pack(side=tk.LEFT, padx=4)

        self.hint_btn = tk.Button(row1, text="💡 Hint", width=10,
                                  font=("Helvetica", 10), bg="#27ae60", fg="white",
                                  command=self.show_hint)
        self.hint_btn.pack(side=tk.LEFT, padx=4)

        self.solve_btn = tk.Button(row1, text="▶ Auto-Solve", width=12,
                                   font=("Helvetica", 10), bg="#8e44ad", fg="white",
                                   command=self.toggle_auto_solve)
        self.solve_btn.pack(side=tk.LEFT, padx=4)

        # ── Button row 2: navigation / sound ─────────────────────────
        row2 = tk.Frame(self.parent, bg="#f0f0f0")
        row2.pack(pady=2)

        tk.Button(row2, text="🏠 Menu", width=10, font=("Helvetica", 10),
                  command=self._safe_back_to_menu).pack(side=tk.LEFT, padx=4)

        self._snd_var = tk.BooleanVar(value=sound.enabled)
        tk.Checkbutton(row2, text="🔊 Sound", variable=self._snd_var, bg="#f0f0f0",
                       font=("Helvetica", 10),
                       command=lambda: setattr(sound, "enabled", self._snd_var.get())
                       ).pack(side=tk.LEFT, padx=4)

        # ── Speed slider for auto-solve ───────────────────────────────
        speed_frame = tk.Frame(self.parent, bg="#f0f0f0")
        speed_frame.pack(pady=2)
        tk.Label(speed_frame, text="Auto-Solve Speed:", font=("Helvetica", 9), bg="#f0f0f0").pack(side=tk.LEFT)
        self.speed_var = tk.IntVar(value=600)   # ms between moves
        tk.Scale(speed_frame, from_=100, to=1500, orient=tk.HORIZONTAL,
                 variable=self.speed_var, length=180, showvalue=False,
                 bg="#f0f0f0", label="Fast ◀─────▶ Slow").pack(side=tk.LEFT)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>",   self.on_press)
        self.canvas.bind("<B1-Motion>",        self.on_drag)
        self.canvas.bind("<ButtonRelease-1>",  self.on_release)

    # ── TIMER ─────────────────────────────────────────────────────────────
    def tick(self):
        if not self.paused and not self.game_over:
            self.time_elapsed += 1
            self._update_info()
        self.parent.after(1000, self.tick)

    def _update_info(self):
        opt = 3 ** self.n - 1
        extra = self.move_count - opt
        extra_str = f" (+{extra} extra)" if extra > 0 and self.move_count > 0 else ""
        self.info_label.config(
            text=f"Player: {self.player_name} | Moves: {self.move_count}{extra_str} | "
                 f"Time: {self.time_elapsed}s | Optimal: {opt}")

    # ── PAUSE ─────────────────────────────────────────────────────────────
    def toggle_pause(self):
        if self.game_over:
            return
        self.paused = not self.paused
        self.pause_btn.config(text="▶ Resume" if self.paused else "⏸ Pause")
        if self.paused and self._solve_running:
            self.toggle_auto_solve()    # stop auto-solve when paused

    # ═════════════════════════════════════════════════════════════════════
    #  IMPROVEMENT 1 — ANIMATED DISK MOVEMENT
    # ═════════════════════════════════════════════════════════════════════
    def animate_move(self, disk_num, frm, to, callback=None):
        """
        Smoothly animate disk_num from tower frm to tower to, then call callback.
        Arc path: rise → slide horizontally → descend.
        """
        # Find the canvas item for disk_num currently on frm
        item_id = None
        for iid, (twr, d) in self.disk_items.items():
            if twr == frm and d == disk_num:
                item_id = iid
                break

        if item_id is None:
            if callback:
                callback()
            return

        coords      = self.canvas.coords(item_id)
        src_cx      = (coords[0] + coords[2]) / 2
        src_cy      = (coords[1] + coords[3]) / 2
        disk_w      = (coords[2] - coords[0]) / 2
        lift_y      = 60     # y-position to lift disks to

        dst_x = self.tower_x[to]
        # Target y when placed on destination
        n_disks_dst = len(self.towers[to])
        dst_cy = (self.BASE_Y - self.DISK_H) - n_disks_dst * (self.DISK_H + self.DISK_GAP) + self.DISK_H / 2

        STEPS  = 18
        FPS_MS = 16        # ~60 fps

        # Build keyframe path: 3 phases
        # Phase 1: rise straight up
        phase1 = [(src_cx, src_cy - (src_cy - lift_y) * t / (STEPS // 3))
                  for t in range(1, STEPS // 3 + 1)]
        # Phase 2: slide horizontally at lift_y
        phase2 = [(src_cx + (dst_x - src_cx) * t / (STEPS // 3), lift_y)
                  for t in range(1, STEPS // 3 + 1)]
        # Phase 3: descend to destination
        phase3 = [(dst_x, lift_y + (dst_cy - lift_y) * t / (STEPS // 3))
                  for t in range(1, STEPS // 3 + 1)]

        path = phase1 + phase2 + phase3
        self._anim_running = True

        def step(idx):
            if idx >= len(path):
                self._anim_running = False
                if callback:
                    callback()
                return
            nx, ny = path[idx]
            self.canvas.coords(item_id,
                               nx - disk_w, ny - self.DISK_H / 2,
                               nx + disk_w, ny + self.DISK_H / 2)
            self.parent.after(FPS_MS, lambda: step(idx + 1))

        step(0)

    # ═════════════════════════════════════════════════════════════════════
    #  IMPROVEMENT 2 — UNDO BUTTON
    # ═════════════════════════════════════════════════════════════════════
    def _snapshot(self):
        """Save a deep copy of tower state and move count."""
        snap = {k: list(v) for k, v in self.towers.items()}
        self.history.append((snap, self.move_count))

    def undo_move(self):
        if self._anim_running or self._solve_running:
            return
        if not self.history:
            self._flash_status("Nothing to undo!", "orange")
            return
        if self.game_over:
            self.game_over = False
            self.canvas.delete("overlay")
            self.pause_btn.config(state=tk.NORMAL)

        snap, prev_moves = self.history.pop()
        self.towers     = snap
        self.move_count = prev_moves
        self._update_info()
        self._clear_hint()
        self._optimal_moves = []     # invalidate hint cache
        sound.play("undo")
        self.draw()

    # ═════════════════════════════════════════════════════════════════════
    #  IMPROVEMENT 3 — HINT SYSTEM
    # ═════════════════════════════════════════════════════════════════════
    def _compute_optimal_from_current(self):
        """Build the optimal move list from the CURRENT state (not initial)."""
        # Simulate forward from current state to find what the solver would do
        # Strategy: rebuild optimal sequence for remaining disks on S+M→D
        moves = []
        solve_restricted(self.n, "S", "M", "D", moves)

        # Replay from initial state, skip moves already made
        sim = {"S": list(range(self.n, 0, -1)), "M": [], "D": []}
        used = 0
        for frm, to in moves:
            if sim == self.towers:
                break
            sim[to].append(sim[frm].pop())
            used += 1

        remaining = moves[used:]
        return remaining

    def show_hint(self):
        if self.paused or self.game_over or self._solve_running:
            return
        self._clear_hint()

        remaining = self._compute_optimal_from_current()
        if not remaining:
            self._flash_status("You're on the optimal path!", "green")
            return

        frm, to = remaining[0]
        # Glow the top disk on frm tower
        if not self.towers[frm]:
            return

        disk = self.towers[frm][-1]
        # Find item
        for iid, (twr, d) in self.disk_items.items():
            if twr == frm and d == disk:
                x1, y1, x2, y2 = self.canvas.coords(iid)
                # Draw glowing border
                self.hint_highlight = self.canvas.create_rectangle(
                    x1 - 4, y1 - 4, x2 + 4, y2 + 4,
                    outline="#FFD700", width=3, tags="hint_glow")
                # Arrow label
                arrow_x = (self.tower_x[frm] + self.tower_x[to]) / 2
                self.canvas.create_text(
                    arrow_x, 70,
                    text=f"Move  {self.tower_lbl[frm]} → {self.tower_lbl[to]}",
                    font=("Helvetica", 11, "bold"), fill="#FFD700", tags="hint_glow")
                sound.play("hint")
                break

        # Auto-clear hint after 2.5 s
        self.parent.after(2500, self._clear_hint)

    def _clear_hint(self):
        self.canvas.delete("hint_glow")
        self.hint_highlight = None

    # ═════════════════════════════════════════════════════════════════════
    #  IMPROVEMENT 4 — SOUND EFFECTS  (integrated throughout via sound.play())
    # ═════════════════════════════════════════════════════════════════════
    # Sound calls are sprinkled in on_release, undo_move, show_hint, check_win.

    # ═════════════════════════════════════════════════════════════════════
    #  IMPROVEMENT 5 — AUTO-SOLVE MODE
    # ═════════════════════════════════════════════════════════════════════
    def toggle_auto_solve(self):
        if self.game_over:
            return
        if self._solve_running:
            # Stop
            self._solve_running = False
            if self._solve_after_id:
                self.parent.after_cancel(self._solve_after_id)
                self._solve_after_id = None
            self.solve_btn.config(text="▶ Auto-Solve", bg="#8e44ad")
            self._set_interactive(True)
            return

        if self.paused:
            self.toggle_pause()

        self._solve_running = True
        self.solve_btn.config(text="⏹ Stop Solve", bg="#c0392b")
        self._set_interactive(False)
        self._clear_hint()

        remaining = self._compute_optimal_from_current()
        self._execute_solve_sequence(remaining)

    def _execute_solve_sequence(self, moves):
        if not self._solve_running or not moves:
            self._solve_running = False
            self.solve_btn.config(text="▶ Auto-Solve", bg="#8e44ad")
            self._set_interactive(True)
            return

        frm, to = moves[0]
        rest    = moves[1:]

        if not self.towers[frm]:
            # Skip invalid (shouldn't happen with correct algorithm)
            self._execute_solve_sequence(rest)
            return

        # Save snapshot for undo
        self._snapshot()

        # Perform the move
        disk = self.towers[frm][-1]
        self.towers[to].append(self.towers[frm].pop())
        self.move_count += 1
        self._update_info()
        sound.play("solve")

        self.draw()

        if self.check_win():
            return

        delay = self.speed_var.get()
        self._solve_after_id = self.parent.after(delay, lambda: self._execute_solve_sequence(rest))

    def _set_interactive(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.pause_btn.config(state=state)
        self.undo_btn.config(state=state)
        self.hint_btn.config(state=state)

    # ── DRAG & DROP ───────────────────────────────────────────────────────
    def on_press(self, event):
        if self.paused or self.game_over or self._anim_running or self._solve_running:
            return
        item = self.canvas.find_closest(event.x, event.y)[0]
        if item in self.disk_items:
            tower, disk = self.disk_items[item]
            if self.towers[tower] and disk == self.towers[tower][-1]:
                self.drag_data = {"item": item, "x": event.x, "y": event.y,
                                  "tower": tower, "disk": disk}
                self._clear_hint()

    def on_drag(self, event):
        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.canvas.move(self.drag_data["item"], dx, dy)
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_release(self, event):
        if self.paused or not self.drag_data["item"]:
            return
        target = min(self.tower_x, key=lambda k: abs(self.tower_x[k] - event.x))
        frm    = self.drag_data["tower"]

        if self.valid_move(frm, target):
            self._snapshot()                            # save for undo
            disk = self.towers[frm][-1]
            self.towers[target].append(self.towers[frm].pop())
            self.move_count += 1
            self._update_info()
            self._optimal_moves = []                    # invalidate hint cache
            sound.play("move")

            self.drag_data = {"item": None, "x": 0, "y": 0, "tower": None, "disk": None}

            # Animate the placed disk
            def after_anim():
                if not self.check_win():
                    pass
            self.draw()
            if self.check_win():
                return
        else:
            self._flash_status("Invalid Move!", "red")
            sound.play("invalid")

        self.drag_data = {"item": None, "x": 0, "y": 0, "tower": None, "disk": None}
        self.draw()

    # ── MOVE VALIDATION ───────────────────────────────────────────────────
    def valid_move(self, frm, to):
        allowed = [("S", "M"), ("M", "S"), ("M", "D"), ("D", "M")]
        if (frm, to) not in allowed or frm == to or not self.towers[frm]:
            return False
        if self.towers[to] and self.towers[to][-1] < self.towers[frm][-1]:
            return False
        return True

    # ── WIN CHECK ─────────────────────────────────────────────────────────
    def check_win(self):
        if len(self.towers["D"]) == self.n:
            self.game_over   = True
            self._solve_running = False
            save_record(self.player_name, self.move_count, self.time_elapsed, self.n)
            self.draw()
            self.pause_btn.config(state=tk.DISABLED)
            self.solve_btn.config(state=tk.DISABLED)
            sound.play("win")

            opt   = 3 ** self.n - 1
            extra = self.move_count - opt
            msg2  = f"Finished in {self.move_count} moves  (optimal: {opt})"
            msg3  = "🏆 Optimal solution!" if extra == 0 else f"  +{extra} extra moves"

            self.canvas.create_rectangle(0, 0, 600, 400, fill="grey",
                                         stipple="gray50", tags="overlay")
            self.canvas.create_rectangle(120, 100, 480, 300, fill="white",
                                         outline="#27ae60", width=3, tags="overlay")
            self.canvas.create_text(300, 135, text="🎉 VICTORY! 🎉",
                                    font=("Helvetica", 22, "bold"), fill="#27ae60", tags="overlay")
            self.canvas.create_text(300, 180, text=msg2,
                                    font=("Helvetica", 13), fill="#2c3e50", tags="overlay")
            self.canvas.create_text(300, 215, text=msg3,
                                    font=("Helvetica", 12, "bold"),
                                    fill="#f39c12" if extra == 0 else "#e74c3c", tags="overlay")
            self.canvas.create_window(300, 265,
                window=tk.Button(self.parent, text="🏠 Back to Menu",
                                 font=("Helvetica", 11), bg="#27ae60", fg="white",
                                 command=self._safe_back_to_menu),
                tags="overlay")
            return True
        return False

    # ── DRAW ──────────────────────────────────────────────────────────────
    def draw(self):
        self.canvas.delete("game_element")
        self.disk_items = {}

        # Tower labels
        for key, x in self.tower_x.items():
            self.canvas.create_text(x, 350, text=self.tower_lbl[key],
                                    font=("Helvetica", 9, "bold"),
                                    fill="#2c3e50", tags="game_element")
            # Base platform
            self.canvas.create_rectangle(x - 80, self.BASE_Y, x + 80, self.BASE_Y + 30,
                                         fill="#CD5C5C", outline="#8B0000", width=2, tags="game_element")
            # Rod
            self.canvas.create_rectangle(x - 5, self.ROD_TOP, x + 5, self.BASE_Y,
                                         fill="#A52A2A", outline="", tags="game_element")

        y_base = self.BASE_Y - self.DISK_H
        for tower, disks in self.towers.items():
            x = self.tower_x[tower]
            for i, disk in enumerate(disks):
                y_top = y_base - i * (self.DISK_H + self.DISK_GAP)
                w     = 15 + disk * 10
                color = self.disk_colors[(disk - 1) % len(self.disk_colors)]
                iid = self.canvas.create_rectangle(
                    x - w, y_top, x + w, y_top + self.DISK_H,
                    fill=color, outline="#333", width=2, tags="game_element")
                # Disk number label
                self.canvas.create_text(x, y_top + self.DISK_H / 2,
                                        text=str(disk), font=("Helvetica", 8, "bold"),
                                        fill="#333", tags="game_element")
                self.disk_items[iid] = (tower, disk)

    # ── HELPERS ───────────────────────────────────────────────────────────
    def _flash_status(self, msg, color="red"):
        self.status_label.config(text=msg, fg=color)
        self.parent.after(1200, lambda: self.status_label.config(text=""))

    def _safe_back_to_menu(self):
        if self._solve_after_id:
            self.parent.after_cancel(self._solve_after_id)
        self._solve_running = False
        self.app.show_main_menu()


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app  = HanoiApp(root)
    root.mainloop()
