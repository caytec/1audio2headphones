"""
1Audio2Headphones - Stream one audio source to two headphone outputs simultaneously.
Uses soundcard library for native WASAPI loopback (zero external setup).
"""

import tkinter as tk
import customtkinter as ctk
import soundcard as sc
import numpy as np
import threading
import json
import os
import queue
from dataclasses import dataclass
from typing import Optional

# silence soundcard data-discontinuity warnings — we use small buffers on purpose
import warnings
warnings.filterwarnings("ignore", category=sc.SoundcardRuntimeWarning) \
    if hasattr(sc, "SoundcardRuntimeWarning") else None

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT   = "#4A9EFF"
SUCCESS  = "#2ECC71"
WARNING  = "#F39C12"
DANGER   = "#E74C3C"
BG_DARK  = "#1A1A2E"
BG_MID   = "#16213E"
BG_CARD  = "#0F3460"
TEXT_DIM = "#8892A4"

# ── Constants ──────────────────────────────────────────────────────────────────
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".1audio2headphones.json")
SAMPLE_RATE   = 48000
CHANNELS      = 2
# WASAPI block size in frames. 480 frames @ 48 kHz = 10 ms.
# Small block = low latency, less risk of WASAPI loopback discontinuity.
WASAPI_BLOCK_FRAMES = 480
# Per-output queue depth (each item ≈ 10 ms).
# 48 ≈ 480 ms — absorbs Bluetooth jitter (typ. 50–200 ms) without audible lag.
QUEUE_DEPTH = 48
# Pre-buffer silence on each player so the device starts with a full HW buffer.
PRIME_BLOCKS = 8

# ── Settings ───────────────────────────────────────────────────────────────────
@dataclass
class Settings:
    """
    Mirror model:
      primary_id  – the headphones that already play natively from Windows
                    (must be set as Windows default output by the user).
                    The app reads its loopback as the source.
      mirror_id   – the second headphones the app COPIES the audio to.
                    Must be different from primary_id (otherwise echo).
    """
    primary_id: Optional[str] = None
    mirror_id:  Optional[str] = None
    volume_primary: float = 1.0  # extra software gain on primary loopback
    volume_mirror:  float = 1.0
    # Legacy fields kept for backwards-compat with old settings file
    input_id:   Optional[str] = None
    output1_id: Optional[str] = None
    output2_id: Optional[str] = None
    volume:  float = 1.0
    volume1: float = 1.0
    volume2: float = 1.0

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, ensure_ascii=False)
        except Exception:
            pass

    @classmethod
    def load(cls) -> "Settings":
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                s = cls()
                for k, v in data.items():
                    if hasattr(s, k):
                        setattr(s, k, v)
                return s
            except Exception:
                pass
        return cls()


# ── Device Helpers ─────────────────────────────────────────────────────────────
def _clean_name(name: str) -> str:
    import re
    name = re.sub(r"\s*\(Realtek[^(]*(?:\([^)]*\)[^(]*)?\)", "", name)
    name = re.sub(r"\(\d+[-\s]+", "(", name)  # "(2- NCX)" → "(NCX)"
    name = re.sub(r"\s*\(\s*\)", "", name)
    return name.strip()


def list_outputs():
    """Return [(id, display_name), ...] – physical playback devices."""
    out = []
    for sp in sc.all_speakers():
        out.append((sp.name, _clean_name(sp.name)))
    return out


def get_default_speaker_name() -> Optional[str]:
    try:
        return sc.default_speaker().name
    except Exception:
        return None


# ── Audio Engine ───────────────────────────────────────────────────────────────
class AudioEngine:
    """
    Mirror engine.

    Source: loopback from `primary_id` (the headphones already playing audio
            natively because Windows default output points at them).
    Sink:   `mirror_id` — the OTHER headphones we copy the audio to.

    There is exactly ONE player and ONE recorder. We never play to the same
    device we capture from, so feedback (echo) is impossible by construction.
    """
    def __init__(self, settings: Settings, on_level):
        self.settings = settings
        self._on_level = on_level
        self._stop_evt = threading.Event()
        self._error: Optional[str] = None
        self._threads: list[threading.Thread] = []
        self._q: queue.Queue = queue.Queue(maxsize=QUEUE_DEPTH)

    def start(self) -> bool:
        s = self.settings
        if not (s.primary_id and s.mirror_id):
            self._error = "Wybierz obie pary słuchawek."
            return False
        if s.primary_id == s.mirror_id:
            self._error = "Pierwsza i druga para muszą być różnymi urządzeniami."
            return False
        self._stop_evt.clear()
        self._error = None
        while not self._q.empty():
            try: self._q.get_nowait()
            except queue.Empty: break

        self._threads = [
            threading.Thread(target=self._capture_loop, daemon=True, name="capture"),
            threading.Thread(target=self._player_loop,  daemon=True, name="player"),
        ]
        for t in self._threads:
            t.start()
        for t in self._threads:
            t.join(timeout=0.4)
        if self._error:
            self.stop()
            return False
        return True

    def stop(self):
        self._stop_evt.set()
        for t in self._threads:
            t.join(timeout=2.0)
        self._threads = []

    @property
    def running(self) -> bool:
        return any(t.is_alive() for t in self._threads)

    @property
    def error(self) -> Optional[str]:
        return self._error

    # ── capture: loopback(primary) → queue ────────────────────────────────────
    def _capture_loop(self):
        s = self.settings
        try:
            mic = sc.get_microphone(id=str(s.primary_id), include_loopback=True)
            recorder = mic.recorder(samplerate=SAMPLE_RATE, channels=CHANNELS,
                                    blocksize=WASAPI_BLOCK_FRAMES)
        except Exception as e:
            self._error = f"Nie można otworzyć źródła ({_clean_name(s.primary_id)}): {e}"
            return
        try:
            with recorder as rec:
                while not self._stop_evt.is_set():
                    data = rec.record(numframes=None)
                    if data is None or len(data) == 0:
                        continue
                    if data.ndim == 1:
                        data = np.column_stack([data, data])
                    elif data.shape[1] == 1:
                        data = np.repeat(data, 2, axis=1)
                    elif data.shape[1] > 2:
                        data = data[:, :2]

                    data = (data * s.volume_primary * s.volume_mirror).astype(
                        np.float32, copy=False)
                    self._on_level(float(np.sqrt(np.mean(data * data))))

                    try: self._q.put_nowait(data.copy())
                    except queue.Full:
                        # Mirror is too slow — drop this frame rather than
                        # block the loopback (would glitch the source app)
                        pass
        except Exception as e:
            if not self._stop_evt.is_set():
                self._error = f"Źródło przerwane: {e}"

    # ── player: queue → mirror device ─────────────────────────────────────────
    def _player_loop(self):
        s = self.settings
        try:
            sp = sc.get_speaker(id=str(s.mirror_id))
            player = sp.player(samplerate=SAMPLE_RATE, channels=CHANNELS,
                               blocksize=WASAPI_BLOCK_FRAMES)
        except Exception as e:
            self._error = f"Nie można otworzyć wyjścia ({_clean_name(s.mirror_id)}): {e}"
            return
        try:
            with player as p:
                silence = np.zeros((WASAPI_BLOCK_FRAMES, CHANNELS), dtype=np.float32)
                for _ in range(PRIME_BLOCKS):
                    p.play(silence)

                while not self._stop_evt.is_set():
                    try:
                        data = self._q.get(timeout=0.1)
                    except queue.Empty:
                        p.play(silence)
                        continue
                    p.play(data)
        except Exception as e:
            if not self._stop_evt.is_set():
                self._error = f"Wyjście przerwane: {e}"


# ── VU Meter ───────────────────────────────────────────────────────────────────
class VUMeter(ctk.CTkCanvas):
    BARS = 24
    COLORS_ON  = [SUCCESS if i < 16 else (WARNING if i < 21 else DANGER) for i in range(BARS)]
    COLORS_OFF = "#1E2A3A"

    def __init__(self, master, **kw):
        super().__init__(master, bg=BG_DARK, highlightthickness=0, **kw)
        self._level  = 0.0
        self._target = 0.0
        self.bind("<Configure>", self._draw)
        self._animate()

    def set_level(self, rms: float):
        self._target = min(rms * 4.0, 1.0)

    def _animate(self):
        if self._target > self._level:
            self._level += (self._target - self._level) * 0.4
        else:
            self._level *= 0.85
        self._target *= 0.85
        self._draw()
        self.after(30, self._animate)

    def _draw(self, *_):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        gap = 2
        bar_w = max(1, (w - gap * (self.BARS - 1)) / self.BARS)
        active = int(self._level * self.BARS)
        for i in range(self.BARS):
            x1 = i * (bar_w + gap)
            color = self.COLORS_ON[i] if i < active else self.COLORS_OFF
            self.create_rectangle(x1, 0, x1 + bar_w, h, fill=color, outline="")


# ── Device Card ────────────────────────────────────────────────────────────────
class DeviceCard(ctk.CTkFrame):
    def __init__(self, master, title: str, role: str, icon: str,
                 items: list, current_id: Optional[str], on_select, **kw):
        super().__init__(master, fg_color=BG_CARD, corner_radius=12, **kw)
        self._on_select = on_select
        self._items = items
        self._label_to_id = {label: dev_id for dev_id, label in items}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(header, text=icon, font=("Segoe UI Emoji", 22)).pack(side="left", padx=(0, 8))
        info = ctk.CTkFrame(header, fg_color="transparent")
        info.pack(side="left")
        ctk.CTkLabel(info, text=title, font=("Segoe UI", 13, "bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(info, text=role, font=("Segoe UI", 10),
                     text_color=TEXT_DIM).pack(anchor="w")

        sep = ctk.CTkFrame(self, fg_color="#1A2A3A", height=1)
        sep.pack(fill="x", padx=16, pady=4)

        labels = [label for _, label in items]
        # preselect by stored id, else first item
        preselect_label: Optional[str] = None
        preselect_id: Optional[str] = None
        if current_id is not None:
            for dev_id, label in items:
                if dev_id == current_id:
                    preselect_label, preselect_id = label, dev_id
                    break
        if preselect_label is None and labels:
            preselect_label = labels[0]
            preselect_id = self._label_to_id[labels[0]]

        self._var = ctk.StringVar(value=preselect_label or "Brak urządzeń")
        self._combo = ctk.CTkComboBox(
            self,
            values=labels if labels else ["Brak dostępnych urządzeń"],
            variable=self._var,
            command=self._changed,
            font=("Segoe UI", 11),
            dropdown_font=("Segoe UI", 11),
            fg_color=BG_MID,
            border_color=ACCENT,
            button_color=ACCENT,
            width=420,
        )
        self._combo.pack(padx=16, pady=(4, 14))

        self._status = ctk.CTkLabel(self, text="● Nie połączono",
                                    font=("Segoe UI", 10), text_color=TEXT_DIM)
        self._status.pack(anchor="w", padx=16, pady=(0, 12))

        if preselect_id is not None:
            self._on_select(preselect_id)

    def _changed(self, value: str):
        dev_id = self._label_to_id.get(value)
        if dev_id is not None:
            self._on_select(dev_id)

    def set_connected(self, connected: bool):
        if connected:
            self._status.configure(text="● Połączono", text_color=SUCCESS)
        else:
            self._status.configure(text="● Nie połączono", text_color=TEXT_DIM)

    def refresh(self, items: list, current_id: Optional[str]):
        self._items = items
        self._label_to_id = {label: dev_id for dev_id, label in items}
        labels = [label for _, label in items]
        self._combo.configure(values=labels if labels else ["Brak dostępnych urządzeń"])
        if current_id is not None:
            for dev_id, label in items:
                if dev_id == current_id:
                    self._var.set(label)
                    return
        if labels:
            self._var.set(labels[0])


# ── Main Window ────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("1Audio2Headphones")
        self.geometry("760x780")
        self.minsize(680, 680)
        self.configure(fg_color=BG_DARK)

        self.settings = Settings.load()
        self._outputs = list_outputs()
        # Migrate legacy settings on first run
        if self.settings.primary_id is None and self.settings.output1_id:
            self.settings.primary_id = self.settings.output1_id
        if self.settings.mirror_id is None and self.settings.output2_id:
            self.settings.mirror_id = self.settings.output2_id
        # If primary still unset, use Windows default
        if self.settings.primary_id is None:
            self.settings.primary_id = get_default_speaker_name()

        self._engine: Optional[AudioEngine] = None
        self._btn_start = None
        self._btn_stop  = None
        self._status_var = None
        self._status_dot = None
        self._pending_level = 0.0

        self._build_ui()
        self._update_ready_state()
        self._poll_level()
        self._poll_engine_health()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Status bar (built first so _set_status works during card init)
        self._status_var = tk.StringVar(value="Skonfiguruj urządzenia i kliknij URUCHOM")
        status_bar = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0, height=36)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        self._status_dot = ctk.CTkLabel(status_bar, text="●", font=("Segoe UI", 14),
                                        text_color=TEXT_DIM)
        self._status_dot.pack(side="left", padx=(14, 4))
        ctk.CTkLabel(status_bar, textvariable=self._status_var,
                     font=("Segoe UI", 11), text_color=TEXT_DIM).pack(side="left")

        # Title
        title_frame = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0, height=64)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        inner = ctk.CTkFrame(title_frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(inner, text="🎧", font=("Segoe UI Emoji", 28)).pack(side="left", padx=(0, 10))
        text_col = ctk.CTkFrame(inner, fg_color="transparent")
        text_col.pack(side="left")
        ctk.CTkLabel(text_col, text="1Audio2Headphones",
                     font=("Segoe UI", 18, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(text_col, text="Jeden dźwięk · Dwie pary słuchawek",
                     font=("Segoe UI", 10), text_color=TEXT_DIM).pack(anchor="w")
        ctk.CTkButton(title_frame, text="⟳ Odśwież",
                      font=("Segoe UI", 11), width=120, height=32,
                      fg_color="transparent", border_width=1, border_color=ACCENT,
                      hover_color=BG_CARD, command=self._refresh_devices
                      ).place(relx=1.0, rely=0.5, anchor="e", x=-16)

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_DARK, scrollbar_button_color=BG_CARD)
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        # Helpful tip panel — explains the model
        tip = ctk.CTkFrame(scroll, fg_color="#0E2A4A", corner_radius=10)
        tip.pack(fill="x", pady=(2, 12))
        ctk.CTkLabel(tip,
            text=("JAK TO DZIAŁA (bez echa, bez sprzężeń):\n\n"
                  "1) W Windows ustaw domyślne wyjście dźwięku na PIERWSZĄ parę\n"
                  "    słuchawek (np. C27). YouTube/gry będą tam grać natywnie.\n\n"
                  "2) W aplikacji wybierz tę samą parę jako Pierwsze słuchawki\n"
                  "    a w Drugich słuchawkach drugą parę (np. NCX).\n\n"
                  "3) URUCHOM. Aplikacja podsłuchuje co gra na pierwszych\n"
                  "    i kopiuje do drugich. Wynik: identyczny dźwięk w obu."),
            font=("Segoe UI", 10), text_color="#B8D4F0", justify="left"
            ).pack(padx=12, pady=10, anchor="w")

        self._section_label(scroll, "  PIERWSZE SŁUCHAWKI (źródło dźwięku)")
        ctk.CTkLabel(scroll,
            text="Te które już grają natywnie z Windows (default output).",
            font=("Segoe UI", 9), text_color=TEXT_DIM
            ).pack(anchor="w", padx=4, pady=(0, 2))
        self._card_primary = DeviceCard(
            scroll,
            title="Pierwsze słuchawki",
            role="Domyślne wyjście Windows (np. C27)",
            icon="🎧",
            items=self._outputs,
            current_id=self.settings.primary_id,
            on_select=self._set_primary,
        )
        self._card_primary.pack(fill="x", pady=(2, 12))

        self._section_label(scroll, "  DRUGIE SŁUCHAWKI (kopia)")
        ctk.CTkLabel(scroll,
            text="Tu aplikacja skopiuje ten sam dźwięk.",
            font=("Segoe UI", 9), text_color=TEXT_DIM
            ).pack(anchor="w", padx=4, pady=(0, 2))
        self._card_mirror = DeviceCard(
            scroll,
            title="Drugie słuchawki",
            role="Druga para – tu trafia kopia (np. NCX)",
            icon="🎧",
            items=self._outputs,
            current_id=self.settings.mirror_id,
            on_select=self._set_mirror,
        )
        self._card_mirror.pack(fill="x", pady=(2, 12))

        self._section_label(scroll, "  GŁOŚNOŚĆ")
        vol_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=12)
        vol_card.pack(fill="x", pady=(4, 12))
        self._add_slider(vol_card, "Głośność źródła",
                         self.settings.volume_primary, self._set_volume_primary)
        ctk.CTkFrame(vol_card, fg_color="#1A2A3A", height=1).pack(fill="x", padx=16, pady=2)
        self._add_slider(vol_card, "Głośność kopii (drugie słuchawki)",
                         self.settings.volume_mirror, self._set_volume_mirror)

        self._section_label(scroll, "  POZIOM SYGNAŁU")
        vu_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=12)
        vu_card.pack(fill="x", pady=(4, 12))
        self._vu = VUMeter(vu_card, height=28)
        self._vu.pack(fill="x", padx=16, pady=14)

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 8))
        self._btn_start = ctk.CTkButton(
            btn_row, text="▶  URUCHOM",
            font=("Segoe UI", 14, "bold"), height=52,
            fg_color=SUCCESS, hover_color="#27AE60", text_color="white",
            corner_radius=12, command=self._start,
        )
        self._btn_start.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._btn_stop = ctk.CTkButton(
            btn_row, text="■  ZATRZYMAJ",
            font=("Segoe UI", 14, "bold"), height=52,
            fg_color=DANGER, hover_color="#C0392B", text_color="white",
            corner_radius=12, command=self._stop, state="disabled",
        )
        self._btn_stop.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Footer with author credit
        footer = ctk.CTkFrame(scroll, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 4))
        ctk.CTkLabel(
            footer,
            text="Created by Kajetan Kupaj  ·  caytec.github.io",
            font=("Segoe UI", 10),
            text_color=TEXT_DIM,
        ).pack()

    def _section_label(self, parent, text: str):
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 10, "bold"),
                     text_color=ACCENT).pack(anchor="w", pady=(8, 2))

    def _add_slider(self, parent, label, value, command):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=label, font=("Segoe UI", 11),
                     text_color="white", width=180, anchor="w").pack(side="left")
        pct_var = tk.StringVar(value=f"{int(value * 100)}%")
        slider = ctk.CTkSlider(
            row, from_=0.0, to=1.0, number_of_steps=100,
            button_color=ACCENT, progress_color=ACCENT,
            command=lambda v, var=pct_var, cb=command: (var.set(f"{int(v*100)}%"), cb(v)),
        )
        slider.set(value)
        slider.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(row, textvariable=pct_var, font=("Segoe UI", 11),
                     text_color=TEXT_DIM, width=40).pack(side="left")

    # ── Selection handlers ────────────────────────────────────────────────────
    def _set_primary(self, dev_id):
        self.settings.primary_id = dev_id
        self.settings.save()
        self._update_ready_state()

    def _set_mirror(self, dev_id):
        self.settings.mirror_id = dev_id
        self.settings.save()
        self._update_ready_state()

    def _set_volume_primary(self, v):
        self.settings.volume_primary = v
        self.settings.save()

    def _set_volume_mirror(self, v):
        self.settings.volume_mirror = v
        self.settings.save()

    # ── Ready state ───────────────────────────────────────────────────────────
    def _update_ready_state(self):
        if self._btn_start is None:
            return
        s = self.settings
        if self._engine and self._engine.running:
            return

        if not (s.primary_id and s.mirror_id):
            self._btn_start.configure(state="disabled")
            missing = []
            if not s.primary_id: missing.append("pierwsze słuchawki")
            if not s.mirror_id:  missing.append("drugie słuchawki")
            self._set_status(f"Wybierz: {', '.join(missing)}", WARNING)
            return

        if s.primary_id == s.mirror_id:
            self._btn_start.configure(state="disabled")
            self._set_status("Pierwsze i drugie słuchawki muszą być różnymi urządzeniami",
                             DANGER)
            return

        # Warn if Windows default doesn't match primary — user might not hear
        # anything on primary unless they switch Windows default to it.
        default_name = get_default_speaker_name()
        self._btn_start.configure(state="normal")
        if default_name and default_name != s.primary_id:
            self._set_status(
                f"Uwaga: w Windows ustaw domyślne wyjście na: {_clean_name(s.primary_id)}",
                WARNING)
        else:
            self._set_status("Gotowy do uruchomienia", TEXT_DIM)

    # ── Start / Stop ──────────────────────────────────────────────────────────
    def _start(self):
        if self._engine and self._engine.running:
            return
        self._engine = AudioEngine(self.settings, self._on_level)
        if self._engine.start():
            self._btn_start.configure(state="disabled")
            self._btn_stop.configure(state="normal")
            self._card_primary.set_connected(True)
            self._card_mirror.set_connected(True)
            self._set_status("Transmisja aktywna – dźwięk kopiowany do drugich słuchawek",
                             SUCCESS)
        else:
            self._show_error(self._engine.error or "Nieznany błąd uruchomienia")

    def _stop(self):
        if self._engine:
            self._engine.stop()
            self._engine = None
        self._btn_start.configure(state="normal")
        self._btn_stop.configure(state="disabled")
        self._card_primary.set_connected(False)
        self._card_mirror.set_connected(False)
        self._vu.set_level(0)
        self._set_status("Zatrzymano", TEXT_DIM)

    def _on_level(self, rms: float):
        # Called from audio thread — only stores value
        self._pending_level = rms

    def _poll_level(self):
        if hasattr(self, "_vu"):
            self._vu.set_level(self._pending_level)
        self.after(30, self._poll_level)

    def _poll_engine_health(self):
        # Detect when audio worker dies unexpectedly (e.g. BT disconnect)
        if self._engine is not None and not self._engine.running:
            err = self._engine.error
            self._engine = None
            self._btn_start.configure(state="normal")
            self._btn_stop.configure(state="disabled")
            self._card_primary.set_connected(False)
            self._card_mirror.set_connected(False)
            if err:
                self._show_error(err)
            else:
                self._set_status("Strumień zatrzymany", WARNING)
        self.after(500, self._poll_engine_health)

    def _refresh_devices(self):
        if self._engine and self._engine.running:
            self._stop()
        self._outputs = list_outputs()
        self._card_primary.refresh(self._outputs, self.settings.primary_id)
        self._card_mirror.refresh(self._outputs, self.settings.mirror_id)
        self._set_status("Lista urządzeń odświeżona", ACCENT)

    def _set_status(self, msg: str, color: str = TEXT_DIM):
        if self._status_var is None:
            return
        self._status_var.set(msg)
        self._status_dot.configure(text_color=color)

    def _show_error(self, msg: str):
        self._set_status(f"Błąd: {msg[:80]}", DANGER)
        win = ctk.CTkToplevel(self)
        win.title("Błąd")
        win.geometry("500x240")
        win.resizable(False, False)
        win.configure(fg_color=BG_DARK)
        win.after(100, lambda: (win.lift(), win.focus_force(), win.grab_set()))
        ctk.CTkLabel(win, text="⚠  Nie można uruchomić strumienia",
                     font=("Segoe UI", 13, "bold"), text_color=DANGER).pack(pady=(24, 8))
        ctk.CTkLabel(win, text=msg, font=("Segoe UI", 10),
                     text_color="white", wraplength=460).pack(pady=4, padx=20)
        ctk.CTkLabel(win,
            text="Wskazówka: zamknij inne aplikacje używające Bluetooth\n"
                 "lub wybierz inne źródło.",
            font=("Segoe UI", 10), text_color=TEXT_DIM, justify="center"
            ).pack(pady=(4, 8), padx=20)
        ctk.CTkButton(win, text="OK", width=100, fg_color=ACCENT,
                      command=win.destroy).pack(pady=12)

    def _on_close(self):
        if self._engine:
            self._engine.stop()
        self.destroy()


# ── Entry ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
