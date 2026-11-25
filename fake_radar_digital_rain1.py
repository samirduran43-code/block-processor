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

# High-contrast luminous palette
TRAIL_COLORS = [
    "#FFFFFF",  # Lead glyph (pure white)
    "#BAE6FD",  # Bright ice blue
    "#7DD3FC",  # Luminous sky cyan
    "#38BDF8",  # Vibrant electric blue
    "#38BDF8",  # Sustained mid-stream clarity
    "#0EA5E9",  # Clean azure
    "#0284C7",  # Readable deep cyan tail
]

HUD_ACCENT_COLOR = "#38BDF8"
HUD_SUBTLE_COLOR = "#0284C7"
HUD_DIM_COLOR = "#0369A1"

# LCD Glass Panel Colors
LCD_BASE_BG = "#041624"      # Deep cybernetic slate-teal glass tint
LCD_SCANLINE_COLOR = "#0A2E46"


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

# 2. Background Mini-LCD Glass Layer (True alpha transparency + subtle backlight flicker)
lcd_bg = tk.Toplevel(root)
lcd_bg.overrideredirect(True)
lcd_bg.attributes("-topmost", True)
lcd_bg.attributes("-alpha", 0.24)
lcd_bg.config(bg=LCD_BASE_BG)
lcd_bg.geometry(f"{BOX_WIDTH}x{BOX_HEIGHT}+{pos_x}+{pos_y}")

bg_canvas = tk.Canvas(
    lcd_bg, width=BOX_WIDTH, height=BOX_HEIGHT, bg=LCD_BASE_BG, highlightthickness=0
)
bg_canvas.pack()

# Draw static fine LCD scanlines & beveled screen border on the glass layer
for y_line in range(0, BOX_HEIGHT, 4):
    bg_canvas.create_line(0, y_line, BOX_WIDTH, y_line, fill=LCD_SCANLINE_COLOR, width=1)
bg_canvas.create_rectangle(
    1, 1, BOX_WIDTH - 2, BOX_HEIGHT - 2, outline="#38BDF8", width=1
)

# Foreground canvas for glowing characters
canvas = tk.Canvas(
    root, width=BOX_WIDTH, height=BOX_HEIGHT, bg="black", highlightthickness=0
)
canvas.pack()

# Make both layers completely click-through
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
    # Keep foreground text window stacked directly above the LCD glass window
    root.lift(lcd_bg)

    # Subtle realistic LCD backlight voltage flicker
    if random.random() < 0.06:
        # Occasional micro-dip like an aging tactical CRT/LCD panel
        flicker_alpha = random.uniform(0.14, 0.19)
    else:
        # Gentle organic ambient shimmer
        flicker_alpha = random.uniform(0.22, 0.27)
    lcd_bg.attributes("-alpha", flicker_alpha)

    # Crisp corner brackets & left spine on the foreground layer
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


def animate():
    canvas.delete("all")
    draw_hud_frame()

    for stream in streams:
        stream.update()
        for idx, char in enumerate(stream.text):
            char_x = stream.x + (idx * CHAR_SPACING)
            if 18 < char_x < BOX_WIDTH - 10:
                color = TRAIL_COLORS[min(idx, len(TRAIL_COLORS) - 1)]
                weight = "bold" if idx == 0 else "normal"
                canvas.create_text(
                    char_x,
                    stream.y,
                    text=char,
                    fill=color,
                    font=("Cascadia Mono", FONT_SIZE, weight),
                )

    root.after(FPS_DELAY_MS, animate)


animate()
root.mainloop()
