#!/usr/bin/env python3
"""High-Performance Interactive Help & User Manual GUI Window.

Directly powered by docs/CONFIGURATION_GUIDE.md via manual_service.py.
Uses a high-performance tagged Text engine (<30ms load time) with instant
chapter navigation, live keyword search, structured Decision Cards, and
1-click browser HTML viewing.
"""
import os
import re
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict, Any
import customtkinter as ctk

from manual_service import manual_service
from theme import (
    BG, SURFACE, OVERLAY, FIELD, BORDER,
    TEXT, SUBTLE, MUTED, ACCENT, PRIMARY, PRIMARY_HOVER,
    GREEN, RED, YELLOW
)

COLOR_BG = BG
COLOR_SURFACE = SURFACE
COLOR_SIDEBAR = "#181926"
COLOR_CODE_BG = "#13141f"
COLOR_CODE_TEXT = "#eed49f"
COLOR_BORDER = BORDER
COLOR_TEXT = TEXT
COLOR_TEXT_DIM = SUBTLE
COLOR_ACCENT = ACCENT


class _ManualWindowMixin:
    """Shared manual UI and rendering logic for both root window and toplevel."""

    def _init_manual(self):
        self.title("📖 AI Voice Refiner — User Manual & Help Center")
        self.geometry("1060x720")
        self.minsize(860, 560)
        self.configure(fg_color=COLOR_BG)

        self.chapters = manual_service.get_chapters()
        self.current_chapter_idx = 0
        self.chapter_buttons = []

        self._build_ui()
        self.select_chapter(0)

        # Center on screen directly without blocking round-trips
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - 1060) // 2)
        y = max(0, (sh - 720) // 2)
        self.geometry(f"1060x720+{x}+{y}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=290)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Left Navigation Sidebar ───────────────────────────────────────────
        self.sidebar_frame = ctk.CTkFrame(self, fg_color=COLOR_SIDEBAR, corner_radius=0, width=290)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        title_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        title_box.pack(fill="x", padx=16, pady=(16, 6))

        lbl_icon = ctk.CTkLabel(title_box, text="📖", font=ctk.CTkFont(size=22))
        lbl_icon.pack(side="left", padx=(0, 8))

        lbl_title = ctk.CTkLabel(
            title_box,
            text="User Manual",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=COLOR_ACCENT
        )
        lbl_title.pack(side="left")

        lbl_sub = ctk.CTkLabel(
            self.sidebar_frame,
            text="Voice Refiner & Review Hub",
            font=ctk.CTkFont(size=11),
            text_color=MUTED
        )
        lbl_sub.pack(anchor="w", padx=20, pady=(0, 10))

        # Search Box
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        self.search_entry = ctk.CTkEntry(
            self.sidebar_frame,
            textvariable=self.search_var,
            placeholder_text="🔍 Search manual...",
            height=32,
            fg_color=FIELD,
            border_color=BORDER,
            text_color=TEXT
        )
        self.search_entry.pack(fill="x", padx=14, pady=(0, 8))

        # Fast Chapter Navigation Container (<1ms)
        self.nav_scroll = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color="transparent"
        )
        self.nav_scroll.pack(fill="both", expand=True, padx=8, pady=4)

        self._populate_sidebar()

        lbl_source = ctk.CTkLabel(
            self.sidebar_frame,
            text="docs/CONFIGURATION_GUIDE.md",
            font=ctk.CTkFont(size=10),
            text_color=MUTED
        )
        lbl_source.pack(side="bottom", pady=8)

        # ── Right Content Area ────────────────────────────────────────────────
        self.content_container = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(1, weight=1)

        # Header Bar
        self.header_bar = ctk.CTkFrame(self.content_container, fg_color=SURFACE, height=54, corner_radius=0)
        self.header_bar.grid(row=0, column=0, sticky="ew")
        self.header_bar.grid_propagate(False)

        self.lbl_chapter_header = ctk.CTkLabel(
            self.header_bar,
            text="Chapter",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT
        )
        self.lbl_chapter_header.pack(side="left", padx=20, pady=12)

        # Header Actions
        btn_browser = ctk.CTkButton(
            self.header_bar,
            text="🌐 Open in Browser",
            width=140,
            height=32,
            fg_color=ACCENT,
            hover_color=PRIMARY_HOVER,
            text_color="#181926",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_browser
        )
        btn_browser.pack(side="right", padx=16, pady=11)

        btn_copy = ctk.CTkButton(
            self.header_bar,
            text="📋 Copy Text",
            width=90,
            height=32,
            fg_color=OVERLAY,
            hover_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=12),
            command=self._copy_current_chapter
        )
        btn_copy.pack(side="right", padx=(0, 8), pady=11)

        btn_refresh = ctk.CTkButton(
            self.header_bar,
            text="🔄 Reload",
            width=80,
            height=32,
            fg_color=OVERLAY,
            hover_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=12),
            command=self._reload_manual
        )
        btn_refresh.pack(side="right", padx=(0, 8), pady=11)

        # High-Performance Formatted Text View Container
        text_frame = ctk.CTkFrame(self.content_container, fg_color=SURFACE, corner_radius=10, border_width=1, border_color=BORDER)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        scrollbar = tk.Scrollbar(text_frame, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns", pady=6, padx=(0, 6))

        self.text_view = tk.Text(
            text_frame,
            bg=SURFACE,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground=ACCENT,
            selectforeground="#181926",
            relief="flat",
            font=("Inter", 11),
            padx=28,
            pady=22,
            wrap="word",
            state="disabled",
            cursor="xterm",
            yscrollcommand=scrollbar.set
        )
        self.text_view.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=6)
        scrollbar.config(command=self.text_view.yview)

        # Setup Rich Typography Tags
        self._setup_text_tags()

    def _setup_text_tags(self):
        self.text_view.tag_configure("h2", font=("Inter", 16, "bold"), foreground=ACCENT, spacing1=12, spacing3=8)
        self.text_view.tag_configure("h3", font=("Inter", 13, "bold"), foreground="#8bd5ca", spacing1=12, spacing3=6)
        self.text_view.tag_configure("h4", font=("Inter", 11, "bold"), foreground="#f5a97f", spacing1=8, spacing3=4)
        self.text_view.tag_configure("bold", font=("Inter", 11, "bold"), foreground="#ffffff")
        self.text_view.tag_configure("bullet", font=("Inter", 11), foreground=TEXT, lmargin1=16, lmargin2=28)
        self.text_view.tag_configure("subbullet", font=("Inter", 10), foreground="#cad3f5", lmargin1=32, lmargin2=44)
        self.text_view.tag_configure("num_item", font=("Inter", 11, "bold"), foreground="#8aadf4", spacing1=8, spacing3=2)
        self.text_view.tag_configure("normal", font=("Inter", 11), foreground=TEXT, spacing1=2, spacing3=4)
        
        # Code & Monospace
        self.text_view.tag_configure("code_block", font=("Monospace", 10), background=COLOR_CODE_BG, foreground=COLOR_CODE_TEXT, lmargin1=24, lmargin2=24, spacing1=4, spacing3=4)
        self.text_view.tag_configure("code_inline", font=("Monospace", 10), background="#1e1e2e", foreground="#f9e2af")
        
        # Callouts
        self.text_view.tag_configure("callout_tip", font=("Inter", 10, "bold"), background="#1e3428", foreground="#a6da95", lmargin1=16, lmargin2=16, spacing1=6, spacing3=6)
        self.text_view.tag_configure("callout_note", font=("Inter", 10, "bold"), background="#1e2a3f", foreground="#8aadf4", lmargin1=16, lmargin2=16, spacing1=6, spacing3=6)
        self.text_view.tag_configure("callout_warn", font=("Inter", 10, "bold"), background="#3f2d1e", foreground="#f5a97f", lmargin1=16, lmargin2=16, spacing1=6, spacing3=6)
        self.text_view.tag_configure("callout_imp", font=("Inter", 10, "bold"), background="#382142", foreground="#c6a0f6", lmargin1=16, lmargin2=16, spacing1=6, spacing3=6)
        
        # Structured Decision & Setting Cards
        self.text_view.tag_configure("card_border", foreground="#45475a", font=("Monospace", 9))
        self.text_view.tag_configure("card_header", font=("Inter", 12, "bold"), foreground=ACCENT, spacing1=10, spacing3=4)
        self.text_view.tag_configure("card_badge", font=("Inter", 10, "bold"), foreground="#8aadf4")
        self.text_view.tag_configure("card_label", font=("Inter", 10, "bold"), foreground="#8bd5ca", lmargin1=18, lmargin2=18)
        self.text_view.tag_configure("card_val", font=("Inter", 10), foreground=TEXT, lmargin1=18, lmargin2=18)
        self.text_view.tag_configure("card_why_lbl", font=("Inter", 10, "bold"), foreground="#f5a97f", lmargin1=18, lmargin2=18)
        self.text_view.tag_configure("card_why_val", font=("Inter", 10, "italic"), foreground="#eed49f", lmargin1=26, lmargin2=26, spacing3=8)

        # Fallback Table Tags
        self.text_view.tag_configure("table_header", font=("Monospace", 9, "bold"), background="#181926", foreground=ACCENT)
        self.text_view.tag_configure("table_cell", font=("Monospace", 9), foreground=TEXT)
        
        # Search Highlights
        self.text_view.tag_configure("search_match", background="#eed49f", foreground="#181926", font=("Inter", 11, "bold"))

    def _populate_sidebar(self, filter_text: str = ""):
        for btn in self.chapter_buttons:
            btn.destroy()
        self.chapter_buttons.clear()

        query = filter_text.strip().lower()
        for idx, ch in enumerate(self.chapters):
            if query and (query not in ch["title"].lower() and query not in ch["markdown"].lower()):
                continue

            btn_text = f"{ch['icon']} {ch['id']}. {ch['title']}"
            btn = ctk.CTkButton(
                self.nav_scroll,
                text=btn_text,
                anchor="w",
                height=36,
                fg_color=SURFACE if idx == self.current_chapter_idx else "transparent",
                hover_color=OVERLAY,
                text_color=TEXT if idx == self.current_chapter_idx else MUTED,
                font=ctk.CTkFont(size=12, weight="bold" if idx == self.current_chapter_idx else "normal"),
                command=lambda i=idx: self.select_chapter(i)
            )
            btn.pack(fill="x", pady=2)
            self.chapter_buttons.append(btn)

    def _on_search_changed(self, *args):
        query = self.search_var.get().strip()
        self._populate_sidebar(filter_text=query)
        if query:
            self._highlight_search_in_text(query)

    def select_chapter(self, index: int):
        if not (0 <= index < len(self.chapters)):
            return
        self.current_chapter_idx = index
        ch = self.chapters[index]

        # Update Sidebar Highlighting
        self._populate_sidebar(filter_text=self.search_var.get())

        # Update Header
        self.lbl_chapter_header.configure(text=f"{ch['icon']} Chapter {ch['id']}: {ch['title']}")

        # Render Content Instantly in Text View (<25ms)
        self._render_text_content(ch)

        # Apply search highlight if active
        query = self.search_var.get().strip()
        if query:
            self._highlight_search_in_text(query)

    def _render_text_content(self, chapter):
        self.text_view.configure(state="normal")
        self.text_view.delete("1.0", tk.END)

        lines = chapter["markdown"].splitlines()
        in_code_block = False
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # Code Block Toggle
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                tag = "code_block" if in_code_block else "normal"
                self.text_view.insert(tk.END, f"  {line}\n", tag)
                i += 1
                continue

            if in_code_block:
                self.text_view.insert(tk.END, f"  {line}\n", "code_block")
                i += 1
                continue

            # Markdown Tables: buffer entire contiguous table block
            if "|" in stripped and (stripped.startswith("|") or stripped.endswith("|")):
                table_lines = []
                while i < n and "|" in lines[i].strip() and (lines[i].strip().startswith("|") or lines[i].strip().endswith("|")):
                    table_lines.append(lines[i].strip())
                    i += 1
                self._render_table_block(table_lines)
                continue

            # Headings
            if stripped.startswith("## "):
                self.text_view.insert(tk.END, f"\n{stripped[3:]}\n", "h2")
            elif stripped.startswith("### "):
                self.text_view.insert(tk.END, f"\n{stripped[4:]}\n", "h3")
            elif stripped.startswith("#### "):
                self.text_view.insert(tk.END, f"\n{stripped[5:]}\n", "h4")
            # Callouts
            elif stripped.startswith("> [!NOTE]"):
                self.text_view.insert(tk.END, "  ℹ️ NOTE: ", "callout_note")
            elif stripped.startswith("> [!TIP]"):
                self.text_view.insert(tk.END, "  💡 TIP: ", "callout_tip")
            elif stripped.startswith("> [!IMPORTANT]"):
                self.text_view.insert(tk.END, "  ⚡ IMPORTANT: ", "callout_imp")
            elif stripped.startswith("> [!WARNING]"):
                self.text_view.insert(tk.END, "  ⚠️ WARNING: ", "callout_warn")
            elif stripped.startswith("> "):
                self.text_view.insert(tk.END, f"{stripped[2:]}\n\n", "normal")
            # Numbered Points (e.g. 1. **Why Model-Specific Prompts...**)
            elif re.match(r"^\d+\.\s+", stripped):
                self.text_view.insert(tk.END, f"\n{stripped}\n", "num_item")
            # Indented Sub-bullets
            elif (line.startswith("   - ") or line.startswith("   * ") or line.startswith("\t- ")):
                content = stripped[2:] if stripped.startswith(("- ", "* ")) else stripped
                self.text_view.insert(tk.END, f"    •  {content}\n", "subbullet")
            # Bullets
            elif stripped.startswith("- ") or stripped.startswith("* "):
                self.text_view.insert(tk.END, f"•  {stripped[2:]}\n", "bullet")
            elif stripped:
                self.text_view.insert(tk.END, f"{stripped}\n\n", "normal")

            i += 1

        self.text_view.configure(state="disabled")
        self.text_view.yview_moveto(0.0)

    def _render_table_block(self, table_lines: List[str]):
        """Parses a markdown table block and renders as structured Decision Cards or Setting Cards."""
        parsed_rows = []
        for tl in table_lines:
            if "---" in tl:
                continue
            cols = [c.strip() for c in tl.split("|")[1:-1]]
            if cols:
                parsed_rows.append(cols)

        if not parsed_rows:
            return

        headers = parsed_rows[0]
        data_rows = parsed_rows[1:]
        headers_lower = [h.lower() for h in headers]

        # Case A: Speed + Accuracy Decision Matrix (Section 9.1)
        if any("input speech" in h or "target output" in h for h in headers_lower):
            self._render_decision_matrix(data_rows)
            return

        # Case B: Configuration Settings Table (Chapters 2, 3, 4)
        if any("configuration key" in h or "config key" in h for h in headers_lower):
            self._render_config_settings_table(headers, data_rows)
            return

        # Case C: General / Fallback Table
        self._render_general_table(headers, data_rows)

    def _render_decision_matrix(self, rows: List[List[str]]):
        """Renders Speed + Accuracy combinations as high-contrast visual strategy cards."""
        divider = "─" * 74 + "\n"
        for row in rows:
            if not row:
                continue
            input_type = row[0].replace("**", "").strip() if len(row) > 0 else ""
            target_goal = row[1].replace("**", "").strip() if len(row) > 1 else ""
            asr = row[2].replace("`", "").strip() if len(row) > 2 else ""
            lang_mode = row[3].replace("`", "").strip() if len(row) > 3 else ""
            llm = row[4].replace("`", "").strip() if len(row) > 4 else ""
            latency = row[5].replace("**", "").replace("*", "").strip() if len(row) > 5 else ""
            accuracy = row[6].replace("**", "").strip() if len(row) > 6 else ""
            why = row[7].strip() if len(row) > 7 else ""

            self.text_view.insert(tk.END, f"\n{divider}", "card_border")
            self.text_view.insert(tk.END, f"🎯  {input_type}  ➔  {target_goal}\n", "card_header")
            self.text_view.insert(tk.END, f"{divider}", "card_border")

            self.text_view.insert(tk.END, "  • 🎙️ Optimal ASR:       ", "card_label")
            self.text_view.insert(tk.END, f"{asr}\n", "card_val")

            self.text_view.insert(tk.END, "  • 🌐 Language Mode:     ", "card_label")
            self.text_view.insert(tk.END, f"{lang_mode}\n", "card_val")

            self.text_view.insert(tk.END, "  • 🤖 Recommended LLM:   ", "card_label")
            self.text_view.insert(tk.END, f"{llm}\n", "card_val")

            self.text_view.insert(tk.END, "  • ⚡ End-to-End Latency: ", "card_label")
            self.text_view.insert(tk.END, f"{latency}\n", "card_val")

            self.text_view.insert(tk.END, "  • 🏆 Accuracy Rating:   ", "card_label")
            self.text_view.insert(tk.END, f"{accuracy}\n", "card_val")

            if why:
                self.text_view.insert(tk.END, "  • 💡 Why This Excels:\n", "card_why_lbl")
                self.text_view.insert(tk.END, f"    {why}\n", "card_why_val")

        self.text_view.insert(tk.END, f"{divider}\n", "card_border")

    def _render_config_settings_table(self, headers: List[str], rows: List[List[str]]):
        """Renders configuration key tables as structured property blocks."""
        for row in rows:
            if not row:
                continue
            key = row[0].replace("`", "").strip()
            type_str = row[1].replace("`", "").strip() if len(row) > 1 else ""
            default_val = row[2].replace("`", "").strip() if len(row) > 2 else ""
            options = row[3].replace("`", "").strip() if len(row) >= 5 else ""
            desc = row[-1].strip() if len(row) >= 4 else ""

            self.text_view.insert(tk.END, f"\n⚙️  {key}", "card_header")
            if type_str or default_val:
                meta = f"  ({type_str}, Default: {default_val})" if default_val else f"  ({type_str})"
                self.text_view.insert(tk.END, f"{meta}\n", "card_badge")
            else:
                self.text_view.insert(tk.END, "\n")

            if options:
                self.text_view.insert(tk.END, "    • Options: ", "card_label")
                self.text_view.insert(tk.END, f"{options}\n", "card_val")

            if desc:
                self.text_view.insert(tk.END, f"    • {desc}\n", "card_val")
        self.text_view.insert(tk.END, "\n")

    def _render_general_table(self, headers: List[str], rows: List[List[str]]):
        """Renders generic tables with aligned column widths."""
        col_widths = []
        for c_idx in range(len(headers)):
            w = len(headers[c_idx])
            for r in rows:
                if c_idx < len(r):
                    w = max(w, len(r[c_idx]))
            col_widths.append(min(max(w + 3, 12), 40))

        hdr_str = "".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
        self.text_view.insert(tk.END, f"\n  {hdr_str}\n", "table_header")
        self.text_view.insert(tk.END, f"  {'─' * len(hdr_str)}\n", "card_border")

        for r in rows:
            row_str = "".join(f"{c:<{w}}" for c, w in zip(r, col_widths))
            self.text_view.insert(tk.END, f"  {row_str}\n", "table_cell")
        self.text_view.insert(tk.END, "\n")

    def _highlight_search_in_text(self, query: str):
        self.text_view.tag_remove("search_match", "1.0", tk.END)
        if not query:
            return
        start = "1.0"
        while True:
            pos = self.text_view.search(query, start, nocase=True, stopindex=tk.END)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.text_view.tag_add("search_match", pos, end)
            start = end

    def _copy_current_chapter(self):
        ch = self.chapters[self.current_chapter_idx]
        self.clipboard_clear()
        self.clipboard_append(ch["markdown"])
        messagebox.showinfo("Copied", f"Chapter {ch['id']} ({ch['title']}) copied to clipboard!", parent=self)

    def _open_browser(self):
        try:
            manual_service.open_in_browser()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser: {e}", parent=self)

    def _reload_manual(self):
        self.chapters = manual_service.get_chapters(force=True)
        self.select_chapter(self.current_chapter_idx)
        messagebox.showinfo("Refreshed", "Manual reloaded from docs/CONFIGURATION_GUIDE.md!", parent=self)


class ManualWindow(ctk.CTk, _ManualWindowMixin):
    """High-performance standalone manual application window (launch <150ms)."""

    def __init__(self, parent=None):
        if parent is not None:
            # If a parent window was provided in an existing CTk process, delegate
            self._top = ManualToplevel(parent=parent)
            return
        super().__init__()
        self._init_manual()


class ManualToplevel(ctk.CTkToplevel, _ManualWindowMixin):
    """Toplevel manual window for opening within an existing CustomTkinter mainloop."""

    def __init__(self, parent):
        super().__init__(parent)
        self._init_manual()


def open_manual_window(parent=None):
    if parent is not None:
        win = ManualToplevel(parent=parent)
    else:
        win = ManualWindow()
    win.lift()
    win.focus_force()
    return win


if __name__ == "__main__":
    manual_service.open_in_browser()
