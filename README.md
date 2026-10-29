# 🛸 wacli-tui // XENO-CLI 👽
> **Extraterrestrial, keyboard-navigable WhatsApp Terminal User Interface powered by `wacli`.**

```
   🛸  ______________________________________________________  🛸
      /                                                      \
     |     __      __  _____   _________ .____    .___       |
     |    /  \    /  \/  _  \  \_   ___ \|    |   |   |      |
     |    \   \/\/   /  /_\  \ /    \  \/|    |   |   |      |
     |     \        /    |    \\     \___|    |___|   |      |
     |      \__/\  /\____|__  / \______  /_______ \___|      |
     |           \/         \/         \/        \/          |
     |          [ XENO-NET // ALIEN TERMINAL v2.5 ]          |
      \______________________________________________________/
```

`wacli-tui` turns WhatsApp into an alien sci-fi cyberpunk terminal client. It hooks into [wacli](https://github.com/openclaw/wacli) to provide instant offline browsing, keyboard-driven navigation, real-time message syncing, WebP sticker rendering, and live text transmission without leaving your terminal shell.

---

## ⚡ Key Features

* **👽 Alien / Sci-Fi Cyberpunk Aesthetics:** Deep space void background (`#030706`), neon slime green accents (`#00ff88` / `#39ff14`), bioluminescent cyan highlights (`#00f5d4`), and mothership terminal borders.
* **👾 Prominent Sticker Transmissions:** Sent and received WhatsApp stickers (WebP payloads) are rendered prominently in terminal sticker transmission pods with file details and status.
* **⌨️ Full Keyboard Navigation:**
  * Move up & down chats with <kbd>↑</kbd> / <kbd>↓</kbd> while immediately previewing messages on the right.
  * Press <kbd>Enter ↵</kbd> on a chat to jump directly into the transmitter to type.
  * Press <kbd>Enter ↵</kbd> in the input box to broadcast messages with optimistic real-time rendering.
  * Press <kbd>Esc</kbd> to disengage transmitter and return to chat selection.
  * Jump straight to frequency search with <kbd>/</kbd>.
  * Cycle sectors seamlessly with <kbd>Tab</kbd> and <kbd>Shift</kbd>+<kbd>Tab</kbd>.
* **📡 Frequency Filter Tabs:**
  * `🌌 All (F1)` — All conversations
  * `👽 Aliens (F2)` — Direct messages (1-on-1)
  * `🛸 Fleets (F3)` — Groups
  * `🧬 Signals (F4)` — Unread messages with signal counters
* **⚡ Live Offline & Online Syncing:**
  * Instant offline loading (2–4ms SQLite reads with WAL concurrency).
  * Auto-detects new incoming messages from `wacli sync`.
  * Trigger manual server sync anytime with <kbd>Ctrl</kbd> + <kbd>S</kbd>.
* **🚀 In-App Slash Commands:**
  * `/sticker <path.webp>` — Send a WebP sticker
  * `/file <path>` — Beam an image, video, audio, or document archive
  * `/react <emoji>` — Transmit orbital reaction to the last signal
  * `/download` — Download media payload from the last transmission
  * `/help` — Display Xeno-CLI comm protocols

---

## 📦 Requirements

* **Python 3.9+**
* **wacli** (WhatsApp CLI: `yay -S wacli-bin` or `brew install openclaw/tap/wacli`)
* Python libraries: `textual>=8.0.0`, `rich>=13.0.0`

---

## 🚀 Quick Start

### 1. Link WhatsApp (if not already authenticated)
```bash
wacli auth
wacli sync --once
```

### 2. Launch wacli-tui
```bash
wacli-tui
```

---

## ⌨️ Keyboard Shortcuts Reference

| Shortcut | Function |
| :--- | :--- |
| <kbd>↑</kbd> / <kbd>↓</kbd> | Navigate contacts / fleets on the sensor grid |
| <kbd>Enter ↵</kbd> on Chat | Lock onto chat and **focus message transmitter** |
| <kbd>Enter ↵</kbd> in Input | **Broadcast / Send** typed message |
| <kbd>Esc</kbd> | Disengage input / search and return to chat list |
| <kbd>/</kbd> | Jump to frequency scan / search bar |
| <kbd>Tab</kbd> / <kbd>Shift</kbd>+<kbd>Tab</kbd> | Cycle through Search, Chat Grid, Log View, and Transmitter |
| <kbd>PgUp</kbd> / <kbd>PgDn</kbd> | Scroll transmission log |
| <kbd>F1</kbd> – <kbd>F4</kbd> | Switch frequency filters (`All`, `Aliens`, `Fleets`, `Signals`) |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Engage Hyper-Sync with WhatsApp servers |
| <kbd>Ctrl</kbd> + <kbd>R</kbd> / <kbd>F5</kbd> | Re-scan local sensor database |
| <kbd>Ctrl</kbd> + <kbd>Q</kbd> | Eject / Abort session cleanly |

---

## 🛠️ Slash Commands

Type these directly into the message input bar:
* `/sticker /path/to/sticker.webp` — Send a sticker to current contact.
* `/file /path/to/image.png` — Send a photo, video, audio, or PDF document.
* `/react 👍` — React to the last incoming message.
* `/download` — Download media from the latest transmission.
* `/help` — Print command guide.

---

## 📄 License

MIT License © 2026 [venkatengineer](https://github.com/venkatengineer)
