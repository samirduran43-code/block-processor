import tkinter as tk
import random
import ctypes

# Sleek, breathable horizontal HUD dimensions
BOX_WIDTH = 310
BOX_HEIGHT = 156
FONT_SIZE = 13
CHAR_SPACING = 16
FPS_DELAY_MS = 30

# Curated high-legibility Neo-Russian glyphs
CLEAN_CYRILLIC = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЭЮЯѲѢѴҒҚҢҮҲ"
NUMBERS = "0123456789"

# High-contrast luminous phosphor palette
TRAIL_COLORS = [
    "#FFFFFF",  # Lead glyph (pure crisp white)
    "#E0F2FE",  # Bright phosphor ice
    "#BAE6FD",  # Luminous sky cyan
    "#7DD3FC",  # Electric ice blue
    "#38BDF8",  # Vibrant cyan
    "#38BDF8",  # Sustained mid-stream clarity
    "#0EA5E9",  # Clean azure tail
]

# Dimmed/flicker states for individual phosphor characters
FLICKER_DIM_COLORS = [
    "#7DD3FC",
    "#38BDF8",
    "#0284C7",
    "#0369A1",
]

SHADOW_COLOR = "#020B12"     # Deep dark contrast shadow behind every glyph
HUD_ACCENT_COLOR = "#7DD3FC"
HUD_SUBTLE_COLOR = "#0EA5E9"
HUD_DIM_COLOR = "#0284C7"

# LCD Glass Panel Colors (slightly deeper tint so bright characters pop)
LCD_BASE_BG = "#020D17"
LCD_SCANLINE_COLOR = "#072236"


def make_clickthrough(widget):
    widget.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(widget.winfo_id())
    styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles | 0x80000 | 0x20)


def generate_aesthetic_token():
    style = random.choice(["code", "word", "pair"])
    if style == "code":
        prefix = "".join(random.choices(CLEAN_CYRILLIC, k=2))
        digits = "".join(random.choices(NUMBERS, k=2))
        return f"{prefix}-{digits}"
    elif style == "word":
        return "".join(random.choices(CLEAN_CYRILLIC, k=random.randint(4, 5)))
    else:
        left = "".join(random.choices(CLEAN_CYRILLIC, k=2))
        right = "".join(random.choices(CLEAN_CYRILLIC, k=2))
        return f"{left}·{right}"


class AestheticStream:
    def __init__(self, y, initial_x=None):
        self.y = y
        self.reset(initial_x)

    def reset(self, initial_x=None):
        self.text = generate_aesthetic_token()
        self.speed = random.uniform(0.65, 1.05)
        self.x = initial_x if initial_x is not None else BOX_WIDTH + random.uniform(15, 90)
        # Per-character flicker phase so letters shimmer organically
        self.char_phases = [random.random() for _ in self.text]

    def update(self):
        self.x -= self.speed
        tail_x = self.x + (len(self.text) * CHAR_SPACING)
        if tail_x < 18:
            self.reset()


# 1. Foreground Text Layer (100% crisp text, chroma-key transparent background)
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "black")
root.config(bg="black")

screen_height = root.winfo_screenheight()
pos_x = 0
pos_y = (screen_height // 2) - (BOX_HEIGHT // 2)
root.geometry(f"{BOX_WIDTH}x{BOX_HEIGHT}+{pos_x}+{pos_y}")

# 2. Background Mini-LCD Glass Layer (True alpha transparency + backlight flicker)
lcd_bg = tk.Toplevel(root)
lcd_bg.overrideredirect(True)
lcd_bg.attributes("-topmost", True)
lcd_bg.attributes("-alpha", 0.34)
lcd_bg.config(bg=LCD_BASE_BG)
lcd_bg.geometry(f"{BOX_WIDTH}x{BOX_HEIGHT}+{pos_x}+{pos_y}")

bg_canvas = tk.Canvas(
    lcd_bg, width=BOX_WIDTH, height=BOX_HEIGHT, bg=LCD_BASE_BG, highlightthickness=0
)
bg_canvas.pack()

# Draw fine LCD scanlines & beveled screen border on the glass layer
for y_line in range(0, BOX_HEIGHT, 3):
    bg_canvas.create_line(0, y_line, BOX_WIDTH, y_line, fill=LCD_SCANLINE_COLOR, width=1)
bg_canvas.create_rectangle(
    1, 1, BOX_WIDTH - 2, BOX_HEIGHT - 2, outline="#38BDF8", width=1
)

# Foreground canvas for glowing characters
canvas = tk.Canvas(
    root, width=BOX_WIDTH, height=BOX_HEIGHT, bg="black", highlightthickness=0
)
canvas.pack()

make_clickthrough(lcd_bg)
make_clickthrough(root)

# Create 4 balanced horizontal telemetry tracks
TOP_MARGIN = 30
ROW_SPACING = 32
NUM_ROWS = 4

streams = [
    AestheticStream(
        y=TOP_MARGIN + (i * ROW_SPACING),
        initial_x=random.uniform(35, BOX_WIDTH - 20),
    )
    for i in range(NUM_ROWS)
]


def draw_hud_frame():
    root.lift(lcd_bg)

    # Synchronized LCD backlight voltage dip
    voltage_dip = random.random() < 0.06
    if voltage_dip:
        flicker_alpha = random.uniform(0.22, 0.28)
    else:
        flicker_alpha = random.uniform(0.32, 0.38)
    lcd_bg.attributes("-alpha", flicker_alpha)

    # Crisp corner brackets & left spine
    canvas.create_line(3, 10, 3, BOX_HEIGHT - 10, fill=HUD_ACCENT_COLOR, width=2)
    canvas.create_line(3, 10, 32, 10, fill=HUD_ACCENT_COLOR, width=1)
    canvas.create_line(3, BOX_HEIGHT - 10, 32, BOX_HEIGHT - 10, fill=HUD_ACCENT_COLOR, width=1)

    # Right-side mini-LCD corner ticks
    canvas.create_line(BOX_WIDTH - 14, 10, BOX_WIDTH - 4, 10, fill=HUD_SUBTLE_COLOR, width=1)
    canvas.create_line(BOX_WIDTH - 4, 10, BOX_WIDTH - 4, 20, fill=HUD_SUBTLE_COLOR, width=1)
    canvas.create_line(
        BOX_WIDTH - 14, BOX_HEIGHT - 10, BOX_WIDTH - 4, BOX_HEIGHT - 10, fill=HUD_SUBTLE_COLOR, width=1
    )
    canvas.create_line(
        BOX_WIDTH - 4, BOX_HEIGHT - 20, BOX_WIDTH - 4, BOX_HEIGHT - 10, fill=HUD_SUBTLE_COLOR, width=1
    )

    # Center 50% height marker
    mid_y = BOX_HEIGHT // 2
    canvas.create_line(3, mid_y, 12, mid_y, fill="#FFFFFF", width=2)

    for i in range(NUM_ROWS):
        row_y = TOP_MARGIN + (i * ROW_SPACING)
        canvas.create_oval(7, row_y - 1, 9, row_y + 1, fill=HUD_DIM_COLOR, outline="")

    return voltage_dip


def animate():
    canvas.delete("all")
    voltage_dip = draw_hud_frame()

    for stream in streams:
        stream.update()
        for idx, char in enumerate(stream.text):
            char_x = stream.x + (idx * CHAR_SPACING)
            if 18 < char_x < BOX_WIDTH - 10:
                base_color = TRAIL_COLORS[min(idx, len(TRAIL_COLORS) - 1)]

                # Organic per-character phosphor flicker + synchronized voltage dip reaction
                if voltage_dip or random.random() < 0.045:
                    color = random.choice(FLICKER_DIM_COLORS)
                elif random.random() < 0.03:
                    color = "#FFFFFF"  # Brief bright phosphor surge
                else:
                    color = base_color

                weight = "bold" if idx <= 1 else "normal"
                font_spec = ("Cascadia Mono", FONT_SIZE, weight)

                # 1. Crisp 1px dark contrast drop-shadow so glyphs pop off the glass
                canvas.create_text(
                    char_x + 1,
                    stream.y + 1,
                    text=char,
                    fill=SHADOW_COLOR,
                    font=font_spec,
                )

                # 2. Luminous foreground glyph
                canvas.create_text(
                    char_x,
                    stream.y,
                    text=char,
                    fill=color,
                    font=font_spec,
                )

    root.after(FPS_DELAY_MS, animate)


animate()
root.mainloop()
