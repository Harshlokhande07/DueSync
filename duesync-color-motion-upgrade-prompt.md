# DueSync: Vibrant Color & Motion Upgrade Prompt

> **For:** Google Antigravity (agent-first IDE)
> **Task type:** Visual polish pass on the existing, working `index.html`. Do **not** rebuild the app.
> **Attach in chat:** (1) the 4 reference UI images, (2) the 2 screenshots of the current DueSync interface
> **Goal:** richer, more beautiful colors in the style of the reference images, plus smooth, tasteful animations throughout

---

## 0. Instructions for the Agent

1. **Look at the current-interface screenshots and the 4 reference images side by side.** Write a short "Gap Analysis" artifact listing exactly what makes the current build feel flatter than the references (Section 1).
2. **Edit the existing file in place.** All behavior, data, urgency logic, storage, search, filters, sorting, and accessibility must remain exactly as they are. This pass changes only **appearance and motion**.
3. Move every color, radius, shadow, duration, and easing into **CSS variables** at the top of the file so the whole theme can be tuned in one place.
4. Implement the color system (Section 2), layout touch-ups (Section 3), and animation system (Section 4).
5. **Verify** at 390×844, 768×1024, and 1440×900 with the browser agent: capture a before/after screenshot pair for each, and record a short screen capture or a frame sequence of the main animations.
6. Run the regression checklist (Section 6) and fix every issue found.
7. Finish with a Walkthrough artifact (what changed, before/after, test results).

**Do not copy any reference screen, illustration, or text.** Take the *color mood and motion quality* only.

---

## 1. What to Fix (Gap Analysis starting points)

The current build is clean and functional, but compared with the references it looks:

| Observation | Fix |
|---|---|
| **Everything sits on one beige tone** (page, cards, tabs, completed cards). Low contrast between layers, so it feels flat. | Give the page a soft colorful backdrop and make cards crisp white so they pop (Section 2.2). |
| **Pastels are muted and slightly grey** (dull peach, sage, dusty pink). | Use fresher, more saturated pastels with a clear accent for each status (Section 2.1). |
| **Dark forest-green is used for everything** (button, tabs, ring, logo accent). | Introduce a lively multi-color system: teal, coral, sunny yellow, violet, and mint, each with one job. |
| **The hero completion card is the same pale style as other cards.** | Make it a bold, color-blocked hero panel like the "Learning progress" and "78%" references (Section 3.1). |
| **Completed cards look almost identical to active ones.** | Desaturate and cool them so active work clearly stands out. |
| **The logo is a generic blue app icon image.** | Replace it with a clean inline SVG logo mark in the brand colors. |
| **No motion at all.** | Add the animation system in Section 4. |

---

## 2. Color System

### 2.1 Brand & status palette (replace the current tokens)

Inspired by the references: coral-pink, teal, sunny yellow, cream, lavender, and mint.

| Token | Hex | Role |
|---|---|---|
| `--ink` | `#1E1B2E` | Primary text (deep blue-violet black, not pure black) |
| `--ink-muted` | `#6A6682` | Secondary text |
| `--teal` | `#1F8A7D` | Brand primary (logo, links, focus ring, Total/Completed accents) |
| `--teal-deep` | `#14645B` | Hero panel and strong teal surfaces |
| `--sun` | `#FFC53D` | Main call-to-action button and highlights (dark ink text on top) |
| `--sun-soft` | `#FFF1C6` | Yellow tints |
| `--coral` | `#F2546F` | Critical / overdue accent |
| `--coral-soft` | `#FFDDE3` | Critical tint |
| `--amber` | `#F59E0B` | Approaching accent |
| `--amber-soft` | `#FFE9BD` | Approaching tint |
| `--mint` | `#2FC48D` | Safe / success accent |
| `--mint-soft` | `#D3F6E6` | Safe tint |
| `--violet` | `#7C6CF2` | Total Active / info accent |
| `--violet-soft` | `#E5E0FF` | Total Active tint |
| `--sky-soft` | `#DAEEFF` | Optional info tint |
| `--surface` | `#FFFFFF` | Cards, toolbar, modals |
| `--border` | `#ECE8F4` | Hairline borders |

**Status mapping (unchanged meaning, new colors):**

| Status | Accent | Tint | Icon |
|---|---|---|---|
| Overdue / Due Today (Critical) | `--coral` | `--coral-soft` | alert-triangle |
| Approaching Soon | `--amber` | `--amber-soft` | hourglass |
| Plenty of Time (Safe) | `--mint` | `--mint-soft` | leaf / check-circle-2 |
| Completed | `--ink-muted` with a mint check | cool grey `#EEF0F6` | check-check |

**Contrast rules (important):**
- Small text must meet **WCAG AA 4.5:1**; large bold text (24px+ or 18.66px+ bold) must meet 3:1. Run a contrast check on every text/background pair and **adjust ink shades, never remove labels**.
- Use **dark ink text on yellow and light tints**. Use **white text only on `--teal-deep`, `--teal`, and other dark fills**.
- Status is always **color + text label + icon**.

### 2.2 Backgrounds & surfaces
- **Page background:** a soft pastel gradient, `linear-gradient(135deg, #F7EEFF 0%, #FFF1EA 45%, #EAFBF4 100%)`, fixed. On top, add 2-3 large, heavily blurred color blobs (lavender, peach, mint) at low opacity, positioned behind the content (pure CSS, `pointer-events: none`). They must never reduce text legibility.
- **Cards and toolbar:** pure white with a 1px `--border` and a soft colored shadow, for example `0 10px 30px -12px rgba(124,108,242,.25)`.
- **Completed cards:** cool grey tint, reduced saturation, title struck through, and a mint check chip.

### 2.3 Buttons
| Button | Style |
|---|---|
| **+ Add Deadline** (main CTA) | `--sun` yellow fill, `--ink` text, bold, soft yellow glow shadow (like the yellow CTAs in the references) |
| Complete | `--mint-soft` fill, dark green text, mint check icon |
| Restore | `--sun-soft` fill, dark amber text |
| Edit / Delete icons | Neutral by default; Edit tints violet on hover, Delete tints coral on hover |
| Active filter tab | `--teal-deep` fill, white text. Inactive tabs are white with a border |

---

## 3. Layout & Component Touch-ups

### 3.1 Hero completion card (bold color block)
- Solid `--teal-deep` panel (optionally with a subtle teal-to-teal gradient), white text.
- A thick-stroke progress ring in `--sun` yellow over a translucent white track, with the large percentage in white inside or beside it.
- Supporting line ("3 of 11 deadlines done") and the "View Done" link in white / light teal.
- Add a small decorative cluster of soft circles in the corner (CSS only) for depth, as in the references. Keep text on flat color for readability.

### 3.2 Metric tiles
Four tiles, each with a vivid soft tint, a **solid-color round icon chip** (white icon on the accent color), and a large number:

| Tile | Tint | Chip |
|---|---|---|
| Active | `--violet-soft` | `--violet` |
| Approaching | `--amber-soft` | `--amber` |
| Critical | `--coral-soft` | `--coral` |
| Completed | `--mint-soft` | `--mint` |

### 3.3 "Next 7 Days" chart
- Line in `--coral` (or a coral-to-violet gradient stroke), smooth curve, soft gradient fill underneath.
- Points are white circles with a colored stroke. **Today** is a filled, pulsing point.
- Hover / focus shows a dark rounded tooltip bubble with the count (like the "78%" bubble in the reference).

### 3.4 Task cards
- White card, 24px radius, **6px left bar** in the status accent color.
- Countdown strip uses the status tint, a large bold tabular-number countdown, and an accent-colored clock icon.
- Priority pills: Low = soft grey, Medium = amber tint, High = coral tint.
- Subject chips use `--violet-soft` or `--sky-soft` instead of the current green, so they do not compete with the status colors.

### 3.5 Logo
Replace the current image with an inline SVG: a rounded square in a teal-to-violet gradient containing a white clock/hourglass mark, with a small yellow dot accent.

### 3.6 Mobile
Keep the existing mobile structure. Apply the same colors, and make the bottom navigation (if present) a white floating pill with a yellow raised "+" button and a violet/teal active indicator.

---

## 4. Animation System

**Rules for all animation:**
- Pure **CSS + vanilla JS**. No animation libraries.
- Animate **`transform` and `opacity` only** where possible (smooth at 60fps). Avoid animating layout properties except for the delete-collapse.
- Keep it **tasteful**: nothing flashes, nothing loops aggressively, nothing blocks interaction.
- Define timing tokens: `--dur-fast: 150ms`, `--dur-base: 250ms`, `--dur-slow: 450ms`, `--ease-out: cubic-bezier(.22,1,.36,1)`, `--ease-spring: cubic-bezier(.34,1.56,.64,1)`.
- **Respect `prefers-reduced-motion: reduce`:** disable movement, looping, count-ups, and particles (keep instant state changes or very short opacity fades). Provide a single `prefersReducedMotion()` helper for JS animations.
- Do **not** replay entrance animations on every 60-second refresh. Only elements whose values changed animate.

### 4.1 Page load (entrance)
- Staggered **fade-up** (translateY 16px → 0, opacity 0 → 1, 450ms, ease-out) in this order: header → heading → metric tiles → hero + chart → toolbar → task cards. Stagger by 60-80ms, capped so the whole sequence finishes in under 1.2s.
- Use `IntersectionObserver` so cards below the fold reveal as they scroll into view (once per element).

### 4.2 Numbers & rings
- **Count-up** on the four metric numbers and the completion percentage: about 800ms, ease-out-cubic, starting from 0 on first load and from the **previous value** on later changes.
- **Ring draw:** animate `stroke-dashoffset` from empty to the current value (about 1s, ease-out). It re-animates smoothly to the new value when the percentage changes.
- **Countdown tick:** when the minute value changes on the 60-second refresh, the changed digits do a quick fade/slide (150ms). Unchanged digits do not move.

### 4.3 Chart
- On first reveal: the line **draws itself** (stroke-dasharray, about 900ms), the area fill fades in, and points pop in one by one (spring).
- Hover / focus on a point: it scales up 1.4× and the tooltip bubble glides to it (150ms) with a small arrow.
- The "Today" point has a soft expanding **pulse ring** (2.4s loop, low opacity).
- When data changes, the line morphs smoothly (or cross-fades) instead of jumping.

### 4.4 Cards & lists
- **Hover (laptop):** lift 3px, shadow deepens, the left accent bar grows slightly. **Press:** scale to 0.98.
- **Search / filter / sort changes:** reordering uses a **FLIP animation** (cards glide to their new positions, 250ms). Cards entering fade-scale in from 0.96, and cards leaving fade out.
- **Add:** the new card slides in from the top of its position and shows a 1.2s soft glow in its accent color.
- **Delete (after confirm):** the card scales to 0.96 and fades, then its height collapses (250ms) while neighbors glide up.
- **Complete:** the check icon **draws itself** (stroke animation, 350ms), the card flashes a brief mint wash, the title strike-through sweeps left to right, and the card glides to its new position. Add a **lightweight confetti burst** (about 14 small particles in teal, yellow, coral, violet, and mint, drawn as absolutely positioned elements, removed after 900ms). Skip this under reduced motion.
- **Restore:** a quick reverse with a gentle spring bounce on the card.

### 4.5 Urgency micro-motion (subtle)
- **Critical / Overdue icon chip:** a soft expanding ring pulse, 2.4s loop, low opacity, never more than a gentle breathing effect. No shaking and no flashing.
- **Approaching and Safe:** no looping animation.

### 4.6 Navigation, tabs & controls
- **Filter tabs:** a single sliding "active pill" element glides (250ms, ease-out) between tabs, and the count badge does a small pop when its number changes.
- **Add Deadline button:** subtle animated shine sweep across the button every ~6s (paused on hover and under reduced motion), the `+` icon rotates 90° on hover, and the button presses down on click.
- **Icon buttons:** a gentle wiggle or nudge on hover (Edit tilts, Delete shakes slightly once).
- **Search field:** the border and shadow smoothly transition to a focus glow, and the clear (×) button fades and scales in.
- **Sort dropdown / inputs:** smooth focus ring transition.
- **Summary pill sparkle:** the sparkle icon twinkles slowly (scale + opacity, 3s loop).
- **Mobile bottom nav (if present):** the active indicator slides between items, and the "+" button bounces on press.

### 4.7 Modal, dialogs & toasts
- **Add / Edit modal:** the backdrop fades in (200ms) with a slight blur. On laptop, the dialog scales from 0.96 and fades with the spring easing. On mobile, the bottom sheet slides up from the bottom and can fade/slide down on close. The first field gets focus **after** the animation starts, and focus return is unchanged.
- **Inline validation errors:** slide down and fade in, and the invalid field does a single small horizontal shake (once, 300ms).
- **Delete confirm dialog:** the same scale-in with a short coral glow on the icon chip.
- **Toasts:** slide in from the bottom (spring), have a thin progress bar that shrinks over the display time, and fade out. Multiple toasts stack and re-flow smoothly.

### 4.8 Background & empty states
- The blurred background blobs **drift slowly** (about 25-35 s loops, transform only). Pause them when the tab is hidden or under reduced motion.
- **Empty-state illustration:** gently floats up and down (4s ease-in-out loop), and its button has the same shine as the main CTA.

---

## 5. Performance & Quality Rules

- Total added JavaScript for animation should stay small and readable, in clearly labeled functions (for example `animateCount`, `animateRing`, `flipList`, `burstConfetti`, `prefersReducedMotion`).
- No layout thrashing: batch reads and writes, and use `requestAnimationFrame` for JS-driven animations.
- No `will-change` on more than a handful of elements, and remove it after animations finish.
- Keep 60fps on a mid-range phone with 50+ tasks (test with a generated large list).
- No new dependencies. Tailwind CDN and Lucide only, as before.
- Do not introduce console errors or warnings.

---

## 6. Regression & QA Checklist

**Look**
- [ ] The page background is a soft colorful gradient, and cards are white and clearly separated from it
- [ ] The hero completion card is a bold teal block with a yellow ring
- [ ] The four metric tiles use violet, amber, coral, and mint with solid icon chips
- [ ] Task cards use the new accents, completed cards are visibly cooler and calmer, and the logo is an inline SVG
- [ ] All text and background pairs pass the contrast check (list any adjustments)
- [ ] Status is shown by color + label + icon everywhere

**Motion**
- [ ] The staggered entrance runs once, in under 1.2s
- [ ] Count-ups and ring draw work on first load and animate from the previous value on later changes
- [ ] The chart draws, the tooltip glides, and Today pulses
- [ ] Filter, sort, and search reorder smoothly (FLIP), and add / complete / restore / delete each animate correctly
- [ ] The critical icon pulse is subtle, and nothing flashes
- [ ] The modal, bottom sheet, dialogs, and toasts animate in and out, and focus management still works
- [ ] The 60-second refresh does **not** replay entrance animations
- [ ] With `prefers-reduced-motion: reduce`, movement, loops, count-ups, and confetti are off, and the app is fully usable
- [ ] Animations stay smooth with 50+ tasks

**Functionality (must be unchanged)**
- [ ] Add, edit, delete (with confirmation), complete, and restore all work and persist
- [ ] Search, all five filters, and all three sorts work together
- [ ] Urgency boundaries (24h, 5 days, overdue) are still correct
- [ ] No horizontal scroll at 320, 390, 768, and 1440px
- [ ] Keyboard navigation and screen-reader labels still work
- [ ] The console shows zero errors and zero warnings

---

## 7. Final Output

1. The updated `index.html` (same single file, upgraded visuals and motion)
2. Gap Analysis artifact
3. Before / after screenshots at 390px, 768px, and 1440px
4. A short screen capture or frame sequence showing the main animations (load, complete, add, delete, modal, filter change)
5. Walkthrough artifact with checklist results and any known limitations

**Final objective:** keep DueSync exactly as reliable as it is today, but make it feel alive and joyful: fresh coral, teal, yellow, violet, and mint colors on crisp white cards, bold color-blocked highlights, and smooth, meaningful motion that makes every action feel satisfying and every deadline easy to read.
