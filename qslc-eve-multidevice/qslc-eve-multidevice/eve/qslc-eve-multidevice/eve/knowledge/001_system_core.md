# QSLC / CEC System Core

- Single repo: qslc-eve-multidevice
- Components:
  - backend/server.py: AI gateway for EVE-HEI
  - Make.com scenario: webhook -> HTTP -> backend
  - GitHub agent: qslc_cleanup.py + qslc_agent.yml
  - Devices: iPhone Shortcut, Telegram, browser
- Goal: multi-device, low-friction, always-on EVE-HEI access.
