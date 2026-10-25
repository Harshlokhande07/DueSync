# DueSync: UI/UX Design Direction Prompt

> **For:** Google Antigravity (agent-first IDE)
> **Use together with:** `duesync-master-spec.md` (functionality, data, logic, tests)
> **Attach in chat:** the 4 reference UI images (Readly onboarding, Learning dashboard, Fitness/Health app, Wellness bento app)
> **Precedence:** where this document and the master spec disagree about **look and feel** (colors, radii, card style, layout, typography, charts), **this document wins**. Where they disagree about **behavior, data, or urgency rules**, the **master spec wins**.

---

## 0. Instructions for the Agent

1. **Study the 4 attached reference images first.** Before planning, write a short "Reference Analysis" artifact that names, in your own words, the shared visual traits you found (cards, color, radii, charts, navigation, type). Use it as the design brief for everything below.
2. **Do not copy any reference screen, layout, brand, illustration, or text.** The references set the *style and quality bar*. DueSync must have its own identity: its own layouts, its own icons, and its own copy.
3. Apply this design direction to **DueSync Web** (the single `index.html`), at mobile (390px), tablet (768px), and laptop (1440px) widths.
4. Make the **whole design system tokens-first** (CSS variables or a Tailwind config in the file), so colors, radii, and shadows are changed in one place.
5. After building, **compare your screenshots against the reference images** at each viewport and fix any gap in polish, spacing, or hierarchy. Attach the comparison to the Walkthrough artifact.
6. Functionality is never sacrificed for style. Every control stays real and working, text stays readable, and urgency is always shown by **color + label + icon**.

---

## 1. What the Reference Images Teach (design takeaways)

| Trait seen across all 4 references | How DueSync should apply it |
|---|---|
| **Soft pastel color blocking.** Peach, lavender, mint, butter-yellow, coral, and sky-blue panels on a calm, light backdrop. | Each metric and status gets its own pastel panel. Pastel fills carry meaning (urgency), not decoration. |
| **Very large corner radii** (about 24 to 32px) on cards, phone frames, and panels. | One consistent radius scale (Section 3.3). Nothing sharp. |
| **Bento-style grids** with tiles of different sizes that still align. | Metrics and the insight panels use an intentional asymmetric bento layout (Section 4). |
| **One big number** per hero card (for example "78%", "95%"), with small supporting labels. | A hero progress card with a large completion percentage. |
| **Thin, elegant line charts** with a highlighted point and a floating value bubble. | A "Next 7 days" line chart with a highlighted selected point (Section 4.4). |
| **Circular progress rings** and small round icon chips. | Completion ring and round icon chips on every tile. |
| **Bold, friendly, rounded sans-serif type** with a strong size hierarchy. | Section 3.2 typography. |
| **Floating pill bottom navigation** with a clear active state and a prominent action. | Mobile floating nav with a center "+" button (Section 5.3). |
| **Strong primary call-to-action** (one saturated button color on a quiet surface). | A single indigo primary for the main actions. |
| **Generous whitespace, clear grouping, and tidy alignment.** | Consistent 8px spacing rhythm and clear section titles. |

---

## 2. Design Personality

**Keywords:** calm, friendly, organized, motivating, modern, tactile.
**Feeling:** a premium student planner that makes a heavy workload feel manageable. It should feel like the reference apps (soft, rounded, colorful, clear), not like a spreadsheet and not like a gym or gaming app.

**Avoid:** harsh neon, dark cyber themes, heavy gradients, glassmorphism, dense tables, tiny text, clip-art illustrations, and visual clutter.

---

## 3. Design System

### 3.1 Color tokens (light theme)

**Base**

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#F4F3F9` | Page background (soft lavender-grey) |
| `--surface` | `#FFFFFF` | Cards, modals, inputs |
| `--surface-muted` | `#F8F7FC` | Subtle panels, tab backgrounds |
| `--border` | `#E8E6F0` | Hairline borders |
| `--ink` | `#1C1B2E` | Primary text |
| `--ink-muted` | `#6B6A80` | Secondary text |
| `--primary` | `#5B5BD6` | Primary buttons, focus rings, active states |
| `--primary-soft` | `#E6E4FB` | Primary tinted backgrounds |

**Pastel panels with matching accents (always paired)**

| Meaning | Panel fill | Accent (icons, borders, badges) | Text on panel |
|---|---|---|---|
| **Critical / Overdue** | Coral-pink `#FFDCDD` | Red `#E5484D` | Dark red-ink `#7A1F23` |
| **Approaching Soon** | Butter-peach `#FFE9C7` | Amber `#E8890C` | Dark amber-ink `#6B3E04` |
| **Safe / Plenty of Time** | Mint `#D6F3E3` | Green `#1F9D62` | Dark green-ink `#0F4D30` |
| **Total Active** | Lavender `#E4DFFC` | Indigo `#5B5BD6` | Deep indigo-ink `#2B2A6B` |
| **Completed** | Cool grey `#ECEBF2` | Green check `#1F9D62` | Muted ink `#6B6A80` |
| **Info / extra** | Sky `#DCEEFF` | Blue `#2F7BE0` | Deep blue-ink `#143D73` |

Rules:
- All text on pastel panels must meet **WCAG AA contrast** (check and adjust ink colors if needed).
- Urgency uses the Critical / Approaching / Safe rows **only**. Do not reuse those pastels for unrelated decoration.
- Red, amber, and green are always accompanied by a **text label and an icon**.

### 3.2 Typography

- **Font:** *Plus Jakarta Sans* (or *Inter* as fallback) via Google Fonts, with a system-font stack as the final fallback. Rounded, friendly, and highly legible, like the references.
- **Scale (mobile / laptop):**
  - Hero number: 48 / 64px, weight 800
  - Page heading: 26 / 34px, weight 800
  - Metric value: 30 / 36px, weight 800
  - Task title: 17 / 18px, weight 700
  - Countdown: 20 / 22px, weight 800, **tabular numerals**
  - Body / metadata: 14 / 15px, weight 500
  - Micro labels: 12px, weight 600, slightly increased letter spacing
- Minimum 16px for any text input on mobile (prevents iOS zoom).

### 3.3 Radius, spacing, elevation

| Element | Radius |
|---|---|
| Page panels, hero card, modals | 28px |
| Task cards, metric tiles | 24px |
| Inputs, buttons, dropdowns | 14px |
| Icon chips | 14px (square-ish) or fully round |
| Badges, tabs, toasts, bottom nav | Fully rounded (pill) |

- **Spacing:** 8px base unit. Card padding 16px (mobile) / 20-24px (laptop). Gap between cards 12px (mobile) / 16-20px (laptop).
- **Elevation:** soft, low-opacity shadows (for example `0 8px 24px rgba(28,27,46,.06)`), plus a 1px border. No heavy drop shadows.
- **Icons:** Lucide line icons, 2px stroke, placed inside round or rounded-square pastel **icon chips** (as in the references).

### 3.4 Motion

- 150-250ms ease-out transitions on hover, press, tab change, modal, and toast.
- Gentle count-up for the hero percentage and ring on first load only.
- Press states: slight scale-down (0.98) on buttons and cards.
- Respect `prefers-reduced-motion` (disable the count-up and the scale animations).

---

## 4. Screen Design: Laptop & Desktop (≥ 1024px)

Centered container, max width about 1240px, generous margins on a `--bg` canvas.

### 4.1 Header (sticky)
Round gradient-free logo chip (clock icon in indigo on lavender), **DueSync**, tagline "Stay ahead of every deadline.", live date pill, and a prominent **+ Add Deadline** primary button.

### 4.2 Welcome row
Heading "Your deadlines, under control." with supporting text, and a small summary pill (for example "3 active · next due in 7h 42m").

### 4.3 Metric bento (4 tiles)
Four pastel tiles in one row. Each tile: round icon chip, big number, label, and a tiny supporting line.

| Tile | Fill | Icon |
|---|---|---|
| Total Active | Lavender | calendar |
| Approaching Soon | Butter-peach | hourglass / clock |
| Urgent / Overdue | Coral-pink | alert-triangle |
| Completed | Mint | check-circle |

### 4.4 Insight row (two panels, new visuals, all derived from the user's real tasks)

1. **Completion progress card** (hero style, like the "78%" and "95%" references):
   - Big percentage = completed ÷ total tasks (show "0%" and a friendly message when there are none).
   - Thin circular progress ring around or beside the number, and a small line: "6 of 8 deadlines done".
   - Soft lavender-to-white panel. A "View completed" link applies the Completed filter.
2. **Next 7 Days chart** (like the line charts with the floating value bubble):
   - Thin line (or smooth bar) chart showing the number of incomplete deadlines due on each of the next 7 days.
   - Highlight today, and show a floating bubble with the value of the hovered / focused / tapped point.
   - Axis labels as short weekday names. Fully keyboard- and touch-accessible, and provide a text summary for screen readers.
   - Built with inline SVG or CSS. **No chart library.**

On laptop, the layout is a **12-column grid**: hero progress (4 columns) + chart (8 columns), directly under the metric tiles.

### 4.5 Toolbar
White rounded toolbar card: search field with icon and clear button, pill-shaped filter tabs (with counts), and a sort dropdown. Active tab is solid indigo with white text. Inactive tabs are quiet.

### 4.6 Task grid
Two-column grid of task cards (Section 6).

---

## 5. Screen Design: Mobile (≤ 639px, designed first at 390px)

The mobile layout is **reorganized**, not just shrunk:

### 5.1 Top area
Compact header (logo chip, "DueSync", date). Below it a large friendly greeting block: "Your deadlines, under control." with the summary pill.

### 5.2 Content order
1. **Hero completion card** (large percentage with ring), full width.
2. **Metric tiles** in a 2×2 pastel bento (tiles may have slightly different heights for rhythm, but alignment must stay clean).
3. **Next 7 Days** chart (compact, horizontally comfortable, no overflow).
4. **Search + horizontally scrollable filter pills** (sticky below the header while scrolling the list).
5. **Task cards**, single column, full width.

### 5.3 Floating bottom navigation (pill)
Floating pill bar above the safe-area inset with **real, working** destinations:

| Item | Action |
|---|---|
| Home | Scrolls to top and sets filter to **All** |
| Urgent | Applies the **Critical** filter |
| Done | Applies the **Completed** filter |
| **+** (center, raised circular button, indigo with soft shadow) | Opens the **Add Deadline** modal |

- Active item gets an indigo-tinted pill and a text label. Icons are 24px, and each target is at least 44px.
- Leave bottom padding on the page so the last card is never hidden. Toasts appear above the nav.
- On tablet and laptop, the bottom nav is hidden (the header button replaces it).

### 5.4 Add / Edit as a bottom sheet
On mobile the modal is a full-width **bottom sheet** with a drag-handle visual, 28px top radius, sticky submit button, and keyboard-safe scrolling. On laptop it is a centered dialog. Same component and behavior as the master spec.

---

## 6. Task Card Design

- White card, 24px radius, soft border and shadow, **a 6px colored left accent bar** in the urgency accent color.
- **Top row:** round urgency icon chip (pastel fill + accent icon), title (bold, wraps to two lines max), and an overflow-free status badge pill on the right ("Due Today", "Overdue", "Approaching Soon", "Plenty of Time", "Completed").
- **Second row:** subject and task type as small neutral chips.
- **Countdown block:** a rounded pastel strip (using the urgency pastel) with a clock icon and the countdown in large tabular numerals, plus a small label ("Time left" / "Overdue by"). The formatted due date and time sit beside or under it.
- **Priority badge:** small pill (Low = grey, Medium = amber, High = coral) with a flag icon and text.
- **Notes preview:** one or two lines, muted.
- **Actions row:** a primary-tinted **Complete** button (full label), plus **Edit** and **Delete** icon buttons with `aria-label`s. Minimum 44px height on touch.
- **Completed state:** grey-lavender card, struck-through title, mint check chip, a "Completed" badge, **no** urgency badge, and a **Restore** button.
- **Hover (laptop):** card lifts 2px and the border tints.

---

## 7. Component Details

- **Buttons:** primary (indigo, white text), secondary (white with border), soft (primary-soft with indigo text), destructive (coral-pink with red text). One clear primary action per view.
- **Inputs:** 14px radius, 48px height, visible labels, soft focus ring in `--primary` at 3px, inline error text in red with an icon.
- **Selects and datetime:** native controls styled consistently.
- **Priority selector in the modal:** three segmented pills (Low / Medium / High) with colored dots instead of a plain dropdown (still a real form control with the same values, accessible by keyboard).
- **Toasts:** pill shape, dark ink background, white text, a small colored status dot. Auto-dismiss, `aria-live="polite"`.
- **Confirm-delete dialog:** small centered card with coral icon chip, task name, and two clear buttons.
- **Empty states:** a friendly inline SVG scene built from soft pastel shapes and Lucide icons (calendar or check), a heading, a description, and an action button. Original artwork only.

---

## 8. Responsive Rules (recap)

| Width | Layout |
|---|---|
| 320-639px | Mobile layout (Section 5), single-column tasks, 2×2 metric bento, floating nav |
| 640-1023px | 2-column metrics, hero and chart stacked or side-by-side, 1-2 column tasks, no bottom nav |
| ≥ 1024px | 4-column metrics, hero + chart row (4 + 8 columns), 2-column tasks |

No horizontal overflow at any width from 320px up. Use `min-w-0`, truncation, and wrapping so long titles and countdowns never break cards.

---

## 9. Showcase Render (secondary deliverable)

After the app is built, produce **one** presentation image of the finished design for the portfolio / README (use Antigravity's image generation, or compose from real screenshots of the running app):

- **Canvas:** landscape 16:9, 3840 × 2160 preferred.
- **Content:** a **MacBook Pro** (left, about 60-65% of the frame) showing the laptop dashboard, and an **iPhone 16 Pro** (right, slightly forward) showing the mobile home screen. If you are rendering rather than compositing, the screen content must match the real app.
- **Setting:** soft, light lavender-grey studio background, natural contact shadows, gentle ambient occlusion, soft directional light, and faint pastel light spill (lavender, peach, mint). The devices must not overlap each other's screen content.
- **Quality:** crisp, readable screens with no heavy glare or blur, realistic device proportions, a clean editorial composition with generous negative space.
- **Do not include:** other devices, extra brand logos, marketing headlines, random text, or misspelled UI copy. All on-screen text must match the real DueSync interface.

---

## 10. Design QA Checklist (verify with the browser agent)

- [ ] Reference Analysis artifact exists, and no reference screen was copied
- [ ] All colors, radii, and shadows come from tokens
- [ ] Pastel + accent pairs are used correctly, and every status has color + label + icon
- [ ] Text contrast is AA on every pastel panel (spot-check the 4 urgency panels)
- [ ] Mobile (390), tablet (768), and laptop (1440) screenshots show the layouts in Sections 4-5
- [ ] No horizontal scroll at 320, 390, 768, and 1440px
- [ ] Hero completion % and the Next 7 Days chart match the real task data and update on add, complete, restore, edit, and delete
- [ ] Chart point selection works with mouse, touch, and keyboard, and has a text alternative
- [ ] Floating bottom nav (Home / Urgent / Done / +) works and never hides content
- [ ] Bottom-sheet modal on mobile and centered dialog on laptop, with correct focus handling
- [ ] Tap targets are at least 44px, and inputs are at least 16px on mobile
- [ ] Reduced-motion preference is respected
- [ ] Console is clean and the master-spec functional checklist still passes
- [ ] Side-by-side comparison with the reference images shows equal or better polish and spacing

---

## 11. Final Output

1. `web/index.html` with the redesigned DueSync Web interface (functionality unchanged from the master spec)
2. Reference Analysis artifact
3. Screenshots at 390px, 768px, and 1440px, plus the reference comparison
4. Showcase render (Section 9)
5. Walkthrough artifact with the QA checklist results

**Final design objective:** a soft, colorful, beautifully organized student planner whose pastel bento cards, big friendly numbers, and clear urgency colors make a heavy workload feel calm and under control on both a phone and a laptop.
