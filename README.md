# 🛸 wacli-tui // XENO-NET 👽
> **Eye-friendly Alien / Weyland-Yutani Sci-Fi WhatsApp Terminal Client with True Multimedia Support.**

```
   //========================================================\\
  ||     __      __  _____   _________ .____    .___          ||
  ||    /  \    /  \/  _  \  \_   ___ \|    |   |   |         ||
  ||    \   \/\/   /  /_\  \ /    \  \/|    |   |   |         ||
  ||     \        /    |    \\     \___|    |___|   |         ||
  ||      \__/\  /\____|__  / \______  /_______ \___|         ||
  ||           \/         \/         \/        \/             ||
  ||        [ WEYLAND-YUTANI // XENO-NET TERMINAL v3.0 ]      ||
   \\========================================================//
```

`wacli-tui` is an eye-friendly, alien sci-fi terminal client for WhatsApp powered by [wacli](https://github.com/openclaw/wacli). It provides full multimedia viewing (stickers, images, videos, audio, emojis), keyboard-driven navigation, in-terminal pixel art previews, and live messaging.

---

## ⚡ Key Highlights

* **👁️ Soothing, Eye-Friendly Sci-Fi Palette:**
  * Deep matte charcoal/slate background (`#0d1416`), zero glaring harsh neon contrast.
  * Soft phosphor emerald (`#10b981` / `#34d399`) and ice cyan (`#38bdf8`) accents.
  * 100% font-safe universal glyphs (`●`, `▲`, `★`, `✓✓`) — **zero broken tofu boxes (`▯`)**.
* **🖼️ True Multimedia Support:**
  * **Stickers & Images:** Automatic in-terminal ANSI pixel art previews powered by Pillow.
  * **Instant Viewer (<kbd>v</kbd> / <kbd>o</kbd>):** Opens stickers, photos, and GIFs in `imv` (or default viewer).
  * **Videos (<kbd>v</kbd>):** Launches video streams in `ffplay` / `xdg-open`.
  * **Voice & Audio (<kbd>p</kbd>):** One-touch audio playback in `ffplay`.
  * **Emojis:** Native color emojis supported across all messages via `noto-fonts-emoji`.
* **⌨️ Seamless Keyboard Control:**
  * Move up & down chats with <kbd>↑</kbd> / <kbd>↓</kbd> (instant preview on right).
  * Press <kbd>Enter ↵</kbd> on a chat to jump directly into the transmitter to type.
  * Press <kbd>Enter ↵</kbd> in input to send messages with real-time optimistic rendering.
  * Press <kbd>Esc</kbd> to return to chat selection.
  * Press <kbd>/</kbd> to search channels & contacts.
  * Compact filter tabs that fit perfectly: `ALL (F1)`, `DMS (F2)`, `FLEET (F3)`, `NEW (F4)`.
* **📡 Live Syncing:**
  * Blazing fast 2–4ms SQLite reads with WAL concurrency.
  * Instant auto-detection of incoming WhatsApp messages.
  * Online Hyper-Sync with <kbd>Ctrl</kbd> + <kbd>S</kbd>.

---

## 📦 Requirements

* **Python 3.9+** (with `textual`, `rich`, and `Pillow`)
* **wacli** (WhatsApp CLI: `yay -S wacli-bin` or `brew install openclaw/tap/wacli`)
* Media Viewers (optional but recommended): `imv`, `ffplay` / `ffmpeg`, `noto-fonts-emoji`

---

## 🚀 Quick Start

### 1. Link WhatsApp (if not already authenticated)
```bash
wacli auth
wacli sync --once
```

### 2. Launch
```bash
wacli-tui
```

---

## ⌨️ Keyboard Shortcuts Reference

| Shortcut | Function |
| :--- | :--- |
| <kbd>↑</kbd> / <kbd>↓</kbd> | Navigate channels on the grid (instant preview) |
| <kbd>Enter ↵</kbd> on Chat | Select chat and focus message transmitter |
| <kbd>Enter ↵</kbd> in Input | Transmit / Send typed message |
| <kbd>v</kbd> or <kbd>o</kbd> | **View/Open** latest sticker, image, or video in external viewer |
| <kbd>p</kbd> | **Play** latest audio recording / voice note |
| <kbd>Esc</kbd> | Disengage transmitter and return to chat list |
| <kbd>/</kbd> | Jump to search bar |
| <kbd>Tab</kbd> / <kbd>Shift</kbd>+<kbd>Tab</kbd> | Cycle focus between Search, Chat List, Log, and Transmitter |
| <kbd>PgUp</kbd> / <kbd>PgDn</kbd> | Scroll transmission history |
| <kbd>F1</kbd> – <kbd>F4</kbd> | Switch filters (`ALL`, `DMS`, `FLEET`, `NEW`) |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Hyper-Sync with WhatsApp servers |
| <kbd>Ctrl</kbd> + <kbd>R</kbd> / <kbd>F5</kbd> | Re-scan local database |
| <kbd>Ctrl</kbd> + <kbd>Q</kbd> | Exit application cleanly |

---

## 🛠️ Slash Commands

Type these directly into the message input bar:
* `/view` or `/open` — View latest sticker/image in `imv`, video in `ffplay`.
* `/play` — Play latest audio/voice note in `ffplay`.
* `/download` — Force download media payload for the current message.
* `/sticker /path/to/sticker.webp` — Send a WebP sticker.
* `/file /path/to/media.jpg` — Send a photo, video, audio, or document archive.
* `/react 👍` — React to the last incoming message.
* `/help` — Print command guide.

---

## 📄 License

MIT License © 2026 [venkatengineer](https://github.com/venkatengineer)
