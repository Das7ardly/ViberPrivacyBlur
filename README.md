# Viber Privacy Blur

A tiny Windows app that frosts your **Viber Desktop** window on demand, so a
bystander can't read your chat. It does **not** modify Viber in any way — it
just places a blurred panel over the Viber window.

## Running it

Double-click **`ViberPrivacyBlur.exe`** (in the `dist` folder). No installation
and no Python needed. It starts quietly:

- A small **control pill** docks to the **top-center of the Viber window**
  (Blur button + blur-intensity slider + a **–** button to hide the pill).
- A **tray icon** (violet eye-with-slash) appears in the system tray.

### Controls

| Action | How |
|---|---|
| Blur / un-blur Viber | Press **Ctrl+Alt+B**, or click the pill, or double-click the tray icon |
| Change how frosted it is | Drag the **Blur** slider on the pill |
| Hide the pill (hotkey still works) | Click the **–** on the pill, or tray → *Hide controls* |
| Show the pill again | Tray → *Show controls* |
| Start automatically with Windows | Tray → *Start with Windows* (toggle) |
| Quit | Tray → *Quit* |

### How it behaves

- The blur and the pill are **attached to the Viber window**: they move with it,
  and **disappear when you minimize Viber**, returning when you restore it.
- They sit **above Viber only** — not on top of your other apps. Switch to
  another app and they drop behind it; return to Viber and they're back.
- While blurred, clicks on Viber are blocked, so a bystander can't read or poke
  the chat.
- Costs essentially **0% CPU when idle** (blur off): the only cost is a one-time
  capture + blur when you trigger it.

## Notes

- Windows 10/11, 64-bit.
- First launch may show a SmartScreen prompt ("Windows protected your PC") because
  the exe isn't code-signed → click **More info → Run anyway**.
- Only one copy runs at a time (launching it again just points you to the tray).

## Antivirus false positives (Kaspersky, etc.)

This app is **not** a virus. But it legitimately does things that antivirus
*heuristics* associate with spyware — it captures the pixels of the Viber window
(to blur it), attaches an overlay onto Viber's window, registers a global
hotkey, and can start with Windows. Combined with being **unsigned** and packed
with PyInstaller, that can cause a **false positive**, most often in Kaspersky.

**What was done to reduce it:** the app is now **compiled to native code with
Nuitka** (not packed with PyInstaller), shipped as a folder app (no
self-extracting stub), with real version/company metadata and a valid PE
checksum. A Nuitka-compiled binary looks like an ordinary C program, so it trips
far fewer antivirus heuristics than any PyInstaller build. Windows Defender scans
the exe, the whole folder, and the installer clean.

**If Kaspersky still blocks it:**

1. **Use it now — add an exclusion.** Kaspersky → *Settings* → *Security
   settings* / *Threats and Exclusions* → *Manage exclusions* → *Add* → the
   install folder `%LOCALAPPDATA%\Programs\ViberPrivacyBlur`. If it was
   quarantined, restore it and add to trusted.
2. **Clear it properly — report the false positive.** Upload the exe to
   **https://opentip.kaspersky.com** (Kaspersky Threat Intelligence Portal); if
   it shows a detection, click *Submit to reanalyze* / request review. Kaspersky
   usually whitelists genuine false positives within a few days. (Developers can
   also use the Kaspersky allowlist program.)
3. **Definitive fix (optional, costs money):** sign the exe with a code-signing
   certificate from a trusted CA. A signed exe is trusted by antivirus and stops
   SmartScreen warnings. The build is ready for signing if you get a cert.

## For developers

- Source: `viberblur/` (pure-logic modules + Qt UI), entry point `main.py`.
- Run from source: `python main.py` (needs `PySide6-Essentials`, `pywin32`, `pillow`).
- Build the exe: `tools/build.ps1` (or see the PyInstaller command in that file).
