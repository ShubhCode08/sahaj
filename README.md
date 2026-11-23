# Sahaj — Effortless Voice-First Browser Agent

> **Say what you need, in your language, and it gets done on the real website—with you.**

Submitted for **wHACKiest 2026 Online Ideathon** (MS Ramaiah Institute of Technology)  
**Track:** Beyond the Browser — Reimagine How We Use the Web  
**Team:** Bug Slayers (PES University)

---

## The Problem
Everyday online tasks—paying a bill, booking a ticket, applying for a government scheme, or comparing options—still force millions to decode cluttered, English-heavy websites on their own.
- **958M** Indians are online, and **57%** prefer content in their own language.
- **149M** Indians are aged 60+ (projected to reach 347M by 2050).
- **95.9%** of top 1M home pages fail WCAG accessibility checks.

## Our Solution
**Sahaj** (Sanskrit for *"effortless"*) is a Chrome Extension side-panel agent that works inside the user's own browser and logged-in sessions:
- **Speak Your Goal:** Voice or text in 22 Indian languages (code-mixed speech supported).
- **Does It With You:** Opens pages, clicks, types, and fills forms while narrating every step.
- **Simple View:** Re-renders cluttered pages into plain-language cards read aloud.
- **Compare in One Go:** Checks multiple sites in parallel and presents one comparison table with source links.
- **Action Guard:** Verifies every step against the user's goal before acting; OTPs, passwords, and payments are always handed back to the user.

## Tech Stack
- **Frontend:** Chrome Extension (Manifest V3), React, TypeScript, Tailwind CSS, WXT
- **Browser Control:** Content Scripts, Chrome DevTools Protocol (Accessibility Tree), Playwright
- **Backend / Agent Core:** Python, FastAPI, WebSockets, LangGraph, Pydantic
- **AI / ML:** Gemini Flash API, Chrome Built-in AI (Gemini Nano Summarizer & Translator)
- **Speech & Language:** Sarvam AI (Saaras v4 STT, Bulbul TTS), Bhashini, Web Speech API
- **Database & Cloud:** Supabase Postgres, IndexedDB + WebCrypto Vault, Google Cloud Run, Docker

## Team Bug Slayers (PES University)
- **Shubham Nayak**  
- **Yashas Sapare** 
- **Achinthya Karaba** 
