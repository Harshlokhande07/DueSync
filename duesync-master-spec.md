# DueSync: Master Product & Engineering Spec

> **One product, two interfaces.** DueSync helps students never miss a deadline.
> - **DueSync Web**: a clean, mobile-first dashboard (single `index.html`)
> - **DueSync CLI** (`duelist`): a fast terminal tracker with reports and Google Sheets sync
>
> **Target environment:** Google Antigravity (agent-first IDE)
> **Recommended mode:** Planning mode, with the browser agent enabled for web verification and the terminal enabled for CLI tests

---

## 0. Instructions for the Agent (read first)

You are building two production-quality deliverables in one repository. Work in this order:

1. **Plan before coding.** Produce an Implementation Plan artifact covering repo layout, data models, urgency logic, UI layout, CLI command design, and the test plan for both products.
2. **Build the CLI first** (Part B). It is smaller and its status logic is the reference for the shared vocabulary.
3. **Build the Web app** (Part A) as a single `index.html`.
4. **Verify.**
   - Web: use the browser agent at **390×844**, **768×1024**, and **1440×900**, and capture screenshots.
   - CLI: run the full command set in the terminal and run the unit tests.
5. **Fix every defect found**, then re-verify.
6. **Finish with a Walkthrough artifact** summarizing what was built, what was tested, and known limitations.

Rules:
- Do not ask clarifying questions unless something is genuinely blocking. Make sensible decisions and record them in the plan.
- No placeholder buttons, stub commands, fake data hooks, or decorative-only controls.
- The browser console (web) and stderr (CLI) must be clean during normal use.
- Never commit secrets. `credentials.json` must never be created, printed, or logged by the agent.

---

## 1. Product Overview

| | **DueSync Web** | **DueSync CLI (`duelist`)** |
|---|---|---|
| Purpose | Visual dashboard with live countdowns | Quick capture, reports, spreadsheet sync |
| Best for | Phone and laptop browsing | Terminal users, scripting, weekly exports |
| Storage | Browser `localStorage` (`dueSyncTasks`) | Local file `assignments.json` |
| Extras | Search, filter, sort, edit, toasts | `.docx` / `.md` export, Google Sheets sync |
| Stack | HTML5, Tailwind CDN, Vanilla JS, Lucide | Python 3, colorama, python-dateutil, python-docx, gspread, google-auth |

**Shared brand voice:** calm, minimal, professional. **Tagline:** *Stay ahead of every deadline.*

**Shared urgency vocabulary:** every task is always one of **Overdue, Due Soon / Critical, Approaching, Safe, Completed**, shown with a text label, an icon or symbol, and a color. Color is never the only signal.

---

## 2. Repository Layout

```
duesync/
├── README.md
├── .gitignore
├── web/
│   └── index.html              # DueSync Web (single self-contained file)
└── cli/
    ├── pyproject.toml          # defines the `duelist` console entry point
    ├── requirements.txt
    ├── duelist/
    │   ├── __init__.py
    │   ├── tracker.py          # CLI + interactive REPL
    │   ├── storage.py          # JSON persistence
    │   ├── export.py           # .docx / .md report generation
    │   ├── sheets.py           # Google Sheets sync
    │   └── status.py           # shared status classification and color mapping
    └── tests/
        ├── test_storage.py
        ├── test_status.py
        ├── test_dates.py
        └── test_export.py
```

The `README.md` must cover installation, quick start for both products, Google Sheets setup, and screenshots.

---

# PART A: DueSync Web

## A1. Technical Constraints

| Area | Requirement |
|---|---|
| Structure | HTML5, semantic landmarks, accessible forms |
| Styling | Tailwind CSS via official CDN, no build step |
| Logic | Vanilla JavaScript (ES6+), no frameworks or TypeScript |
| Icons | Lucide via CDN |
| Storage | `localStorage`, key `dueSyncTasks` |
| Font | Inter (Google Fonts) with a system-font fallback stack |
| Delivery | Single `web/index.html`, opens directly via `file://` |
| Backend / APIs | None |

- No npm, Node, bundler, or server required.
- Modular JavaScript with descriptive function names.
- Guard all `localStorage` access with `try/catch`. The app must still run if storage is blocked.

## A2. Design System

**Principles**
- Mobile-first: design at 390px width, then scale up.
- Minimal, calm, highly organized. Soft off-white background, white cards, subtle gray borders, restrained shadows.
- Consistent radii (`rounded-2xl` cards, `rounded-xl` controls).
- Strong type hierarchy. No oversized headings, heavy gradients, or glassmorphism.
- Subtle motion only. Respect `prefers-reduced-motion`.

**Color tokens**

| Role | Usage |
|---|---|
| Primary | Deep indigo / blue-violet: buttons, active tabs, focus rings, logo |
| Background / Surface | Soft off-white / white |
| Text | Dark slate (primary), muted gray (secondary) |
| Safe | Green |
| Approaching | Amber |
| Critical | Red |
| Completed | Muted gray with green accents |

**Typography:** app name → page heading → metric values → task titles → countdowns (tabular numerals) → metadata → timestamps.

**Responsive behavior**

| Viewport | Layout |
|---|---|
| Mobile (< 640px) | Single column, full-width cards, stacked header, 2-column metrics, horizontally scrollable filter tabs, touch targets ≥ 44px |
| Tablet (640-1023px) | 2-column metrics, one or two-column task grid |
| Laptop / Desktop (≥ 1024px) | 4-column metrics, two-column task grid, centered container (about 1200px max) |

No horizontal page overflow from 320px up. Modals are bottom-sheet style on mobile and centered dialogs on larger screens.

## A3. Layout

**Header (sticky):** logo icon, **DueSync**, subtitle "Stay ahead of every deadline.", live date, prominent **+ Add Deadline** button (a floating action button is acceptable on mobile if the header button stays accessible).

**Welcome section (compact):** heading "Your deadlines, under control." Subtext "Track upcoming submissions, prioritize your work, and stay on schedule." Optional summary line, e.g. "3 active tasks · next due in 7h 42m".

**Metric cards**

| Card | Definition | Accent | Icon |
|---|---|---|---|
| Total Active | Incomplete tasks | Indigo / neutral | calendar |
| Approaching Soon | Incomplete, > 24h and ≤ 5 days away | Amber | clock / hourglass |
| Urgent / Overdue | Incomplete, ≤ 24h away or past due | Red | alert-triangle |
| Completed | Tasks marked complete | Green | check-circle |

Metrics update instantly on any add, edit, delete, complete, restore, or clock-driven category change.

## A4. Countdown Engine & Urgency Rules

**Calculation**
- Store `dueDate` as an ISO string. Compute `remaining = dueTimestamp − Date.now()` on every refresh. **Never store or decrement countdown values.**
- Show days, hours, minutes using timestamp math (correct across midnight, month, year, leap-year, and DST boundaries).
- Formats: `6d 08h 25m` (≥ 1 day), `08h 35m` / `00h 42m` (< 1 day), `Overdue by 2h 15m`, `Overdue by 3d 04h`.
- Reject invalid or missing dates at input and handle them safely when read from storage.
- **One** centralized 60-second timer refreshes all countdowns and states, and a refresh also runs on `visibilitychange`. No per-task intervals.
- Countdown text and urgency badge come from the same single calculation per render.

**Urgency classification (mutually exclusive, incomplete tasks)**

| Condition | Status | Color |
|---|---|---|
| remaining > 5 days | Plenty of Time | Green |
| 24h < remaining ≤ 5 days | Approaching Soon | Amber |
| 0 < remaining ≤ 24h | Due Today | Red |
| remaining ≤ 0 | Overdue | Red |
| Completed | Completed | Muted gray / green |

Boundaries: exactly 24h → critical; exactly 5 days → approaching; now or earlier → overdue. Completed tasks are never urgent, even if past due.

**Card indicators:** visible countdown, text badge, colored left border or top accent, and a small status icon. No flashing animation.

## A5. Add / Edit Modal

One component, two modes: **Add** ("Add Deadline") and **Edit** ("Update Deadline", pre-filled).

| Field | Type | Rules |
|---|---|---|
| Task Title | text | Required, trimmed, reject whitespace-only |
| Subject / Course | text | Optional |
| Task Type | select | Assignment (default), Exam, Project, Practical, Presentation, Other |
| Due Date & Time | `datetime-local` | Required, valid, helpful error message |
| Priority | select | Low, Medium (default), High, with colored indicators |
| Notes | textarea | Optional, 500-char limit with live counter |

Behavior: visible labels, inline validation, double-submit guard, close on backdrop / close icon / **Escape**, focus trap with `role="dialog"` and `aria-modal`, auto-focus title on open, return focus to the trigger on close, reset after add. Editing preserves `id`, `createdAt`, and `completed`, and updates `updatedAt`.

## A6. Task Cards & Actions

**Card hierarchy:** title + status indicator → subject and type → countdown and local due date/time → priority and urgency badges → notes preview → actions (**Complete / Restore**, **Edit**, **Delete**).

- Nothing overflows its container. Action buttons have accessible names and are at least 44px tall on touch screens.
- Completed cards: struck-through title, muted styling, completion badge, **no** urgent/overdue badge, and a Restore action.
- **Complete / Restore** toggles state and updates metrics, filters, and storage, with a toast.
- **Edit** saves to the same record (no duplicates) and recalculates immediately.
- **Delete** requires a small custom confirm dialog that names the task. Cancel leaves it untouched.

## A7. Search, Filter, Sort

- **Search:** instant, case-insensitive across title, subject, type, and notes. Search icon, placeholder "Search tasks or subjects...", clear (×) button.
- **Filters** (counts calculated from the full collection): `All` · `Critical` · `Approaching` · `Safe` · `Completed`. Critical, Approaching, and Safe contain incomplete tasks only.
- **Sort:** Closest Deadline First (default) · Furthest Deadline · Priority: High to Low (ties broken by due date). Sorting must be stable and deterministic.
- All three work together (for example "Physics" + Critical + Priority).

## A8. Empty States & Feedback

| Situation | Message |
|---|---|
| No tasks at all | "Your schedule is clear. Add your first deadline to get started." |
| No search / filter match | "No tasks match your search. Try another keyword or clear your filters." (with **Clear filters** button) |
| No critical tasks | "You're all caught up on urgent work." |
| No completed tasks | "Completed tasks will appear here when you finish an assignment." |

**Toasts:** "Deadline added", "Changes saved", "Task marked complete", "Task restored", "Task deleted". They auto-dismiss, use `role="status"` / `aria-live="polite"`, and stay clear of the floating button and safe areas on mobile.

## A9. Data & Persistence (Web)

```js
{
  id: string,          // crypto.randomUUID() with fallback
  title: string,
  subject: string,
  type: "Assignment" | "Exam" | "Project" | "Practical" | "Presentation" | "Other",
  dueDate: string,     // ISO date-time
  priority: "Low" | "Medium" | "High",
  notes: string,
  completed: boolean,
  createdAt: string,
  updatedAt: string
}
```

- Load on startup, save after every mutation, and validate or repair malformed records instead of crashing.
- **Seed data only when the storage key does not exist.** Deleting everything keeps the key as `[]`, so the empty state survives reloads.

| Seed task | Subject | Type | Priority | Due |
|---|---|---|---|---|
| Data Structures Assignment | Computer Science | Assignment | High | now + ~8 hours |
| Engineering Physics Practical File | Engineering Physics | Practical | Medium | now + ~2 days |
| Mini Project Submission | Software Development | Project | High | now + ~8 days |
| Mathematics Quiz | Mathematics | Exam | Medium | now − ~2 days |

## A10. Accessibility, Security & Code Quality (Web)

- Semantic landmarks, proper heading order, labeled inputs, `aria-label` on icon-only buttons.
- Visible focus rings, full keyboard operation, WCAG AA contrast, 16px minimum base text on mobile, safe-area insets, `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- **Never inject user text through `innerHTML`.** Use `textContent` / DOM creation or an escape helper.
- Suggested sections: constants → state/seed → storage → task CRUD → countdown/urgency → search/filter/sort → metrics → rendering → modal/validation → confirm/toast → event listeners → init + timer.
- Suggested functions: `loadTasks`, `saveTasks`, `calculateTimeRemaining`, `getUrgencyStatus`, `renderDashboard`, `renderTaskList`, `updateMetrics`, `filterTasks`, `sortTasks`, `openTaskModal`, `handleTaskSubmit`, `toggleTaskCompletion`, `deleteTask`.
- Event delegation on the task list, one timer, no leaks, unique IDs (never array indexes), `lucide.createIcons()` after renders that add icons.

---

# PART B: DueSync CLI (`duelist`)

## B1. Stack & Dependencies

- **Language:** Python 3.9+
- **Libraries:** `python-dateutil` (date parsing), `colorama` (terminal colors), `python-docx` (Word reports), `gspread` and `google-auth` (Google Sheets)
- **Packaging:** `pyproject.toml` with a console entry point so that `pip install -e .` provides the `duelist` command. `python -m duelist` must also work.
- **Testing:** `pytest`, listed as a dev dependency.

## B2. Data Storage: `storage.py`

- Local JSON file `assignments.json`, stored in the current working directory by default. Allow an override through the `DUELIST_DATA` environment variable.
- **Schema**

| Field | Type | Notes |
|---|---|---|
| `id` | int | Auto-incremented, never reused within a file |
| `title` | str | Required, trimmed |
| `class` | str | Course name (may be empty) |
| `due` | str | ISO date `YYYY-MM-DD` |
| `done` | bool | Completion flag |
| `added` | str | ISO date `YYYY-MM-DD`, set on creation |

- **Required helpers:** `load()`, `save(data)`, `next_id(data)`.
- `load()` returns `[]` if the file is missing, and handles corrupt JSON gracefully (clear error message, never silently overwrite a corrupt file; back it up to `assignments.json.bak` first).
- `save()` writes atomically (write to a temp file, then replace).

## B3. Status Logic: `status.py`

A single source of truth used by the terminal table, the export engine, and the Sheets sync. Dates are compared at date granularity against today's local date.

| Condition (incomplete task) | Status | Terminal color | Sheets row color |
|---|---|---|---|
| `due` < today | Overdue | Red | Red |
| today ≤ `due` ≤ today + 3 days | Due Soon | Yellow | Yellow |
| `due` > today + 3 days | Pending | Default | None |
| `done` is true | Done | Green | Green |

- A task due **today** is Due Soon, not Overdue.
- Completed tasks are always Done, even if the due date has passed.
- Every colored status also carries a text label, so output stays readable with colors disabled (honor `NO_COLOR`, and add `--no-color` if practical).

## B4. CLI & Interactive REPL: `tracker.py`

- With arguments, run **one-shot** commands. With no arguments, start an **interactive REPL** with the prompt `duelist>`. The REPL supports `help`, `exit`, and `quit`, and handles Ctrl+C and Ctrl+D without a traceback.
- Use `argparse` with sub-commands, and share a single command dispatcher between one-shot mode and the REPL. Parse REPL lines with `shlex` so quoted titles work.

| Command | Behavior |
|---|---|
| `add <title> --class <class> --due <due>` | Parse a flexible date (for example `June 20`, `2026-11-05`, `next friday`) and save. Print a confirmation with the new ID and the resolved date. |
| `list` | Formatted table of all assignments sorted by due date, color coded. |
| `upcoming` | Pending assignments due within the next 7 days (today through today + 7), sorted by due date. |
| `done <id>` | Mark an assignment complete. |
| `remove <id>` | Delete an assignment by ID. |
| `export [--format docx\|md] [--output <path>]` | Generate a summary document (default format `docx`). |
| `sync [--sheet <sheet_name>]` | Sync all data to the Google Sheets worksheet (default `DueList`). |

**Behavior details**
- **Dates without a year** (such as `June 20`): use the current year. If that date has already passed, roll to the next year, and show the resolved full date in the confirmation so the user can see it.
- Reject unparseable dates with a friendly message and a non-zero exit code. Never show a raw traceback for expected errors.
- Unknown or non-numeric IDs show a clear error. Commands that change data confirm what changed.
- `list` and `upcoming` show an empty-state message ("No assignments yet. Add one with: duelist add ...").
- The table columns are `ID`, `Title`, `Class`, `Due`, `Status`, with a legend line explaining the colors. Align columns correctly even with long titles (truncate with an ellipsis rather than breaking the layout).
- Call `colorama.init()` for Windows compatibility.

**Example session**

```
$ duelist add "Binary Search Assignment" --class "Data Structures" --due "June 20"
✔ Added #4 · Binary Search Assignment · due 2027-06-20

$ duelist upcoming
ID  Title                      Class             Due         Status
 2  Physics Practical File     Engg. Physics     2026-10-27  Due Soon
```

## B5. Export Engine: `export.py`

Categorize tasks into four sections, in this order:

1. **Overdue**: incomplete and past due
2. **Due This Week**: incomplete and due within the next 7 days
3. **Coming Up Later**: incomplete and due beyond 7 days
4. **Completed**: `done` is true

Formats:
- **`.docx`** (via `python-docx`): title, generated-on date, summary counts, a custom heading per section, styled bullets (title, class, due date), and RGB color highlights per category (red for Overdue, amber for Due This Week, blue/neutral for Coming Up Later, green for Completed).
- **`.md`**: clean headers and list items with the same four sections, and a summary line at the top.

Rules:
- Default output filename: `DueList_Summary_YYYY-MM-DD.<ext>` in the current directory. `--output` overrides it, and the parent folder is created if needed.
- Empty sections still appear with a short "Nothing here" line.
- Print the final path on success.

## B6. Google Sheets Sync: `sheets.py`

- **Authentication:** Google Cloud **Service Account** credentials in `credentials.json`, with the Sheets and Drive scopes. The target spreadsheet must be shared with the service-account email, and the README documents this step with exact instructions.
- **Config:** preferences in `config.json`, for example `{"spreadsheet_id": "...", "worksheet": "DueList"}`. If `spreadsheet_id` is missing, prompt the user for it once (or accept `--spreadsheet-id`) and save it.
- **Sync behavior:** open the spreadsheet, get or create the worksheet (default title `DueList`, override with `--sheet`), **clear it, then write** headers and rows in one batched update.
- **Columns:** `ID`, `Title`, `Class`, `Due Date`, `Status`, `Date Added`.
- **Batch styling** (a single `batch_update` or `format` call set, to stay within rate limits):
  - Header row: bold, white text on a dark background, frozen.
  - Row backgrounds from the B3 mapping: red for overdue, yellow for due soon, green for completed.
  - Auto-resize columns.
- Handle errors with friendly messages: missing `credentials.json`, missing spreadsheet access, API failure, no network. None should show a traceback.
- Print the spreadsheet URL on success.

## B7. Git Configuration: `.gitignore`

```
# Secrets & local data
credentials.json
config.json
assignments.json
assignments.json.bak

# Generated reports
DueList_Summary_*.docx
DueList_Summary_*.md
*.docx
*.md.generated

# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/

# Virtual environments
.venv/
venv/
```

> Note: do **not** ignore the repository's own `README.md` or this spec. Use only the `DueList_Summary_*` patterns for generated markdown reports.

## B8. CLI Code Quality

- Type hints and docstrings on all public functions.
- Pure functions for classification, parsing, and categorization, so they are easy to test.
- Network and filesystem access isolated in `sheets.py` and `storage.py`.
- Consistent exit codes: `0` success, `1` user error, `2` system error.
- `--help` text for every command with at least one example.

---

# PART C: Cross-Product Consistency

| Concept | Web | CLI | Notes |
|---|---|---|---|
| Name and tagline | DueSync | `duelist` (DueSync CLI) | Same tagline in both |
| Overdue | Red, "Overdue" | Red, "Overdue" | Identical meaning |
| Soon | Red "Due Today" (≤ 24h), Amber "Approaching" (≤ 5 days) | Yellow "Due Soon" (≤ 3 days) | The CLI works with dates only (no times), so it uses one simpler band. This difference is **intentional**. |
| Completed | Muted gray / green | Green | |
| Course field | `subject` | `class` | Same meaning |
| Due field | `dueDate` (date-time) | `due` (date only) | |

Out of scope for v1: automatic data sync between the web app and the CLI. (Optional later: a JSON import/export bridge using the field mapping above.)

---

## Verification Plan

### Web (browser agent, at 390×844, 768×1024, 1440×900; capture screenshots)

**Layout:** no horizontal scroll at 320 / 390 / 768 / 1440px · header, metrics, toolbar, cards, and modal render correctly · touch targets ≥ 44px

**Countdown and urgency** (use a temporary test hook or edit tasks to exact offsets):
- [ ] Exactly 24h → Critical · 24h 1m → Approaching
- [ ] Exactly 5 days → Approaching · 5 days 1m → Safe
- [ ] Now or earlier → Overdue · completed past-due task shows no urgent badge
- [ ] Countdown formats match A4 · metrics and badges agree
- [ ] 60-second refresh moves a task between categories without reload

**CRUD and forms**
- [ ] Valid add works · empty / whitespace title / empty date show inline errors
- [ ] Edit updates the same record · id and completion state preserved
- [ ] Delete confirmation: cancel keeps, confirm removes
- [ ] Complete → Completed list · Restore → active list
- [ ] Escape, backdrop, and close icon dismiss the modal · focus returns correctly

**Search / filter / sort:** instant case-insensitive search and clear button · all five filters correct, counts ignore search text · three sorts work · combined use works

**Persistence:** data survives reload · seed only on first load · delete-all stays empty after reload · corrupt storage value does not crash the app

**Quality:** zero console errors or warnings · `<img src=x onerror=alert(1)>` renders as plain text · full keyboard-only walkthrough succeeds

### CLI (terminal + `pytest`)

- [ ] `pip install -e .` provides a working `duelist` command, and `python -m duelist` works
- [ ] `add` accepts `June 20`, `2026-11-05`, and `next friday`, and rejects garbage dates with a friendly error
- [ ] Year rollover for past year-less dates works and is shown in the confirmation
- [ ] IDs auto-increment and are never reused after `remove`
- [ ] `list` is sorted by due date with correct colors: green done, red overdue, yellow due ≤ 3 days
- [ ] `upcoming` shows only pending tasks within 7 days
- [ ] `done` and `remove` handle valid, missing, and non-numeric IDs
- [ ] Interactive REPL: prompt `duelist>`, quoted arguments, `help`, `exit`, Ctrl+C, and Ctrl+D behave cleanly
- [ ] `export --format md` and `export --format docx` produce the four sections, default filename `DueList_Summary_YYYY-MM-DD.<ext>`, and `--output` works
- [ ] The `.docx` opens correctly and shows the color highlights
- [ ] `sync` (with a test spreadsheet and service account, or mocked `gspread` in tests) clears, writes six columns, and applies header and row styling
- [ ] Missing `credentials.json` / `config.json` and corrupt `assignments.json` produce friendly errors with no tracebacks
- [ ] `.gitignore` excludes every listed file, and `git status` stays clean after running all commands

---

## Acceptance Criteria

The project is done only when:

**Web**
- The app runs from one `index.html` with no build tooling or backend.
- It looks polished and works well on mobile and laptop.
- Metrics, countdowns, and urgency rules are correct at every boundary.
- Add, edit, complete/restore, and delete work with validation and delete confirmation.
- Search, five filters, and three sorts work individually and together.
- Data persists, seed logic is correct, and empty states and toasts are present.
- User content is rendered safely, accessibility requirements are met, and the console is clean.

**CLI**
- All seven commands work in one-shot mode and in the REPL.
- Color coding and status labels follow B3.
- Reports export to `.docx` and `.md` with four correctly categorized sections.
- Google Sheets sync works with a service account and styles the sheet as specified.
- Secrets and local data are never committed.
- Unit tests pass.

**Repository**
- The README gives clear setup steps for both products, including Google Sheets service-account setup.
- Every item in the Verification Plan is checked and the results are recorded in the Walkthrough artifact.

---

## Final Output

1. `web/index.html`, the complete DueSync Web app
2. `cli/`, the complete `duelist` package with tests, `requirements.txt`, and `pyproject.toml`
3. Root `README.md` and `.gitignore`
4. Implementation Plan artifact (before coding)
5. Web screenshots at the three viewports
6. Walkthrough artifact summarizing the build, test results, and known limitations

**Final objective:** one clean, reliable product that lets students see their workload at a glance in the browser, capture and report on it from the terminal, and never miss a submission.
