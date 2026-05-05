import json
import os
import sys
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date, timedelta, time as dtime
import winsound
import math

APP_NAME = "🌸 Racha 30 Días 🌸"
META_DIAS = 30

# 🎀 Paleta kawaii
BG_COLOR = "#ffe6f2"
FRAME_COLOR = "#ffd6eb"
BUTTON_COLOR = "#ff9fcd"
DANGER_COLOR = "#ff4d88"
TEXT_COLOR = "#2d2d2d"
TEXT_SOFT = "#7a4a5e"
INPUT_BG = "#ffffff"

FONT_MAIN = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_SECTION = ("Segoe UI", 11, "bold")
FONT_HERO = ("Segoe UI", 22, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_ASCII = ("Consolas", 10)

TIMER_MINUTES = 30
DEFAULT_REMINDER = "21:00"


# ===== HELPERS DE COLOR Y DIBUJO =====

def _adjust_color(hex_color, amount):
    """amount > 0 aclara, < 0 oscurece. Devuelve hex."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if amount >= 0:
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
    else:
        a = -amount
        r = max(0, int(r * (1 - a)))
        g = max(0, int(g * (1 - a)))
        b = max(0, int(b * (1 - a)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _rounded_rect_points(x1, y1, x2, y2, r):
    """Puntos para create_polygon(smooth=True) que forman un rectángulo
    con esquinas redondeadas."""
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


# ===== WIDGETS CUSTOM =====

class KawaiiButton(tk.Canvas):
    """Botón con esquinas redondeadas + hover + animación al click."""

    def __init__(self, parent, text="", command=None, bg=BUTTON_COLOR,
                 fg="white", font=FONT_MAIN, width=140, height=32,
                 radius=12, **kwargs):
        parent_bg = parent.cget("bg")
        super().__init__(parent, width=width, height=height,
                         bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.command = command
        self.bg = bg
        self.hover_bg = _adjust_color(bg, 0.15)
        self.press_bg = _adjust_color(bg, -0.10)
        self.fg = fg
        self.text = text
        self.font = font
        self.btn_w = width
        self.btn_h = height
        self.radius = radius
        self._pressed = False

        self._draw(bg)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.configure(cursor="hand2")

    def _draw(self, color):
        self.delete("all")
        pts = _rounded_rect_points(0, 0, self.btn_w - 1, self.btn_h - 1, self.radius)
        self.create_polygon(pts, smooth=True, fill=color, outline=color)
        self.create_text(self.btn_w / 2, self.btn_h / 2,
                         text=self.text, fill=self.fg, font=self.font)

    def _on_enter(self, _):
        if not self._pressed:
            self._draw(self.hover_bg)

    def _on_leave(self, _):
        self._pressed = False
        self._draw(self.bg)

    def _on_press(self, _):
        self._pressed = True
        self._draw(self.press_bg)

    def _on_release(self, _):
        was_pressed = self._pressed
        self._pressed = False
        self._draw(self.hover_bg)
        if was_pressed and self.command:
            self.command()


class KawaiiCheckbox(tk.Frame):
    """Checkbox custom: cuadradito redondeado + corazón ♥ cuando está marcado."""

    def __init__(self, parent, text="", variable=None, command=None,
                 bg=BG_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
                 box_color=BUTTON_COLOR, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.variable = variable if variable is not None else tk.IntVar(value=0)
        self.command = command
        self.bg = bg
        self.fg = fg
        self.box_color = box_color
        self._disabled = False

        self.box_size = 22
        self.box = tk.Canvas(self, width=self.box_size, height=self.box_size,
                             bg=bg, highlightthickness=0, bd=0)
        self.box.pack(side="left", padx=(0, 8))

        self.label = tk.Label(self, text=text, bg=bg, fg=fg, font=font)
        self.label.pack(side="left")

        self._draw_box()

        for w in (self, self.box, self.label):
            w.bind("<Button-1>", self._on_click)

        self._update_cursor()

    def _draw_box(self):
        self.box.delete("all")
        s = self.box_size
        r = 5

        if self._disabled:
            outline_color = "#cccccc"
            fill_color = "#f5f5f5"
            heart_color = "#aaaaaa"
            show_heart = bool(self.variable.get())
        elif self.variable.get():
            outline_color = self.box_color
            fill_color = self.box_color
            heart_color = "white"
            show_heart = True
        else:
            outline_color = self.box_color
            fill_color = "white"
            heart_color = self.box_color
            show_heart = False

        pts = _rounded_rect_points(1, 1, s - 2, s - 2, r)
        self.box.create_polygon(pts, smooth=True,
                                fill=fill_color, outline=outline_color, width=2)

        if show_heart:
            self.box.create_text(s / 2, s / 2 - 1, text="♥",
                                 fill=heart_color, font=("Segoe UI", 12, "bold"))

    def _on_click(self, _):
        if self._disabled:
            return
        self.variable.set(0 if self.variable.get() else 1)
        self._draw_box()
        if self.command:
            self.command()

    def _update_cursor(self):
        cursor = "" if self._disabled else "hand2"
        for w in (self.box, self.label):
            try:
                w.configure(cursor=cursor)
            except Exception:
                pass

    def configure(self, **kwargs):
        if "state" in kwargs:
            self._disabled = (kwargs.pop("state") == "disabled")
            self.label.configure(fg="#999999" if self._disabled else self.fg)
            self._draw_box()
            self._update_cursor()
        if kwargs:
            super().configure(**kwargs)

    config = configure


def make_card(parent, padx=14, pady=10):
    """🆕 Helper para crear una 'card' con padding configurable."""
    return tk.Frame(parent, bg=FRAME_COLOR, padx=padx, pady=pady)


# ===== DATOS =====

def get_data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "Racha30")
    os.makedirs(path, exist_ok=True)
    return path


DATA_FILE = os.path.join(get_data_dir(), "racha30_data.json")


def hoy_iso():
    return date.today().isoformat()


def parse_iso_dt(s: str):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def parse_iso_date(s: str):
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def cargar_data():
    if not os.path.exists(DATA_FILE):
        return {
            "days": {}, "streak": 0, "total_done": 0,
            "reminder_time": DEFAULT_REMINDER,
            "timer_end": None, "timer_day": None, "celebrated": False,
        }
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {
            "days": {}, "streak": 0, "total_done": 0,
            "reminder_time": DEFAULT_REMINDER,
            "timer_end": None, "timer_day": None, "celebrated": False,
        }

    data.setdefault("days", {})
    data.setdefault("streak", 0)
    data.setdefault("total_done", 0)
    data.setdefault("reminder_time", DEFAULT_REMINDER)
    data.setdefault("timer_end", None)
    data.setdefault("timer_day", None)
    data.setdefault("celebrated", False)
    return data


def guardar_data(data):
    """Escritura atómica: temporal + replace."""
    tmp_file = DATA_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, DATA_FILE)


def parse_hhmm(hhmm: str):
    try:
        hh, mm = hhmm.strip().split(":")
        h = int(hh)
        m = int(mm)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except Exception:
        pass
    return None


# ===== APP =====

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.configure(bg=BG_COLOR)
        self.resizable(True, True)
        self.geometry("540x720+40+40")
        self.minsize(500, 600)

        # 🆕 Cargar icono si existe (busca icon.ico junto al script)
        # Si no tienes uno todavía, esto simplemente se ignora.
        try:
            if getattr(sys, 'frozen', False):
                # cuando se ejecuta desde un .exe hecho con PyInstaller
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_dir, "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self.data = cargar_data()
        self.vars = []
        self.checkbuttons = {}
        self.reminder_job = None
        self.timer_job = None

        # contenedor para las cards superiores
        cards = tk.Frame(self, bg=BG_COLOR, padx=14)
        cards.pack(fill="x", pady=(14, 0))

        # ===== HEADER CARD =====
        header = make_card(cards, padx=16, pady=14)
        header.pack(fill="x")

        title_row = tk.Frame(header, bg=FRAME_COLOR)
        title_row.pack(fill="x")

        tk.Label(
            title_row, text="🌸 Misiones 30 días",
            bg=FRAME_COLOR, fg=TEXT_COLOR, font=FONT_TITLE
        ).pack(side="left")

        tk.Label(
            title_row, text="(ง •̀_•́)ง",
            bg=FRAME_COLOR, fg=TEXT_SOFT, font=FONT_MAIN
        ).pack(side="right")

        # body: izquierda hero + stats; derecha reloj
        body = tk.Frame(header, bg=FRAME_COLOR)
        body.pack(fill="x", pady=(10, 0))

        left = tk.Frame(body, bg=FRAME_COLOR)
        left.pack(side="left", fill="both", expand=True, anchor="n")

        # Hero "Día X / 30"
        self.hero_label = tk.Label(
            left, text="", bg=FRAME_COLOR, fg=BUTTON_COLOR, font=FONT_HERO
        )
        self.hero_label.pack(anchor="w")

        # 🆕 Stats fila 1: Faltan + Racha
        self.stats_label = tk.Label(
            left, text="", bg=FRAME_COLOR, fg=TEXT_COLOR, font=FONT_MAIN
        )
        self.stats_label.pack(anchor="w", pady=(4, 0))

        # 🆕 Stats fila 2: fecha + hora
        self.date_label = tk.Label(
            left, text="", bg=FRAME_COLOR, fg=TEXT_SOFT, font=FONT_MAIN
        )
        self.date_label.pack(anchor="w", pady=(2, 0))

        # bunny mini, abajito (sigue ahí porque es kawaii ♡)
        tk.Label(
            left, text="( •ᴗ• ) ♡",
            bg=FRAME_COLOR, fg=TEXT_SOFT, font=FONT_ASCII
        ).pack(anchor="w", pady=(8, 0))

        # 🆕 Reloj más chico (95 px) y modernizado
        self.clock_size = 95
        self.clock = tk.Canvas(
            body, width=self.clock_size, height=self.clock_size,
            bg=FRAME_COLOR, highlightthickness=0
        )
        self.clock.pack(side="right", padx=(8, 0), anchor="n")
        self.update_kawaii_clock()

        # ===== TIMER CARD (más compacta) =====
        timer_card = make_card(cards, padx=14, pady=10)
        timer_card.pack(fill="x", pady=(8, 0))

        tk.Label(
            timer_card,
            text=f"⏳  Temporizador · {TIMER_MINUTES} min",
            bg=FRAME_COLOR, fg=TEXT_COLOR, font=FONT_SECTION
        ).pack(anchor="w")

        self.timer_label = tk.Label(
            timer_card, text="Listo para empezar (｡•̀ᴗ-)✧",
            bg=FRAME_COLOR, fg=TEXT_SOFT, font=FONT_MAIN
        )
        self.timer_label.pack(anchor="w", pady=(2, 8))

        timer_btn_row = tk.Frame(timer_card, bg=FRAME_COLOR)
        timer_btn_row.pack(anchor="w")

        KawaiiButton(
            timer_btn_row, text="▶  Iniciar 30 min",
            command=self.iniciar_timer,
            bg=BUTTON_COLOR, width=150, height=32
        ).pack(side="left")

        KawaiiButton(
            timer_btn_row, text="✖  Cancelar",
            command=self.cancelar_timer,
            bg=DANGER_COLOR, width=110, height=32
        ).pack(side="left", padx=(8, 0))

        # ===== RECORDATORIO CARD (todo en una línea) =====
        rec_card = make_card(cards, padx=14, pady=10)
        rec_card.pack(fill="x", pady=(8, 0))

        rec_row = tk.Frame(rec_card, bg=FRAME_COLOR)
        rec_row.pack(fill="x")

        tk.Label(
            rec_row, text="⏰  Recordatorio:",
            bg=FRAME_COLOR, fg=TEXT_COLOR, font=FONT_SECTION
        ).pack(side="left", padx=(0, 8))

        self.reminder_var = tk.StringVar(
            value=self.data.get("reminder_time", DEFAULT_REMINDER)
        )
        tk.Entry(
            rec_row, textvariable=self.reminder_var,
            width=6, justify="center",
            font=("Segoe UI", 11, "bold"),
            bg=INPUT_BG, fg=TEXT_COLOR,
            relief="flat", bd=6,
            highlightthickness=2,
            highlightbackground=BUTTON_COLOR,
            highlightcolor=BUTTON_COLOR,
            insertbackground=TEXT_COLOR,
        ).pack(side="left", ipady=2)

        KawaiiButton(
            rec_row, text="💾  Guardar", command=self.guardar_hora,
            bg=BUTTON_COLOR, width=110, height=32
        ).pack(side="left", padx=(8, 0))

        KawaiiButton(
            rec_row, text="🔔  Probar", command=self.sonar_alarma_inicio,
            bg=BUTTON_COLOR, width=100, height=32
        ).pack(side="left", padx=(6, 0))

        # ===== CHECKLIST =====
        checklist_outer = tk.Frame(self, bg=BG_COLOR, padx=14, pady=10)
        checklist_outer.pack(fill="both", expand=True)

        tk.Label(
            checklist_outer, text="✿  Tus 30 días  ✿",
            bg=BG_COLOR, fg=TEXT_SOFT, font=FONT_SECTION
        ).pack(anchor="w", pady=(0, 8))

        scroll_container = tk.Frame(checklist_outer, bg=BG_COLOR)
        scroll_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(scroll_container, bg=BG_COLOR, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(scroll_container, orient="vertical",
                                      command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg=BG_COLOR)
        self.grid_window = self.canvas.create_window(
            (0, 0), window=self.grid_frame, anchor="nw"
        )

        self.grid_frame.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.grid_window, width=e.width)
        )

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(_):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(_):
            self.canvas.unbind_all("<MouseWheel>")

        self.canvas.bind("<Enter>", _bind_wheel)
        self.canvas.bind("<Leave>", _unbind_wheel)

        for i in range(META_DIAS):
            day_num = i + 1
            var = tk.IntVar(value=1 if self.data["days"].get(str(day_num), {}).get("done") else 0)
            self.vars.append(var)

            r = i % 10
            c = i // 10

            cb = KawaiiCheckbox(
                self.grid_frame,
                text=f"Día {day_num:02d}",
                variable=var,
                bg=BG_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
                box_color=BUTTON_COLOR,
                command=lambda dn=day_num: self.toggle_day(dn)
            )
            cb.grid(row=r, column=c, sticky="w", padx=14, pady=6)
            self.checkbuttons[day_num] = cb

        # ===== BOTONES INFERIORES =====
        bottom = tk.Frame(self, bg=BG_COLOR, padx=14, pady=12)
        bottom.pack(fill="x")

        KawaiiButton(
            bottom, text="✨  Recalcular", command=self.actualizar_info,
            bg=BUTTON_COLOR, width=130, height=32
        ).pack(side="left")

        KawaiiButton(
            bottom, text="🗑  Reiniciar todo", command=self.reiniciar,
            bg=DANGER_COLOR, width=150, height=32
        ).pack(side="right")

        # init
        self.actualizar_info()
        self.refrescar_timer_ui()
        self.programar_recordatorio_diario()

    # ===== RELOJ KAWAII MODERNIZADO =====
    def update_kawaii_clock(self):
        """
        🆕 Reloj rediseñado: más limpio, manecillas rosas en degradé,
        corazones grandes solo en 12/3/6/9, puntitos en las demás horas,
        fondo blanco y borde rosa.
        """
        c = self.clock
        c.delete("all")

        size = self.clock_size
        cx = cy = size / 2
        r_outer = size * 0.46

        dark_pink = _adjust_color(BUTTON_COLOR, -0.25)

        # Círculo exterior con borde rosa y fondo blanco
        c.create_oval(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
                      outline=BUTTON_COLOR, width=3, fill="white")

        # Marcadores: corazones en 12, 3, 6, 9
        for h in (0, 3, 6, 9):
            ang = math.radians(h * 30 - 90)
            x = cx + (r_outer * 0.78) * math.cos(ang)
            y = cy + (r_outer * 0.78) * math.sin(ang)
            c.create_text(x, y, text="♡", fill=BUTTON_COLOR,
                          font=("Segoe UI", 9, "bold"))

        # Marcadores: puntitos en las demás horas
        for h in range(12):
            if h in (0, 3, 6, 9):
                continue
            ang = math.radians(h * 30 - 90)
            x = cx + (r_outer * 0.83) * math.cos(ang)
            y = cy + (r_outer * 0.83) * math.sin(ang)
            c.create_oval(x - 1.5, y - 1.5, x + 1.5, y + 1.5,
                          fill=BUTTON_COLOR, outline=BUTTON_COLOR)

        now = datetime.now()
        sec = now.second
        minute = now.minute + sec / 60.0
        hour = (now.hour % 12) + minute / 60.0

        ang_h = math.radians(hour * 30 - 90)
        ang_m = math.radians(minute * 6 - 90)
        ang_s = math.radians(sec * 6 - 90)

        # Manecilla hora: rosa oscura, gruesa, corta
        c.create_line(cx, cy,
                      cx + (r_outer * 0.50) * math.cos(ang_h),
                      cy + (r_outer * 0.50) * math.sin(ang_h),
                      fill=dark_pink, width=4, capstyle=tk.ROUND)
        # Manecilla minuto: rosa principal
        c.create_line(cx, cy,
                      cx + (r_outer * 0.72) * math.cos(ang_m),
                      cy + (r_outer * 0.72) * math.sin(ang_m),
                      fill=BUTTON_COLOR, width=3, capstyle=tk.ROUND)
        # Manecilla segundo: rosa fuerte, fina
        c.create_line(cx, cy,
                      cx + (r_outer * 0.78) * math.cos(ang_s),
                      cy + (r_outer * 0.78) * math.sin(ang_s),
                      fill=DANGER_COLOR, width=1, capstyle=tk.ROUND)

        # Centro: pequeño círculo rosa fuerte con borde blanco
        c.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                      fill=DANGER_COLOR, outline="white", width=1)

        self.after(1000, self.update_kawaii_clock)

    # ===== PROGRESO =====
    def calcular_racha(self):
        streak = 0
        fecha_anterior = None
        for day in range(1, META_DIAS + 1):
            info = self.data["days"].get(str(day), {})
            if not info.get("done"):
                break
            fecha = parse_iso_date(info.get("date", ""))
            if fecha is None:
                streak += 1
                continue
            if fecha_anterior is None:
                streak = 1
            elif (fecha - fecha_anterior).days <= 1:
                streak += 1
            else:
                streak = 1
            fecha_anterior = fecha
        return streak

    def dia_actual(self):
        for day in range(1, META_DIAS + 1):
            if not self.data["days"].get(str(day), {}).get("done"):
                return day
        return None

    def ya_marco_hoy(self):
        hoy = hoy_iso()
        for day in range(1, META_DIAS + 1):
            info = self.data["days"].get(str(day), {})
            if info.get("done") and info.get("date") == hoy:
                return True
        return False

    # ===== TIMER =====
    def esta_timer_activo(self):
        end_s = self.data.get("timer_end")
        if not end_s:
            return False
        end_dt = parse_iso_dt(end_s)
        if not end_dt:
            return False
        return datetime.now() < end_dt

    def aplicar_bloqueo_por_timer(self):
        for d, cb in self.checkbuttons.items():
            cb.configure(state="normal")
        if self.esta_timer_activo() and self.data.get("timer_day"):
            d = int(self.data["timer_day"])
            if d in self.checkbuttons:
                self.checkbuttons[d].configure(state="disabled")

    def iniciar_timer(self):
        d_act = self.dia_actual()
        if not d_act:
            messagebox.showinfo(APP_NAME, "Ya está todo completado 🎉")
            return
        if self.esta_timer_activo():
            messagebox.showinfo(APP_NAME, "Ya hay un temporizador corriendo ⏳")
            return
        if self.ya_marco_hoy():
            messagebox.showinfo(
                APP_NAME,
                "Ya completaste tu misión de hoy 💖\n¡Vuelve mañana para el siguiente día!"
            )
            return

        end_dt = datetime.now() + timedelta(minutes=TIMER_MINUTES)
        self.data["timer_day"] = d_act
        self.data["timer_end"] = end_dt.isoformat(timespec="seconds")
        guardar_data(self.data)

        self.aplicar_bloqueo_por_timer()
        self.refrescar_timer_ui()

    def cancelar_timer(self):
        if not self.data.get("timer_end"):
            self.timer_label.config(text="Listo para empezar (｡•̀ᴗ-)✧")
            return
        if messagebox.askyesno(APP_NAME, "¿Cancelar el temporizador? (｡•́︿•̀｡)"):
            self.data["timer_day"] = None
            self.data["timer_end"] = None
            guardar_data(self.data)
            self.aplicar_bloqueo_por_timer()
            self.timer_label.config(text="Listo para empezar (｡•̀ᴗ-)✧")
            if self.timer_job is not None:
                try:
                    self.after_cancel(self.timer_job)
                except Exception:
                    pass
                self.timer_job = None

    def refrescar_timer_ui(self):
        if self.timer_job is not None:
            try:
                self.after_cancel(self.timer_job)
            except Exception:
                pass
            self.timer_job = None

        if not self.data.get("timer_end") or not self.data.get("timer_day"):
            self.timer_label.config(text="Listo para empezar (｡•̀ᴗ-)✧")
            self.aplicar_bloqueo_por_timer()
            return

        end_dt = parse_iso_dt(self.data.get("timer_end"))
        if not end_dt:
            self.data["timer_end"] = None
            self.data["timer_day"] = None
            guardar_data(self.data)
            self.timer_label.config(text="Listo para empezar (｡•̀ᴗ-)✧")
            self.aplicar_bloqueo_por_timer()
            return

        now = datetime.now()
        if now >= end_dt:
            try:
                winsound.Beep(1310, 200)
                winsound.Beep(1560, 200)
                winsound.Beep(1760, 200)
            except Exception:
                pass

            d = self.data.get("timer_day")
            self.data["timer_end"] = None
            guardar_data(self.data)

            self.timer_label.config(
                text=f"✅ ¡Cumpliste tu día! Ya puedes marcar el Día {d} (๑•̀ㅂ•́)و✧"
            )
            self.aplicar_bloqueo_por_timer()
            return

        remaining = end_dt - now
        total_sec = int(remaining.total_seconds())
        mm = total_sec // 60
        ss = total_sec % 60
        d = self.data.get("timer_day")
        self.timer_label.config(
            text=f"⏳ Día {d}: faltan {mm:02d}:{ss:02d}  (ง •̀_•́)ง"
        )
        self.aplicar_bloqueo_por_timer()
        self.timer_job = self.after(1000, self.refrescar_timer_ui)

    # ===== CHECKLIST =====
    def toggle_day(self, day_num):
        key = str(day_num)
        done_now = bool(self.vars[day_num - 1].get())

        if done_now and day_num > 1 and not self.data["days"].get(str(day_num - 1), {}).get("done"):
            self.vars[day_num - 1].set(0)
            self.checkbuttons[day_num]._draw_box()
            messagebox.showwarning(APP_NAME,
                                   f"Primero completa el Día {day_num - 1} (｡•́︿•̀｡)")
            return

        if done_now and self.esta_timer_activo() and self.data.get("timer_day") == day_num:
            self.vars[day_num - 1].set(0)
            self.checkbuttons[day_num]._draw_box()
            messagebox.showwarning(APP_NAME,
                                   "Aún no termina el temporizador ⏳ (｡•́︿•̀｡)")
            return

        if done_now and self.ya_marco_hoy():
            self.vars[day_num - 1].set(0)
            self.checkbuttons[day_num]._draw_box()
            messagebox.showinfo(
                APP_NAME,
                "Ya marcaste un día hoy 💖\nVuelve mañana para seguir tu racha real."
            )
            return

        if done_now:
            self.data["days"][key] = {"done": True, "date": hoy_iso()}
        else:
            if key in self.data["days"]:
                self.data["days"][key]["done"] = False

        guardar_data(self.data)
        self.actualizar_info()

    def actualizar_info(self):
        total_done = sum(
            1 for i in range(1, META_DIAS + 1)
            if self.data["days"].get(str(i), {}).get("done")
        )
        streak = self.calcular_racha()
        self.data["total_done"] = total_done
        self.data["streak"] = streak

        faltan = max(0, META_DIAS - total_done)
        d_act = self.dia_actual()

        # hero label + título de la ventana
        if d_act:
            self.hero_label.config(text=f"Día {d_act} / {META_DIAS}")
            self.title(f"🌸 Día {d_act}/{META_DIAS} — Racha 30 Días")
        else:
            self.hero_label.config(text="¡30 / 30! 🎉")
            self.title("🎉 ¡30/30 completados! — Racha 30 Días")

        # 🆕 Stats reorganizadas en dos líneas
        self.stats_label.config(
            text=f"Faltan: {faltan}  ·  Racha: {streak}"
        )
        # fecha en formato dd/mm para que se vea más natural
        fecha_corta = date.today().strftime("%d/%m")
        self.date_label.config(
            text=f"📅 {fecha_corta}  ·  ⏰ {self.data.get('reminder_time', DEFAULT_REMINDER)}"
        )

        self.aplicar_bloqueo_por_timer()

        if total_done >= META_DIAS and not self.data.get("celebrated"):
            self.data["celebrated"] = True
            guardar_data(self.data)
            messagebox.showinfo(APP_NAME, "🎉 ¡Completaste los 30 días! (≧▽≦)✨")
        elif total_done < META_DIAS and self.data.get("celebrated"):
            self.data["celebrated"] = False
            guardar_data(self.data)
        else:
            guardar_data(self.data)

    # ===== RECORDATORIO =====
    def programar_recordatorio_diario(self):
        if self.reminder_job is not None:
            try:
                self.after_cancel(self.reminder_job)
            except Exception:
                pass
            self.reminder_job = None

        hhmm = self.data.get("reminder_time", DEFAULT_REMINDER)
        parsed = parse_hhmm(hhmm)
        if not parsed:
            return

        h, m = parsed
        now = datetime.now()
        target = datetime.combine(date.today(), dtime(hour=h, minute=m))
        if target <= now:
            target += timedelta(days=1)

        delay_ms = int((target - now).total_seconds() * 1000)

        def run_and_reschedule():
            self.sonar_alarma_inicio()
            self.programar_recordatorio_diario()

        self.reminder_job = self.after(delay_ms, run_and_reschedule)

    def sonar_alarma_inicio(self):
        try:
            winsound.Beep(1000, 200)
            winsound.Beep(1000, 200)
        except Exception:
            pass
        messagebox.showinfo(
            APP_NAME,
            "⏰ ¡Debes comenzar ahora! (๑•̀ㅂ•́)و✧\n\n"
            "Aprieta \"Iniciar 30 min\" cuando empieces."
        )

    def guardar_hora(self):
        hhmm = self.reminder_var.get().strip()
        if not parse_hhmm(hhmm):
            messagebox.showerror(APP_NAME, "Formato inválido. Usa HH:MM (ej: 21:00)")
            return
        self.data["reminder_time"] = hhmm
        guardar_data(self.data)
        messagebox.showinfo(APP_NAME, "💖 ¡Hora guardada!")
        self.programar_recordatorio_diario()
        self.actualizar_info()

    # ===== RESET =====
    def reiniciar(self):
        if messagebox.askyesno(APP_NAME, "¿Seguro que quieres reiniciar todo?"):
            self.data = {
                "days": {}, "streak": 0, "total_done": 0,
                "reminder_time": self.data.get("reminder_time", DEFAULT_REMINDER),
                "timer_end": None, "timer_day": None, "celebrated": False,
            }
            guardar_data(self.data)

            for v in self.vars:
                v.set(0)
            for cb in self.checkbuttons.values():
                cb._draw_box()

            self.timer_label.config(text="Listo para empezar (｡•̀ᴗ-)✧")
            self.actualizar_info()
            self.refrescar_timer_ui()
            self.programar_recordatorio_diario()


if __name__ == "__main__":
    App().mainloop()