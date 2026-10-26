# DueSync

<p align="center">
  <img src="web/logo.png" alt="DueSync Logo" width="100" style="border-radius: 20px;">
</p>

> **Stay ahead of every deadline.**  
> A unified deadline tracking system tailored for students and busy developers.

DueSync combines two interfaces:
1. **DueSync Web**: A responsive, mobile-first visual dashboard designed with a calm, tactile pastel-bento aesthetic, featuring live countdowns, circular progress tracking, 7-day workload curves, urgency badges, and zero-build local storage.
2. **DueSync CLI (`duelist`)**: A terminal command-line tool with interactive REPL, export reports (`.docx` & `.md`), and Google Sheets synchronization.

---

## Repository Structure

```
DueSync/
├── README.md                   # Project documentation & quick start
├── .gitignore                  # Git ignore rules
├── duesync-master-spec.md      # Specification file
├── web/
│   └── index.html              # Self-contained Web dashboard (single file)
└── cli/
    ├── pyproject.toml          # Python package configuration & `duelist` entrypoint
    ├── requirements.txt        # Runtime and test dependencies
    ├── duelist/
    │   ├── __init__.py
    │   ├── tracker.py          # CLI commands & interactive REPL
    │   ├── storage.py          # Atomic JSON persistence & corruption backup
    │   ├── status.py           # Single source of truth for urgency and colors
    │   ├── export.py           # .docx and .md report generator
    │   └── sheets.py           # Google Sheets sync with batch formatting
    └── tests/
        ├── test_storage.py     # Persistence, corruption handling, and atomic writes
        ├── test_status.py      # Urgency logic and color mappings
        ├── test_dates.py       # Relative and rollover date parsing
        └── test_export.py      # Document export & categorization tests
```

---

## 1. DueSync Web

### Features
- **Zero build step**: Single `web/index.html` file using Tailwind CSS CDN, Lucide Icons, and Google Fonts (Inter).
- **Responsive Layout**: Designed mobile-first for phones (390px), tablets (768px), and desktop widescreen (1440px+).
- **Urgency Classification**: Real-time evaluation into **Overdue**, **Due Today**, **Approaching Soon**, and **Plenty of Time**.
- **Live Tabular Countdowns**: Accurate countdown tickers refreshed every 60 seconds.
- **Search, Filter & Sort**: Multi-criteria search, 5 filter tabs with real-time task counts, and 3 sort modes.
- **Accessible & Safe**: Full keyboard navigation, inline form validation, character counter, focus trapping, and strict HTML escaping.

### Quick Start
Open `web/index.html` directly in any web browser:
```bash
# Double-click web/index.html or run:
start web/index.html
```
Or serve locally via Python:
```bash
python -m http.server 8080 --directory web
# Open http://localhost:8080 in your browser
```

---

## 2. DueSync CLI (`duelist`)

### Installation
From the root directory:
```bash
python -m pip install -e ./cli
```

### Usage Modes

#### 1. Direct Command-Line Execution
```bash
# Add a deadline
python -m duelist add "Data Structures Lab" --class "CS 101" --due "tomorrow"

# Add with flexible date syntax (auto rolls over past dates to next year)
python -m duelist add "Physics Midterm" --class "Physics" --due "June 20"

# List all deadlines sorted by date with terminal colors
python -m duelist list

# View upcoming deadlines due within the next 7 days
python -m duelist upcoming

# Mark a deadline complete
python -m duelist done 1

# Delete a deadline by ID
python -m duelist remove 2

# Export weekly summary as Markdown
python -m duelist export --format md

# Export weekly summary as styled Word Document (.docx)
python -m duelist export --format docx

# Synchronize with Google Sheets
python -m duelist sync
```

#### 2. Interactive REPL Mode
Launch without arguments to enter the interactive shell:
```bash
python -m duelist
```
```
============================================================
 DueSync CLI (duelist) · Stay ahead of every deadline.
 Type a command (e.g. 'list', 'add --help') or 'help' or 'exit'.
============================================================
duelist> list
duelist> add "Final Presentation" --class "Capstone" --due "next friday"
duelist> upcoming
duelist> done 3
duelist> exit
```

---

## 3. Google Sheets Integration

DueSync supports synchronizing your local deadlines directly to a Google Sheet with automated table formatting and status color highlights.

### Setup Instructions
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable both the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account**, generate a JSON key, and save it as `credentials.json` in your working directory.
4. Open your target Google Spreadsheet in your browser and share it with the service account client email address (found inside `credentials.json`) with **Editor** permissions.
5. Run the sync command:
   ```bash
   python -m duelist sync
   ```
6. On first run, enter the Spreadsheet ID (found in the sheet URL: `https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit`). The ID is automatically saved to `config.json` for future runs.

---

---

## 4. Daily Email Digest (`duelist digest`)

Get one automated email briefing every morning detailing **Today's** and **Tomorrow's** deadlines, plus any **Overdue** tasks.

**Subject:** `DueSync · 1 due today, 1 tomorrow · 1 overdue`

```
DueSync                                   Mon, 26 Oct 2026
Stay ahead of every deadline.

[ Today · 1 ]
  • Chemistry Lab Report        Chemistry        due today

[ Tomorrow · 1 ]
  • Data Structures Assignment  Computer Science

[ Overdue · 1 ]
  • History Essay               History          6 days overdue

Sent by duelist · 4 active, 1 completed
```

The email is delivered as a **multipart/alternative** message with a clean plain-text twin and a responsive, table-based HTML email featuring DueSync's signature color palette (teal header `#14645B`, mint `#2FC48D` for Today, amber `#F59E0B` for Tomorrow, and coral `#F2546F` for Overdue).

### 1. Gmail Setup (Recommended)
1. Turn on **2-Step Verification** on your Google Account: [myaccount.google.com/security](https://myaccount.google.com/security).
2. Go to **Security > App passwords**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Generate an App Password for "DueSync" and copy the 16-character code (e.g. `abcd efgh ijkl mnop`).

### 2. Set the Environment Variable
Secrets are strictly read from environment variables and are never stored in files or printed in logs.

* **Linux / macOS:**
  ```bash
  export DUELIST_SMTP_PASSWORD="your 16 character app password"
  ```
  *(To make persistent, add the line to `~/.bashrc` or `~/.zshrc`).*

* **Windows (PowerShell):**
  ```powershell
  $env:DUELIST_SMTP_PASSWORD="your 16 character app password"
  ```
  *(To make permanent across sessions in Windows):*
  ```powershell
  [System.Environment]::SetEnvironmentVariable('DUELIST_SMTP_PASSWORD', 'your 16 character app password', 'User')
  ```

* **Windows (Command Prompt):**
  ```cmd
  set DUELIST_SMTP_PASSWORD=your 16 character app password
  ```

### 3. Interactive Setup & Preview
Run the setup wizard:
```bash
python -m duelist digest setup
```
1. Select provider preset: **Gmail** (default, `smtp.gmail.com:587`), **Outlook** (`smtp.office365.com:587`), or **Custom SMTP**.
2. Enter sender email address (e.g. `you@example.com`).
3. Enter recipient email address (press Enter to send to yourself).
4. Choose send time (default `08:00`) and label language (`english` for *Today/Tomorrow* or `hinglish` for *Aaj/Kal*).

Verify your setup:
```bash
# Preview the plain-text digest and write HTML to digest_preview.html
python -m duelist digest preview --html

# Check current configuration and last sent date (addresses are masked)
python -m duelist digest status

# Send a real test email to confirm SMTP connectivity
python -m duelist digest test
```

### 4. Automated Daily Scheduling

The `--if-not-sent-today` flag ensures that only one message is sent per day.

#### Linux / macOS (`cron`)
Run `crontab -e` and add a line to trigger every morning at 08:00:
```bash
0 8 * * * cd /path/to/DueSync && python -m duelist digest --if-not-sent-today
```

#### Windows (Task Scheduler)
Create a scheduled task via PowerShell or Command Prompt that runs daily at 08:00 and upon user login:
```powershell
schtasks /create /tn "DueSyncDailyDigest" /tr "python -m duelist digest --if-not-sent-today" /sc daily /st 08:00 /ri 15 /du 24:00
```
*(Tip: In Windows Task Scheduler GUI, check "Run task as soon as possible after a scheduled start is missed" so that if your computer was asleep or off at 08:00, the digest will arrive immediately after you log in).*

> **Note on Always-On Delivery:** Scheduled commands run only when your computer is powered on and connected to the internet. For 24/7 delivery without relying on your laptop being awake, run the CLI task on a lightweight always-on server, Raspberry Pi, or cloud VM.

### 5. Limits, Tips & Privacy
* **Sending Limits:** Standard Gmail accounts allow up to 500 emails/day, which is far beyond one digest per day.
* **Inbox Placement:** If the first digest email lands in your Spam or Junk folder, mark it "Not spam". Sending to your own email address works best.
* **Privacy:** Emails are sent directly through your configured SMTP server to your personal address. No data is sent to third parties or tracking servers.
* **Adding WhatsApp later:** Notification delivery is abstracted in `cli/duelist/channels/`. A WhatsApp channel can be added in the future as another channel without modifying the core `digest.py` logic.

---

## 5. Testing

Run the automated test suite using `pytest`:
```bash
python -m pytest cli/tests
```
All 33 unit and integration tests cover:
- JSON persistence, atomic file replacement, and corruption backup.
- Urgency classification boundaries and color mapping.
- Date parsing with relative expressions and year-rollovers.
- Summary report categorization and `.docx` / `.md` generation.
- Email digest data building (sorting, 60-char title truncation, overdue day calculations, empty states).
- Accessible table-based HTML email rendering with inline CSS, WCAG AA contrast, and `html.escape()` security.
- Email address validation (rejecting header injection) and masking.
- Mocked SMTP delivery (`smtplib.SMTP`, STARTTLS, SSL, certificate verification, and error handling).
