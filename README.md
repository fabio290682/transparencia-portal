# Instituto Meio do Mundo — Design System

## Overview

**Instituto Meio do Mundo** (IMM) is an OSCIP (Organização da Sociedade Civil de Interesse Público) headquartered in Macapá, Amapá, Brazil (CNPJ 08.962.333/0001-03). Its mission is to promote social development, civic participation, cultural initiatives, and environmental sustainability in the Amazon region.

The primary digital product is the **Portal da Transparência** — a public transparency portal that exposes financial documents, public works projects, procurement records, and an e-SIC (Electronic Citizen Information Service) request system, in compliance with Brazil's Lei de Acesso à Informação (LAI, Law 12.527/2011) and LGPD (Law 13.709/2018).

### Products / Surfaces

| Surface | Description | Tech |
|---|---|---|
| **Public Portal** (`index.html`) | Transparency portal for citizens — project records, financial docs, e-SIC form | Vanilla HTML/CSS/JS |
| **Admin Dashboard** | Internal management panel for reviewing e-SIC requests, managing documents | Django + custom CSS |
| **Admin Login** | Branded login screen for staff access | Django admin override |

### Sources

- **GitHub repository**: `fabio290682/transparencia-portal` (https://github.com/fabio290682/transparencia-portal)
- **Backend**: Django (Python 3.12+), REST Framework, PostgreSQL
- **Static assets**: `static/img/`, `static/css/`

---

## CONTENT FUNDAMENTALS

### Language & Tone
- All copy is written in **Brazilian Portuguese** (pt-BR)
- Tone is **formal, civic, and institutional** — this is a government-adjacent NGO transparency portal
- Language is precise and uses legal/bureaucratic terminology: "Instrumento nº", "Fonte de Recurso", "Natureza da Despesa", "Termo de Fomento"
- Copy uses third person when describing the organization: "O Instituto Meio do Mundo disponibiliza..."
- When addressing the user, formal "você" is used: "O que você procura?"

### Headlines & Labels
- Section headers use **ALL CAPS** with wide letter-spacing (eyebrow labels): e.g. `ACESSO RÁPIDO`, `ÚLTIMOS REGISTROS`
- Page titles use Title Case and Montserrat Black: `Portal da Transparência`
- Navigation items use Title Case: `Página Inicial`, `Acesso a Informação`, `Fale Conosco`

### Specific Phrases / Examples
- Hero tagline: *"Este espaço representa mais uma ação de promoção da transparência pública do Instituto Meio do Mundo."*
- CTA: *"Solicitar via e-SIC"*, *"Baixar Documento PDF"*, *"Ver todos os projetos →"*
- Form note: uses a green left-border callout with informational text
- Protocol format: `ESIC-YYYYMMDD-XXXXXXXX`

### Emoji Usage
- Emoji are used sparingly and functionally as **thumbnail/icon proxies** inside project cards (🏃 🎖️ 🌴 🎵 🎭)
- Emoji also appear in dropdown menus as quick visual cues (📊 🔍 📅)
- **Not** used decoratively in body copy or headings
- Admin dark UI uses **no emoji** — fully text/icon driven

---

## VISUAL FOUNDATIONS

### Color Palette
Two distinct themes share the same brand palette:

**Public Portal (Light Mode)**
- Background: `#f5f8f5` — very light green-tinted white
- Deep forest green: `#0d3318` → `#1e5420` (darkest to card-level)
- Gold accent: `#f5c800` / `#ffd700` — used for CTAs, active nav underlines, eyebrow bars
- Body text: `#1a3020` (near-black with green cast), muted: `#4a6550`

**Admin (Dark Mode)**
- Background: near-black `#0a1f0e` → `#08180b` with radial gold glow at top-right
- Panels: `#0f2914` / `#13341a`
- Gold accent same: `#f5c800`
- Text: `#e8f0ea`, muted: 62% opacity

### Typography
- **Display / UI**: Montserrat — weights 600–900. Used for all headings, nav, labels, buttons, stats
- **Body**: Open Sans — weights 300–600. Used for body copy, form fields, descriptive text
- Admin fallback: `"Segoe UI", system-ui`
- Eyebrow labels: 11px, weight 800, letter-spacing 1.8em, uppercase, gold color
- Stat numbers: 34px, weight 900, letter-spacing −2px

### Backgrounds
- Public portal: flat `#f5f8f5` page background; no images or textures
- Hero sections use `linear-gradient(135deg, #0d3318 → #1a4a1a → #1e5a20)` with a white ellipse clip at the bottom
- Impact block: same dark green gradient with a decorative circle border (opacity 8%)
- Admin: `radial-gradient` (gold glow top-right) + `linear-gradient` (near-black vertical)
- **No full-bleed photography** used in the UI (logo only)

### Cards
- Light cards: `background: #fff`, border `1.5px solid #e8ede8`, border-radius 14px, hover: `box-shadow 0 6px 28px rgba(21,82,36,0.13)` + `translateY(-2px)`
- Dark cards (admin): border `1px solid #1f4a25`, `linear-gradient(180deg, rgba(20,52,26,0.94), rgba(12,32,16,0.98))`, `box-shadow 0 18px 50px rgba(0,0,0,0.18)`, border-radius 18–22px
- Icon cards (public): dark green `#1a4a1a` bg, border-radius 16px, 2px gold border on hover, gold underline bar via `::before scaleX(1)` on hover

### Hover & Interactive States
- Buttons: `translateY(-2px)` on hover across all surfaces
- Active: `translateY(0)` press — no shrink
- Nav items: gold bottom border + gold text color
- Cards: translateY(-2px) + box-shadow deepens
- Dark sidebar links: gold-tinted background + gold border

### Borders & Radius Scale
- Pill badges: `border-radius: 999px`
- Buttons: 9–10px
- Cards: 14–22px (scale up for more prominent cards)
- Brand mark (admin): 12px

### Animations
- All transitions: `0.18–0.25s ease` — subtle, no bounce
- Page transitions: `opacity 0 → 1 + translateY(10px → 0)` on page switch
- Hover icon scale: `transform: scale(1.08)` on card images
- Bottom border reveal on icon cards: `scaleX(0 → 1)` from left origin

### Shadow System
- Light UI shadow: `0 4px 24px rgba(0,0,0,0.08)`
- Elevated light card: `0 6px 28px rgba(21,82,36,0.13)`
- Dark panel shadow: `0 18px 50px rgba(0,0,0,0.18)`
- Gold button glow: `0 4px 16px rgba(245,200,0,0.35)`
- Logo drop-shadow: `drop-shadow(0 2px 8px rgba(0,0,0,0.3))`

### Layout
- Max content width: `1100px`, centered
- Sticky nav bar (`position: sticky; top: 0; z-index: 100`)
- Admin: 260px fixed sidebar + fluid main
- Grid: 3-col icon cards, 4-col impact stats, 2-col content panels
- Responsive breakpoints: 900px (2-col collapse), 600px (single col)

### Imagery
- No photography in the portal UI
- Logo is the main brand visual — horizontally wide banner format (PNG with transparency)
- Icons are minimal line SVGs (custom set, white fill, single-color)
- Color vibe: deep forest green + warm gold — Amazon-inspired

### Use of Blur / Transparency
- Topbar links: `rgba` white at low opacity for de-emphasized text
- Nav dropdown: `rgba(245,200,0,0.08)` hover tint
- Admin radial glow: `rgba(245,200,0,0.08)` — very subtle
- No backdrop-filter blur used

---

## ICONOGRAPHY

### Custom Icon Set
The project ships 6 custom SVG icons in `assets/icons/`:

| File | Represents | Usage |
|---|---|---|
| `icon-chat.svg` | Speech bubble | Fale Conosco / e-SIC |
| `icon-group.svg` | People group | Beneficiários & Comunidades |
| `icon-impact.svg` | Rising arrow/chart | Impactos e Resultados |
| `icon-location.svg` | Map pin | Localização & Sede |
| `icon-partnership.svg` | Handshake | Parcerias & Termos |
| `icon-tower.svg` | Tower/signal | Acesso à Informação |

- Icons are **white stroke/fill SVGs**, displayed at 90×90px in cards with `drop-shadow(0 4px 12px rgba(0,0,0,0.3))`
- Style: **line/outline**, geometric, minimal — not filled, no color other than white
- No icon font or CDN icon library used — all custom files
- Admin panel uses **no icons** (text labels only in sidebar)
- Emoji used as quick avatar proxies in project card thumbnails

### Logos
- `assets/logo-header.png` — Full horizontal wordmark (light on transparent), used in the green header band
- `assets/logo-portal.svg` — Fallback SVG version of the logo
- Partner logos in `static/img/logos/` (Logo 1–8, Marca d'água variants) — import as needed

---

## FILE INDEX

```
/
├── README.md                    ← This file
├── SKILL.md                     ← Agent skill definition
├── colors_and_type.css          ← All design tokens (colors, type, spacing)
│
├── assets/
│   ├── logo-header.png          ← Full horizontal wordmark
│   ├── logo-portal.svg          ← SVG logo fallback
│   └── icons/
│       ├── icon-chat.svg
│       ├── icon-group.svg
│       ├── icon-impact.svg
│       ├── icon-location.svg
│       ├── icon-partnership.svg
│       └── icon-tower.svg
│
├── preview/                     ← Design System tab cards
│   ├── colors-brand.html
│   ├── colors-dark.html
│   ├── colors-semantic.html
│   ├── type-display.html
│   ├── type-body.html
│   ├── type-scale.html
│   ├── spacing-tokens.html
│   ├── shadows-radii.html
│   ├── components-buttons.html
│   ├── components-badges.html
│   ├── components-cards-light.html
│   ├── components-cards-dark.html
│   ├── components-nav.html
│   ├── components-form.html
│   ├── brand-logo.html
│   ├── brand-icons.html
│
└── ui_kits/
    └── portal/
        ├── README.md
        ├── index.html           ← Interactive portal prototype
        ├── PublicPortal.jsx     ← Main portal components
        └── AdminDashboard.jsx   ← Admin panel components
```
