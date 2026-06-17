# QuickApply — Brand Identity & Design System

**Version:** 1.0
**Date:** 2026-06-17
**Status:** Draft for review

---

## 1. Brand Overview

### 1.1 What is QuickApply

QuickApply is a SaaS platform that eliminates the repetitive pain of filling out job application forms. Users upload their CV once, and QuickApply automatically detects forms on any job portal, maps fields to their profile, and fills them in seconds — with AI-powered smart matching and full user control.

### 1.2 Brand Concept: "Velocity with Precision"

QuickApply is about **speed without chaos**. The brand conveys that complex tasks can be done effortlessly, like a well-oiled machine. The blue palette communicates **trust, intelligence, and professionalism** — critical for a tool handling personal career data. The lightning bolt motif reinforces **instant action**, while the document/form elements ground the brand in its core function.

### 1.3 Brand Personality

- **Efficient** — Gets to the point, no wasted words or pixels
- **Trustworthy** — Handles sensitive career data; must feel secure
- **Modern** — Clean, minimal, premium SaaS aesthetic
- **Empowering** — Makes the user feel in control, not overwhelmed
- **Smart** — AI-powered, but never intimidating

### 1.4 Brand Voice

- **Tone:** Confident, concise, helpful
- **Avoid:** Corporate jargon, excessive exclamation marks, patronizing language
- **Example headline:** "Your next application, filled in seconds."
- **Example CTA:** "Start filling" (not "Get started now!!!")

---

## 2. Logo System

### 2.1 Primary Logo

The primary logo combines the **icon mark** (document + lightning bolt) with the **wordmark** ("QuickApply").

- **"Quick"** — Bold weight (800), dark slate (`#1e293b`) — conveys speed, strength
- **"Apply"** — Regular weight (400), blue (`#3b82f6`) — conveys the action, approachable
- **Tagline:** "FILL FORMS IN SECONDS" — uppercase, tracked, muted gray

**File:** `docs/branding/logo-quickapply.svg`

### 2.2 Icon Mark

A standalone icon for favicons, extension icons, app tiles, and social profiles.

- Rounded document shape with folded corner
- Three form lines (representing fields to fill)
- Lightning bolt centered, overlapping the document
- Gradient from deep blue (`#1e40af`) to vibrant blue (`#3b82f6`)
- Lightning bolt has a subtle glow effect

**File:** `docs/branding/logo-icon.svg`

### 2.3 Logo Variations

| Variant | Use case | File |
|---|---|---|
| Primary (icon + wordmark) | Website header, landing page, docs | `logo-quickapply.svg` |
| Icon only | Favicon, extension icon, social avatar | `logo-icon.svg` |
| Wordmark only | Text-heavy contexts, email signatures | Text rendering of "QuickApply" |
| Monochrome (white) | Dark backgrounds, overlays | White version of icon |
| Monochrome (dark) | Light backgrounds, print | Dark version of icon |

### 2.4 Logo Clear Space

Maintain minimum clear space around the logo equal to **50% of the icon height** on all sides. No text, graphics, or UI elements may encroach on this space.

### 2.5 Minimum Sizes

| Variant | Minimum width |
|---|---|
| Primary logo | 140px |
| Icon only | 24px |
| Wordmark only | 100px |

---

## 3. Color System

### 3.1 Brand Palette

The primary palette is **blue-only**, ranging from deep navy to bright sky blue. This monochromatic approach conveys trust, intelligence, and focus.

| Token | Hex | RGB | Usage |
|---|---|---|---|
| `blue-950` | `#172554` | 23, 37, 84 | Dark text on light, deep backgrounds |
| `blue-900` | `#1e3a8a` | 30, 58, 138 | Hover states, dark accents |
| `blue-800` | `#1e40af` | 30, 64, 175 | Icon gradient start, primary dark |
| `blue-700` | `#1d4ed8` | 29, 78, 216 | Interactive elements, focus rings |
| `blue-600` | `#2563eb` | 37, 99, 235 | Links, active states |
| `blue-500` | `#3b82f6` | 59, 130, 246 | **Primary brand color**, CTAs, icon gradient end |
| `blue-400` | `#60a5fa` | 96, 165, 250 | Lightning bolt, hover accents |
| `blue-300` | `#93c5fd` | 147, 197, 253 | Bolt highlight, subtle fills |
| `blue-200` | `#bfdbfe` | 191, 219, 254 | Light backgrounds, borders |
| `blue-100` | `#dbeafe` | 219, 234, 254 | Card backgrounds, hover tints |
| `blue-50` | `#eff6ff` | 239, 246, 255 | Page background, surface |

### 3.2 Neutral Palette

| Token | Hex | Usage |
|---|---|---|
| `slate-900` | `#0f172a` | Primary text |
| `slate-700` | `#334155` | Secondary text |
| `slate-500` | `#64748b` | Tertiary text, placeholders |
| `slate-300` | `#cbd5e1` | Borders, dividers |
| `slate-200` | `#e2e8f0` | Subtle borders |
| `slate-100` | `#f1f5f9` | Surface backgrounds |
| `slate-50` | `#f8fafc` | Page background |
| `white` | `#ffffff` | Cards, modals, elevated surfaces |

### 3.3 Semantic Colors

| Token | Hex | Usage |
|---|---|---|
| `success` | `#22c55e` | Field resolved, form complete |
| `warning` | `#f59e0b` | Field needs review, partial confidence |
| `error` | `#ef4444` | Failed resolution, validation errors |
| `info` | `#3b82f6` | Informational messages (same as primary) |

### 3.4 Gradient System

| Name | From | To | Angle | Usage |
|---|---|---|---|---|
| Primary | `#1e40af` | `#3b82f6` | 135deg | Logo, hero backgrounds, CTA buttons |
| Subtle | `#eff6ff` | `#dbeafe` | 180deg | Page backgrounds, card hover |
| Glow | `#3b82f6` | `#60a5fa` | 0deg | Icon glow, sparkle effects |

### 3.5 Opacity Variants

| Opacity | Use case |
|---|---|
| 100% | Primary elements, text |
| 80% | Secondary text, icons |
| 60% | Placeholder text |
| 40% | Disabled states |
| 20% | Borders, subtle dividers |
| 10% | Background tints, hover overlays |
| 5% | Very subtle backgrounds |

---

## 4. Typography

### 4.1 Font Family

| Role | Family | Fallback | Usage |
|---|---|---|---|
| **Display / Headlines** | Inter | SF Pro Display, -apple-system, sans-serif | Hero sections, marketing pages |
| **Body / UI** | Inter | SF Pro Text, -apple-system, sans-serif | All body text, form labels, UI elements |
| **Code / Monospace** | JetBrains Mono | Fira Code, monospace | Code snippets, technical values |

**Why Inter?** It's the gold standard for SaaS: excellent legibility at all sizes, variable font support, free, and has a neutral-professional feel that lets the blue brand color dominate.

### 4.2 Type Scale

| Level | Size | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|
| Display XL | 48px / 3rem | 800 | 1.1 | -0.02em | Hero headline |
| Display | 36px / 2.25rem | 800 | 1.15 | -0.015em | Section headlines |
| H1 | 30px / 1.875rem | 700 | 1.2 | -0.01em | Page title |
| H2 | 24px / 1.5rem | 700 | 1.25 | -0.005em | Section title |
| H3 | 20px / 1.25rem | 600 | 1.3 | 0 | Subsection title |
| Body | 16px / 1rem | 400 | 1.5 | 0 | Default body text |
| Body Small | 14px / 0.875rem | 400 | 1.5 | 0 | Secondary text, labels |
| Caption | 12px / 0.75rem | 500 | 1.4 | 0.01em | Metadata, timestamps |
| Overline | 11px / 0.6875rem | 600 | 1.3 | 0.08em | Tagline, category labels |

### 4.3 Type Rules

- **Headlines:** Always tight letter-spacing (-0.02em to -0.005em) for impact
- **Body:** Never smaller than 14px for readability
- **Line length:** Max 65-75 characters per line for body text
- **Weight contrast:** Pair bold headlines (700-800) with regular body (400) for clear hierarchy

---

## 5. Spacing & Layout

### 5.1 Spacing Scale

Based on a **4px base unit**:

| Token | Value | Usage |
|---|---|---|
| `space-0.5` | 2px | Tight inline spacing |
| `space-1` | 4px | Icon padding, micro gaps |
| `space-2` | 8px | Compact element spacing |
| `space-3` | 12px | Form field gaps |
| `space-4` | 16px | Standard element spacing |
| `space-5` | 20px | Card padding |
| `space-6` | 24px | Section internal spacing |
| `space-8` | 32px | Section gaps |
| `space-10` | 40px | Large section spacing |
| `space-12` | 48px | Page section margins |
| `space-16` | 64px | Major section breaks |
| `space-20` | 80px | Hero section padding |

### 5.2 Grid System

| Property | Value |
|---|---|
| Columns | 12 |
| Gutter | 24px |
| Max width | 1200px |
| Side padding (mobile) | 16px |
| Side padding (desktop) | 32px |

### 5.3 Breakpoints

| Name | Width | Behavior |
|---|---|---|
| `sm` | ≥640px | Single column, stacked layout |
| `md` | ≥768px | Two-column layout possible |
| `lg` | ≥1024px | Full dashboard layout, sidebar |
| `xl` | ≥1280px | Max-width container, generous whitespace |

---

## 6. Borders & Shadows

### 6.1 Border Philosophy

QuickApply uses a **layered elevation system** — surfaces are differentiated by subtle shadows rather than heavy borders. Borders are used sparingly for structure; shadows create depth and hierarchy.

### 6.2 Border Radius

| Token | Value | Usage |
|---|---|---|
| `radius-sm` | 6px | Buttons, inputs, small elements |
| `radius-md` | 10px | Cards, modals |
| `radius-lg` | 16px | Large cards, hero sections |
| `radius-xl` | 24px | Feature cards, promotional elements |
| `radius-full` | 9999px | Pills, badges, avatars |

### 6.3 Shadows

| Level | Value | Usage |
|---|---|---|
| `shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift for inputs, buttons |
| `shadow-md` | `0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)` | Cards, dropdowns |
| `shadow-lg` | `0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04)` | Modals, elevated panels |
| `shadow-xl` | `0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.05)` | Popovers, floating elements |
| `shadow-blue` | `0 4px 14px rgba(59,130,246,0.25)` | CTA buttons, active states (blue glow) |

---

## 7. Components

### 7.1 Buttons

| Variant | Background | Text | Border | Radius | Usage |
|---|---|---|---|---|---|
| **Primary** | `blue-500` | white | none | `radius-sm` | Main CTAs, form submission |
| **Primary Hover** | `blue-700` | white | none | `radius-sm` | Hover state |
| **Secondary** | white | `blue-600` | `blue-300` | `radius-sm` | Secondary actions |
| **Ghost** | transparent | `blue-600` | none | `radius-sm` | Tertiary actions, nav |
| **Danger** | `error` | white | none | `radius-sm` | Destructive actions |

**Sizes:**
- `sm`: height 32px, padding 8px 16px, font 14px
- `md`: height 40px, padding 10px 20px, font 14px
- `lg`: height 48px, padding 12px 24px, font 16px

**States:**
- Default: solid background
- Hover: darker shade, `shadow-blue` for primary
- Active: even darker, slight scale-down (0.98)
- Focus: 2px `blue-500` ring with 2px offset
- Disabled: `slate-200` bg, `slate-400` text, no pointer

### 7.2 Form Inputs

| Property | Value |
|---|---|
| Height | 40px |
| Padding | 10px 14px |
| Border | 1px solid `slate-300` |
| Border radius | `radius-sm` (6px) |
| Background | white |
| Text | `slate-900`, 14px |
| Placeholder | `slate-500`, 14px |
| Focus border | `blue-500` |
| Focus ring | `0 0 0 3px rgba(59,130,246,0.15)` |
| Error border | `error` |
| Error text | `error`, 12px below input |
| Success border | `success` |

### 7.3 Cards

| Property | Value |
|---|---|
| Background | white |
| Border | 1px solid `slate-200` |
| Border radius | `radius-md` (10px) |
| Padding | `space-6` (24px) |
| Shadow | `shadow-md` |
| Hover shadow | `shadow-lg` |
| Hover border | `blue-200` |

### 7.4 Navigation

| Property | Value |
|---|---|
| Height | 64px |
| Background | white with 80% opacity + `backdrop-blur-md` |
| Border bottom | 1px solid `slate-200` |
| Logo size | 140px wide |
| Nav items | 14px, weight 500, `slate-700` |
| Active item | `blue-600`, bottom border 2px |

### 7.5 Badges / Tags

| Variant | Background | Text | Usage |
|---|---|---|---|
| Default | `slate-100` | `slate-700` | Neutral labels |
| Blue | `blue-100` | `blue-700` | Active states, categories |
| Success | `green-100` | `green-700` | Resolved fields, complete |
| Warning | `amber-100` | `amber-700` | Needs review |
| Error | `red-100` | `red-700` | Failed, errors |

**Shape:** `radius-full` (pill), padding 4px 10px, font 12px weight 500.

### 7.6 Modals

| Property | Value |
|---|---|
| Overlay | `rgba(0,0,0,0.4)` with `backdrop-blur-sm` |
| Container | white, `radius-lg`, `shadow-xl` |
| Max width | 480px (sm), 640px (md), 800px (lg) |
| Padding | `space-8` (32px) |
| Close button | top-right, `slate-400`, hover `slate-600` |

---

## 8. Iconography

### 8.1 Icon Set

Use **Lucide Icons** (lucide.dev) — clean, consistent, open-source, MIT licensed.

**Primary icons used:**

| Icon | Name | Context |
|---|---|---|
| ⚡ | `zap` | Lightning bolt, speed, fill action |
| 📄 | `file-text` | Document, CV, form |
| ✅ | `check-circle` | Resolved field, success |
| ⏳ | `clock` | Processing, pending |
| ❌ | `x-circle` | Failed, error |
| 🔒 | `lock` | Security, encrypted |
| 👤 | `user` | Profile, account |
| ⚙️ | `settings` | Configuration |
| 📊 | `bar-chart` | Analytics, progress |
| 🔍 | `search` | Detection, scanning |

### 8.2 Icon Sizing

| Context | Size | Stroke width |
|---|---|---|
| Inline with text | 16px | 2px |
| Button left icon | 18px | 2px |
| Standalone | 24px | 1.5px |
| Feature highlight | 32px | 1.5px |
| Hero / empty state | 48px | 1.25px |

### 8.3 Icon Color

- Icons inherit text color by default
- Use `blue-500` for primary action icons
- Use semantic colors (success, warning, error) for status icons

---

## 9. Animation & Motion

### 9.1 Motion Principles

- **Purposeful** — Every animation communicates a state change
- **Quick** — 150-300ms for most transitions (feels snappy, not sluggish)
- **Smooth** — Use `ease-out` for entrances, `ease-in` for exits
- **Respectful** — Honor `prefers-reduced-motion: reduce`

### 9.2 Transition Durations

| Context | Duration | Easing |
|---|---|---|
| Button hover | 150ms | `ease-out` |
| Input focus | 150ms | `ease-out` |
| Card hover | 200ms | `ease-out` |
| Modal enter | 250ms | `ease-out` |
| Modal exit | 200ms | `ease-in` |
| Page transition | 300ms | `ease-in-out` |
| Tooltip enter | 150ms | `ease-out` |
| Skeleton pulse | 1.5s | `ease-in-out` infinite |

### 9.3 Micro-interactions

- **Button press:** scale down to 0.98 on `:active`, return on release
- **Card hover:** shadow elevates from `md` to `lg`, border shifts to `blue-200`
- **Field resolved:** brief green pulse on the check icon
- **Progress fill:** smooth width transition with `ease-out`
- **Banner slide-in:** translate from bottom 20px → 0, opacity 0 → 1, 300ms

### 9.4 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 10. Accessibility

### 10.1 Color Contrast

| Pair | Ratio | WCAG Level |
|---|---|---|
| `slate-900` on white | 15.4:1 | AAA |
| `slate-700` on white | 8.5:1 | AAA |
| `blue-600` on white | 5.2:1 | AA |
| `blue-500` on white | 4.6:1 | AA (large text only) |
| white on `blue-500` | 4.6:1 | AA |
| white on `blue-700` | 7.2:1 | AAA |

### 10.2 Focus Management

- All interactive elements have visible focus indicators
- Focus ring: 2px solid `blue-500` with 2px offset
- Skip-to-content link as first focusable element
- Focus trap in modals

### 10.3 ARIA Patterns

- All form inputs have associated `<label>` elements
- Error messages linked via `aria-describedby`
- Loading states announced with `aria-live="polite"`
- Progress bars use `role="progressbar"` with `aria-valuenow`

---

## 11. Do's & Don'ts

### Do

- ✅ Use `blue-500` as the primary action color — it's the brand
- ✅ Pair bold headlines (700-800) with regular body (400)
- ✅ Use shadows for elevation, not heavy borders
- ✅ Keep card padding consistent at 24px
- ✅ Use Inter for all UI text
- ✅ Test all color combinations for WCAG AA contrast
- ✅ Use `radius-sm` (6px) for interactive elements, `radius-md` (10px) for containers
- ✅ Animate with purpose — every transition communicates something

### Don't

- ❌ Use colors outside the blue palette for brand elements
- ❌ Use font sizes below 14px for body text
- ❌ Mix multiple font families in the same view
- ❌ Use shadows AND heavy borders on the same element
- ❌ Animate without respecting `prefers-reduced-motion`
- ❌ Use `blue-500` for large background fills (too intense — use `blue-50` or `blue-100`)
- ❌ Place text on `blue-500` backgrounds without checking contrast
- ❌ Use more than 3 font weights in a single view

---

## 12. CSS Custom Properties

```css
:root {
  /* Brand Blues */
  --blue-50: #eff6ff;
  --blue-100: #dbeafe;
  --blue-200: #bfdbfe;
  --blue-300: #93c5fd;
  --blue-400: #60a5fa;
  --blue-500: #3b82f6;
  --blue-600: #2563eb;
  --blue-700: #1d4ed8;
  --blue-800: #1e40af;
  --blue-900: #1e3a8a;
  --blue-950: #172554;

  /* Neutrals */
  --slate-50: #f8fafc;
  --slate-100: #f1f5f9;
  --slate-200: #e2e8f0;
  --slate-300: #cbd5e1;
  --slate-500: #64748b;
  --slate-700: #334155;
  --slate-900: #0f172a;

  /* Semantic */
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;

  /* Typography */
  --font-sans: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
  --space-16: 64px;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
  --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.05);
  --shadow-blue: 0 4px 14px rgba(59,130,246,0.25);

  /* Transitions */
  --transition-fast: 150ms ease-out;
  --transition-base: 200ms ease-out;
  --transition-slow: 300ms ease-in-out;
}
```

---

## 13. File Structure

```
docs/branding/
├── BRANDING.md              # This document
├── logo-quickapply.svg      # Primary logo (icon + wordmark)
├── logo-icon.svg            # Icon only (favicon, extension)
├── logo-wordmark.svg        # Wordmark only (text contexts)
├── logo-white.svg           # White version for dark backgrounds
└── palette.svg              # Visual color palette reference
```

---

## 14. Implementation Notes

### For the Chrome Extension

- The extension icon should use `logo-icon.svg` at 16px, 48px, and 128px
- The popup should use the blue gradient system from the existing `epic-design` implementation
- All extension UI should use the CSS custom properties defined above
- The banner (Shadow DOM) should inherit the blue palette

### For the SaaS Landing Page

- Hero section: `blue-50` background, primary logo, Display XL headline
- CTA buttons: Primary variant with `shadow-blue` on hover
- Feature cards: white background, `shadow-md`, `radius-md`
- Footer: `slate-900` background, white text

### For Marketing Materials

- Always use the primary logo on white or `blue-50` backgrounds
- For dark backgrounds, use the white variant
- Minimum logo size: 140px wide (primary), 24px (icon)
- Never stretch, rotate, or add effects to the logo

---

*This document is the single source of truth for QuickApply's visual identity. Any new component, page, or material must follow these guidelines. If something isn't covered here, default to the existing patterns in the codebase.*
