normalOS Workstation — Übersicht
================================
Datum: 2026-07-09

Dies ist dein zentraler Startpunkt für den täglichen PC-Betrieb.

SCHNELLSTART
  Desktop\normalOS\Start normalOS.lnk   → startet Fusion Hero OS + Bridge + Docs
  Desktop\normalOS\Status normalOS.lnk  → zeigt Gesamtstatus

KANONISCHE PFADE
  normalOS Code:     C:\Users\Admin\normalOS
  Fusion Hero OS:    C:\Users\Admin\fusion-hero-os
  MCP-Konnektoren:   C:\Users\Admin\mcps
  Grok Skills:       C:\Users\Admin\.grok\skills
  Fusion-Profil:     C:\Users\Admin\.fusion-hero-os

ENDPUNKTE (nach Start)
  Fusion Dashboard:  http://127.0.0.1:8000
  Hero Docs / Mesh:  http://127.0.0.1:8088
  normalOS Bridge:   http://127.0.0.1:8765
  Ollama (lokal):    http://127.0.0.1:11434

API KEYS
  Trage Keys in ein:
    normalOS\workstation\.env
    fusion-hero-os\.env
  Vorlage: .env.example in beiden Ordnern

DESKTOP-STRUKTUR (nach Restore 2026-07-09)
  Desktop\Dokumente, Bilder, Videos, Forschung, Fusion-Hero
  Desktop\Projekte, Spiele, System-Tools, Sonstiges
  Desktop\Apps\ (Shortcuts) | Desktop\normalOS\ (Start/Status)

TAILSCALE MESH
  Desktop: desktop-kpki9e4.tail391adb.ts.net (100.80.63.0)
  Phone:   redmi-note-13-pro-5g.tail391adb.ts.net (Android)
  Mainframe: mainframe.tail391adb.ts.net (offline)
  Vom Handy: http://desktop-kpki9e4.tail391adb.ts.net:8000 / :8088 / :8765

VERALTETE ORDNER (nicht mehr nutzen)
  fusion-hero-os-llm-push, hero-os, fusion-hero-core
  → siehe VERWEIS.txt in diesen Ordnern