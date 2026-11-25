import math
import os
import random
import time
import tkinter as tk

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

TRANSPARENT_KEY = "#010101"
ASSET_CANDIDATES = ("cube.png", "cube.jpg", "cube.jpeg")

# Guaranteed visible, non-combining BMP Unicode ranges supported out-of-the-box on Windows 10
WIN10_UNICODE_BLOCKS = [
    ("KR", 0xAC00, 0xD7A3),   # Korean Hangul Syllables
    ("ZH", 0x4E00, 0x9FFF),   # Chinese / CJK Unified Ideographs
    ("AR", 0x0621, 0x063A),   # Arabic Letters (Part 1, non-combining)
    ("AR", 0x0641, 0x064A),   # Arabic Letters (Part 2, non-combining)
    ("JA", 0x3041, 0x3096),   # Japanese Hiragana
    ("JA", 0x30A1, 0x30FA),   # Japanese Katakana
    ("CY", 0x0410, 0x044F),   # Cyrillic
    ("GR", 0x0391, 0x03A9),   # Greek Uppercase
    ("GR", 0x03B1, 0x03C9),   # Greek Lowercase
    ("HE", 0x05D0, 0x05EA),   # Hebrew Letters
    ("HI", 0x0905, 0x0939),   # Devanagari (Hindi) Vowels & Consonants
    ("TH", 0x0E01, 0x0E2E),   # Thai Consonants
    ("KA", 0x10D0, 0x10F0),   # Georgian Mkhedruli
    ("HY", 0x0531, 0x0556),   # Armenian
    ("LA", 0x0041, 0x005A),   # Basic Latin
    ("LA", 0x00C0, 0x00D6),   # Latin-1 Supplement
]


def forge_unicode_string(length: int = 10) -> str:
    chars = []
    chosen_blocks = random.sample(WIN10_UNICODE_BLOCKS, k=min(length, len(WIN10_UNICODE_BLOCKS)))
    while len(chosen_blocks) < length:
        chosen_blocks.append(random.choice(WIN10_UNICODE_BLOCKS))
    random.shuffle(chosen_blocks)

    for _, start, end in chosen_blocks[:length]:
        for _ in range(12):
            cp = random.randint(start, end)
            ch = chr(cp)
            if ch.isprintable() and not ch.isspace():
                chars.append(ch)
                break
        else:
            chars.append("X")
    return "".join(chars)


def random_safe_hex() -> str:
    while True:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        if not (r < 6 and g < 6 and b < 6):
            return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_col: str):
    h = hex_col.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: float, g: float, b: float) -> str:
    ri = max(0, min(255, int(round(r))))
    gi = max(0, min(255, int(round(g))))
    bi = max(0, min(255, int(round(b))))
    if ri < 4 and gi < 4 and bi < 4:
        ri, gi, bi = 4, 4, 4
    return f"#{ri:02x}{gi:02x}{bi:02x}"


def lerp_hex(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def scale_hex(hex_col: str, factor: float) -> str:
    r, g, b = hex_to_rgb(hex_col)
    return rgb_to_hex(r * factor, g * factor, b * factor)


def mix_hex(c1: str, c2: str, ratio: float) -> str:
    return lerp_hex(c1, c2, ratio)


def luminance(hex_col: str) -> float:
    r, g, b = hex_to_rgb(hex_col)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


class CanvasPool:
    """Zero-allocation per-frame object pool for 60 FPS tkinter rendering."""

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.pools = {"poly": [], "line": [], "oval": [], "text": []}
        self.cursors = {"poly": 0, "line": 0, "oval": 0, "text": 0}

    def begin_frame(self):
        for k in self.cursors:
            self.cursors[k] = 0

    def poly(self, coords, fill="", outline="", width=1):
        idx = self.cursors["poly"]
        pool = self.pools["poly"]
        if idx >= len(pool):
            item = self.canvas.create_polygon(coords, fill=fill, outline=outline, width=width)
            pool.append(item)
        else:
            item = pool[idx]
            self.canvas.coords(item, *coords)
            self.canvas.itemconfigure(item, fill=fill, outline=outline, width=width, state="normal")
        self.cursors["poly"] = idx + 1
        return item

    def line(self, x1, y1, x2, y2, fill="#ffffff", width=1):
        idx = self.cursors["line"]
        pool = self.pools["line"]
        if idx >= len(pool):
            item = self.canvas.create_line(x1, y1, x2, y2, fill=fill, width=width)
            pool.append(item)
        else:
            item = pool[idx]
            self.canvas.coords(item, x1, y1, x2, y2)
            self.canvas.itemconfigure(item, fill=fill, width=width, state="normal")
        self.cursors["line"] = idx + 1
        return item

    def oval(self, x1, y1, x2, y2, fill="", outline="", width=1):
        idx = self.cursors["oval"]
        pool = self.pools["oval"]
        if idx >= len(pool):
            item = self.canvas.create_oval(x1, y1, x2, y2, fill=fill, outline=outline, width=width)
            pool.append(item)
        else:
            item = pool[idx]
            self.canvas.coords(item, x1, y1, x2, y2)
            self.canvas.itemconfigure(item, fill=fill, outline=outline, width=width, state="normal")
        self.cursors["oval"] = idx + 1
        return item

    def text(self, x, y, text="", fill="#ffffff", font=("Segoe UI", 10, "bold"), anchor="center"):
        idx = self.cursors["text"]
        pool = self.pools["text"]
        if idx >= len(pool):
            item = self.canvas.create_text(x, y, text=text, fill=fill, font=font, anchor=anchor)
            pool.append(item)
        else:
            item = pool[idx]
            self.canvas.coords(item, x, y)
            self.canvas.itemconfigure(item, text=text, fill=fill, font=font, anchor=anchor, state="normal")
        self.cursors["text"] = idx + 1
        return item

    def end_frame(self):
        for kind, cursor in self.cursors.items():
            pool = self.pools[kind]
            for i in range(cursor, len(pool)):
                self.canvas.itemconfigure(pool[i], state="hidden")


class ModernCubeWidget:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Modern Cyber Cube Overlay")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT_KEY)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_KEY)

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{self.screen_w}x{self.screen_h}+0+0")

        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_w,
            height=self.screen_h,
            bg=TRANSPARENT_KEY,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.pool = CanvasPool(self.canvas)

        # Cube position and scale on fullscreen canvas
        self.cx = self.screen_w * 0.5
        self.cy = self.screen_h * 0.52
        self.cube_radius = min(self.screen_w, self.screen_h) * 0.15

        # Interaction state
        self.dragging = False
        self.drag_off_x = 0.0
        self.drag_off_y = 0.0
        self.mouse_x = -9999.0
        self.mouse_y = -9999.0
        self.hovered = False
        self.was_hovered = False
        self.expand_amount = 0.0
        self.show_hex_hud = True

        # Unicode cipher bubble state
        self.unicode_cipher = forge_unicode_string(10)
        self.cipher_timer = 0.0
        self.cipher_interval = 0.22

        # Random hex palette morphing
        self.auto_morph = True
        self.morph_duration = 4.0
        self.morph_elapsed = 0.0
        self.pal_prev = self.generate_hex_palette()
        self.pal_next = self.generate_hex_palette()
        self.pal_curr = dict(self.pal_prev)

        # Bindings
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.toggle_asset_mode)
        self.canvas.bind("<ButtonPress-2>", lambda e: self.reroll_colors())
        self.canvas.bind("<ButtonPress-3>", lambda e: self.root.destroy())
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<space>", lambda e: self.reroll_colors())
        self.root.bind("<r>", lambda e: self.reroll_colors())
        self.root.bind("<R>", lambda e: self.reroll_colors())
        self.root.bind("<m>", lambda e: self.toggle_auto_morph())
        self.root.bind("<M>", lambda e: self.toggle_auto_morph())
        self.root.bind("<h>", lambda e: self.toggle_hud())
        self.root.bind("<H>", lambda e: self.toggle_hud())

        # Optional image asset fallback
        self.raw_asset = self.load_raw_asset()
        self.asset_photo = None
        self.asset_cached_size = 0
        self.use_asset_mode = False

        # Precompute unit geometry
        self._build_precomputed_geometry()

        # Animation state
        self.angle_x = 0.52
        self.angle_y = 0.78
        self.angle_z = 0.14
        self.tick = 0.0
        self.last_time = time.perf_counter()

        self.particles = [self._new_particle() for _ in range(26)]
        self.animate()

    def generate_hex_palette(self):
        primary = random_safe_hex()
        secondary = random_safe_hex()
        accent = random_safe_hex()
        chassis = mix_hex("#10141c", primary, 0.16)
        return {
            "primary": primary,
            "secondary": secondary,
            "accent": accent,
            "chassis": chassis,
        }

    def reroll_colors(self):
        self.pal_prev = dict(self.pal_curr)
        self.pal_next = self.generate_hex_palette()
        self.morph_elapsed = 0.0

    def toggle_auto_morph(self):
        self.auto_morph = not self.auto_morph

    def toggle_hud(self):
        self.show_hex_hud = not self.show_hex_hud

    def update_palette(self, dt: float):
        if not self.auto_morph:
            return
        self.morph_elapsed += dt
        if self.morph_elapsed >= self.morph_duration:
            self.pal_prev = dict(self.pal_next)
            self.pal_next = self.generate_hex_palette()
            self.morph_elapsed = 0.0
        raw_t = min(1.0, self.morph_elapsed / self.morph_duration)
        smooth_t = raw_t * raw_t * (3.0 - 2.0 * raw_t)
        for k in self.pal_curr:
            self.pal_curr[k] = lerp_hex(self.pal_prev[k], self.pal_next[k], smooth_t)

    def load_raw_asset(self):
        if not HAS_PIL:
            return None
        for path in ASSET_CANDIDATES:
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                pixels = img.load()
                w, h = img.size
                bg_r, bg_g, bg_b, _ = pixels[0, 0]
                for y in range(h):
                    for x in range(w):
                        r, g, b, _ = pixels[x, y]
                        if (r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2 < 1444:
                            pixels[x, y] = (1, 1, 1, 255)
                return img
        return None

    def get_scaled_asset(self):
        if self.raw_asset is None:
            return None
        target = max(96, int(self.cube_radius * 2.5))
        if self.asset_photo is None or abs(target - self.asset_cached_size) > 6:
            resized = self.raw_asset.resize((target, target), Image.Resampling.LANCZOS)
            self.asset_photo = ImageTk.PhotoImage(resized)
            self.asset_cached_size = target
        return self.asset_photo

    def toggle_asset_mode(self, _event=None):
        if self.raw_asset is not None:
            self.use_asset_mode = not self.use_asset_mode

    def on_motion(self, event):
        self.mouse_x = float(event.x)
        self.mouse_y = float(event.y)

    def on_press(self, event):
        dist = math.hypot(event.x - self.cx, event.y - self.cy)
        if dist <= self.cube_radius * 1.65:
            self.dragging = True
            self.drag_off_x = event.x - self.cx
            self.drag_off_y = event.y - self.cy

    def on_drag(self, event):
        self.mouse_x = float(event.x)
        self.mouse_y = float(event.y)
        if self.dragging:
            self.cx = max(90.0, min(self.screen_w - 90.0, event.x - self.drag_off_x))
            self.cy = max(130.0, min(self.screen_h - 90.0, event.y - self.drag_off_y))

    def on_release(self, _event):
        self.dragging = False

    def on_scroll(self, event):
        step = 1.1 if event.delta > 0 else 0.9
        min_r = 55.0
        max_r = min(self.screen_w, self.screen_h) * 0.40
        self.cube_radius = max(min_r, min(max_r, self.cube_radius * step))

    def _new_particle(self):
        ang = random.uniform(0, math.tau)
        dist = random.uniform(1.15, 2.05)
        return {
            "ang": ang,
            "dist": dist,
            "speed": random.uniform(0.18, 0.55) * random.choice([-1, 1]),
            "size": random.uniform(1.6, 3.6),
            "phase": random.uniform(0, math.tau),
        }

    def _build_precomputed_geometry(self):
        self.cube_verts = [
            (-1.0, -1.0, -1.0),
            (1.0, -1.0, -1.0),
            (1.0, 1.0, -1.0),
            (-1.0, 1.0, -1.0),
            (-1.0, -1.0, 1.0),
            (1.0, -1.0, 1.0),
            (1.0, 1.0, 1.0),
            (-1.0, 1.0, 1.0),
        ]
        self.cube_faces = [
            ((0, 1, 2, 3), (0.0, 0.0, -1.0)),
            ((5, 4, 7, 6), (0.0, 0.0, 1.0)),
            ((4, 0, 3, 7), (-1.0, 0.0, 0.0)),
            ((1, 5, 6, 2), (1.0, 0.0, 0.0)),
            ((4, 5, 1, 0), (0.0, -1.0, 0.0)),
            ((3, 2, 6, 7), (0.0, 1.0, 0.0)),
        ]
        self.octa_verts = [
            (0.0, -0.58, 0.0),
            (0.0, 0.58, 0.0),
            (-0.58, 0.0, 0.0),
            (0.58, 0.0, 0.0),
            (0.0, 0.0, -0.58),
            (0.0, 0.0, 0.58),
        ]
        self.octa_edges = [
            (0, 2), (0, 3), (0, 4), (0, 5),
            (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 4), (4, 3), (3, 5), (5, 2),
        ]

        c = 0.80
        b = 0.96
        self.outer_oct = [
            (-c, -b), (c, -b), (b, -c), (b, c),
            (c, b), (-c, b), (-b, c), (-b, -c),
        ]
        ic = 0.64
        ib = 0.78
        self.inner_oct = [
            (-ic, -ib), (ic, -ib), (ib, -ic), (ib, ic),
            (ic, ib), (-ic, ib), (-ib, ic), (-ib, -ic),
        ]

        self.brackets = [
            [(-0.88, -0.66), (-0.88, -0.88), (-0.66, -0.88)],
            [(0.66, -0.88), (0.88, -0.88), (0.88, -0.66)],
            [(0.88, 0.66), (0.88, 0.88), (0.66, 0.88)],
            [(-0.66, 0.88), (-0.88, 0.88), (-0.88, 0.66)],
        ]

        self.traces = [
            ((-0.88, 0.0), (-0.54, 0.0)),
            ((0.88, 0.0), (0.54, 0.0)),
            ((0.0, -0.88), (0.0, -0.54)),
            ((0.0, 0.88), (0.0, 0.54)),
            ((-0.58, -0.58), (-0.36, -0.36)),
            ((0.58, -0.58), (0.36, -0.36)),
            ((0.58, 0.58), (0.36, 0.36)),
            ((-0.58, 0.58), (-0.36, 0.36)),
        ]

        self.ring_uv = []
        for i in range(24):
            a = (math.tau * i) / 24.0
            self.ring_uv.append((0.46 * math.cos(a), 0.46 * math.sin(a)))

        self.ring_configs = [
            (1.52, 0.48, 0.32, 0.55),
            (1.70, -0.56, -0.26, -0.42),
            (1.86, 0.16, -0.62, 0.30),
        ]
        self.ring_samples = 48
        self.ring_angles = [(math.tau * i) / self.ring_samples for i in range(self.ring_samples)]

    def get_rotation_matrix(self, ax, ay, az):
        cx, sx = math.cos(ax), math.sin(ax)
        cy, sy = math.cos(ay), math.sin(ay)
        cz, sz = math.cos(az), math.sin(az)
        return (
            cy * cz,
            sx * sy * cz - cx * sz,
            cx * sy * cz + sx * sz,
            cy * sz,
            sx * sy * sz + cx * cz,
            cx * sy * sz - sx * cz,
            -sy,
            sx * cy,
            cx * cy,
        )

    @staticmethod
    def mul_mat(m, x, y, z):
        return (
            m[0] * x + m[1] * y + m[2] * z,
            m[3] * x + m[4] * y + m[5] * z,
            m[6] * x + m[7] * y + m[8] * z,
        )

    def project(self, x, y, z):
        fov = 4.6
        factor = fov / (fov + z)
        return (
            self.cx + x * self.cube_radius * factor,
            self.cy + y * self.cube_radius * factor,
            z,
        )

    @staticmethod
    def map_uv(quad, u, v):
        a = (u + 1.0) * 0.5
        b = (v + 1.0) * 0.5
        na = 1.0 - a
        nb = 1.0 - b
        w0 = na * nb
        w1 = a * nb
        w2 = a * b
        w3 = na * b
        p0, p1, p2, p3 = quad
        return (
            w0 * p0[0] + w1 * p1[0] + w2 * p2[0] + w3 * p3[0],
            w0 * p0[1] + w1 * p1[1] + w2 * p2[1] + w3 * p3[1],
        )

    def draw_particles(self):
        p_col = self.pal_curr["primary"]
        s_col = self.pal_curr["secondary"]
        for i, p in enumerate(self.particles):
            ang = p["ang"] + self.tick * p["speed"]
            r = self.cube_radius * (p["dist"] + 0.08 * math.sin(self.tick * 1.4 + p["phase"]))
            px = self.cx + math.cos(ang) * r
            py = self.cy + math.sin(ang) * r * 0.72
            sz = p["size"] * (0.7 + 0.3 * math.sin(self.tick * 2.5 + p["phase"]))
            col = p_col if i % 2 == 0 else s_col
            self.pool.oval(px - sz, py - sz, px + sz, py + sz, fill=col, outline="")

    def draw_gyro_rings(self, front_half: bool):
        cols = (self.pal_curr["primary"], self.pal_curr["secondary"], self.pal_curr["accent"])
        for r_idx, (radius, tx, tz, spd) in enumerate(self.ring_configs):
            phase = self.tick * spd + r_idx * 1.1
            col = cols[r_idx]
            node_col = cols[(r_idx + 1) % 3]
            ctx, stx = math.cos(tx), math.sin(tx)
            ctz, stz = math.cos(tz), math.sin(tz)

            pts = []
            for base_a in self.ring_angles:
                theta = base_a + phase
                x = radius * math.cos(theta)
                z = radius * math.sin(theta)
                y1 = -z * stx
                z1 = z * ctx
                x2 = x * ctz - y1 * stz
                y2 = x * stz + y1 * ctz
                pts.append(self.project(x2, y2, z1))

            n = len(pts)
            for i in range(n):
                x1, y1, z1 = pts[i]
                x2, y2, z2 = pts[(i + 1) % n]
                is_front = (z1 + z2) * 0.5 < 0.0
                if is_front != front_half:
                    continue
                if i % 4 != 3:
                    w = 2.0 if is_front else 1.2
                    self.pool.line(x1, y1, x2, y2, fill=col if is_front else scale_hex(col, 0.55), width=w)
                if i % 12 == 0:
                    nr = 3.2 if is_front else 2.0
                    self.pool.oval(x1 - nr, y1 - nr, x1 + nr, y1 + nr, fill=node_col, outline="")

    def draw_wireframe_core(self):
        if self.expand_amount <= 0.03:
            return
        m = self.get_rotation_matrix(-self.angle_x * 1.6, self.angle_y * 1.9, self.angle_z)
        sc = 0.65 + 0.45 * self.expand_amount
        proj = []
        for vx, vy, vz in self.octa_verts:
            rx, ry, rz = self.mul_mat(m, vx * sc, vy * sc, vz * sc)
            proj.append(self.project(rx, ry, rz))

        core_col = self.pal_curr["accent"]
        glow_col = self.pal_curr["primary"]
        for i, j in self.octa_edges:
            x1, y1, _ = proj[i]
            x2, y2, _ = proj[j]
            self.pool.line(x1, y1, x2, y2, fill=glow_col, width=2.2)

        r = self.cube_radius * 0.16 * self.expand_amount
        self.pool.oval(self.cx - r, self.cy - r, self.cx + r, self.cy + r, fill=core_col, outline="#ffffff", width=1.4)

    def draw_modern_face(self, quad, shade: float):
        chassis = self.pal_curr["chassis"]
        primary = self.pal_curr["primary"]
        secondary = self.pal_curr["secondary"]
        accent = self.pal_curr["accent"]

        plate_outer = scale_hex(chassis, 0.72 + 0.55 * shade)
        plate_inner = scale_hex(chassis, 0.52 + 0.42 * shade)
        edge_col = scale_hex(primary, 0.55 + 0.45 * shade)
        sec_col = scale_hex(secondary, 0.55 + 0.45 * shade)

        base_flat = []
        for px, py in quad:
            base_flat.extend((px, py))
        self.pool.poly(base_flat, fill=scale_hex(chassis, 0.45), outline=edge_col, width=1.6)

        outer_flat = []
        for u, v in self.outer_oct:
            px, py = self.map_uv(quad, u, v)
            outer_flat.extend((px, py))
        self.pool.poly(outer_flat, fill=plate_outer, outline=edge_col, width=1.8)

        inner_flat = []
        for u, v in self.inner_oct:
            px, py = self.map_uv(quad, u, v)
            inner_flat.extend((px, py))
        self.pool.poly(inner_flat, fill=plate_inner, outline=sec_col, width=1.3)

        for br in self.brackets:
            p0 = self.map_uv(quad, br[0][0], br[0][1])
            p1 = self.map_uv(quad, br[1][0], br[1][1])
            p2 = self.map_uv(quad, br[2][0], br[2][1])
            self.pool.line(p0[0], p0[1], p1[0], p1[1], fill=edge_col, width=1.8)
            self.pool.line(p1[0], p1[1], p2[0], p2[1], fill=edge_col, width=1.8)

        for (u1, v1), (u2, v2) in self.traces:
            p1 = self.map_uv(quad, u1, v1)
            p2 = self.map_uv(quad, u2, v2)
            self.pool.line(p1[0], p1[1], p2[0], p2[1], fill=sec_col, width=1.2)

        n_ring = len(self.ring_uv)
        for i in range(0, n_ring, 2):
            u1, v1 = self.ring_uv[i]
            u2, v2 = self.ring_uv[(i + 1) % n_ring]
            p1 = self.map_uv(quad, u1, v1)
            p2 = self.map_uv(quad, u2, v2)
            self.pool.line(p1[0], p1[1], p2[0], p2[1], fill=edge_col, width=1.5)

        spin = self.tick * 0.9
        cs, sn = math.cos(spin), math.sin(spin)
        d_rad = 0.32
        diamond_flat = []
        for k in range(4):
            a = k * (math.pi * 0.5)
            du = d_rad * (math.cos(a) * cs - math.sin(a) * sn)
            dv = d_rad * (math.cos(a) * sn + math.sin(a) * cs)
            px, py = self.map_uv(quad, du, dv)
            diamond_flat.extend((px, py))
        self.pool.poly(diamond_flat, fill=scale_hex(accent, 0.35), outline=accent, width=1.6)

        c0 = self.map_uv(quad, -0.11, 0.0)
        c1 = self.map_uv(quad, 0.0, -0.11)
        c2 = self.map_uv(quad, 0.11, 0.0)
        c3 = self.map_uv(quad, 0.0, 0.11)
        self.pool.poly(
            [c0[0], c0[1], c1[0], c1[1], c2[0], c2[1], c3[0], c3[1]],
            fill=accent,
            outline="#ffffff" if shade > 0.5 else edge_col,
            width=1.2,
        )

    def draw_unicode_hover_bubble(self):
        """Draws a fixed-anchor, Bayer-dithered cyber bubble above the cube with 10 live Unicode glyphs."""
        if not self.hovered:
            return

        primary = self.pal_curr["primary"]
        secondary = self.pal_curr["secondary"]
        accent = self.pal_curr["accent"]

        jx = random.choice((-1.5, -0.5, 0.5, 1.5))
        jy = random.choice((-1.5, -0.5, 0.5, 1.5))

        bw = 320.0
        bh = 56.0
        anchor_x = max(bw * 0.5 + 16.0, min(self.screen_w - bw * 0.5 - 16.0, self.cx))
        anchor_y = max(bh * 0.5 + 16.0, self.cy - self.cube_radius * 2.15)

        bx = anchor_x + jx
        by = anchor_y + jy
        x1 = bx - bw * 0.5
        y1 = by - bh * 0.5
        x2 = bx + bw * 0.5
        y2 = by + bh * 0.5
        cut = 10.0

        outer_poly = [
            x1 + cut, y1,
            x2 - cut, y1,
            x2, y1 + cut,
            x2, y2 - cut,
            x2 - cut, y2,
            x1 + cut, y2,
            x1, y2 - cut,
            x1, y1 + cut,
        ]
        self.pool.poly(outer_poly, fill="#0b0f17", outline=primary, width=2.0)

        stem_top_y = y2
        stem_bot_y = min(self.cy - self.cube_radius * 1.45, y2 + 18.0)
        if stem_bot_y > stem_top_y + 2.0:
            self.pool.line(anchor_x, stem_top_y, anchor_x, stem_bot_y, fill=secondary, width=1.6)
            self.pool.oval(anchor_x - 3, stem_bot_y - 3, anchor_x + 3, stem_bot_y + 3, fill=accent, outline="")

        cols = 26
        dx = (bw - 24.0) / cols
        phase_flip = int(self.tick * 24) % 2
        for c in range(cols):
            px = x1 + 12.0 + c * dx
            if (c + phase_flip) % 2 == 0:
                self.pool.oval(px - 1.2, y1 + 4.5, px + 1.2, y1 + 6.9, fill=secondary, outline="")
            else:
                self.pool.oval(px - 1.2, y2 - 6.9, px + 1.2, y2 - 4.5, fill=primary, outline="")

        self.pool.text(
            x1 + 14.0,
            y1 + 11.0,
            text="UNICODE // BMP-10",
            fill=secondary,
            font=("Consolas", 7, "bold"),
            anchor="w",
        )

        glyph_area_w = bw - 32.0
        step_x = glyph_area_w / 10.0
        start_gx = x1 + 16.0 + step_x * 0.5
        gy = by + 5.0

        glyph_col = "#ffffff" if luminance(accent) < 170 else accent

        for idx, ch in enumerate(self.unicode_cipher[:10]):
            gx = start_gx + idx * step_x + random.choice((-0.8, 0.0, 0.8))
            gy_i = gy + random.choice((-0.8, 0.0, 0.8))
            self.pool.text(
                gx,
                gy_i,
                text=ch,
                fill=glyph_col,
                font=("Segoe UI", 14, "bold"),
                anchor="center",
            )

    def draw_hex_hud(self):
        if not self.show_hex_hud:
            return
        p = self.pal_curr["primary"].upper()
        s = self.pal_curr["secondary"].upper()
        a = self.pal_curr["accent"].upper()
        mode_tag = "AUTO" if self.auto_morph else "LOCK"
        label = f"{p}  |  {s}  |  {a}   [{mode_tag}]"

        hx = self.cx
        hy = min(self.screen_h - 24.0, self.cy + self.cube_radius * 2.05)
        w = 175.0
        h = 13.0
        self.pool.poly(
            [hx - w, hy - h, hx + w, hy - h, hx + w - 8, hy + h, hx - w + 8, hy + h],
            fill="#0b0f17",
            outline=self.pal_curr["secondary"],
            width=1.2,
        )
        self.pool.text(
            hx,
            hy,
            text=label,
            fill="#e6edf3",
            font=("Consolas", 9, "bold"),
            anchor="center",
        )

    def animate(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last_time)
        self.last_time = now
        self.tick += dt

        self.update_palette(dt)

        dist = math.hypot(self.mouse_x - self.cx, self.mouse_y - self.cy)
        self.hovered = dist <= self.cube_radius * 1.55

        if self.hovered:
            if not self.was_hovered:
                self.unicode_cipher = forge_unicode_string(10)
                self.cipher_timer = 0.0
            else:
                self.cipher_timer += dt
                if self.cipher_timer >= self.cipher_interval:
                    self.unicode_cipher = forge_unicode_string(10)
                    self.cipher_timer = 0.0
        self.was_hovered = self.hovered

        target_expand = 0.34 if self.hovered else 0.0
        self.expand_amount += (target_expand - self.expand_amount) * min(1.0, dt * 10.0)

        self.pool.begin_frame()

        if self.use_asset_mode and self.raw_asset is not None:
            photo = self.get_scaled_asset()
            if photo is not None:
                self.canvas.delete("asset_img")
                self.canvas.create_image(self.cx, self.cy, image=photo, tags="asset_img")
        else:
            self.canvas.delete("asset_img")
            self.draw_particles()
            self.draw_gyro_rings(front_half=False)
            self.draw_wireframe_core()

            m = self.get_rotation_matrix(self.angle_x, self.angle_y, self.angle_z)
            visible_faces = []
            for idx_list, (nx, ny, nz) in self.cube_faces:
                rnx, rny, rnz = self.mul_mat(m, nx, ny, nz)
                if rnz < 0.25:
                    off = self.expand_amount
                    quad = []
                    z_sum = 0.0
                    for vi in idx_list:
                        vx, vy, vz = self.cube_verts[vi]
                        rx, ry, rz = self.mul_mat(m, vx + nx * off, vy + ny * off, vz + nz * off)
                        sx, sy, sz = self.project(rx, ry, rz)
                        quad.append((sx, sy))
                        z_sum += sz
                    x0, y0 = quad[0]
                    x1, y1 = quad[1]
                    x2, y2 = quad[2]
                    if (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0) > 0:
                        shade = max(0.25, min(1.0, 0.65 - rnz * 0.45))
                        visible_faces.append((z_sum * 0.25, quad, shade))

            visible_faces.sort(key=lambda item: item[0], reverse=True)
            for _, quad, shade in visible_faces:
                self.draw_modern_face(quad, shade)

            self.draw_gyro_rings(front_half=True)

        # Draw HUD and Hover Unicode Bubble LAST so they always stay on top
        self.draw_hex_hud()
        self.draw_unicode_hover_bubble()

        self.pool.end_frame()

        self.angle_y += dt * 0.85
        self.angle_x = 0.50 + 0.14 * math.sin(self.tick * 0.9)
        self.angle_z = 0.12 * math.cos(self.tick * 0.7)

        self.root.after(16, self.animate)


if __name__ == "__main__":
    root_win = tk.Tk()
    ModernCubeWidget(root_win)
    root_win.mainloop()
