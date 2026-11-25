import tkinter as tk
import random
import ctypes

# Overlay dimensions (adjust as needed)
BOX_WIDTH = 220
BOX_HEIGHT = 280
FONT_SIZE = 16
SPEED_MS = 50
CHARS = "가나다라마바사아자차카타파하거너더러머버서어저처커터퍼허고노도로모보소오조초코토포호구누두루무부수우주추쿠투푸후"

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "black")
root.config(bg="black")

# Position at left outermost edge (x = 0) and centered at 50% monitor height
screen_height = root.winfo_screenheight()
pos_x = 0
pos_y = (screen_height // 2) - (BOX_HEIGHT // 2)
root.geometry(f"{BOX_WIDTH}x{BOX_HEIGHT}+{pos_x}+{pos_y}")

canvas = tk.Canvas(root, width=BOX_WIDTH, height=BOX_HEIGHT, bg="black", highlightthickness=0)
canvas.pack()

# Make the window completely click-through on Windows
root.update_idletasks()
hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles | 0x80000 | 0x20)

columns = BOX_WIDTH // FONT_SIZE
drops = [random.randint(0, BOX_HEIGHT // FONT_SIZE) for _ in range(columns)]

def update_rain():
    canvas.delete("all")
    for i in range(columns):
        char = random.choice(CHARS)
        x = i * FONT_SIZE + (FONT_SIZE // 2)
        y = drops[i] * FONT_SIZE
        
        # Draw bright lead character and slightly dimmer trail character above it
        canvas.create_text(x, y, text=char, fill="#00FF82", font=("Malgun Gothic", FONT_SIZE, "bold"))
        if y - FONT_SIZE > 0:
            trail_char = random.choice(CHARS)
            canvas.create_text(x, y - FONT_SIZE, text=trail_char, fill="#008F4C", font=("Malgun Gothic", FONT_SIZE))

        if y > BOX_HEIGHT and random.random() > 0.95:
            drops[i] = 0
        else:
            drops[i] += 1

    root.after(SPEED_MS, update_rain)

update_rain()
root.mainloop()
