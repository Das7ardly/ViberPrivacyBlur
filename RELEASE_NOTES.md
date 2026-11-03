# Viber Privacy Blur v1.0.0

Instantly blur your **Viber Desktop** chat window for privacy — a panic-button
frosted overlay you toggle with a hotkey. It never modifies Viber; it just
places a blurred panel over the window.

## Download
**[ViberPrivacyBlur-Setup-1.0.0.exe](#)** — Windows 10/11, 64-bit. No Python needed.

> **First run:** Windows may show *"Windows protected your PC"* because the app
> isn't code-signed (normal for free open-source apps). Click **More info →
> Run anyway**. The app is open source — you can read every line here.

## Features
- **Ctrl+Alt+B** toggles the blur from anywhere (also a floating button + a tray icon).
- Blur-intensity slider.
- Overlay and controls **attach to the Viber window** — they move with it, hide
  when you minimize Viber, and stay above Viber only (not over your other apps).
- Blocks clicks on Viber while blurred, so a bystander can't read or poke the chat.
- Optional **Start with Windows**.
- ~0% CPU when idle.

## Install
1. Download and run the Setup (click **Run anyway** if prompted).
2. Keep **"Start automatically when Windows starts"** ticked if you want it always on.
3. Open Viber's chat window, press **Ctrl+Alt+B**.

## Notes
- Built with **Nuitka** (native compile) — scans clean in Windows Defender.
- Only blurs when Viber's chat window is open (closed-to-tray = nothing to blur).
- Uninstall anytime from Start Menu → *Uninstall Viber Privacy Blur*.
