#!/usr/bin/env python3
"""
wacli-tui: Alien-Themed WhatsApp Terminal User Interface
An extraterrestrial, keyboard-navigable terminal client for WhatsApp powered by wacli.

Features:
- Extraterrestrial Sci-Fi / Cyberpunk Neon Alien Aesthetic
- Full keyboard navigation (Arrow keys, Enter, Tab, Esc, PgUp/PgDn, / for scan)
- Prominent sticker transmission rendering (sent & received WebP stickers)
- Real-time offline database sync & instant message reading
- Online server hyper-sync (Ctrl+S)
- Transmit messages directly with optimistic rendering
- Alien slash commands: /sticker <path>, /file <path>, /react <emoji>, /download, /help
- Frequency filter tabs: 🌌 All, 👽 Aliens (DMs), 🛸 Fleets (Groups), 🧬 Signals (Unread)
"""

import sys
import os
import sqlite3
import datetime
import subprocess
import json
from typing import Optional, List, Dict, Any, Tuple

from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import OptionList, Input, Static, RichLog, Button
from textual.widgets.option_list import Option


DB_PATH = os.path.expanduser("~/.local/state/wacli/wacli.db")


def format_ts(ts: Optional[int]) -> str:
    """Format unix epoch seconds to human readable timestamp."""
    if not ts:
        return ""
    try:
        dt = datetime.datetime.fromtimestamp(ts)
        now = datetime.datetime.now()
        if dt.date() == now.date():
            return dt.strftime("%I:%M %p")
        elif dt.date() == (now - datetime.timedelta(days=1)).date():
            return "Yesterday"
        elif (now - dt).days < 7:
            return dt.strftime("%a")
        else:
            return dt.strftime("%d/%m/%y")
    except Exception:
        return ""


def format_time_only(ts: Optional[int]) -> str:
    if not ts:
        return ""
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%I:%M %p")
    except Exception:
        return ""


def format_date_header(ts: Optional[int]) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.datetime.fromtimestamp(ts)
        now = datetime.datetime.now()
        if dt.date() == now.date():
            return "STARDATE // TODAY"
        elif dt.date() == (now - datetime.timedelta(days=1)).date():
            return "STARDATE // YESTERDAY"
        else:
            return f"STARDATE // {dt.strftime('%d %b %Y').upper()}"
    except Exception:
        return ""


def get_db():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=5.0)
    conn.execute("PRAGMA query_only = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


class WhatsAppAlienTUI(App):
    CSS = """
    Screen {
        background: #030706;
        color: #d1fae5;
    }

    #app_header {
        height: 1;
        background: #071a12;
        color: #00ff88;
        dock: top;
        padding: 0 1;
        text-style: bold;
    }

    #main_layout {
        height: 1fr;
        width: 100%;
    }

    #sidebar {
        width: 44;
        min-width: 38;
        max-width: 52;
        height: 100%;
        background: #050f0b;
        border-right: double #00ff66;
    }

    #search_container {
        height: 3;
        padding: 0 1;
        background: #050f0b;
    }

    #search_input {
        background: #091f16;
        border: none;
        color: #00ff88;
        height: 1;
        padding: 0 1;
    }

    #search_input:focus {
        border: tall #00ff66;
    }

    #filter_container {
        height: 3;
        padding: 0 1;
        background: #050f0b;
        align: center middle;
    }

    .filter_btn {
        margin: 0 1;
        min-width: 7;
        height: 1;
        background: #0b241a;
        color: #4ade80;
        border: none;
    }

    .filter_btn:hover {
        background: #00ff66;
        color: #030706;
        text-style: bold;
    }

    .filter_btn.-active {
        background: #00ff66;
        color: #030706;
        text-style: bold;
    }

    #chat_list {
        height: 1fr;
        background: #050f0b;
        border: none;
        padding: 0;
    }

    #chat_list:focus {
        border: none;
    }

    #chat_panel {
        height: 100%;
        width: 1fr;
        background: #030706;
    }

    #chat_header {
        height: 3;
        background: #071a12;
        border-bottom: solid #00ff66;
        padding: 0 1;
        color: #00f5d4;
    }

    #messages_view {
        height: 1fr;
        background: #030706;
        border: none;
        padding: 1 2;
    }

    #messages_view:focus {
        border: round #a855f7;
    }

    #input_area {
        height: auto;
        min-height: 4;
        background: #071a12;
        border-top: double #00ff66;
        padding: 0 1;
    }

    #msg_input {
        background: #0a261a;
        border: none;
        color: #00ff88;
        margin: 1 0 0 0;
    }

    #msg_input:focus {
        border: tall #00ff66;
    }

    #input_hints {
        height: 1;
        color: #5e8a75;
        padding: 0 1;
    }

    #status_bar {
        height: 1;
        background: #050f0b;
        color: #39ff14;
        padding: 0 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Abort", priority=True),
        Binding("ctrl+r", "refresh_all", "Scan", priority=True),
        Binding("f5", "refresh_all", "Scan", priority=True),
        Binding("ctrl+s", "trigger_sync", "Hyper-Sync", priority=True),
        Binding("slash", "focus_search", "Scan (/)", priority=False),
        Binding("escape", "handle_escape", "Disengage", priority=True),
        Binding("tab", "cycle_focus", "Next Sector", priority=True),
        Binding("shift+tab", "cycle_focus_reverse", "Prev Sector", priority=True),
        Binding("pageup", "scroll_messages_up", "Scroll Up", priority=True),
        Binding("pagedown", "scroll_messages_down", "Scroll Down", priority=True),
        Binding("f1", "set_filter_all", "All", priority=False),
        Binding("f2", "set_filter_dm", "Aliens", priority=False),
        Binding("f3", "set_filter_group", "Fleets", priority=False),
        Binding("f4", "set_filter_unread", "Signals", priority=False),
    ]

    def __init__(self):
        super().__init__()
        self.current_chat_jid: Optional[str] = None
        self.current_chat_name: str = ""
        self.current_filter: str = "all"
        self.search_query: str = ""
        self.chats_data: List[Dict[str, Any]] = []
        self.last_db_revision: int = 0
        self.is_syncing: bool = False
        self.last_incoming_msg_id: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Static(" 🛸 XENO-CLI // ALIEN COMM-LINK v2.5 👽 ── [Ctrl+S: Hyper-Sync] [F5: Re-scan] [Tab: Move] [/ : Scan Freq] [Ctrl+Q: Eject]", id="app_header", markup=False)
        with Horizontal(id="main_layout"):
            with Vertical(id="sidebar"):
                with Container(id="search_container"):
                    yield Input(placeholder="📡 Scan alien frequencies... (Press /)", id="search_input")
                with Horizontal(id="filter_container"):
                    yield Button("🌌 All (F1)", id="btn_all", classes="filter_btn -active")
                    yield Button("👽 Aliens (F2)", id="btn_dm", classes="filter_btn")
                    yield Button("🛸 Fleets (F3)", id="btn_group", classes="filter_btn")
                    yield Button("🧬 Signals (F4)", id="btn_unread", classes="filter_btn")
                yield OptionList(id="chat_list")

            with Vertical(id="chat_panel"):
                yield Static(" [!] Select a lifeform or fleet from the sensor grid to establish comms", id="chat_header")
                yield RichLog(id="messages_view", highlight=False, markup=True, wrap=True, auto_scroll=True)
                with Vertical(id="input_area"):
                    yield Input(placeholder="Lock on to an alien frequency to transmit...", id="msg_input", disabled=True)
                    yield Static(" [Enter ↵] Transmit  |  [Esc] Release  |  [PgUp/PgDn] Log Scroll  |  /help for Xeno protocols", id="input_hints", markup=False)

        yield Static(" 🟢 XENO-LINK // FREQUENCY: 1420.405 MHz // WARP DRIVE STANDBY", id="status_bar", markup=False)

    def on_mount(self) -> None:
        self.set_interval(1.5, self.check_live_updates)
        self.load_chats()
        chat_list = self.query_one("#chat_list", OptionList)
        chat_list.focus()

    def get_db_revision(self) -> int:
        try:
            conn = get_db()
            if not conn:
                return 0
            cur = conn.cursor()
            cur.execute("SELECT revision FROM retrieval_state WHERE id = 1")
            row = cur.fetchone()
            conn.close()
            return row[0] if row else 0
        except Exception:
            return 0

    def check_live_updates(self) -> None:
        rev = self.get_db_revision()
        if self.last_db_revision == 0:
            self.last_db_revision = rev
            return
        if rev != self.last_db_revision:
            self.last_db_revision = rev
            self.load_chats(preserve_selection=True)
            if self.current_chat_jid:
                self.load_messages(self.current_chat_jid, self.current_chat_name, force_reload=True)

    def load_chats(self, preserve_selection: bool = False) -> None:
        conn = get_db()
        if not conn:
            self.update_status("⚠️ Transceiver offline. Run 'wacli auth' to establish link.")
            return

        try:
            cur = conn.cursor()
            filter_sql = ""
            if self.current_filter == "dm":
                filter_sql = "AND c.kind = 'dm'"
            elif self.current_filter == "group":
                filter_sql = "AND c.kind = 'group'"
            elif self.current_filter == "unread":
                filter_sql = "AND (c.unread_count > 0 OR c.unread = 1)"

            search_sql = ""
            params = []
            if self.search_query.strip():
                search_sql = """
                AND (
                    c.name LIKE ? 
                    OR co.full_name LIKE ? 
                    OR co.push_name LIKE ? 
                    OR co.phone LIKE ? 
                    OR c.jid LIKE ?
                )
                """
                pattern = f"%{self.search_query.strip()}%"
                params = [pattern, pattern, pattern, pattern, pattern]

            query = f"""
            SELECT 
                c.jid,
                c.kind,
                COALESCE(NULLIF(c.name, ''), NULLIF(co.full_name, ''), NULLIF(co.push_name, ''), NULLIF(co.phone, ''), c.jid) AS display_name,
                c.unread_count,
                c.last_message_ts,
                (SELECT COALESCE(NULLIF(m.text, ''), m.display_text, '') 
                 FROM messages m 
                 WHERE m.chat_jid = c.jid 
                 ORDER BY m.ts DESC LIMIT 1) AS last_snippet,
                (SELECT m.ts 
                 FROM messages m 
                 WHERE m.chat_jid = c.jid 
                 ORDER BY m.ts DESC LIMIT 1) AS latest_msg_ts,
                (SELECT m.media_type 
                 FROM messages m 
                 WHERE m.chat_jid = c.jid 
                 ORDER BY m.ts DESC LIMIT 1) AS last_media
            FROM chats c
            LEFT JOIN contacts co ON c.jid = co.jid
            WHERE c.kind IN ('dm', 'group', 'newsletter')
            {filter_sql}
            {search_sql}
            ORDER BY COALESCE(latest_msg_ts, c.last_message_ts, 0) DESC
            LIMIT 150;
            """

            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()

            chat_list = self.query_one("#chat_list", OptionList)
            current_highlighted_jid = None
            if preserve_selection and chat_list.highlighted is not None and chat_list.option_count > 0:
                try:
                    current_highlighted_jid = chat_list.get_option_at_index(chat_list.highlighted).id
                except Exception:
                    pass

            self.chats_data = []
            options = []
            selected_idx = 0

            for idx, (jid, kind, name, unread, lts, snippet, mts, media_type) in enumerate(rows):
                name_clean = (name or jid).strip()
                if name_clean.endswith("@s.whatsapp.net"):
                    name_clean = "+" + name_clean.split("@")[0]

                ts_val = mts or lts
                time_str = format_ts(ts_val)
                icon = "🛸 " if kind == "group" else ("🌌 " if kind == "newsletter" else "👽 ")

                t = Text()
                t.append(icon, style="bold #00f5d4")
                t.append(name_clean[:22].ljust(22), style="bold #00ff88")
                if unread and unread > 0:
                    t.append(f" 🧬{unread} ", style="bold #39ff14 on #082414")
                else:
                    t.append("     ")
                t.append(f" {time_str:>8}\n", style="dim #5e8a75")

                # Format snippet with alien flair
                snip_clean = (snippet or "").replace("\n", " ").strip()
                if media_type == "sticker" or "sticker" in snip_clean.lower():
                    snip_clean = "👾 [Sticker Payload]"
                elif media_type == "image":
                    snip_clean = "📷 [Hologram Image]"
                elif media_type == "audio":
                    snip_clean = "🎙️ [Sonic Intercept]"
                elif media_type == "video":
                    snip_clean = "🎥 [Visual Feed]"
                elif media_type == "document":
                    snip_clean = "📄 [Data Archive]"
                elif not snip_clean:
                    snip_clean = "(quarantine empty)"

                t.append(f"  {snip_clean[:32]}", style="dim #4ade80")

                options.append(Option(t, id=jid))
                self.chats_data.append({
                    "jid": jid,
                    "kind": kind,
                    "name": name_clean,
                    "unread": unread
                })

                if current_highlighted_jid and jid == current_highlighted_jid:
                    selected_idx = idx

            chat_list.clear_options()
            if options:
                chat_list.add_options(options)
                chat_list.highlighted = selected_idx
                if not self.current_chat_jid and self.chats_data:
                    first_chat = self.chats_data[0]
                    self.load_messages(first_chat["jid"], first_chat["name"])
            else:
                self.update_status("⚠️ No alien frequencies match your sensor query.")

        except Exception as e:
            self.update_status(f"Sensor error: {e}")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_input":
            self.search_query = event.value
            self.load_chats(preserve_selection=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        filter_map = {
            "btn_all": "all",
            "btn_dm": "dm",
            "btn_group": "group",
            "btn_unread": "unread"
        }
        if btn_id in filter_map:
            self.apply_filter(filter_map[btn_id])

    def apply_filter(self, filter_name: str) -> None:
        self.current_filter = filter_name
        buttons = ["btn_all", "btn_dm", "btn_group", "btn_unread"]
        filter_map = {"all": "btn_all", "dm": "btn_dm", "group": "btn_group", "unread": "btn_unread"}
        active_btn = filter_map.get(filter_name, "btn_all")

        for b_id in buttons:
            btn = self.query_one(f"#{b_id}", Button)
            if b_id == active_btn:
                btn.add_class("-active")
            else:
                btn.remove_class("-active")
        self.load_chats()

    def action_set_filter_all(self) -> None:
        self.apply_filter("all")

    def action_set_filter_dm(self) -> None:
        self.apply_filter("dm")

    def action_set_filter_group(self) -> None:
        self.apply_filter("group")

    def action_set_filter_unread(self) -> None:
        self.apply_filter("unread")

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if not event.option:
            return
        chat_jid = str(event.option.id)
        chat_name = chat_jid
        for c in self.chats_data:
            if c["jid"] == chat_jid:
                chat_name = c["name"]
                break
        self.load_messages(chat_jid, chat_name)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        # User pressed Enter on chat -> lock on and focus transmitter
        msg_input = self.query_one("#msg_input", Input)
        msg_input.focus()

    def load_messages(self, chat_jid: str, chat_name: str, force_reload: bool = False) -> None:
        if not force_reload and self.current_chat_jid == chat_jid:
            return

        self.current_chat_jid = chat_jid
        self.current_chat_name = chat_name

        header = self.query_one("#chat_header", Static)
        header_text = Text()
        header_text.append(" 🛸 COMMS LOCKED: ", style="dim #39ff14")
        header_text.append(f"{chat_name} ", style="bold #00ff88")
        header_text.append(f"// CHANNEL: {chat_jid}", style="dim #00f5d4")
        header.update(header_text)

        msg_input = self.query_one("#msg_input", Input)
        msg_input.disabled = False
        msg_input.placeholder = f"🛸 Transmit to {chat_name}... (Enter to broadcast, Esc to disengage)"

        conn = get_db()
        if not conn:
            return

        try:
            cur = conn.cursor()
            query = """
            SELECT * FROM (
                SELECT 
                    m.rowid, m.msg_id, 
                    COALESCE(NULLIF(m.sender_name, ''), NULLIF(co.full_name, ''), NULLIF(co.push_name, ''), NULLIF(co.phone, ''), m.sender_jid, 'Alien Lifeform') AS sender_display,
                    m.from_me, m.ts, 
                    COALESCE(NULLIF(m.text, ''), m.display_text, '') AS body,
                    m.media_type, m.media_caption, m.reaction_emoji, m.quoted_msg_id,
                    m.local_path
                FROM messages m
                LEFT JOIN contacts co ON m.sender_jid = co.jid
                WHERE m.chat_jid = ?
                ORDER BY m.ts DESC, m.rowid DESC
                LIMIT 100
            ) sub ORDER BY ts ASC, rowid ASC;
            """
            cur.execute(query, (chat_jid,))
            rows = cur.fetchall()
            conn.close()

            log = self.query_one("#messages_view", RichLog)
            log.clear()

            if not rows:
                empty_text = Text("\n  🌌 No orbital transmissions recorded in this sector. Initiate first broadcast below!\n", style="dim italic #4ade80")
                log.write(empty_text)
                return

            last_date_str = ""
            for row in rows:
                rowid, msg_id, sender_name, from_me, ts, body, media_type, caption, reaction, quote, local_path = row
                if not from_me:
                    self.last_incoming_msg_id = msg_id

                date_str = format_date_header(ts)
                if date_str != last_date_str:
                    last_date_str = date_str
                    div = Text()
                    div.append(f"\n───────────── 🛸 {date_str} // SECTOR 4 ─────────────\n", style="bold #5e8a75")
                    log.write(div)

                time_str = format_time_only(ts)
                t = Text()

                # Check if this is a sticker transmission
                is_sticker = (media_type == "sticker") or (body and "Sent sticker" in body)

                if from_me:
                    t.append(f"[{time_str}] ", style="dim #00ff88")
                    t.append("🛸 YOU (COMMANDER)", style="bold #39ff14")
                    t.append("\n")

                    if is_sticker:
                        # RENDER PROMINENT ALIEN STICKER PAYLOAD
                        t.append("   ╭──────────────────────────────╮\n", style="#a855f7")
                        t.append("   │        👾  ( ⊙ _ ⊙ )  🛸      │\n", style="bold #00ff88")
                        t.append("   │    [ STICKER TRANSMISSION ]  │\n", style="bold #39ff14")
                        if local_path:
                            t.append(f"   │  📁 {os.path.basename(local_path)[:22]:<22}  │\n", style="dim #00f5d4")
                        t.append("   ╰──────────────────────────────╯", style="#a855f7")
                        t.append(" 🧬✓✓\n", style="bold #00f5d4")
                    else:
                        if media_type:
                            m_icon = "📷" if media_type == "image" else ("📄" if media_type == "document" else "🎙️")
                            t.append(f"  [{m_icon} PAYLOAD: {media_type.upper()}] ", style="italic #00ff88")

                        msg_content = body or caption or ""
                        t.append("  ")
                        t.append(f"  {msg_content}  ", style="on #00381e bold #00ff88")
                        t.append(" 🧬✓✓\n", style="bold #00f5d4")

                else:
                    t.append(f"[{time_str}] ", style="dim #00f5d4")
                    s_clean = sender_name or "Alien Lifeform"
                    if s_clean.endswith("@s.whatsapp.net"):
                        s_clean = "+" + s_clean.split("@")[0]
                    t.append(f"👽 {s_clean}", style="bold #00f5d4")
                    t.append("\n")

                    if is_sticker:
                        # RENDER PROMINENT ALIEN STICKER PAYLOAD
                        t.append("   ╭──────────────────────────────╮\n", style="#a855f7")
                        t.append("   │        👾  ( ⊙ _ ⊙ )  🛸      │\n", style="bold #00f5d4")
                        t.append("   │    [ INCOMING STICKER ]      │\n", style="bold #00ff88")
                        if local_path:
                            t.append(f"   │  📁 {os.path.basename(local_path)[:22]:<22}  │\n", style="dim #00f5d4")
                        t.append("   ╰──────────────────────────────╯\n", style="#a855f7")
                    else:
                        if media_type:
                            m_icon = "📷" if media_type == "image" else ("📄" if media_type == "document" else "🎙️")
                            t.append(f"  [{m_icon} PAYLOAD: {media_type.upper()}] ", style="italic #00f5d4")

                        msg_content = body or caption or ""
                        t.append("  ")
                        t.append(f"  {msg_content}  ", style="on #08261e #d1fae5")
                        t.append("\n")

                if reaction:
                    t.append(f"     🧬 Orbital Reaction: {reaction}\n", style="dim #39ff14")

                log.write(t)

        except Exception as e:
            self.update_status(f"Transceiver reading error: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "msg_input":
            raw_text = event.value.strip()
            if not raw_text:
                return
            if not self.current_chat_jid:
                self.update_status("⚠️ Lock on to a target lifeform first!")
                return

            event.input.value = ""

            # Check slash commands
            if raw_text == "/help":
                log = self.query_one("#messages_view", RichLog)
                help_text = Text()
                help_text.append("\n── 🛸 XENO-CLI COMM PROTOCOLS ──\n", style="bold #00ff88")
                help_text.append(" • Standard text      : Type message and press Enter to broadcast.\n", style="white")
                help_text.append(" • /sticker <file>    : Transmit a WebP sticker to target lifeform\n", style="bold #a855f7")
                help_text.append(" • /file <path>       : Beam an image, video, audio, or document archive\n", style="#00f5d4")
                help_text.append(" • /react <emoji>     : Transmit orbital reaction to last signal\n", style="#00f5d4")
                help_text.append(" • /download          : Download incoming media payload from last signal\n", style="#39ff14")
                help_text.append(" • Ctrl+S             : Engage hyper-sync with WhatsApp servers\n", style="#39ff14")
                help_text.append(" • Ctrl+R / F5        : Re-scan local sensor database\n", style="#39ff14")
                help_text.append(" • Esc                : Disengage transmitter / return to sensor grid\n", style="yellow")
                help_text.append(" • PageUp / PgDn      : Scroll orbital transmission log\n", style="yellow")
                help_text.append("────────────────────────────────\n", style="dim #5e8a75")
                log.write(help_text)
                return

            if raw_text.startswith("/sticker "):
                sticker_path = os.path.expanduser(raw_text[9:].strip())
                if not os.path.exists(sticker_path):
                    self.update_status(f"❌ WebP sticker payload not found: {sticker_path}")
                    return
                self.update_status(f"Transmitting WebP sticker {os.path.basename(sticker_path)}...")
                self.send_sticker_async(self.current_chat_jid, self.current_chat_name, sticker_path)
                return

            if raw_text.startswith("/file "):
                file_path = os.path.expanduser(raw_text[6:].strip())
                if not os.path.exists(file_path):
                    self.update_status(f"❌ Archive not found: {file_path}")
                    return
                self.update_status(f"Beaming archive {os.path.basename(file_path)}...")
                self.send_file_async(self.current_chat_jid, self.current_chat_name, file_path)
                return

            if raw_text.startswith("/react "):
                emoji = raw_text[7:].strip()
                if not self.last_incoming_msg_id:
                    self.update_status("❌ No previous alien signal detected to react to.")
                    return
                self.update_status(f"Transmitting reaction {emoji}...")
                self.send_reaction_async(self.current_chat_jid, self.last_incoming_msg_id, emoji)
                return

            if raw_text == "/download":
                if not self.last_incoming_msg_id:
                    self.update_status("❌ No previous media payload detected.")
                    return
                self.update_status("Downloading media payload from target lifeform...")
                self.download_media_async(self.current_chat_jid, self.last_incoming_msg_id)
                return

            # Regular broadcast:
            log = self.query_one("#messages_view", RichLog)
            time_now = datetime.datetime.now().strftime("%I:%M %p")
            opt_text = Text()
            opt_text.append(f"[{time_now}] ", style="dim #00ff88")
            opt_text.append("🛸 YOU (COMMANDER)", style="bold #39ff14")
            opt_text.append("\n  ")
            opt_text.append(f"  {raw_text}  ", style="on #00381e bold #00ff88")
            opt_text.append("  🧬 Broadcasting...\n", style="dim #39ff14")
            log.write(opt_text)

            self.update_status(f"Broadcasting to {self.current_chat_name}...")
            self.send_message_async(self.current_chat_jid, self.current_chat_name, raw_text)

        elif event.input.id == "search_input":
            chat_list = self.query_one("#chat_list", OptionList)
            chat_list.focus()

    @work(thread=True)
    def send_message_async(self, chat_jid: str, chat_name: str, message_text: str) -> None:
        try:
            cmd = [
                "wacli", "send", "text", "--json",
                "--lock-wait", "12s",
                "--to", chat_jid,
                "--message", message_text
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = False
            error_msg = None

            if proc.returncode == 0:
                try:
                    data = json.loads(proc.stdout)
                    success = data.get("success", False)
                    error_msg = data.get("error")
                except Exception:
                    success = True
            else:
                error_msg = proc.stderr or proc.stdout

            def on_complete():
                if success:
                    self.update_status(f"🟢 Signal confirmed by {chat_name}!")
                    self.check_live_updates()
                else:
                    self.update_status(f"❌ Transmission failed: {error_msg}")

            self.call_from_thread(on_complete)

        except subprocess.TimeoutExpired:
            self.call_from_thread(lambda: self.update_status("❌ Hyper-relay timed out (30s)."))
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"❌ Transmission error: {e}"))

    @work(thread=True)
    def send_sticker_async(self, chat_jid: str, chat_name: str, sticker_path: str) -> None:
        try:
            cmd = [
                "wacli", "send", "sticker", "--json",
                "--lock-wait", "15s",
                "--to", chat_jid,
                "--file", sticker_path
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = False
            error_msg = None
            if proc.returncode == 0:
                try:
                    data = json.loads(proc.stdout)
                    success = data.get("success", False)
                    error_msg = data.get("error")
                except Exception:
                    success = True
            else:
                error_msg = proc.stderr or proc.stdout

            def on_complete():
                if success:
                    self.update_status(f"👾 Sticker payload delivered to {chat_name}!")
                    self.check_live_updates()
                else:
                    self.update_status(f"❌ Sticker transmission failed: {error_msg}")

            self.call_from_thread(on_complete)
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"❌ Sticker error: {e}"))

    @work(thread=True)
    def send_file_async(self, chat_jid: str, chat_name: str, file_path: str) -> None:
        try:
            cmd = [
                "wacli", "send", "file", "--json",
                "--lock-wait", "15s",
                "--to", chat_jid,
                "--file", file_path
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            success = False
            error_msg = None
            if proc.returncode == 0:
                try:
                    data = json.loads(proc.stdout)
                    success = data.get("success", False)
                    error_msg = data.get("error")
                except Exception:
                    success = True
            else:
                error_msg = proc.stderr or proc.stdout

            def on_complete():
                if success:
                    self.update_status(f"✓ Archive beamed to {chat_name}!")
                    self.check_live_updates()
                else:
                    self.update_status(f"❌ Beam failed: {error_msg}")

            self.call_from_thread(on_complete)
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"❌ Archive beam error: {e}"))

    @work(thread=True)
    def send_reaction_async(self, chat_jid: str, msg_id: str, emoji: str) -> None:
        try:
            cmd = [
                "wacli", "send", "react", "--json",
                "--lock-wait", "10s",
                "--to", chat_jid,
                "--id", msg_id,
                "--reaction", emoji
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            def on_complete():
                if proc.returncode == 0:
                    self.update_status(f"🧬 Reaction {emoji} acknowledged!")
                    self.check_live_updates()
                else:
                    self.update_status("❌ Reaction transmission failed.")

            self.call_from_thread(on_complete)
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"❌ Reaction error: {e}"))

    @work(thread=True)
    def download_media_async(self, chat_jid: str, msg_id: str) -> None:
        try:
            cmd = [
                "wacli", "media", "download",
                "--lock-wait", "15s",
                "--chat", chat_jid,
                "--id", msg_id
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            def on_complete():
                if proc.returncode == 0:
                    self.update_status("✓ Media payload downloaded to local store!")
                    self.check_live_updates()
                else:
                    self.update_status(f"❌ Download failed: {proc.stderr or proc.stdout}")
            self.call_from_thread(on_complete)
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"❌ Download error: {e}"))

    @work(thread=True)
    def run_sync_online(self) -> None:
        if self.is_syncing:
            return
        self.is_syncing = True
        self.call_from_thread(lambda: self.update_status("🔄 Engaging Hyper-Sync with orbital relays..."))

        try:
            cmd = ["wacli", "sync", "--once", "--idle-exit", "2s"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            def on_finish():
                self.is_syncing = False
                self.update_status("🟢 Hyper-Sync complete! Sensor grid refreshed.")
                self.load_chats(preserve_selection=True)
                if self.current_chat_jid:
                    self.load_messages(self.current_chat_jid, self.current_chat_name, force_reload=True)

            self.call_from_thread(on_finish)
        except Exception as e:
            def on_err():
                self.is_syncing = False
                self.update_status(f"⚠️ Hyper-Sync aborted: {e}")
            self.call_from_thread(on_err)

    def action_trigger_sync(self) -> None:
        self.run_sync_online()

    def action_refresh_all(self) -> None:
        self.update_status("Re-scanning local sensor telemetry...")
        self.load_chats(preserve_selection=True)
        if self.current_chat_jid:
            self.load_messages(self.current_chat_jid, self.current_chat_name, force_reload=True)

    def action_focus_search(self) -> None:
        search_input = self.query_one("#search_input", Input)
        search_input.focus()

    def action_handle_escape(self) -> None:
        search_input = self.query_one("#search_input", Input)
        msg_input = self.query_one("#msg_input", Input)
        chat_list = self.query_one("#chat_list", OptionList)

        if search_input.has_focus:
            if search_input.value:
                search_input.value = ""
            chat_list.focus()
        elif msg_input.has_focus:
            chat_list.focus()
        else:
            chat_list.focus()

    def action_cycle_focus(self) -> None:
        search_input = self.query_one("#search_input", Input)
        chat_list = self.query_one("#chat_list", OptionList)
        messages_view = self.query_one("#messages_view", RichLog)
        msg_input = self.query_one("#msg_input", Input)

        if search_input.has_focus:
            chat_list.focus()
        elif chat_list.has_focus:
            messages_view.focus()
        elif messages_view.has_focus:
            msg_input.focus()
        else:
            search_input.focus()

    def action_cycle_focus_reverse(self) -> None:
        search_input = self.query_one("#search_input", Input)
        chat_list = self.query_one("#chat_list", OptionList)
        messages_view = self.query_one("#messages_view", RichLog)
        msg_input = self.query_one("#msg_input", Input)

        if msg_input.has_focus:
            messages_view.focus()
        elif messages_view.has_focus:
            chat_list.focus()
        elif chat_list.has_focus:
            search_input.focus()
        else:
            msg_input.focus()

    def action_scroll_messages_up(self) -> None:
        log = self.query_one("#messages_view", RichLog)
        log.scroll_page_up()

    def action_scroll_messages_down(self) -> None:
        log = self.query_one("#messages_view", RichLog)
        log.scroll_page_down()

    def update_status(self, text: str) -> None:
        status_bar = self.query_one("#status_bar", Static)
        status_bar.update(f" {text}")


def main():
    app = WhatsAppAlienTUI()
    app.run()


if __name__ == "__main__":
    main()
