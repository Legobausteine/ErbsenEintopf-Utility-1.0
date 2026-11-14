"""
ErbsenEinntopf Crossair 2.0 - Fadenkreuz-Overlay für Fortnite (Windows)

Start:    python erbseneinntopf_crossair.py
Standard-Hotkeys (im Menü änderbar):
          F8 = Fadenkreuz an/aus      F9 = Menü ein-/ausblenden

WICHTIG: Fortnite muss im Modus "Vollbild im Fenster" (Windowed Fullscreen)
laufen. Im echten Vollbild kann kein Overlay darüber angezeigt werden.

Das Overlay ist ein eigenes, klick-durchlässiges Fenster. Es greift nicht in
das Spiel ein (kein Auslesen oder Verändern von Spieldaten).
"""
import base64
import ctypes
import json
import math
import os
import random
import sys
import tkinter as tk
from tkinter import colorchooser
from tkinter import font as tkfont

IS_WIN = sys.platform == "win32"

if IS_WIN:
    from ctypes import wintypes

    # Scharfe Pixel auch bei Windows-Skalierung (125 %, 150 % ...)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    user32 = ctypes.windll.user32
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    user32.SetWindowLongW.restype = ctypes.c_long
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
VK_RBUTTON = 0x02

# ----------------------------------------------------------------- Farben
BG = "#0a0713"
SIDEBAR = "#0e0a1b"
CARD = "#15112a"
CARD_HI = "#1e1842"
LINE = "#261f45"
ACCENT = "#a15cff"
ACCENT_HI = "#b985ff"
CYAN = "#4de8ff"
PINK = "#ff3d9a"
TEXT = "#f3f0ff"
MUTED = "#8f88b3"
FAINT = "#5d5782"

F_BODY = ("Segoe UI", 10)
F_BOLD = ("Segoe UI", 10, "bold")
F_NAV = ("Segoe UI", 11)
F_ICON = ("Segoe UI Symbol", 13)
F_TITLE = ("Segoe UI", 20, "bold")
F_TAB = ("Segoe UI", 12, "bold")
F_PILL = ("Segoe UI", 9, "bold")
F_SMALL = ("Segoe UI", 9)

OVERLAY_SIZE = 600
KEY_COLOR = "#010101"  # wird im Overlay komplett durchsichtig
TILE_W, TILE_H = 128, 104

CONFIG_PATH = os.path.join(os.path.expanduser("~"), "crosshair_studio.json")

STYLES = ["Kreuz", "T-Form", "X", "Kreis", "Quadrat", "Raute", "Chevron",
          "Ecken", "Nur Punkt"]
QUICK_COLORS = ["#00ff66", "#00e5ff", "#ff2bd6", "#ff2d2d", "#ffe600", "#ffffff"]

KEYS = {f"F{i}": 0x6F + i for i in range(1, 13)}
KEYS.update({"Einfg": 0x2D, "Entf": 0x2E, "Pos1": 0x24, "Ende": 0x23,
             "BildAuf": 0x21, "BildAb": 0x22})

PRESET_KEYS = ["style", "color", "outline_color", "length", "thickness",
               "gap", "dot", "dot_size", "outline"]
NUM_RANGE = {"length": (1, 60), "thickness": (1, 10), "gap": (0, 40), "dot_size": (1, 10)}

DEFAULTS = {
    "style": "Kreuz",
    "color": "#00ff66",
    "outline_color": "#000000",
    "length": 10,
    "thickness": 2,
    "gap": 4,
    "dot": False,
    "dot_size": 2,
    "outline": True,
    "opacity": 100,
    "scale": 100,
    "offset_x": 0,
    "offset_y": 0,
    "mode": "always",
    "key_toggle": "F8",
    "key_menu": "F9",
    "topmost": True,
    "saved": [],  # Favoriten
}


# ---------------------------------------------------------------- Designs
def P(style, color, length, thickness, gap, dot=False, outline=True,
      oc="#000000", dot_size=2):
    return {"style": style, "color": color, "outline_color": oc, "length": length,
            "thickness": thickness, "gap": gap, "dot": dot, "dot_size": dot_size,
            "outline": outline}


GRN, CYN, MAG, RED = "#00ff66", "#00e5ff", "#ff2bd6", "#ff2d2d"
YEL, WHT, ORG, VIO = "#ffe600", "#ffffff", "#ff9500", "#a15cff"
PNK, LIME = "#ff3d9a", "#b6ff00"

PROFI = [
    P("Kreuz", GRN, 8, 3, 0), P("Kreuz", RED, 7, 2, 5), P("Kreuz", CYN, 4, 4, 5),
    P("Kreuz", MAG, 6, 4, 0, outline=False), P("Kreuz", WHT, 10, 3, 0),
    P("Kreuz", CYN, 8, 3, 5, outline=False), P("Kreuz", WHT, 8, 1, 3, outline=False),
    P("Kreuz", RED, 3, 3, 0), P("Kreuz", WHT, 4, 3, 0, oc="#2040ff"),
    P("Kreuz", GRN, 2, 2, 2), P("Kreuz", GRN, 5, 2, 0), P("Nur Punkt", WHT, 4, 1, 0),
    P("Kreuz", YEL, 9, 2, 4), P("Kreuz", VIO, 7, 3, 3),
    P("Kreuz", LIME, 6, 2, 6, outline=False), P("Kreuz", ORG, 5, 3, 2),
]
TAKTISCH = [
    P("Kreuz", GRN, 6, 2, 6, dot=True), P("T-Form", WHT, 8, 2, 4),
    P("Kreis", CYN, 8, 2, 0, dot=True), P("Kreuz", YEL, 12, 2, 8, dot=True),
    P("T-Form", RED, 10, 2, 3, dot=True), P("Kreis", WHT, 12, 1, 0, outline=False),
    P("Kreuz", MAG, 5, 2, 10, dot=True), P("T-Form", CYN, 6, 3, 2),
    P("Kreuz", WHT, 14, 1, 10, dot=True, dot_size=1), P("Kreuz", ORG, 8, 2, 6, dot=True),
    P("T-Form", GRN, 12, 2, 6, dot=True, dot_size=1), P("Kreuz", VIO, 10, 2, 7, dot=True),
]
PUNKTE = [P("Nur Punkt", c, 4, 1, 0, dot_size=s)
          for c in (GRN, RED, CYN, WHT, MAG, YEL) for s in (2, 4)]
KREISE = [P("Kreis", c, r, 3 if r > 10 else 2, 0, dot=(r == 9), dot_size=1)
          for r in (6, 9, 13) for c in (GRN, CYN, MAG, RED)]
FORMEN = [
    P("Quadrat", CYN, 7, 2, 0), P("Quadrat", WHT, 10, 1, 0, dot=True, dot_size=1),
    P("Quadrat", RED, 5, 3, 0), P("Quadrat", GRN, 12, 2, 0, dot=True),
    P("Raute", MAG, 8, 2, 0), P("Raute", YEL, 11, 2, 0, dot=True),
    P("Raute", WHT, 6, 3, 0), P("Raute", CYN, 14, 1, 0, dot=True, dot_size=1),
    P("Chevron", GRN, 8, 3, 0), P("Chevron", RED, 10, 2, 0, dot=True),
    P("Chevron", WHT, 6, 2, 0), P("Chevron", VIO, 12, 3, 0),
    P("Ecken", CYN, 6, 2, 6), P("Ecken", WHT, 8, 2, 10),
    P("Ecken", GRN, 5, 2, 4, dot=True), P("Ecken", MAG, 10, 2, 8),
    P("X", WHT, 6, 3, 2), P("X", CYN, 5, 3, 1), P("X", MAG, 8, 2, 3), P("X", RED, 4, 4, 0),
]
KOMISCH = [
    P("X", YEL, 10, 2, 4, dot=True), P("Kreis", RED, 18, 3, 0, dot=True),
    P("Nur Punkt", RED, 4, 1, 0, dot_size=6), P("Nur Punkt", VIO, 4, 1, 0, dot_size=8),
    P("Kreis", GRN, 14, 5, 0), P("Kreuz", MAG, 14, 6, 0), P("X", CYN, 12, 4, 6, dot=True),
    P("Kreuz", YEL, 3, 6, 3), P("Raute", PNK, 16, 4, 0),
    P("Quadrat", ORG, 14, 5, 0, dot=True, dot_size=3), P("Chevron", CYN, 16, 5, 0),
    P("Ecken", RED, 14, 4, 12, dot=True),
]

CATS = {"Profi": PROFI, "Taktisch": TAKTISCH, "Punkte": PUNKTE, "Kreise": KREISE,
        "Formen": FORMEN, "Komisch": KOMISCH}
ALL_PRESETS = []
for _items in CATS.values():
    for _p in _items:
        if _p not in ALL_PRESETS:
            ALL_PRESETS.append(_p)
RECOMMENDED = [PROFI[0], PROFI[1], PROFI[4], PROFI[5], TAKTISCH[0], TAKTISCH[2],
               FORMEN[4], FORMEN[8], FORMEN[12], KREISE[1], PUNKTE[2], KOMISCH[8]]

CATEGORIES = ["Alle", "Profi", "Taktisch", "Punkte", "Kreise", "Formen", "Komisch",
              "Zufällig"]
CAT_DESC = {
    "Alle": "Alle Designs auf einen Blick. Mit dem Stern speicherst du Favoriten.",
    "Profi": "Minimalistisch und präzise: so spielen viele Profis.",
    "Taktisch": "Mit Mittelpunkt, T-Form oder Kreis: gut für Mittel- und Fernkampf.",
    "Punkte": "Nur ein Punkt in der Mitte, in verschiedenen Größen und Farben.",
    "Kreise": "Ringe in drei Größen, auf Wunsch mit Mittelpunkt.",
    "Formen": "Quadrat, Raute, Chevron, Ecken und X-Formen.",
    "Komisch": "Ausgefallene Designs für alle, die Abwechslung mögen.",
    "Zufällig": "Zufällig erzeugte Designs. Klicke erneut auf „Zufällig“ für neue.",
}

MODES = [
    ("always", "Immer sichtbar", "Das Fadenkreuz wird dauerhaft angezeigt."),
    ("ads_only", "Nur beim Zielen",
     "Sichtbar, solange die rechte Maustaste gehalten wird."),
    ("ads_hide", "Beim Zielen ausblenden",
     "Verschwindet, solange die rechte Maustaste gehalten wird (z. B. bei Zielfernrohren)."),
]


def random_preset():
    return P(random.choice(STYLES), random.choice(QUICK_COLORS),
             random.randint(3, 14), random.randint(1, 4), random.randint(0, 10),
             dot=random.random() < 0.4, outline=random.random() < 0.8,
             dot_size=random.randint(1, 4))


def sanitize(d):
    """Prüft ein importiertes Design und gibt eine saubere Kopie zurück."""
    out = {}
    if d["style"] not in STYLES:
        raise ValueError("Stil")
    out["style"] = d["style"]
    for k, (lo, hi) in NUM_RANGE.items():
        out[k] = max(lo, min(hi, int(d[k])))
    for k in ("color", "outline_color"):
        v = str(d[k])
        if len(v) != 7 or v[0] != "#":
            raise ValueError("Farbe")
        int(v[1:], 16)
        out[k] = v.lower()
    for k in ("dot", "outline"):
        out[k] = bool(d[k])
    return out


def load_config():
    cfg = dict(DEFAULTS)
    cfg["saved"] = []
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in DEFAULTS:
            if k in data:
                cfg[k] = data[k]
    except Exception:
        pass
    if cfg["style"] not in STYLES:
        cfg["style"] = DEFAULTS["style"]
    if cfg["mode"] not in [m[0] for m in MODES]:
        cfg["mode"] = "always"
    for k in ("key_toggle", "key_menu"):
        if cfg[k] not in KEYS:
            cfg[k] = DEFAULTS[k]
    if not isinstance(cfg["saved"], list):
        cfg["saved"] = []
    clean = []
    for p in cfg["saved"]:
        try:
            clean.append(sanitize(p))
        except Exception:
            pass
    cfg["saved"] = clean
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


# ----------------------------------------------------------- Windows-Helfer
def key_down(vk):
    if not IS_WIN:
        return False
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def resource_path(name):
    """Pfad zu einer Datei, die neben dem Script oder in der EXE liegt."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def make_clickthrough(win):
    """Fenster klick-durchlässig machen, ohne Fokus zu stehlen."""
    if not IS_WIN:
        return
    win.update_idletasks()
    hwnd = user32.GetParent(win.winfo_id()) or win.winfo_id()
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


def dark_titlebar(win):
    """Dunkle Titelleiste (Windows 10/11)."""
    if not IS_WIN:
        return
    try:
        win.update_idletasks()
        hwnd = user32.GetParent(win.winfo_id()) or win.winfo_id()
        value = ctypes.c_int(1)
        dwm = ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD,
                                              ctypes.c_void_p, wintypes.DWORD]
        for attr in (20, 19):  # 20 = Win11/neues Win10, 19 = ältere Win10-Builds
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(value), 4)
    except Exception:
        pass


# ------------------------------------------------------------- Zeichnen
def extent(cfg):
    st, ln, gap, t = cfg["style"], cfg["length"], cfg["gap"], cfg["thickness"]
    if st in ("Kreuz", "T-Form", "X", "Ecken"):
        ext = ln + gap + t
    elif st == "Nur Punkt":
        ext = cfg["dot_size"] + 1
    else:  # Kreis, Quadrat, Raute, Chevron
        ext = ln + t
    if cfg["dot"]:
        ext = max(ext, cfg["dot_size"] + 1)
    return max(ext, 1)


def draw_crosshair(c, cfg, cx, cy, k=1.0):
    """Zeichnet das Fadenkreuz auf eine Canvas (k = Vergrößerungsfaktor)."""
    def s(v, mn=0):
        return max(mn, int(round(v * k)))

    t = s(cfg["thickness"], 1)
    gap = s(cfg["gap"])
    ln = s(cfg["length"], 1)
    col, oc = cfg["color"], cfg["outline_color"]
    o = max(1, int(round(k))) if cfg["outline"] else 0
    style = cfg["style"]
    half = t // 2
    corners = ((-1, -1), (1, -1), (-1, 1), (1, 1))

    def strokes(segs):
        if o:
            for sg in segs:
                c.create_line(*sg, fill=oc, width=t + 2 * o, capstyle="projecting")
        for sg in segs:
            c.create_line(*sg, fill=col, width=t, capstyle="projecting")

    if style in ("Kreuz", "T-Form"):
        rects = []
        if style == "Kreuz":  # bei der T-Form entfällt der obere Arm
            rects.append((cx - half, cy - gap - ln, cx - half + t, cy - gap))
        rects.append((cx - half, cy + gap, cx - half + t, cy + gap + ln))
        rects.append((cx - gap - ln, cy - half, cx - gap, cy - half + t))
        rects.append((cx + gap, cy - half, cx + gap + ln, cy - half + t))
        # Erst alle Umrandungen, dann alle Füllungen (damit sich nichts überdeckt)
        if o:
            for x0, y0, x1, y1 in rects:
                c.create_rectangle(x0 - o, y0 - o, x1 + o, y1 + o, fill=oc, outline="")
        for x0, y0, x1, y1 in rects:
            c.create_rectangle(x0, y0, x1, y1, fill=col, outline="")

    elif style == "X":
        d = max(1, int(round(ln * 0.7071)))
        g = int(round(gap * 0.7071))
        strokes([(cx + sx * g, cy + sy * g, cx + sx * (g + d), cy + sy * (g + d))
                 for sx, sy in corners])

    elif style == "Ecken":
        h = gap + ln
        arm = min(h, max(2, ln - 1))
        segs = []
        for sx, sy in corners:
            segs.append((cx + sx * h, cy + sy * h, cx + sx * (h - arm), cy + sy * h))
            segs.append((cx + sx * h, cy + sy * h, cx + sx * h, cy + sy * (h - arm)))
        strokes(segs)

    elif style == "Kreis":
        r = max(ln, 2)
        if o:
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=oc, width=t + 2 * o)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=col, width=t)

    elif style == "Quadrat":
        r = max(ln, 2)
        if o:
            c.create_rectangle(cx - r, cy - r, cx + r, cy + r, outline=oc, width=t + 2 * o)
        c.create_rectangle(cx - r, cy - r, cx + r, cy + r, outline=col, width=t)

    elif style == "Raute":
        r = max(ln, 2)
        pts = [cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy]
        if o:
            c.create_polygon(pts, fill="", outline=oc, width=t + 2 * o, joinstyle="miter")
        c.create_polygon(pts, fill="", outline=col, width=t, joinstyle="miter")

    elif style == "Chevron":
        pts = (cx - ln, cy + ln, cx, cy, cx + ln, cy + ln)
        if o:
            c.create_line(*pts, fill=oc, width=t + 2 * o, joinstyle="miter",
                          capstyle="projecting")
        c.create_line(*pts, fill=col, width=t, joinstyle="miter", capstyle="projecting")

    if cfg["dot"] or style == "Nur Punkt":
        r = s(cfg["dot_size"], 1)
        if o:
            c.create_oval(cx - r - o, cy - r - o, cx + r + o, cy + r + o,
                          fill=oc, outline="")
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=col, outline="")


def round_rect(c, x0, y0, x1, y1, r, **kw):
    """Abgerundetes Rechteck auf einer Canvas."""
    pts = [x0 + r, y0, x0 + r, y0, x1 - r, y0, x1 - r, y0, x1, y0, x1, y0 + r,
           x1, y0 + r, x1, y1 - r, x1, y1 - r, x1, y1, x1 - r, y1, x1 - r, y1,
           x0 + r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y1 - r, x0, y0 + r,
           x0, y0 + r, x0, y0]
    return c.create_polygon(pts, smooth=True, **kw)


def star_points(cx, cy, ro, ri):
    pts = []
    for i in range(10):
        r = ro if i % 2 == 0 else ri
        a = -math.pi / 2 + i * math.pi / 5
        pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


# ------------------------------------------------------------- Widgets
class Slider(tk.Canvas):
    def __init__(self, parent, lo, hi, value, command, width=260):
        super().__init__(parent, width=width, height=28, bg=BG,
                         highlightthickness=0, cursor="hand2")
        self.lo, self.hi, self.value, self.command, self.w = lo, hi, value, command, width
        self.bind("<Button-1>", self._drag)
        self.bind("<B1-Motion>", self._drag)
        self.draw()

    def _drag(self, e):
        f = min(1.0, max(0.0, (e.x - 12) / (self.w - 24)))
        v = int(round(self.lo + f * (self.hi - self.lo)))
        if v != self.value:
            self.value = v
            self.draw()
            self.command(v)

    def set(self, v):
        self.value = v
        self.draw()

    def draw(self):
        self.delete("all")
        f = (self.value - self.lo) / (self.hi - self.lo)
        x = 12 + f * (self.w - 24)
        self.create_line(12, 14, self.w - 12, 14, fill=LINE, width=5, capstyle="round")
        self.create_line(12, 14, x, 14, fill=ACCENT, width=5, capstyle="round")
        self.create_oval(x - 9, 5, x + 9, 23, fill=ACCENT, outline="")
        self.create_oval(x - 4, 10, x + 4, 18, fill="white", outline="")


class Toggle(tk.Canvas):
    def __init__(self, parent, value, command):
        super().__init__(parent, width=46, height=24, bg=BG,
                         highlightthickness=0, cursor="hand2")
        self.value, self.command = bool(value), command
        self.bind("<Button-1>", self._click)
        self.draw()

    def _click(self, _e):
        self.value = not self.value
        self.draw()
        self.command(self.value)

    def set(self, v):
        self.value = bool(v)
        self.draw()

    def draw(self):
        self.delete("all")
        col = ACCENT if self.value else LINE
        self.create_oval(1, 1, 23, 23, fill=col, outline="")
        self.create_oval(23, 1, 45, 23, fill=col, outline="")
        self.create_rectangle(12, 1, 34, 23, fill=col, outline="")
        x = 34 if self.value else 12
        self.create_oval(x - 8, 4, x + 8, 20, fill="white", outline="")


class Pill(tk.Canvas):
    """Runder Button / Auswahl-Pille."""

    def __init__(self, parent, text, command, font=F_PILL, padx=16, h=32,
                 primary=False, bg=BG):
        self._fnt = tkfont.Font(font=font)
        self.padx = padx
        w = self._fnt.measure(text) + 2 * padx
        super().__init__(parent, width=w, height=h, bg=bg, highlightthickness=0,
                         bd=0, cursor="hand2")
        self.label, self.command, self.w, self.h = text, command, w, h
        self.primary, self.active, self.hover = primary, False, False
        self.bind("<Button-1>", lambda _e: self.command())
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.draw()

    def _set_hover(self, v):
        self.hover = v
        self.draw()

    def set_active(self, v):
        self.active = bool(v)
        self.draw()

    def set_text(self, text):
        self.label = text
        self.w = self._fnt.measure(text) + 2 * self.padx
        self.configure(width=self.w)
        self.draw()

    def draw(self):
        self.delete("all")
        if self.primary or self.active:
            fill = ACCENT_HI if (self.hover and self.primary) else ACCENT
            fg = "white"
        else:
            fill = CARD_HI if self.hover else CARD
            fg = TEXT if self.hover else MUTED
        round_rect(self, 1, 1, self.w - 1, self.h - 1, self.h // 2, fill=fill, outline="")
        self.create_text(self.w // 2, self.h // 2, text=self.label, fill=fg,
                         font=self._fnt)


class Segmented(tk.Frame):
    """Reihe von Auswahl-Pillen."""

    def __init__(self, parent, items, value, command, per_row=99, upper=False):
        super().__init__(parent, bg=BG)
        self.command = command
        self.pills = {}
        for i, it in enumerate(items):
            p = Pill(self, it.upper() if upper else it, lambda v=it: self.pick(v))
            p.grid(row=i // per_row, column=i % per_row, padx=(0, 6), pady=(0, 6),
                   sticky="w")
            self.pills[it] = p
        self.select(value)

    def pick(self, v):
        self.select(v)
        self.command(v)

    def select(self, v):
        self.value = v
        for k, p in self.pills.items():
            p.set_active(k == v)


def make_button(parent, text, command, primary=False):
    return Pill(parent, text, command, font=F_BOLD, padx=22, h=36, primary=primary)


class ScrollArea(tk.Frame):
    """Scrollbarer Bereich mit schmaler, eigener Scrollleiste."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0,
                                yscrollincrement=52)
        self.bar = tk.Canvas(self, width=8, bg=BG, highlightthickness=0, bd=0)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.bar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self.win, width=e.width))
        self.bar.bind("<Button-1>", self._bar_drag)
        self.bar.bind("<B1-Motion>", self._bar_drag)
        self.bind_all("<MouseWheel>", self._wheel, add="+")

    def _wheel(self, e):
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except Exception:
            return
        while w is not None:
            if w is self:
                self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")
                return
            w = w.master

    def _on_scroll(self, first, last):
        first, last = float(first), float(last)
        self.bar.delete("all")
        if first <= 0.0 and last >= 1.0:
            return
        h = max(self.bar.winfo_height(), 1)
        y0 = first * h
        y1 = max(last * h, y0 + 30)
        round_rect(self.bar, 1, y0, 7, y1, 3, fill=LINE, outline="")

    def _bar_drag(self, e):
        h = max(self.bar.winfo_height(), 1)
        first, last = self.canvas.yview()
        self.canvas.yview_moveto(max(0.0, e.y / h - (last - first) / 2))


class Tile(tk.Canvas):
    """Design-Kachel mit Favoriten-Stern."""

    def __init__(self, parent, app, preset):
        super().__init__(parent, width=TILE_W, height=TILE_H, bg=BG,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.app, self.preset = app, preset
        selected = all(app.cfg.get(k) == v for k, v in preset.items())
        self.bgid = round_rect(self, 1, 1, TILE_W - 1, TILE_H - 1, 16, fill=CARD,
                               outline=ACCENT if selected else LINE,
                               width=2 if selected else 1)
        full = {**DEFAULTS, **preset}
        k = max(0.6, min(1.9, 40.0 / extent(full)))
        draw_crosshair(self, full, TILE_W // 2, TILE_H // 2 + 2, k)

        fav = preset in app.cfg["saved"]
        self.create_polygon(star_points(TILE_W - 20, 20, 9, 4), fill=PINK if fav else "",
                            outline=PINK if fav else FAINT, width=1.5)
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda _e: self.itemconfigure(self.bgid, fill=CARD_HI))
        self.bind("<Leave>", lambda _e: self.itemconfigure(self.bgid, fill=CARD))

    def _click(self, e):
        if e.x > TILE_W - 40 and e.y < 40:
            self.app.toggle_saved(self.preset)
        else:
            self.app.apply_preset(self.preset)


# ------------------------------------------------------------------- App
NAV = [
    ("Wesentliches", None),
    ("Fadenkreuz", "◎"),
    ("Anzeigemodi", "▭"),
    ("Position und Größe", "✥"),
    ("Anpassung", None),
    ("Tastenbelegungen", "⌨"),
    ("Designer", "✎"),
    ("Support", None),
    ("Einstellungen", "⚙"),
    ("Hilfe", "?"),
]

LOGO_44_B64 = "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"
ICON_64_B64 = "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"


class App:
    def __init__(self):
        self.cfg = load_config()
        self.root = tk.Tk()
        self.root.title("ErbsenEinntopf Crossair")
        self.root.geometry("1180x720")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", bool(self.cfg["topmost"]))
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self.logo_img = self._image(LOGO_44_B64)
        self.icon_img = self._image(ICON_64_B64)
        self.set_window_icon()

        self.user_visible = True
        self.overlay_shown = True
        self.panel_visible = True
        self.prev = {}
        self.controls = {}
        self.pages = {}
        self.nav_items = {}
        self.current_page = None
        self.save_job = None
        self.toast_job = None
        self.toast_label = None
        self.tab = "Empfohlen"
        self.category = "Alle"
        self.random_items = [random_preset() for _ in range(18)]
        self.designer_preview = None
        self.fav_pill = None

        self.build_overlay()
        self.build_ui()
        self.show_page("Fadenkreuz")
        self.set_tab("Empfohlen")
        self.changed(save=False)
        self.poll()
        self.keep_on_top()
        self.root.after(150, lambda: dark_titlebar(self.root))

    # ------------------------------------------------------------ Icons
    def _image(self, data):
        try:
            return tk.PhotoImage(data=data)
        except Exception:
            return None

    def set_window_icon(self):
        ok = False
        if IS_WIN:
            try:
                self.root.iconbitmap(resource_path("icon.ico"))
                ok = True
            except Exception:
                pass
        if not ok and self.icon_img is not None:
            try:
                self.root.iconphoto(True, self.icon_img)
            except Exception:
                pass

    # -------------------------------------------------------------- Overlay
    def build_overlay(self):
        self.ov = None
        if not IS_WIN:
            return
        self.ov = tk.Toplevel(self.root)
        self.ov.overrideredirect(True)
        self.ov.configure(bg=KEY_COLOR)
        self.ov.attributes("-topmost", True)
        self.ov.attributes("-transparentcolor", KEY_COLOR)
        self.canvas = tk.Canvas(self.ov, width=OVERLAY_SIZE, height=OVERLAY_SIZE,
                                bg=KEY_COLOR, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.place_overlay()
        make_clickthrough(self.ov)

    def place_overlay(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = sw // 2 - OVERLAY_SIZE // 2 + int(self.cfg["offset_x"])
        y = sh // 2 - OVERLAY_SIZE // 2 + int(self.cfg["offset_y"])
        self.ov.geometry(f"{OVERLAY_SIZE}x{OVERLAY_SIZE}+{x}+{y}")

    def redraw_overlay(self):
        if not self.ov:
            return
        self.canvas.delete("all")
        if self.overlay_shown:
            draw_crosshair(self.canvas, self.cfg, OVERLAY_SIZE // 2, OVERLAY_SIZE // 2,
                           self.cfg["scale"] / 100.0)
        self.place_overlay()
        self.ov.attributes("-alpha", max(0.2, min(1.0, self.cfg["opacity"] / 100.0)))

    def keep_on_top(self):
        if self.ov and self.overlay_shown:
            self.ov.attributes("-topmost", True)
            self.ov.lift()
        self.root.after(1000, self.keep_on_top)

    # ----------------------------------------------------------- Hotkeys
    def poll(self):
        k_toggle = key_down(KEYS[self.cfg["key_toggle"]])
        k_menu = key_down(KEYS[self.cfg["key_menu"]])
        if k_toggle and not self.prev.get("t"):
            self.toggle_visible()
        if k_menu and not self.prev.get("m"):
            self.toggle_panel()
        self.prev["t"], self.prev["m"] = k_toggle, k_menu

        if self.ov:
            rmb = key_down(VK_RBUTTON)
            mode = self.cfg["mode"]
            shown = self.user_visible and (
                mode == "always"
                or (mode == "ads_only" and rmb)
                or (mode == "ads_hide" and not rmb))
            if shown != self.overlay_shown:
                self.overlay_shown = shown
                self.redraw_overlay()
        self.root.after(30, self.poll)

    def toggle_visible(self):
        self.user_visible = not self.user_visible
        self.draw_eye()

    def toggle_panel(self):
        self.panel_visible = not self.panel_visible
        if self.panel_visible:
            self.root.deiconify()
        else:
            self.root.withdraw()

    # ------------------------------------------------------------ Aufbau
    def build_ui(self):
        root = self.root
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # Obere Leiste
        top = tk.Frame(root, bg=BG, height=64)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.pack_propagate(False)
        if self.logo_img is not None:
            tk.Label(top, image=self.logo_img, bg=BG).pack(side="left", padx=(22, 10))
            pad = 0
        else:
            pad = 24
        tk.Label(top, text="ErbsenEinntopf", bg=BG, fg="white",
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=(pad, 0))
        tk.Label(top, text=" Crossair", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 15, "bold")).pack(side="left")

        self.eye = tk.Canvas(top, width=34, height=34, bg=BG, highlightthickness=0,
                             cursor="hand2")
        self.eye.pack(side="right", padx=(6, 24))
        self.eye.bind("<Button-1>", lambda _e: self.toggle_visible())
        self.fav_btn = tk.Canvas(top, width=34, height=34, bg=BG, highlightthickness=0,
                                 cursor="hand2")
        self.fav_btn.pack(side="right", padx=6)
        self.fav_btn.bind("<Button-1>", lambda _e: self.toggle_saved(self.current_preset()))
        self.mini = tk.Canvas(top, width=44, height=44, bg=BG, highlightthickness=0)
        self.mini.pack(side="right", padx=8)
        self.vis_label = tk.Label(top, text="SICHTBAR", bg=BG, fg=TEXT,
                                  font=("Segoe UI", 9, "bold"))
        self.vis_label.pack(side="right", padx=(0, 4))
        tk.Frame(root, bg=LINE, height=1).grid(row=0, column=0, columnspan=2,
                                               sticky="sew")

        # Seitenleiste
        side = tk.Frame(root, bg=SIDEBAR, width=240)
        side.grid(row=1, column=0, sticky="ns")
        side.pack_propagate(False)
        tk.Label(side, text="ErbsenEinntopf Crossair 2.0", bg=SIDEBAR, fg=FAINT,
                 font=F_SMALL).pack(side="bottom", pady=16)
        for name, icon in NAV:
            if icon is None:
                tk.Label(side, text=name.upper(), bg=SIDEBAR, fg=FAINT, font=F_PILL,
                         anchor="w").pack(fill="x", padx=28, pady=(22, 6))
                continue
            row = tk.Frame(side, bg=SIDEBAR, cursor="hand2")
            row.pack(fill="x", padx=12, pady=1)
            strip = tk.Frame(row, bg=SIDEBAR, width=3)
            strip.pack(side="left", fill="y")
            ic = tk.Label(row, text=icon, bg=SIDEBAR, fg=MUTED, font=F_ICON, width=2)
            ic.pack(side="left", padx=(12, 8), pady=8)
            tx = tk.Label(row, text=name, bg=SIDEBAR, fg=TEXT, font=F_NAV)
            tx.pack(side="left")
            self.nav_items[name] = (row, strip, ic, tx)
            for w in (row, ic, tx):
                w.bind("<Button-1>", lambda _e, n=name: self.show_page(n))
                w.bind("<Enter>", lambda _e, n=name: self.paint_nav(n, True))
                w.bind("<Leave>", lambda _e, n=name: self.paint_nav(n))

        # Inhalt
        self.content = tk.Frame(root, bg=BG)
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        builders = {
            "Fadenkreuz": self.page_fadenkreuz,
            "Anzeigemodi": self.page_anzeige,
            "Position und Größe": self.page_position,
            "Tastenbelegungen": self.page_tasten,
            "Designer": self.page_designer,
            "Einstellungen": self.page_settings,
            "Hilfe": self.page_hilfe,
        }
        for name, build in builders.items():
            page = tk.Frame(self.content, bg=BG)
            page.grid(row=0, column=0, sticky="nsew", padx=34)
            self.pages[name] = page
            build(page)

    def paint_nav(self, name, hover=False):
        row, strip, ic, tx = self.nav_items[name]
        active = name == self.current_page
        bg = "#1a1432" if active else ("#130f26" if hover else SIDEBAR)
        for w in (row, ic, tx):
            w.configure(bg=bg)
        strip.configure(bg=ACCENT if active else bg)
        ic.configure(fg=ACCENT if active else MUTED)
        tx.configure(fg="white" if active else TEXT)

    def show_page(self, name):
        self.pages[name].tkraise()
        self.current_page = name
        for n in self.nav_items:
            self.paint_nav(n)

    # --------------------------------------------------- Gemeinsame Helfer
    def page_title(self, page, title, desc=None):
        tk.Label(page, text=title, bg=BG, fg="white", font=F_TITLE,
                 anchor="w").pack(fill="x", pady=(28, 2))
        if desc:
            tk.Label(page, text=desc, bg=BG, fg=MUTED, font=F_BODY, anchor="w",
                     justify="left", wraplength=780).pack(fill="x", pady=(0, 16))

    def row_slider(self, parent, label, key, lo, hi, width=260):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg=BG, fg=TEXT, font=F_BODY, width=17,
                 anchor="w").pack(side="left")
        val = tk.Label(row, text=str(self.cfg[key]), bg=BG, fg=ACCENT_HI, font=F_BOLD,
                       width=5, anchor="e")

        def cmd(v):
            self.cfg[key] = v
            val.configure(text=str(v))
            self.changed()

        sl = Slider(row, lo, hi, self.cfg[key], cmd, width=width)
        sl.pack(side="left", padx=8)
        val.pack(side="left")

        def sync():
            sl.set(self.cfg[key])
            val.configure(text=str(self.cfg[key]))

        self.controls[key] = sync

    def row_toggle(self, parent, label, key, on_change=None):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=7)
        tk.Label(row, text=label, bg=BG, fg=TEXT, font=F_BODY, width=30,
                 anchor="w").pack(side="left")

        def cmd(v):
            self.cfg[key] = v
            if on_change:
                on_change(v)
            self.changed()

        tg = Toggle(row, self.cfg[key], cmd)
        tg.pack(side="left")
        self.controls[key] = lambda: tg.set(self.cfg[key])

    def color_row(self, parent, label, key):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=5)
        tk.Label(row, text=label, bg=BG, fg=TEXT, font=F_BODY, width=17,
                 anchor="w").pack(side="left")
        for col in QUICK_COLORS + ["#000000"]:
            sw = tk.Canvas(row, width=26, height=26, bg=BG, highlightthickness=0,
                           cursor="hand2")
            sw.create_oval(3, 3, 23, 23, fill=col, outline=LINE, width=2)
            sw.bind("<Button-1>", lambda _e, c=col: self.set_color(key, c))
            sw.pack(side="left", padx=1)
        cur = tk.Canvas(row, width=32, height=28, bg=BG, highlightthickness=0)

        def draw_cur():
            cur.delete("all")
            cur.create_oval(4, 3, 28, 27, fill=self.cfg[key], outline=ACCENT, width=2)

        draw_cur()
        Pill(row, "Eigene…", lambda: self.pick_color(key), padx=14, h=28).pack(
            side="left", padx=(10, 6))
        cur.pack(side="left")
        self.controls[key] = draw_cur

    def set_color(self, key, col):
        self.cfg[key] = col
        self.controls[key]()
        self.changed()

    def pick_color(self, key):
        result = colorchooser.askcolor(color=self.cfg[key], parent=self.root)
        if result and result[1]:
            self.set_color(key, result[1])

    def toast(self, text):
        if self.toast_job:
            self.root.after_cancel(self.toast_job)
        if self.toast_label is not None:
            self.toast_label.destroy()
        self.toast_label = tk.Label(self.content, text=text, bg=CARD_HI, fg=TEXT,
                                    font=F_BODY, padx=22, pady=11)
        self.toast_label.place(relx=0.5, rely=0.96, anchor="s")
        self.toast_job = self.root.after(2500, self.toast_label.destroy)

    # --------------------------------------------------------- Seite: Fadenkreuz
    def page_fadenkreuz(self, page):
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(4, weight=1)
        head = tk.Frame(page, bg=BG)
        head.grid(row=0, column=0, sticky="ew", pady=(26, 0))
        self.tab_widgets = {}
        for name in ("Empfohlen", "Bibliothek", "Favoriten"):
            f = tk.Frame(head, bg=BG, cursor="hand2")
            f.pack(side="left", padx=(0, 30))
            lb = tk.Label(f, text=name, bg=BG, fg=MUTED, font=F_TAB)
            lb.pack()
            ul = tk.Frame(f, bg=BG, height=3)
            ul.pack(fill="x", pady=(10, 0))
            for w in (f, lb):
                w.bind("<Button-1>", lambda _e, n=name: self.set_tab(n))
            self.tab_widgets[name] = (lb, ul)

        Pill(head, "Importieren", self.import_code, padx=14, h=30).pack(
            side="right", pady=(0, 8))
        Pill(head, "Teilen", self.share, padx=14, h=30).pack(
            side="right", padx=(0, 8), pady=(0, 8))

        tk.Frame(page, bg=LINE, height=1).grid(row=1, column=0, sticky="ew")
        self.pills = Segmented(page, CATEGORIES, self.category, self.set_category,
                               upper=True)
        self.pills.grid(row=2, column=0, sticky="w", pady=(18, 0))
        self.desc = tk.Label(page, text="", bg=BG, fg=TEXT, font=F_BODY, anchor="w",
                             justify="left")
        self.desc.grid(row=3, column=0, sticky="w", pady=(10, 8))
        self.scroll = ScrollArea(page)
        self.scroll.grid(row=4, column=0, sticky="nsew", pady=(0, 16))

    def set_tab(self, name):
        self.tab = name
        for n, (lb, ul) in self.tab_widgets.items():
            on = n == name
            lb.configure(fg="white" if on else MUTED)
            ul.configure(bg=ACCENT if on else BG)
        if name == "Bibliothek":
            self.pills.grid()
        else:
            self.pills.grid_remove()
        self.refresh_grid()

    def set_category(self, cat):
        self.category = cat
        if cat == "Zufällig":
            self.random_items = [random_preset() for _ in range(18)]
        self.refresh_grid()

    def current_items(self):
        if self.tab == "Empfohlen":
            return RECOMMENDED, "Unsere Empfehlungen für Fortnite."
        if self.tab == "Favoriten":
            n = len(self.cfg["saved"])
            return self.cfg["saved"], (f"Deine {n} Favoriten." if n else
                                       "Hier erscheinen deine Favoriten.")
        cat = self.category
        if cat == "Alle":
            items = ALL_PRESETS
        elif cat == "Zufällig":
            items = self.random_items
        else:
            items = CATS[cat]
        return items, CAT_DESC[cat]

    def refresh_grid(self, keep_scroll=False):
        inner = self.scroll.inner
        pos = self.scroll.canvas.yview()[0] if keep_scroll else 0.0
        for w in inner.winfo_children():
            w.destroy()
        items, desc = self.current_items()
        self.desc.configure(text=desc)
        if not items:
            tk.Label(inner, text="Noch keine Favoriten.\nKlicke bei einem Design auf den "
                     "Stern, um es hier zu speichern.", bg=BG, fg=MUTED, font=F_BODY,
                     justify="left").grid(row=0, column=0, sticky="w", pady=30)
        for i, preset in enumerate(items):
            Tile(inner, self, preset).grid(row=i // 6, column=i % 6, padx=6, pady=6)
        self.root.after(40, lambda: self.scroll.canvas.yview_moveto(pos))

    def current_preset(self):
        return {k: self.cfg[k] for k in PRESET_KEYS}

    def apply_preset(self, preset):
        self.cfg.update(preset)
        for fn in self.controls.values():
            fn()
        self.changed()
        self.refresh_grid(keep_scroll=True)

    def toggle_saved(self, preset):
        saved = self.cfg["saved"]
        if preset in saved:
            saved.remove(preset)
            self.toast("Aus Favoriten entfernt")
        else:
            saved.append(dict(preset))
            self.toast("Zu Favoriten hinzugefügt")
        self.changed()
        self.refresh_grid(keep_scroll=True)

    def share(self):
        code = "CSX1:" + base64.urlsafe_b64encode(
            json.dumps(self.current_preset()).encode()).decode()
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.toast("Code in die Zwischenablage kopiert")

    def import_code(self):
        try:
            txt = self.root.clipboard_get().strip()
            if not txt.startswith("CSX1:"):
                raise ValueError("Format")
            data = json.loads(base64.urlsafe_b64decode(txt[5:]).decode())
            preset = sanitize(data)
        except Exception:
            self.toast("Kein gültiger Code in der Zwischenablage")
            return
        self.apply_preset(preset)
        self.toast("Design importiert")

    # ---------------------------------------------------------- Seite: Anzeigemodi
    def page_anzeige(self, page):
        self.page_title(page, "Anzeigemodi",
                        "Lege fest, wann das Fadenkreuz eingeblendet wird.")
        cards = {}

        def select(mode):
            self.cfg["mode"] = mode
            sync()
            self.changed()

        def sync():
            for m, card in cards.items():
                on = m == self.cfg["mode"]
                card.configure(highlightbackground=ACCENT if on else LINE,
                               highlightcolor=ACCENT if on else LINE)

        for mode, title, desc in MODES:
            card = tk.Frame(page, bg=CARD, highlightthickness=2, cursor="hand2")
            card.pack(fill="x", pady=7)
            t = tk.Label(card, text=title, bg=CARD, fg="white",
                         font=("Segoe UI", 12, "bold"), anchor="w")
            t.pack(fill="x", padx=22, pady=(16, 2))
            d = tk.Label(card, text=desc, bg=CARD, fg=MUTED, font=F_BODY, anchor="w")
            d.pack(fill="x", padx=22, pady=(0, 16))
            for w in (card, t, d):
                w.bind("<Button-1>", lambda _e, m=mode: select(m))
            cards[mode] = card
        sync()
        self.controls["mode"] = sync

    # ---------------------------------------------------- Seite: Position und Größe
    def page_position(self, page):
        self.page_title(page, "Position und Größe",
                        "Das Fadenkreuz liegt in der Bildschirmmitte. Mit dem Versatz "
                        "verschiebst du es feiner.")
        self.row_slider(page, "Versatz X", "offset_x", -100, 100, 340)
        self.row_slider(page, "Versatz Y", "offset_y", -100, 100, 340)
        self.row_slider(page, "Gesamtgröße (%)", "scale", 50, 300, 340)
        self.row_slider(page, "Deckkraft (%)", "opacity", 20, 100, 340)

        def center():
            self.cfg["offset_x"] = 0
            self.cfg["offset_y"] = 0
            self.controls["offset_x"]()
            self.controls["offset_y"]()
            self.changed()

        make_button(page, "Zentrieren", center).pack(anchor="w", pady=(20, 0))

    # ---------------------------------------------------- Seite: Tastenbelegungen
    def page_tasten(self, page):
        self.page_title(page, "Tastenbelegungen",
                        "Diese Tasten funktionieren auch, während Fortnite im Vordergrund ist.")
        self.key_vars = {}
        for label, key in (("Fadenkreuz an/aus", "key_toggle"),
                           ("Menü ein-/ausblenden", "key_menu")):
            row = tk.Frame(page, bg=BG)
            row.pack(fill="x", pady=8)
            tk.Label(row, text=label, bg=BG, fg=TEXT, font=F_NAV, width=24,
                     anchor="w").pack(side="left")
            var = tk.StringVar(value=self.cfg[key])
            self.key_vars[key] = var
            om = tk.OptionMenu(row, var, *KEYS.keys(),
                               command=lambda v, k=key: self.set_key(k, v))
            om.configure(bg=CARD, fg=TEXT, activebackground=CARD_HI,
                         activeforeground="white", highlightthickness=0, bd=0,
                         relief="flat", font=F_BOLD, width=8, indicatoron=True)
            om["menu"].configure(bg=CARD, fg=TEXT, activebackground=ACCENT,
                                 activeforeground="white", font=F_BODY, bd=0)
            om.pack(side="left")
            self.controls[key] = lambda v=var, k=key: v.set(self.cfg[k])

    def set_key(self, key, value):
        other = "key_menu" if key == "key_toggle" else "key_toggle"
        if self.cfg[other] == value:
            self.key_vars[key].set(self.cfg[key])
            self.toast("Diese Taste ist schon belegt")
            return
        self.cfg[key] = value
        self.changed()

    # --------------------------------------------------------- Seite: Designer
    def page_designer(self, page):
        self.page_title(page, "Designer", "Baue dein eigenes Fadenkreuz.")
        wrap = tk.Frame(page, bg=BG)
        wrap.pack(fill="both", expand=True)
        left = tk.Frame(wrap, bg=BG)
        left.pack(side="left", fill="y")
        right = tk.Frame(wrap, bg=BG)
        right.pack(side="right", anchor="n", padx=(10, 0))

        def on_style(v):
            self.cfg["style"] = v
            self.changed()

        tk.Label(left, text="Stil", bg=BG, fg=MUTED, font=F_PILL, anchor="w").pack(fill="x")
        seg = Segmented(left, STYLES, self.cfg["style"], on_style, per_row=5)
        seg.pack(anchor="w", pady=(6, 8))
        self.controls["style"] = lambda: seg.select(self.cfg["style"])

        self.color_row(left, "Farbe", "color")
        self.row_toggle(left, "Umrandung", "outline")
        self.color_row(left, "Umrandungsfarbe", "outline_color")
        self.row_toggle(left, "Punkt in der Mitte", "dot")
        self.row_slider(left, "Länge / Radius", "length", 1, 60, 240)
        self.row_slider(left, "Dicke", "thickness", 1, 10, 240)
        self.row_slider(left, "Abstand zur Mitte", "gap", 0, 40, 240)
        self.row_slider(left, "Punkt-Größe", "dot_size", 1, 10, 240)

        tk.Label(right, text="Vorschau", bg=BG, fg=MUTED, font=F_PILL).pack(anchor="w")
        self.designer_preview = tk.Canvas(right, width=260, height=260, bg=BG,
                                          highlightthickness=0)
        self.designer_preview.pack(pady=(8, 12))
        self.fav_pill = make_button(right, "Zu Favoriten hinzufügen",
                                    lambda: self.toggle_saved(self.current_preset()),
                                    primary=True)
        self.fav_pill.pack()

    # -------------------------------------------------------- Seite: Einstellungen
    def page_settings(self, page):
        self.page_title(page, "Einstellungen")

        def set_top(v):
            self.root.attributes("-topmost", bool(v))

        self.row_toggle(page, "Fenster immer im Vordergrund", "topmost", set_top)

        def reset_all():
            for k, v in DEFAULTS.items():
                if k != "saved":
                    self.cfg[k] = v
            self.root.attributes("-topmost", bool(self.cfg["topmost"]))
            for fn in self.controls.values():
                fn()
            self.changed()
            self.refresh_grid()
            self.toast("Alle Einstellungen zurückgesetzt")

        make_button(page, "Alles zurücksetzen", reset_all).pack(anchor="w", pady=(16, 0))
        tk.Label(page, text="Gespeichert in: " + CONFIG_PATH, bg=BG, fg=FAINT,
                 font=F_SMALL, anchor="w").pack(fill="x", pady=(26, 0))

    # ------------------------------------------------------------ Seite: Hilfe
    def page_hilfe(self, page):
        self.page_title(page, "Hilfe")
        tips = [
            "Fortnite muss im Modus „Vollbild im Fenster“ laufen. Im echten Vollbild "
            "wird das Overlay nicht angezeigt.",
            "Das Overlay ist klick-durchlässig. Deine Mausklicks gehen direkt ins Spiel.",
            "Fadenkreuz an/aus: Standard F8. Menü ein-/ausblenden: Standard F9 "
            "(unter „Tastenbelegungen“ änderbar).",
            "Favoriten: Klicke bei einem Design auf den Stern oder oben auf den Stern "
            "neben dem Auge. Alle Favoriten findest du im Tab „Favoriten“.",
            "Unter „Anzeigemodi“ kannst du das Fadenkreuz nur beim Zielen "
            "(rechte Maustaste) ein- oder ausblenden.",
            "Mit „Teilen“ kopierst du dein aktuelles Design als Code, mit „Importieren“ "
            "fügst du einen Code aus der Zwischenablage ein.",
            "Bei Turnieren und Events gelten eigene Regeln. Prüfe vorher, ob Overlays "
            "erlaubt sind.",
        ]
        for t in tips:
            tk.Label(page, text="•  " + t, bg=BG, fg=TEXT, font=F_BODY, anchor="w",
                     justify="left", wraplength=780).pack(fill="x", pady=5)

    # --------------------------------------------------------------- Zeichnen
    def is_favorite(self):
        return self.current_preset() in self.cfg["saved"]

    def draw_eye(self):
        c = self.eye
        c.delete("all")
        col = ACCENT if self.user_visible else FAINT
        c.create_oval(3, 10, 31, 24, outline=col, width=2)
        c.create_oval(12, 11, 22, 23, outline=col, width=2)
        c.create_oval(15, 14, 19, 20, fill=col, outline=col)
        if not self.user_visible:
            c.create_line(5, 29, 29, 5, fill=col, width=2)
        self.vis_label.configure(text="SICHTBAR" if self.user_visible else "VERSTECKT",
                                 fg=TEXT if self.user_visible else MUTED)

    def draw_fav(self):
        fav = self.is_favorite()
        c = self.fav_btn
        c.delete("all")
        c.create_polygon(star_points(17, 18, 13, 5.5), fill=PINK if fav else "",
                         outline=PINK if fav else FAINT, width=2)
        lb, _ul = self.tab_widgets["Favoriten"]
        n = len(self.cfg["saved"])
        lb.configure(text=f"Favoriten ({n})" if n else "Favoriten")
        if self.fav_pill is not None:
            self.fav_pill.set_text("Aus Favoriten entfernen" if fav
                                   else "Zu Favoriten hinzufügen")

    def draw_previews(self):
        self.draw_eye()
        self.draw_fav()
        self.mini.delete("all")
        round_rect(self.mini, 1, 1, 43, 43, 10, fill=CARD, outline=LINE)
        draw_crosshair(self.mini, self.cfg, 22, 22,
                       max(0.4, min(1.0, 15.0 / extent(self.cfg))))
        if self.designer_preview is not None:
            c = self.designer_preview
            c.delete("all")
            round_rect(c, 1, 1, 259, 259, 18, fill=CARD, outline=LINE)
            c.create_line(130, 18, 130, 242, fill=LINE)
            c.create_line(18, 130, 242, 130, fill=LINE)
            k = max(0.5, min(3.0, 105.0 / extent(self.cfg)))
            draw_crosshair(c, self.cfg, 130, 130, k)

    def changed(self, save=True):
        self.redraw_overlay()
        self.draw_previews()
        if save:
            if self.save_job:
                self.root.after_cancel(self.save_job)
            self.save_job = self.root.after(400, lambda: save_config(self.cfg))

    def quit(self):
        save_config(self.cfg)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
