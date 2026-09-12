"""
N.E.X.I.S. GUI
Neural EXecution & Intelligence System

Modern dark command-center interface inspired by the approved NEXIS reference.
Provides:
- Home dashboard
- Chat interface
- Voice interface
- Settings
- Real NEXIS AI integration
- Real microphone integration
- Non-blocking AI/voice operations
"""

import os
import platform
import shutil
import threading
import time
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

try:
    from tools.ai import ask_ai
except Exception as error:
    ask_ai = None
    AI_IMPORT_ERROR = str(error)

try:
    from modules.voice import (
        listen,
        speak,
        set_voice,
        initialize_microphone,
        CURRENT_VOICE,
        VOICE_PROFILES,
    )
except Exception as error:
    listen = None
    speak = None
    set_voice = None
    initialize_microphone = None
    CURRENT_VOICE = "Ryan"
    VOICE_PROFILES = {"Ryan": {"name": "Ryan - British Assistant"}}
    VOICE_IMPORT_ERROR = str(error)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

BG = "#070B12"
SIDEBAR = "#0A0F19"
PANEL = "#0D1522"
PANEL_2 = "#101A2A"
BORDER = "#1B2A3D"
TEXT = "#E7EEF8"
MUTED = "#78879A"
BLUE = "#08A8F7"
BLUE_DARK = "#0879B5"
GREEN = "#28D17C"
RED = "#FF4D5F"
ORANGE = "#F5A623"


class NexusGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("N.E.X.I.S. — Neural EXecution & Intelligence System")
        self.geometry("1400x850")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)

        self.current_page = "HOME"
        self.voice_running = False
        self.voice_thread = None
        self.ai_busy = False
        self.chat_messages = []

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

        self.show_page("HOME")
        self._update_clock()
        self._update_system_status()

    # -----------------------------------------------------------------------
    # Sidebar
    # -----------------------------------------------------------------------

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=SIDEBAR,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        logo = ctk.CTkLabel(
            self.sidebar,
            text="N E X I S",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=TEXT,
        )
        logo.pack(anchor="w", padx=24, pady=(28, 2))

        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="PERSONAL AI SYSTEM",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=MUTED,
        )
        subtitle.pack(anchor="w", padx=25)

        online_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
        )
        online_frame.pack(anchor="w", padx=24, pady=(18, 32))

        self.online_dot = ctk.CTkLabel(
            online_frame,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=GREEN,
        )
        self.online_dot.pack(side="left")

        ctk.CTkLabel(
            online_frame,
            text=" SYSTEM ONLINE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=GREEN,
        ).pack(side="left")

        self.nav_buttons = {}

        for name in ("HOME", "CHAT", "VOICE", "SETTINGS"):
            button = ctk.CTkButton(
                self.sidebar,
                text=name,
                anchor="w",
                height=42,
                corner_radius=7,
                fg_color="transparent",
                hover_color=PANEL_2,
                text_color=TEXT,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda n=name: self.show_page(n),
            )
            button.pack(fill="x", padx=14, pady=3)
            self.nav_buttons[name] = button

        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        status_title = ctk.CTkLabel(
            self.sidebar,
            text="SYSTEM STATUS",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=MUTED,
        )
        status_title.pack(anchor="w", padx=24, pady=(0, 12))

        self.sidebar_status = {}

        for key in ("AI CORE", "WEB", "VOICE"):
            row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=3)

            ctk.CTkLabel(
                row,
                text=key,
                font=ctk.CTkFont(size=9),
                text_color=MUTED,
            ).pack(side="left")

            label = ctk.CTkLabel(
                row,
                text="READY",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=GREEN,
            )
            label.pack(side="right")
            self.sidebar_status[key] = label

        ctk.CTkLabel(
            self.sidebar,
            text="N.E.X.I.S. v1.0",
            font=ctk.CTkFont(size=9),
            text_color="#4C5969",
        ).pack(anchor="w", padx=24, pady=(28, 20))

    # -----------------------------------------------------------------------
    # Main shell
    # -----------------------------------------------------------------------

    def _build_main(self):
        self.main = ctk.CTkFrame(
            self,
            fg_color=BG,
            corner_radius=0,
        )
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(
            self.main,
            height=65,
            fg_color=BG,
            corner_radius=0,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.page_title = ctk.CTkLabel(
            header,
            text="HOME",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT,
        )
        self.page_title.grid(row=0, column=0, sticky="w", padx=30, pady=20)

        self.clock_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
        )
        self.clock_label.grid(row=0, column=1, padx=(0, 30))

        self.content = ctk.CTkFrame(
            self.main,
            fg_color=BG,
            corner_radius=0,
        )
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.statusbar = ctk.CTkFrame(
            self.main,
            height=36,
            fg_color=SIDEBAR,
            corner_radius=0,
        )
        self.statusbar.grid(row=2, column=0, sticky="ew")
        self.statusbar.grid_columnconfigure(0, weight=1)

        self.status_text = ctk.CTkLabel(
            self.statusbar,
            text="SYSTEM STATUS    AI CORE ● READY    WEB ● READY    VOICE ● READY",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=MUTED,
        )
        self.status_text.grid(row=0, column=0, sticky="w", padx=25)

        self._build_pages()

    # -----------------------------------------------------------------------
    # Pages
    # -----------------------------------------------------------------------

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _build_pages(self):
        self.pages = {
            "HOME": self._page_home,
            "CHAT": self._page_chat,
            "VOICE": self._page_voice,
            "SETTINGS": self._page_settings,
        }

    def show_page(self, page):
        self.current_page = page
        self._clear_content()

        for name, button in self.nav_buttons.items():
            button.configure(
                fg_color=PANEL_2 if name == page else "transparent",
                text_color=BLUE if name == page else TEXT,
            )

        self.page_title.configure(text=page)

        builder = self.pages.get(page, self._page_home)
        builder()

    # -----------------------------------------------------------------------
    # HOME
    # -----------------------------------------------------------------------

    def _page_home(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew", padx=25, pady=10)
        frame.grid_columnconfigure(0, weight=3)
        frame.grid_columnconfigure(1, weight=2)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        now = datetime.now()
        if now.hour < 12:
            greeting = "GOOD MORNING, CREATOR"
        elif now.hour < 18:
            greeting = "GOOD AFTERNOON, CREATOR"
        else:
            greeting = "GOOD EVENING, CREATOR"

        ctk.CTkLabel(
            frame,
            text=greeting,
            font=ctk.CTkFont(size=27, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w", pady=(8, 2))

        ctk.CTkLabel(
            frame,
            text="Your personal intelligence dashboard",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
        ).grid(row=0, column=0, sticky="w", pady=(42, 0))

        ctk.CTkLabel(
            frame,
            text=now.strftime("%A, %d %B"),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=MUTED,
        ).grid(row=0, column=1, sticky="e", pady=(25, 0))

        # ---------------- Core ----------------

        core_card = ctk.CTkFrame(
            frame,
            fg_color=PANEL,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        core_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(15, 8))
        core_card.grid_rowconfigure(1, weight=1)
        core_card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(core_card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="N.E.X.I.S. CORE",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=MUTED,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top,
            text="●  READY",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=GREEN,
        ).grid(row=0, column=1, sticky="e")

        orb_canvas = tk.Canvas(
            core_card,
            bg=PANEL,
            highlightthickness=0,
        )
        orb_canvas.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        self.home_orb_canvas = orb_canvas
        self._draw_orb(orb_canvas)

        ctk.CTkLabel(
            core_card,
            text="READY FOR YOUR COMMAND",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT,
        ).grid(row=2, column=0, pady=(0, 3))

        ctk.CTkLabel(
            core_card,
            text="Ask, control, search, analyse or automate.",
            font=ctk.CTkFont(size=9),
            text_color=MUTED,
        ).grid(row=3, column=0, pady=(0, 12))

        actions = ctk.CTkFrame(core_card, fg_color="transparent")
        actions.grid(row=4, column=0, pady=(0, 18))

        ctk.CTkButton(
            actions,
            text="CHAT",
            width=115,
            height=35,
            fg_color=BLUE,
            hover_color=BLUE_DARK,
            command=lambda: self.show_page("CHAT"),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions,
            text="VOICE",
            width=115,
            height=35,
            fg_color=PANEL_2,
            hover_color=BORDER,
            border_width=1,
            border_color=BORDER,
            command=lambda: self.show_page("VOICE"),
        ).pack(side="left", padx=4)

        # ---------------- Right cards ----------------

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(15, 8))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        weather = self._home_card(right, "WEATHER", height=105)
        weather.grid(row=0, column=0, sticky="ew", pady=(0, 7))

        weather_body = ctk.CTkFrame(weather, fg_color="transparent")
        weather_body.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            weather_body,
            text="Mumbai",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT,
        ).pack(side="left")

        ctk.CTkLabel(
            weather_body,
            text="LIVE WEATHER",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color=BLUE,
        ).pack(side="right")

        self.home_weather_label = ctk.CTkLabel(
            weather,
            text="Weather data will appear here",
            font=ctk.CTkFont(size=9),
            text_color=MUTED,
        )
        self.home_weather_label.pack(anchor="w", padx=16, pady=(0, 13))

        markets = self._home_card(right, "MARKETS", height=145)
        markets.grid(row=1, column=0, sticky="ew", pady=7)

        self.home_market_labels = {}
        for name in ("NIFTY 50", "SENSEX", "BANK NIFTY"):
            row = ctk.CTkFrame(markets, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)

            ctk.CTkLabel(
                row,
                text=name,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=TEXT,
            ).pack(side="left")

            value = ctk.CTkLabel(
                row,
                text="—  LIVE",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=MUTED,
            )
            value.pack(side="right")
            self.home_market_labels[name] = value

        ctk.CTkLabel(
            markets,
            text="Live market data will be connected next.",
            font=ctk.CTkFont(size=8),
            text_color=MUTED,
        ).pack(anchor="w", padx=16, pady=(7, 12))

        system = self._home_card(right, "SYSTEM", height=190)
        system.grid(row=2, column=0, sticky="nsew", pady=(7, 0))

        self.home_status_rows = {}
        for label in ("AI CORE", "WEB", "VOICE", "MICROPHONE", "COMPUTER"):
            self._status_row(system, label, "READY")

        # ---------------- News ----------------

        news_card = ctk.CTkFrame(
            frame,
            fg_color=PANEL,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        news_card.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(8, 0),
        )
        news_card.grid_columnconfigure(0, weight=1)
        news_card.grid_rowconfigure(1, weight=1)

        news_header = ctk.CTkFrame(news_card, fg_color="transparent")
        news_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 4))
        news_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            news_header,
            text="LATEST NEWS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w")

        self.news_refresh_label = ctk.CTkLabel(
            news_header,
            text="LIVE • UPDATING",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color=BLUE,
        )
        self.news_refresh_label.grid(row=0, column=1, sticky="e")

        self.home_news_box = ctk.CTkTextbox(
            news_card,
            height=120,
            fg_color=PANEL,
            border_width=0,
            text_color=TEXT,
            font=ctk.CTkFont(size=10),
            wrap="word",
        )
        self.home_news_box.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=15,
            pady=(0, 12),
        )
        self.home_news_box.configure(state="normal")
        self.home_news_box.insert(
            "end",
            "Loading the latest headlines..."
        )
        self.home_news_box.configure(state="disabled")

        # Start live news retrieval without freezing the GUI.
        self._refresh_home_news()

    def _home_card(self, parent, title, height=None):
        card = ctk.CTkFrame(
            parent,
            fg_color=PANEL,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        if height:
            card.configure(height=height)
            card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=MUTED,
        ).pack(anchor="w", padx=16, pady=(14, 8))

        return card

    def _refresh_home_news(self):
        if getattr(self, "home_news_busy", False):
            return

        self.home_news_busy = True

        if hasattr(self, "news_refresh_label"):
            self.news_refresh_label.configure(
                text="LIVE • UPDATING",
                text_color=BLUE,
            )

        threading.Thread(
            target=self._home_news_worker,
            daemon=True,
        ).start()

    def _home_news_worker(self):
        try:
            if ask_ai is None:
                raise RuntimeError(
                    "AI core is unavailable, so live news cannot be loaded."
                )

            prompt = (
                "Find the latest major news right now, prioritising India and "
                "then important world news. Return exactly 5 concise headlines. "
                "For each item use this format: "
                "CATEGORY | HEADLINE | SOURCE. "
                "Use current web information and do not add an introduction "
                "or conclusion."
            )

            response = ask_ai(prompt)

            if not response:
                raise RuntimeError("No news response was returned.")

            cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", response)
            cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned).strip()

            self.after(0, self._finish_home_news, cleaned, None)

        except Exception as error:
            self.after(0, self._finish_home_news, None, str(error))

    def _finish_home_news(self, news, error):
        self.home_news_busy = False

        if not hasattr(self, "home_news_box"):
            return

        self.home_news_box.configure(state="normal")
        self.home_news_box.delete("1.0", "end")

        if error:
            self.home_news_box.insert(
                "end",
                "Unable to load live news right now.\n\n"
                "Open NEWS through N.E.X.I.S. when the news service is available.",
            )
            if hasattr(self, "news_refresh_label"):
                self.news_refresh_label.configure(
                    text="NEWS • UNAVAILABLE",
                    text_color=RED,
                )
        else:
            self.home_news_box.insert("end", news)
            if hasattr(self, "news_refresh_label"):
                self.news_refresh_label.configure(
                    text="LIVE • JUST UPDATED",
                    text_color=GREEN,
                )

        self.home_news_box.configure(state="disabled")

    def _status_row(self, parent, name, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(
            row,
            text=name,
            font=ctk.CTkFont(size=8),
            text_color=MUTED,
        ).pack(side="left")

        label = ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color=GREEN,
        )
        label.pack(side="right")

        if hasattr(self, "home_status_rows"):
            self.home_status_rows[name] = label


    # -----------------------------------------------------------------------
    # CHAT
    # -----------------------------------------------------------------------

    def _page_chat(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew", padx=25, pady=10)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="CHAT",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w", pady=(5, 3))

        ctk.CTkLabel(
            frame,
            text="Communicate naturally with N.E.X.I.S.",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
        ).grid(row=0, column=0, sticky="w", pady=(45, 0))

        chat_panel = ctk.CTkFrame(
            frame,
            fg_color=PANEL,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        chat_panel.grid(row=1, column=0, sticky="nsew", pady=(15, 12))
        chat_panel.grid_rowconfigure(0, weight=1)
        chat_panel.grid_columnconfigure(0, weight=1)

        self.chat_box = ctk.CTkTextbox(
            chat_panel,
            fg_color=PANEL,
            border_width=0,
            text_color=TEXT,
            font=ctk.CTkFont(size=12),
            wrap="word",
        )
        self.chat_box.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        self.chat_box.configure(state="disabled")

        if not self.chat_messages:
            self._append_chat("N.E.X.I.S.", "Good evening, sir. How may I assist you?")
        else:
            for sender, message in self.chat_messages:
                self._append_chat(sender, message)

        input_row = ctk.CTkFrame(frame, fg_color="transparent")
        input_row.grid(row=2, column=0, sticky="ew")
        input_row.grid_columnconfigure(0, weight=1)

        self.chat_entry = ctk.CTkEntry(
            input_row,
            height=45,
            placeholder_text="Type a command or message...",
            fg_color=PANEL,
            border_color=BORDER,
            text_color=TEXT,
            placeholder_text_color=MUTED,
        )
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda event: self.send_chat())

        self.chat_send_button = ctk.CTkButton(
            input_row,
            text="SEND",
            width=110,
            height=45,
            fg_color=BLUE,
            hover_color=BLUE_DARK,
            command=self.send_chat,
        )
        self.chat_send_button.grid(row=0, column=1)

    def _append_chat(self, sender, message):
        if not hasattr(self, "chat_box"):
            return

        self.chat_messages.append((sender, message))

        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{sender}\n", "sender")
        self.chat_box.insert("end", f"{message}\n\n")
        self.chat_box.tag_config("sender", foreground=BLUE)
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def send_chat(self):
        if self.ai_busy:
            return

        text = self.chat_entry.get().strip()
        if not text:
            return

        self.chat_entry.delete(0, "end")
        self._append_chat("YOU", text)

        if ask_ai is None:
            self._append_chat(
                "N.E.X.I.S.",
                f"AI unavailable: {globals().get('AI_IMPORT_ERROR', 'tools.ai could not be loaded.')}",
            )
            return

        self.ai_busy = True
        self.chat_send_button.configure(state="disabled", text="WORKING")

        threading.Thread(
            target=self._chat_worker,
            args=(text,),
            daemon=True,
        ).start()

    def _chat_worker(self, text):
        try:
            response = ask_ai(text)
            if not response:
                response = "I did not receive a response, sir."
        except Exception as error:
            response = f"I encountered an error, sir: {error}"

        self.after(0, self._finish_chat, response)

    def _finish_chat(self, response):
        self.ai_busy = False
        if hasattr(self, "chat_send_button"):
            self.chat_send_button.configure(state="normal", text="SEND")
        self._append_chat("N.E.X.I.S.", response)

    # -----------------------------------------------------------------------
    # VOICE
    # -----------------------------------------------------------------------

    def _page_voice(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew", padx=25, pady=10)
        frame.grid_columnconfigure(0, weight=3)
        frame.grid_columnconfigure(1, weight=2)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="VOICE",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w", pady=(5, 3))

        ctk.CTkLabel(
            frame,
            text="Speak naturally with N.E.X.I.S.",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
        ).grid(row=0, column=0, sticky="w", pady=(45, 0))

        main_card = ctk.CTkFrame(
            frame,
            fg_color=PANEL,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        main_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(15, 0))
        main_card.grid_rowconfigure(0, weight=1)
        main_card.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(
            main_card,
            bg=PANEL,
            highlightthickness=0,
        )
        canvas.grid(row=0, column=0, sticky="nsew", padx=25, pady=25)
        self.voice_canvas = canvas
        self._draw_orb(canvas)

        self.voice_status_label = ctk.CTkLabel(
            main_card,
            text="VOICE READY",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BLUE,
        )
        self.voice_status_label.grid(row=1, column=0, pady=(0, 4))

        self.voice_transcript = ctk.CTkLabel(
            main_card,
            text="Microphone ready.",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
            wraplength=500,
        )
        self.voice_transcript.grid(row=2, column=0, padx=25, pady=(0, 18))

        self.listen_button = ctk.CTkButton(
            main_card,
            text="START LISTENING",
            width=190,
            height=42,
            fg_color=BLUE,
            hover_color=BLUE_DARK,
            command=self.toggle_voice,
        )
        self.listen_button.grid(row=3, column=0, pady=(0, 12))

        self.recalibrate_button = ctk.CTkButton(
            main_card,
            text="RECALIBRATE MICROPHONE",
            width=190,
            height=35,
            fg_color="transparent",
            hover_color=PANEL_2,
            border_width=1,
            border_color=BORDER,
            text_color=MUTED,
            command=self.recalibrate_mic,
        )
        self.recalibrate_button.grid(row=4, column=0, pady=(0, 25))

        profile_card = ctk.CTkFrame(
            frame,
            fg_color=PANEL,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        profile_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(15, 0))

        ctk.CTkLabel(
            profile_card,
            text="VOICE PROFILE",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=MUTED,
        ).pack(anchor="w", padx=20, pady=(22, 9))

        names = [data.get("name", name) for name, data in VOICE_PROFILES.items()]
        self.voice_profile = ctk.CTkOptionMenu(
            profile_card,
            values=names or ["Ryan - British Assistant"],
            fg_color=PANEL_2,
            button_color=BLUE,
            button_hover_color=BLUE_DARK,
            dropdown_fg_color=PANEL_2,
            text_color=TEXT,
        )
        self.voice_profile.pack(fill="x", padx=20)

        ctk.CTkButton(
            profile_card,
            text="TEST VOICE",
            height=35,
            fg_color=PANEL_2,
            hover_color=BORDER,
            command=self.test_voice,
        ).pack(fill="x", padx=20, pady=(10, 25))

        ctk.CTkLabel(
            profile_card,
            text="CURRENT PROFILE",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=MUTED,
        ).pack(anchor="w", padx=20)

        self.current_profile_label = ctk.CTkLabel(
            profile_card,
            text=VOICE_PROFILES.get(
                CURRENT_VOICE,
                {"name": "Ryan - British Assistant"},
            ).get("name", "Ryan - British Assistant"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT,
        )
        self.current_profile_label.pack(anchor="w", padx=20, pady=(6, 0))

    def toggle_voice(self):
        if self.voice_running:
            self.voice_running = False
            self.listen_button.configure(text="START LISTENING")
            self.voice_status_label.configure(text="VOICE READY", text_color=BLUE)
            self.voice_transcript.configure(text="Listening stopped.")
            return

        if listen is None:
            self.voice_transcript.configure(
                text=f"Voice unavailable: {globals().get('VOICE_IMPORT_ERROR', 'modules.voice could not be loaded.')}"
            )
            return

        self.voice_running = True
        self.listen_button.configure(text="STOP LISTENING")
        self.voice_status_label.configure(text="LISTENING", text_color=GREEN)
        self.voice_transcript.configure(text="Listening...")

        self.voice_thread = threading.Thread(
            target=self._voice_worker,
            daemon=True,
        )
        self.voice_thread.start()

    def _voice_worker(self):
        try:
            if initialize_microphone:
                initialize_microphone()

            while self.voice_running:
                # Keep listening until the user presses STOP LISTENING.
                command = listen(timeout=8, phrase_time_limit=10)

                if not self.voice_running:
                    break

                # Timeouts/empty recognition do not end the voice session.
                if not command:
                    self.after(0, self._voice_transcript_update, "Listening...")
                    continue

                self.after(0, self._voice_transcript_update, f"You: {command}")

                if ask_ai is None:
                    self.after(
                        0,
                        self._voice_finished,
                        "AI is unavailable because tools.ai could not be loaded.",
                    )
                    break

                response = ask_ai(command)

                if not self.voice_running:
                    break

                if not response:
                    self.after(
                        0,
                        self._voice_transcript_update,
                        "NEXIS did not return a response. Listening...",
                    )
                    continue

                self.after(
                    0,
                    self._voice_transcript_update,
                    f"You: {command}\n\nNEXIS: {response}",
                )

                if speak:
                    try:
                        speak(response)
                    except Exception as speech_error:
                        self.after(
                            0,
                            self._voice_transcript_update,
                            f"You: {command}\n\nNEXIS: {response}\n\nVoice output error: {speech_error}",
                        )

                # Automatically return to listening for the next utterance.

            self.after(0, self._voice_stopped)

        except Exception as error:
            self.after(0, self._voice_finished, f"Voice error: {error}")

    def _voice_transcript_update(self, text):
        self.voice_transcript.configure(text=text)

    def _voice_stopped(self):
        self.voice_running = False
        if hasattr(self, "listen_button"):
            self.listen_button.configure(text="START LISTENING")
        self.voice_status_label.configure(text="VOICE READY", text_color=BLUE)
        self.voice_transcript.configure(text="Voice session stopped.")

    def _voice_finished(self, text):
        self.voice_running = False
        if hasattr(self, "listen_button"):
            self.listen_button.configure(text="START LISTENING")
        self.voice_status_label.configure(text="VOICE READY", text_color=BLUE)
        self.voice_transcript.configure(text=text)

    def recalibrate_mic(self):
        if initialize_microphone is None:
            self.voice_transcript.configure(text="Microphone system unavailable.")
            return

        self.recalibrate_button.configure(state="disabled")
        self.voice_status_label.configure(text="CALIBRATING", text_color=ORANGE)
        self.voice_transcript.configure(text="Calibrating microphone...")

        threading.Thread(
            target=self._recalibrate_worker,
            daemon=True,
        ).start()

    def _recalibrate_worker(self):
        try:
            # Force a fresh calibration in the existing voice module.
            import modules.voice as voice_module

            voice_module.microphone = None
            voice_module.microphone_calibrated = False

            success = initialize_microphone()

            if success:
                message = "Microphone calibrated and ready."
                color = GREEN
            else:
                message = "Microphone calibration failed."
                color = RED
        except Exception as error:
            message = f"Calibration error: {error}"
            color = RED

        self.after(0, self._finish_recalibration, message, color)

    def _finish_recalibration(self, message, color):
        if hasattr(self, "recalibrate_button"):
            self.recalibrate_button.configure(state="normal")
        self.voice_status_label.configure(
            text="VOICE READY" if color == GREEN else "VOICE ERROR",
            text_color=BLUE if color == GREEN else RED,
        )
        self.voice_transcript.configure(text=message)

    def test_voice(self):
        if speak is None:
            return

        selected = self.voice_profile.get()

        selected_key = None
        for key, data in VOICE_PROFILES.items():
            if data.get("name") == selected:
                selected_key = key
                break

        if selected_key and set_voice:
            set_voice(selected_key)

        self.current_profile_label.configure(text=selected)

        threading.Thread(
            target=lambda: speak("Voice profile test successful, sir."),
            daemon=True,
        ).start()

    # -----------------------------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------------------------

    def _page_settings(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew", padx=25, pady=10)

        ctk.CTkLabel(
            frame,
            text="SETTINGS",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w", pady=(5, 3))

        ctk.CTkLabel(
            frame,
            text="Configure N.E.X.I.S. system preferences.",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
        ).pack(anchor="w", pady=(0, 18))

        card = ctk.CTkFrame(
            frame,
            fg_color=PANEL,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        card.pack(fill="x")

        ctk.CTkLabel(
            card,
            text="INTERFACE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=MUTED,
        ).pack(anchor="w", padx=22, pady=(22, 12))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(0, 20))

        ctk.CTkLabel(
            row,
            text="Appearance",
            font=ctk.CTkFont(size=11),
            text_color=TEXT,
        ).pack(side="left")

        ctk.CTkOptionMenu(
            row,
            values=["Dark"],
            width=120,
            fg_color=PANEL_2,
            button_color=BLUE,
        ).pack(side="right")

        ctk.CTkLabel(
            card,
            text="VOICE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=MUTED,
        ).pack(anchor="w", padx=22, pady=(10, 12))

        ctk.CTkLabel(
            card,
            text="Current voice: Ryan — British Assistant",
            font=ctk.CTkFont(size=11),
            text_color=TEXT,
        ).pack(anchor="w", padx=22, pady=(0, 25))

    # -----------------------------------------------------------------------
    # Visuals / system
    # -----------------------------------------------------------------------

    def _draw_orb(self, canvas):
        def draw():
            try:
                canvas.delete("all")
                width = max(canvas.winfo_width(), 400)
                height = max(canvas.winfo_height(), 350)
                cx = width // 2
                cy = height // 2 - 10

                radius = min(width, height) // 7
                canvas.create_oval(
                    cx - radius - 8,
                    cy - radius - 8,
                    cx + radius + 8,
                    cy + radius + 8,
                    outline=BLUE,
                    width=3,
                )
                canvas.create_oval(
                    cx - radius + 4,
                    cy - radius + 4,
                    cx + radius - 4,
                    cy + radius - 4,
                    outline=BLUE,
                    width=2,
                )
                canvas.create_oval(
                    cx - radius // 2,
                    cy - radius // 2,
                    cx + radius // 2,
                    cy + radius // 2,
                    fill=BLUE,
                    outline=BLUE,
                )
                canvas.create_text(
                    cx,
                    cy + radius + 45,
                    text="N.E.X.I.S.",
                    fill=TEXT,
                    font=("Segoe UI", 12, "bold"),
                )
            except Exception:
                pass

        canvas.after(50, draw)

    def _update_clock(self):
        self.clock_label.configure(
            text=datetime.now().strftime("%d %b %Y   %H:%M:%S")
        )
        self.after(1000, self._update_clock)

    def _update_system_status(self):
        # AI
        ai_ready = ask_ai is not None
        self._set_status("AI CORE", ai_ready)

        # Voice
        voice_ready = listen is not None and speak is not None
        self._set_status("VOICE", voice_ready)

        # Web is provided through tools.ai / Responses API in the current build.
        self._set_status("WEB", ai_ready)

        # Microphone
        mic_ready = False
        try:
            import modules.voice as voice_module
            mic_ready = voice_module.microphone_calibrated
        except Exception:
            pass
        self._set_status("MICROPHONE", mic_ready)

        self._set_status("COMPUTER", True)

        self.after(3000, self._update_system_status)

    def _set_status(self, name, ready):
        color = GREEN if ready else RED
        text = "READY" if ready else "ERROR"

        if hasattr(self, "sidebar_status") and name in self.sidebar_status:
            self.sidebar_status[name].configure(
                text=text,
                text_color=color,
            )

        if hasattr(self, "home_status_rows") and name in self.home_status_rows:
            self.home_status_rows[name].configure(
                text=text,
                text_color=color,
            )


def launch_gui():
    app = NexusGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
