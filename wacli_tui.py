#!/usr/bin/env python3
"""
wacli-tui: Alien Weyland-Yutani Sci-Fi WhatsApp Terminal User Interface
An eye-friendly extraterrestrial terminal client with multimedia support for WhatsApp powered by wacli.

Features:
- Eye-Friendly Sci-Fi / Weyland-Yutani HUD Aesthetic (soft phosphor emerald #10b981, deep matte charcoal #0d1416)
- 100% Font-Safe Universal Glyphs (zero broken tofu '▯' boxes)
- Multimedia Support:
  * Stickers & Images: In-terminal ANSI pixel art previews (via Pillow)
  * Instant Viewer ('v' / 'o' / /view): Opens stickers & images in imv / xdg-open
  * Video & Audio: Play videos and voice notes in ffplay / xdg-open ('p' / /play)
  * Auto-download media payloads on demand
- Full Keyboard Navigation (Arrow keys, Enter, Esc, Tab, PgUp/PgDn, / for search)
- Filter Tabs: ALL (F1), DMS (F2), FLEET (F3), NEW (F4)
- Live SQLite database monitoring & online hyper-sync (Ctrl+S)
- Slash commands: /view, /play, /download, /sticker, /file, /react, /help
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

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


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


def render_ansi_thumbnail(filepath: str, max_w: int = 18, max_h: int = 8) -> Optional[Text]:
    """Render a compact true-color half-block ANSI thumbnail using Pillow."""
    if not HAS_PILLOW or not os.path.exists(filepath):
        return None
    try:
        img = Image.open(filepath).convert("RGBA")
        img.thumbnail((max_w, max_h))
        w, h = img.size
        t = Text()
        for y in range(0, h, 2):
            t.append("    ")
            for x in range(w):
                r1, g1, b1, a1 = img.getpixel((x, y))
                if y + 1 < h:
                    r2, g2, b2, a2 = img.getpixel((x, y + 1))
                else:
                    r2, g2, b2, a2 = 0, 0, 0, 0

                if a1 < 30 and a2 < 30:
                    t.append(" ")
                elif a1 < 30:
                    t.append("▄", style=f"#{r2:02x}{g2:02x}{b2:02x}")
                elif a2 < 30:
                    t.append("▀", style=f"#{r1:02x}{g1:02x}{b1:02x}")
                else:
                    t.append("▀", style=f"#{r1:02x}{g1:02x}{b1:02x} on #{r2:02x}{g2:02x}{b2:02x}")
            t.append("\n")
        return t
    except Exception:
        return None


class WhatsAppAlienTUI(App):
    CSS = """
    Screen {
        background: #0d1416;
        color: #e2e8f0;
    }

    #app_header {
        height: 1;
        background: #111d21;
        color: #10b981;
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
        max-width: 50;
        height: 100%;
        background: #10191c;
        border-right: solid #1e3137;
    }

    #search_container {
        height: 3;
        padding: 0 1;
        background: #10191c;
    }

    #search_input {
        background: #142226;
        border: none;
        color: #34d399;
        height: 1;
        padding: 0 1;
    }

    #search_input:focus {
        border: tall #10b981;
    }

    #filter_container {
        height: 3;
        padding: 0 1;
        background: #10191c;
        align: center middle;
    }

    .filter_btn {
        margin: 0 1;
        min-width: 7;
        max-width: 9;
        height: 1;
        padding: 0;
        background: #162429;
        color: #64748b;
        border: none;
    }

    .filter_btn:hover {
        background: #1e3a34;
        color: #34d399;
    }

    .filter_btn.-active {
        background: #064e3b;
        color: #34d399;
        text-style: bold;
    }

    #chat_list {
        height: 1fr;
        background: #10191c;
        border: none;
        padding: 0;
        scrollbar-size-horizontal: 0;
        scrollbar-gutter: stable;
        scrollbar-color: #1e3137 #10191c;
        scrollbar-color-hover: #10b981 #10191c;
    }

    #chat_list:focus {
        border: none;
    }

    #chat_panel {
        height: 100%;
        width: 1fr;
        background: #0b1013;
    }

    #chat_header {
        height: 3;
        background: #111d21;
        border-bottom: solid #1e3137;
        padding: 0 1;
        color: #38bdf8;
    }

    #messages_view {
        height: 1fr;
        background: #0b1013;
        border: none;
        padding: 1 2;
        scrollbar-size-horizontal: 0;
        scrollbar-gutter: stable;
        scrollbar-color: #1e3137 #0b1013;
        scrollbar-color-hover: #10b981 #0b1013;
    }

    #messages_view:focus {
        border: round #10b981;
    }

    #input_area {
        height: auto;
        min-height: 4;
        background: #111d21;
        border-top: solid #1e3137;
        padding: 0 1;
    }

    #msg_input {
        background: #162429;
        border: none;
        color: #34d399;
        margin: 1 0 0 0;
    }

    #msg_input:focus {
        border: tall #10b981;
    }

    #input_hints {
        height: 1;
        color: #64748b;
        padding: 0 1;
    }

    #status_bar {
        height: 1;
        background: #10191c;
        color: #34d399;
        padding: 0 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Exit", priority=True),
        Binding("ctrl+r", "refresh_all", "Refresh", priority=True),
        Binding("f5", "refresh_all", "Refresh", priority=True),
        Binding("ctrl+s", "trigger_sync", "Hyper-Sync", priority=True),
        Binding("slash", "focus_search", "Search (/)", priority=False),
        Binding("escape", "handle_escape", "Back", priority=True),
        Binding("tab", "cycle_focus", "Next", priority=True),
        Binding("shift+tab", "cycle_focus_reverse", "Prev", priority=True),
        Binding("pageup", "scroll_messages_up", "Page Up", priority=True),
        Binding("pagedown", "scroll_messages_down", "Page Down", priority=True),
        Binding("v", "open_latest_media", "View Media", priority=False),
        Binding("o", "open_latest_media", "Open Media", priority=False),
        Binding("p", "play_latest_audio", "Play Audio", priority=False),
        Binding("f1", "set_filter_all", "All", priority=False),
        Binding("f2", "set_filter_dm", "DMs", priority=False),
        Binding("f3", "set_filter_group", "Fleet", priority=False),
        Binding("f4", "set_filter_unread", "New", priority=False),
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
        self.last_media_item: Optional[Dict[str, Any]] = None

    def compose(self) -> ComposeResult:
        yield Static(" // WEYLAND-YUTANI // XENO-NET v3.0  ──  [Ctrl+S: Sync] [F5: Refresh] [Tab: Move] [/ : Search] [v: View Media] [Ctrl+Q: Exit]", id="app_header", markup=False)
        with Horizontal(id="main_layout"):
            with Vertical(id="sidebar"):
                with Container(id="search_container"):
                    yield Input(placeholder="Search channels & signals... (Press /)", id="search_input")
                with Horizontal(id="filter_container"):
                    yield Button("ALL (F1)", id="btn_all", classes="filter_btn -active")
                    yield Button("DMS (F2)", id="btn_dm", classes="filter_btn")
                    yield Button("FLEET (F3)", id="btn_group", classes="filter_btn")
                    yield Button("NEW (F4)", id="btn_unread", classes="filter_btn")
                yield OptionList(id="chat_list")

            with Vertical(id="chat_panel"):
                yield Static(" Select a lifeform or channel from the grid to establish comms", id="chat_header")
                yield RichLog(id="messages_view", highlight=False, markup=True, wrap=True, auto_scroll=True)
                with Vertical(id="input_area"):
                    yield Input(placeholder="Lock onto a frequency to transmit...", id="msg_input", disabled=True)
                    yield Static(" [Enter] Transmit  |  [Esc] Back  |  [v] View Sticker/Image/Video  |  /help for protocols", id="input_hints", markup=False)

        yield Static(" ● ONLINE // 1420.405 MHz // WACLI STORE: OK", id="status_bar", markup=False)

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
            self.update_status("Transceiver offline. Run 'wacli auth' to establish link.")
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
                icon = "▲ " if kind == "group" else ("★ " if kind == "newsletter" else "● ")

                t = Text()
                t.append(icon, style="bold #38bdf8")
                t.append(name_clean[:22].ljust(22), style="bold #f1f5f9")
                if unread and unread > 0:
                    t.append(f" [{unread}] ", style="bold #34d399 on #064e3b")
                else:
                    t.append("     ")
                t.append(f" {time_str:>8}\n", style="dim #64748b")

                snip_clean = (snippet or "").replace("\n", " ").strip()
                if media_type == "sticker" or "sticker" in snip_clean.lower():
                    snip_clean = "[Sticker]"
                elif media_type == "image":
                    snip_clean = "[Image]"
                elif media_type == "audio":
                    snip_clean = "[Audio Recording]"
                elif media_type == "video":
                    snip_clean = "[Video Stream]"
                elif media_type == "document":
                    snip_clean = "[Data Archive]"
                elif not snip_clean:
                    snip_clean = "(empty)"

                t.append(f"  {snip_clean[:32]}", style="dim #94a3b8")

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
                self.update_status("No channels match your sensor query.")

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
        msg_input = self.query_one("#msg_input", Input)
        msg_input.focus()

    def load_messages(self, chat_jid: str, chat_name: str, force_reload: bool = False) -> None:
        if not force_reload and self.current_chat_jid == chat_jid:
            return

        self.current_chat_jid = chat_jid
        self.current_chat_name = chat_name
        self.last_media_item = None

        header = self.query_one("#chat_header", Static)
        header_text = Text()
        header_text.append(" [●] CHANNEL LOCKED: ", style="bold #10b981")
        header_text.append(f"{chat_name} ", style="bold #f1f5f9")
        header_text.append(f"// {chat_jid}", style="dim #64748b")
        header.update(header_text)

        msg_input = self.query_one("#msg_input", Input)
        msg_input.disabled = False
        msg_input.placeholder = f"Transmit message to {chat_name}... (Enter to broadcast, Esc to disengage)"

        conn = get_db()
        if not conn:
            return

        try:
            cur = conn.cursor()
            query = """
            SELECT * FROM (
                SELECT 
                    m.rowid, m.msg_id, 
                    COALESCE(NULLIF(m.sender_name, ''), NULLIF(co.full_name, ''), NULLIF(co.push_name, ''), NULLIF(co.phone, ''), m.sender_jid, 'Contact') AS sender_display,
                    m.from_me, m.ts, 
                    COALESCE(NULLIF(m.text, ''), m.display_text, '') AS body,
                    m.media_type, m.media_caption, m.reaction_emoji, m.quoted_msg_id,
                    m.local_path, m.filename
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
                empty_text = Text("\n  No transmissions recorded in this channel. Send the first message below!\n", style="dim italic #64748b")
                log.write(empty_text)
                return

            last_date_str = ""
            for row in rows:
                rowid, msg_id, sender_name, from_me, ts, body, media_type, caption, reaction, quote, local_path, filename = row
                if not from_me:
                    self.last_incoming_msg_id = msg_id

                if media_type:
                    self.last_media_item = {
                        "msg_id": msg_id,
                        "chat_jid": chat_jid,
                        "media_type": media_type,
                        "local_path": local_path,
                        "filename": filename
                    }

                date_str = format_date_header(ts)
                if date_str != last_date_str:
                    last_date_str = date_str
                    div = Text()
                    div.append(f"\n─── [ {date_str} ] ───\n", style="bold #475569")
                    log.write(div)

                time_str = format_time_only(ts)
                t = Text()

                is_sticker = (media_type == "sticker") or (body and "Sent sticker" in body)
                is_image = (media_type == "image")
                is_video = (media_type == "video")
                is_audio = (media_type == "audio")
                is_doc = (media_type == "document")

                if from_me:
                    t.append(f"[{time_str}] ", style="dim #64748b")
                    t.append(">>> YOU", style="bold #34d399")
                    t.append("\n")

                    if is_sticker or is_image:
                        # Try ANSI pixel art thumbnail
                        thumb = None
                        if local_path and os.path.exists(local_path):
                            thumb = render_ansi_thumbnail(local_path, max_w=20, max_h=8)
                        
                        tag = "STICKER" if is_sticker else "IMAGE"
                        t.append(f"   ┌── [ {tag} TRANSMISSION ] ────────────────┐\n", style="#059669")
                        if thumb:
                            t.append(thumb)
                        t.append(f"   │  [Press 'v' to view in imv]                │\n", style="dim #34d399")
                        t.append(f"   └────────────────────────────────────────────┘", style="#059669")
                        t.append(" ✓✓\n", style="#38bdf8")

                    elif is_video:
                        v_name = filename or "video.mp4"
                        t.append(f"   ┌── [ VIDEO STREAM: {v_name} ] ──┐\n", style="#059669")
                        t.append(f"   │  [Press 'v' to play in ffplay]             │\n", style="dim #34d399")
                        t.append(f"   └────────────────────────────────────────────┘", style="#059669")
                        t.append(" ✓✓\n", style="#38bdf8")

                    elif is_audio:
                        a_name = filename or "audio_note"
                        t.append(f"   ┌── [ AUDIO RECORDING: {a_name} ] ──┐\n", style="#059669")
                        t.append(f"   │  [Press 'p' to play audio in ffplay]       │\n", style="dim #34d399")
                        t.append(f"   └────────────────────────────────────────────┘", style="#059669")
                        t.append(" ✓✓\n", style="#38bdf8")

                    elif is_doc:
                        d_name = filename or "document"
                        t.append(f"   ┌── [ DATA ARCHIVE: {d_name} ] ──┐\n", style="#059669")
                        t.append(f"   │  [Press 'v' to open archive]               │\n", style="dim #34d399")
                        t.append(f"   └────────────────────────────────────────────┘", style="#059669")
                        t.append(" ✓✓\n", style="#38bdf8")

                    else:
                        msg_content = body or caption or ""
                        t.append("  ")
                        t.append(f"  {msg_content}  ", style="on #064e3b #d1fae5")
                        t.append(" ✓✓\n", style="#38bdf8")

                else:
                    t.append(f"[{time_str}] ", style="dim #64748b")
                    s_clean = sender_name or "Contact"
                    if s_clean.endswith("@s.whatsapp.net"):
                        s_clean = "+" + s_clean.split("@")[0]
                    t.append(f"<<< {s_clean}", style="bold #38bdf8")
                    t.append("\n")

                    if is_sticker or is_image:
                        thumb = None
                        if local_path and os.path.exists(local_path):
                            thumb = render_ansi_thumbnail(local_path, max_w=20, max_h=8)
                        
                        tag = "STICKER" if is_sticker else "IMAGE"
                        t.append(f"   ┌── [ INCOMING {tag} ] ─────────────────────┐\n", style="#1e3a47")
                        if thumb:
                            t.append(thumb)
                        elif not local_path:
                            t.append(f"   │  [Uncached: Press 'v' to download & view]  │\n", style="italic #94a3b8")
                        else:
                            t.append(f"   │  [Press 'v' to view in imv]                │\n", style="dim #38bdf8")
                        t.append(f"   └────────────────────────────────────────────┘\n", style="#1e3a47")

                    elif is_video:
                        v_name = filename or "video.mp4"
                        t.append(f"   ┌── [ INCOMING VIDEO: {v_name} ] ──┐\n", style="#1e3a47")
                        t.append(f"   │  [Press 'v' to play in ffplay]             │\n", style="dim #38bdf8")
                        t.append(f"   └────────────────────────────────────────────┘\n", style="#1e3a47")

                    elif is_audio:
                        a_name = filename or "audio_note"
                        t.append(f"   ┌── [ INCOMING AUDIO: {a_name} ] ──┐\n", style="#1e3a47")
                        t.append(f"   │  [Press 'p' to play audio in ffplay]       │\n", style="dim #38bdf8")
                        t.append(f"   └────────────────────────────────────────────┘\n", style="#1e3a47")

                    elif is_doc:
                        d_name = filename or "document"
                        t.append(f"   ┌── [ INCOMING ARCHIVE: {d_name} ] ──┐\n", style="#1e3a47")
                        t.append(f"   │  [Press 'v' to open archive]               │\n", style="dim #38bdf8")
                        t.append(f"   └────────────────────────────────────────────┘\n", style="#1e3a47")

                    else:
                        msg_content = body or caption or ""
                        t.append("  ")
                        t.append(f"  {msg_content}  ", style="on #1e293b #f1f5f9")
                        t.append("\n")

                if reaction:
                    t.append(f"     Reacted: {reaction}\n", style="dim #34d399")

                log.write(t)

        except Exception as e:
            self.update_status(f"Error reading messages: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "msg_input":
            raw_text = event.value.strip()
            if not raw_text:
                return
            if not self.current_chat_jid:
                self.update_status("Select a target channel first.")
                return

            event.input.value = ""

            if raw_text == "/help":
                log = self.query_one("#messages_view", RichLog)
                help_text = Text()
                help_text.append("\n── 💡 WEYLAND COMM PROTOCOLS ──\n", style="bold #10b981")
                help_text.append(" • Standard text      : Type message and press Enter to broadcast.\n", style="white")
                help_text.append(" • /view or /open     : Open latest sticker/image in imv, video in ffplay\n", style="#38bdf8")
                help_text.append(" • /play              : Play latest audio recording in ffplay\n", style="#38bdf8")
                help_text.append(" • /download          : Download media payload from latest signal\n", style="#34d399")
                help_text.append(" • /sticker <file>    : Send a WebP sticker\n", style="#a78bfa")
                help_text.append(" • /file <path>       : Send an image, video, audio, or document archive\n", style="#38bdf8")
                help_text.append(" • /react <emoji>     : Transmit reaction to last signal\n", style="#34d399")
                help_text.append(" • Hotkeys            : 'v' View Media, 'p' Play Audio, 'F5' Scan, 'Ctrl+S' Sync\n", style="yellow")
                help_text.append("───────────────────────────────\n", style="dim #64748b")
                log.write(help_text)
                return

            if raw_text in ("/view", "/open"):
                self.action_open_latest_media()
                return

            if raw_text == "/play":
                self.action_play_latest_audio()
                return

            if raw_text == "/download":
                if not self.last_media_item:
                    self.update_status("No media payload detected in current channel.")
                    return
                self.download_media_async(self.last_media_item["chat_jid"], self.last_media_item["msg_id"])
                return

            if raw_text.startswith("/sticker "):
                sticker_path = os.path.expanduser(raw_text[9:].strip())
                if not os.path.exists(sticker_path):
                    self.update_status(f"File not found: {sticker_path}")
                    return
                self.update_status(f"Transmitting WebP sticker {os.path.basename(sticker_path)}...")
                self.send_sticker_async(self.current_chat_jid, self.current_chat_name, sticker_path)
                return

            if raw_text.startswith("/file "):
                file_path = os.path.expanduser(raw_text[6:].strip())
                if not os.path.exists(file_path):
                    self.update_status(f"File not found: {file_path}")
                    return
                self.update_status(f"Sending file {os.path.basename(file_path)}...")
                self.send_file_async(self.current_chat_jid, self.current_chat_name, file_path)
                return

            if raw_text.startswith("/react "):
                emoji = raw_text[7:].strip()
                if not self.last_incoming_msg_id:
                    self.update_status("No signal detected to react to.")
                    return
                self.update_status(f"Transmitting reaction {emoji}...")
                self.send_reaction_async(self.current_chat_jid, self.last_incoming_msg_id, emoji)
                return

            # Regular broadcast:
            log = self.query_one("#messages_view", RichLog)
            time_now = datetime.datetime.now().strftime("%I:%M %p")
            opt_text = Text()
            opt_text.append(f"[{time_now}] ", style="dim #64748b")
            opt_text.append(">>> YOU", style="bold #34d399")
            opt_text.append("\n  ")
            opt_text.append(f"  {raw_text}  ", style="on #064e3b #d1fae5")
            opt_text.append("  Sending...\n", style="dim #34d399")
            log.write(opt_text)

            self.update_status(f"Transmitting to {self.current_chat_name}...")
            self.send_message_async(self.current_chat_jid, self.current_chat_name, raw_text)

        elif event.input.id == "search_input":
            chat_list = self.query_one("#chat_list", OptionList)
            chat_list.focus()

    def action_open_latest_media(self) -> None:
        if not self.last_media_item:
            self.update_status("No media payload in current channel.")
            return
        m = self.last_media_item
        self.open_media_worker(m["chat_jid"], m["msg_id"], m.get("local_path"), m.get("media_type"))

    def action_play_latest_audio(self) -> None:
        if not self.last_media_item:
            self.update_status("No audio payload in current channel.")
            return
        m = self.last_media_item
        self.open_media_worker(m["chat_jid"], m["msg_id"], m.get("local_path"), "audio")

    @work(thread=True)
    def open_media_worker(self, chat_jid: str, msg_id: str, local_path: Optional[str], media_type: Optional[str]) -> None:
        path = local_path
        if not path or not os.path.exists(path):
            self.call_from_thread(lambda: self.update_status("Downloading media payload..."))
            cmd = ["wacli", "media", "download", "--chat", chat_jid, "--id", msg_id]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "(" in line and ")" in line:
                        potential_path = line.split("(")[0].strip()
                        if os.path.exists(potential_path):
                            path = potential_path
                            break

        if path and os.path.exists(path):
            self.call_from_thread(lambda: self.update_status(f"Opening {os.path.basename(path)}..."))
            try:
                if media_type in ("video", "audio"):
                    subprocess.Popen(["ffplay", "-autoexit", "-loglevel", "quiet", path])
                else:
                    subprocess.Popen(["imv", path])
            except Exception:
                subprocess.Popen(["xdg-open", path])
        else:
            self.call_from_thread(lambda: self.update_status("Could not locate or download media file."))

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
                    self.update_status("Media payload downloaded successfully!")
                    self.check_live_updates()
                else:
                    self.update_status(f"Download failed: {proc.stderr or proc.stdout}")
            self.call_from_thread(on_complete)
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"Download error: {e}"))

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
                    self.update_status(f"Signal confirmed by {chat_name}!")
                    self.check_live_updates()
                else:
                    self.update_status(f"Transmission failed: {error_msg}")

            self.call_from_thread(on_complete)

        except subprocess.TimeoutExpired:
            self.call_from_thread(lambda: self.update_status("Relay timed out (30s)."))
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"Transmission error: {e}"))

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
                    self.update_status(f"Sticker delivered to {chat_name}!")
                    self.check_live_updates()
                else:
                    self.update_status(f"Sticker failed: {error_msg}")

            self.call_from_thread(on_complete)
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"Sticker error: {e}"))

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
                    self.update_status(f"File beamed to {chat_name}!")
                    self.check_live_updates()
                else:
                    self.update_status(f"Beam failed: {error_msg}")

            self.call_from_thread(on_complete)
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"File send error: {e}"))

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
                    self.update_status(f"Reaction {emoji} acknowledged!")
                    self.check_live_updates()
                else:
                    self.update_status("Reaction failed.")

            self.call_from_thread(on_complete)
        except Exception as e:
            self.call_from_thread(lambda: self.update_status(f"Reaction error: {e}"))

    @work(thread=True)
    def run_sync_online(self) -> None:
        if self.is_syncing:
            return
        self.is_syncing = True
        self.call_from_thread(lambda: self.update_status("Engaging Hyper-Sync with servers..."))

        try:
            cmd = ["wacli", "sync", "--once", "--idle-exit", "2s"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            def on_finish():
                self.is_syncing = False
                self.update_status("Hyper-Sync complete! Grid refreshed.")
                self.load_chats(preserve_selection=True)
                if self.current_chat_jid:
                    self.load_messages(self.current_chat_jid, self.current_chat_name, force_reload=True)

            self.call_from_thread(on_finish)
        except Exception as e:
            def on_err():
                self.is_syncing = False
                self.update_status(f"Hyper-Sync ended: {e}")
            self.call_from_thread(on_err)

    def action_trigger_sync(self) -> None:
        self.run_sync_online()

    def action_refresh_all(self) -> None:
        self.update_status("Re-scanning local sensor database...")
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
