# GROW — Visual Appearance & Design System (`DESIGN.md`)

## 1. Core Design Philosophy

GROW is a mobile-first Progressive Web App (PWA) designed to feel like a **native mobile application** rather than a website. Every visual decision prioritizes **readability and a mature, timeless aesthetic**.

### Aesthetic Direction
> *Mobile app UI, glassmorphism aesthetic with frosted glass panels, soft glossy accents, subtle lighting effects, a calming color palette featuring soft whites and muted grays, clean composition with layered depth, modern and minimalist mood.*

### Anti-Patterns (What to Avoid)
- **No "Typical JS / SaaS Template" Look**: Avoid patterns associated with generic Tailwind, React/Next/Nuxt marketing pages, or early-2000s "Photoshop" design marks.
- **No Neon or Harsh Glow Orbs**: Do not use large blurred background blobs (`blur-3xl` neon circles), multi-stop gradient text headings, or glowing neon borders.
- **No Harsh High-Contrast Dark Mode**: Avoid pitch-black (`#000000`) backgrounds paired with oversaturated neon accents.
- **No Visual Clutter**: Avoid decorative pill badges, excessive metadata, harsh drop shadows, or dense walls of text.

---

## 2. Foundational References & Division of Responsibilities

GROW intentionally combines **Apple Human Interface Guidelines (HIG)** and **Material Design 3 (M3)**. Where the two systems differ, GROW resolves conflicts using a strict division of responsibilities:

| Design Domain | Governing Standard | How GROW Applies It |
| :--- | :--- | :--- |
| **Spatial Layout & Card Hierarchy** | **Apple HIG** (*Inset Grouped*) | Flat app canvas (`--bg-app`) behind sections. Sections themselves have **no outer border or panel background on mobile**; only the leaf items/groups inside have elevated panel borders (`.card-theme`). Never nest a bordered card inside another bordered card. |
| **Viewport Margins (Mobile-First)** | **Apple HIG** | Content extends nearly to the mobile viewport edges (`10px` / `px-2.5` outer margin on mobile) to maximize horizontal space for numbers and steppers. |
| **Navigation & Floating Chrome** | **Apple Liquid Glass** | Translucent frosted glass (`backdrop-filter: blur(...) saturate(...)` + specular edge) reserved exclusively for the sticky top header and collapsible mobile menu. |
| **Color Tokens & Light/Dark Tinting** | **Material Design 3** | Semantic tonal surface variables (`--bg-app`, `--bg-surface`, `--bg-surface-elevated`) and lightly tinted Light/Dark palettes driven by a single replaceable `static/css/theme.css` file. |
| **Web Adaptability & States** | **Material Design 3** | Responsive desktop/tablet grid breakpoints (`sm:`, `md:`, `lg:`), keyboard focus rings, and pointer hover state layers not covered by device-only iOS guidelines. |

### Reference Links
1. **[Apple Interface Fundamentals](https://developer.apple.com/documentation/technologyoverviews/interface-fundamentals)**
   - **Clarity & Deference**: The interface defers to the user's workout and nutrition data. Chrome is minimal; typography and whitespace establish hierarchy.
   - **Inset Grouped Layout (No "Card-in-a-Card")**: Like iOS Settings, Health, and Fitness, outer sections sit directly on the flat canvas. Only individual items or inset control groups have a panel background and border.
   - **Tactile Native Controls**: Use clean inset grouped rows, segmented controls, and large steppers (`+` / `-`) sized for effortless thumb interaction (minimum `44x44px` touch targets).

2. **[Apple Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass)**
   - **Selective Application**: Liquid Glass is reserved **exclusively for floating navigation and chrome layers** that sit above scrolling content:
     - Sticky top navigation header
     - Collapsible mobile navigation menu (3-line hamburger toggle expanding a Liquid Glass sheet)
     - Floating bottom action bar / modal sheets
   - **Never Overuse on Content**: Standard content items, exercise rows, and form inputs sit on solid tonal surfaces so scrolling content remains crisp and legible.

3. **[Material Design 3 (M3)](https://m3.material.io/)**
   - **Tonal Surface Elevation**: Instead of heavy drop shadows, depth in the main content area is expressed through subtle shifts in surface luminance.
   - **Web Layout & State Layers**: Responsive container widths on desktop browsers, predictable focus/hover/pressed state overlays, and accessible contrast ratios across Light and Dark modes.

---

## 3. Theming Architecture: Light, Dark & Tinted Variables

### Light & Dark Modes (User-Selectable)
Instead of a multi-season dropdown in the UI, the user interface provides a clean **Light / Dark theme toggle** (respecting system preference by default):

- **Light Theme**: Calming soft whites, warm/cool muted grays, subtle hairline borders, and airy frosted glass chrome with soft specular highlights.
- **Dark Theme**: Mature, muted charcoal/slate surfaces (never harsh neon-on-black), soft contrast text, and translucent dark glass headers with subtle top-edge illumination.

### Lightly Tinted Surfaces
Both Light and Dark themes are **lightly tinted** using a shared set of CSS custom properties. Rather than pure neutral grays (`#f5f5f5` or `#171717`), background and surface tokens carry a subtle underlying hue and saturation tint. This creates a warm, cohesive atmosphere while keeping text contrast effortless to read.

### Single-File Theme & Future Seasonal Swaps (`static/css/theme.css`)
- **Default Starting Season**: **Autumn** is the default baseline theme.
- **Centralized Stylesheet**: All seasonal color tokens, surface tints, brightness levels, glass material variables, **and theme-specific asset URLs** live in a single replaceable file: [`static/css/theme.css`](../static/css/theme.css).
- **Seasonal Asset Folders**:
  - Theme-tied visual assets (logos, header imagery, seasonal mood icons, and decorative illustrations) are stored in permanent per-season subdirectories (e.g., `static/images/autumn/`, `static/images/winter/`, `static/images/spring/`, `static/images/summer/`) so files never need to be manually overwritten on disk.
  - Templates should not hardcode seasonal image paths in HTML. Instead, theme-bound icons and images are referenced via CSS variables or utility classes defined inside `static/css/theme.css` (e.g., `--theme-logo-url`, `--theme-header-image`, `--theme-mood-icon-*`).
- **Zero-Friction Seasonal Switching**:
  - Seasonal theming is not exposed as a user-facing switcher in the UI for now.
  - Changing the app's season only requires replacing `static/css/theme.css` with that season's stylesheet, which updates both the Light/Dark color & tint variables and points all theme asset URLs to the corresponding seasonal subfolder (`autumn`, `winter`, `spring`, or `summer`).

---

## 4. Visual Building Blocks & Component Guidelines

### Surfaces, Sections & Single-Layer Items
- **App Canvas (`--bg-app`)**: Flat, lightly tinted off-white in Light mode; deep muted slate/stone in Dark mode.
- **Section Containers (`.section-theme`)**:
  - On **mobile (`< 640px`)**: Completely unboxed (`background: transparent`, `border: 0`, `padding: 0`, `box-shadow: none`). Section titles sit directly on the flat canvas so zero horizontal space is wasted on outer card margins.
  - On **desktop/tablet (`>= 640px`)**: May optionally apply subtle surface grouping where helpful for wide multi-column layouts.
- **Leaf Items & Inset Groups (`.card-theme`)**:
  - Applied **only to the inner items or grouped control rows** (e.g., an individual exercise item, an inset list of `Sets` / `Reps` / `Weight` rows, or a standalone widget).
  - Uses solid tonal surface (`--bg-surface`), subtle `1px` border (`--border-subtle`), rounded corners (`16px`), and compact mobile padding (`p-3.5 sm:p-5`).
  - **No Double-Nesting Rule**: Never place a bordered `.card-theme` or bordered sub-panel inside another `.card-theme` on mobile. Separate rows inside an item using hairline horizontal dividers (`divide-y divide-[var(--border-subtle)]`).
- **Liquid Glass Chrome (`.surface-glass`)**: Translucent background (`--bg-glass`), `backdrop-filter: blur(28px) saturate(200%)`, and a subtle specular border highlight (`--border-glass-specular`) that mimics light catching a frosted glass edge.

### Typography & Hierarchy
- **Font Stack**: Clean geometric/humanist sans-serif (`Plus Jakarta Sans`, `-apple-system`, `SF Pro Display`, system-ui).
- **Restrained Scale**: Use font weight (`500` medium, `600` semibold, `700` bold) and tonal text color (`--text-primary`, `--text-secondary`, `--text-muted`) to create hierarchy—never gradient text or decorative all-caps badges unless functionally necessary.
- **Tabular Numerals**: Always use `font-variant-numeric: tabular-nums` on sets, reps, weights, and countdown timers so numbers never jitter when incremented.

### Gym Usability & Touch Targets
- **44x44px Minimum**: Every interactive button, stepper (`+`/`-`), checkbox, and navigation link must have a minimum hit area of `44x44px`.
- **Vertically Stacked Exercise Prescriptions**: When adding or editing exercises (`Sets`, `Reps`, `Weight (kg)`), stack the controls vertically in full-width inset rows rather than cramming multiple steppers side-by-side horizontally. This guarantees numbers remain clearly legible on mobile screens.
- **Calm, Focused Layouts**: Single-column vertical flow on mobile (`9:16` proportion). Group related controls cleanly inside inset cards with clear dividers so the user can log sets mid-workout with zero cognitive load.

