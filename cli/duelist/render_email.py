"""
DueSync Email & Plain-Text Digest Renderer
Pure functions for converting DigestData into beautiful, accessible table-based HTML
and matching plain-text representations.
No network calls or file access are performed in this module.
"""

import html
import re
from typing import Tuple

from duelist.digest import DigestData, DigestSection, DigestTaskItem


def clean_header_value(text: str, max_len: int = 100) -> str:
    """Strip newlines and control characters from header values and enforce length limits."""
    if not text:
        return ""
    # Strip carriage returns and newlines to prevent header injection
    cleaned = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    # Remove any unprintable ASCII / control characters
    cleaned = "".join(ch for ch in cleaned if ord(ch) >= 32)
    # Collapse consecutive spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_len]


def render_subject(data: DigestData) -> str:
    """
    Build clean subject line:
    e.g. 'DueSync · 3 due today, 2 tomorrow' (adds '· 1 overdue' when relevant)
    """
    if data.is_empty:
        return clean_header_value("DueSync · All clear today ✅", max_len=100)

    parts = []
    today_count = data.today_section.count if data.today_section else 0
    tomorrow_count = data.tomorrow_section.count if data.tomorrow_section else 0
    overdue_count = data.overdue_section.count if data.overdue_section else 0

    is_hinglish = (data.labels or "").strip().lower() == "hinglish"
    today_word = "aaj" if is_hinglish else "due today"
    tomorrow_word = "kal" if is_hinglish else "tomorrow"

    if today_count > 0:
        parts.append(f"{today_count} {today_word}")
    if tomorrow_count > 0:
        parts.append(f"{tomorrow_count} {tomorrow_word}")

    primary_desc = ", ".join(parts) if parts else "Daily Digest"

    if overdue_count > 0:
        subject = f"DueSync · {primary_desc} · {overdue_count} overdue"
    else:
        subject = f"DueSync · {primary_desc}"

    return clean_header_value(subject, max_len=100)


def render_preheader(data: DigestData) -> str:
    """Build short preheader for email inbox preview."""
    if data.is_empty:
        return "All clear today. No upcoming or overdue deadlines."

    today_cnt = data.today_section.count if data.today_section else 0
    tom_cnt = data.tomorrow_section.count if data.tomorrow_section else 0
    od_cnt = data.overdue_section.count if data.overdue_section else 0

    bits = []
    if today_cnt:
        bits.append(f"{today_cnt} due today")
    if tom_cnt:
        bits.append(f"{tom_cnt} tomorrow")
    if od_cnt:
        bits.append(f"{od_cnt} overdue")
    return ", ".join(bits) if bits else "Your daily deadline briefing"


def render_plain_text(data: DigestData) -> str:
    """
    Build clean ASCII plain-text version of the digest.
    Matches layout in Section 1.
    """
    header_line = f"DueSync                                   {data.date_display}"
    tagline = "Stay ahead of every deadline."
    sections = [header_line, tagline, ""]

    if data.is_empty:
        sections.append("All clear today ✅")
        sections.append("")
        sections.append(f"Sent by duelist · {data.active_count} active, {data.completed_count} completed")
        return "\n".join(sections)

    def format_plain_section(sec: DigestSection) -> List[str]:
        lines = [f"[ {sec.heading_name} · {sec.count} ]"]
        for it in sec.items:
            cls_part = f"        {it.cls}" if it.cls else ""
            status_part = f"        {it.status_label}" if it.status_label else ""
            lines.append(f"  • {it.title}{cls_part}{status_part}")
        if sec.has_more > 0:
            lines.append(f"  +{sec.has_more} more")
        return lines

    if data.today_section:
        sections.extend(format_plain_section(data.today_section))
        sections.append("")

    if data.tomorrow_section:
        sections.extend(format_plain_section(data.tomorrow_section))
        sections.append("")

    if data.overdue_section:
        sections.extend(format_plain_section(data.overdue_section))
        sections.append("")

    sections.append(f"Sent by duelist · {data.active_count} active, {data.completed_count} completed")
    return "\n".join(sections)


def render_html(data: DigestData) -> str:
    """
    Build accessible, single-column table-based HTML email with inline CSS.
    Max width 600px, responsive, WCAG AA compliant contrast, no external scripts or remote images.
    """
    subject_raw = render_subject(data)
    subject_esc = html.escape(subject_raw)
    preheader_esc = html.escape(render_preheader(data))
    date_display_esc = html.escape(data.date_display)

    content_cards = []

    if data.is_empty:
        content_cards.append("""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="padding:40px 16px;text-align:center;">
          <tr>
            <td align="center">
              <div style="display:inline-block;width:52px;height:52px;line-height:52px;border-radius:50%;background-color:#D3F6E6;font-size:26px;margin-bottom:14px;">✅</div>
              <h2 style="margin:0 0 8px 0;font-size:20px;color:#1E1B2E;font-weight:700;">All clear today</h2>
              <p style="margin:0;font-size:14px;color:#6A6682;line-height:1.5;">You have no deadlines due today, tomorrow, or overdue. Great job staying ahead!</p>
            </td>
          </tr>
        </table>
        """)
    else:
        # Today Card
        if data.today_section:
            sec = data.today_section
            sec_heading_esc = html.escape(sec.heading_name)
            rows_html = []
            for it in sec.items:
                title_esc = html.escape(it.title)
                cls_esc = html.escape(it.cls) if it.cls else ""
                cls_span = (
                    f'<span style="color:#6A6682;font-size:12px;margin-left:6px;font-weight:normal;">({cls_esc})</span>'
                    if cls_esc
                    else ""
                )
                rows_html.append(f"""
                <tr>
                  <td style="padding:10px 0;border-bottom:1px solid #ECE8F4;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="vertical-align:middle;font-size:14px;color:#1E1B2E;line-height:1.4;">
                          <strong style="color:#1E1B2E;font-weight:600;">• {title_esc}</strong>{cls_span}
                        </td>
                        <td align="right" style="vertical-align:middle;white-space:nowrap;padding-left:12px;">
                          <span style="display:inline-block;color:#0F5132;background-color:#D3F6E6;font-size:11px;font-weight:700;padding:3px 8px;border-radius:12px;border:1px solid #A3E9C8;">⏰ due today</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                """)

            if sec.has_more > 0:
                rows_html.append(f"""
                <tr>
                  <td style="padding:10px 0 2px 0;font-size:12px;color:#6A6682;font-style:italic;">
                    +{sec.has_more} more
                  </td>
                </tr>
                """)

            content_cards.append(f"""
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;background-color:#FFFFFF;border:1px solid #ECE8F4;border-left:5px solid #2FC48D;border-radius:12px;padding:16px 20px;">
              <tr>
                <td style="padding-bottom:12px;">
                  <span style="display:inline-block;background-color:#D3F6E6;color:#0F5132;font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;letter-spacing:0.3px;">
                    {sec_heading_esc} · {sec.count}
                  </span>
                </td>
              </tr>
              {"".join(rows_html)}
            </table>
            """)

        # Tomorrow Card
        if data.tomorrow_section:
            sec = data.tomorrow_section
            sec_heading_esc = html.escape(sec.heading_name)
            rows_html = []
            for it in sec.items:
                title_esc = html.escape(it.title)
                cls_esc = html.escape(it.cls) if it.cls else ""
                cls_span = (
                    f'<span style="color:#6A6682;font-size:12px;margin-left:6px;font-weight:normal;">({cls_esc})</span>'
                    if cls_esc
                    else ""
                )
                rows_html.append(f"""
                <tr>
                  <td style="padding:10px 0;border-bottom:1px solid #ECE8F4;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="vertical-align:middle;font-size:14px;color:#1E1B2E;line-height:1.4;">
                          <strong style="color:#1E1B2E;font-weight:600;">• {title_esc}</strong>{cls_span}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                """)

            if sec.has_more > 0:
                rows_html.append(f"""
                <tr>
                  <td style="padding:10px 0 2px 0;font-size:12px;color:#6A6682;font-style:italic;">
                    +{sec.has_more} more
                  </td>
                </tr>
                """)

            content_cards.append(f"""
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;background-color:#FFFFFF;border:1px solid #ECE8F4;border-left:5px solid #F59E0B;border-radius:12px;padding:16px 20px;">
              <tr>
                <td style="padding-bottom:12px;">
                  <span style="display:inline-block;background-color:#FFE9BD;color:#854D0E;font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;letter-spacing:0.3px;">
                    {sec_heading_esc} · {sec.count}
                  </span>
                </td>
              </tr>
              {"".join(rows_html)}
            </table>
            """)

        # Overdue Card
        if data.overdue_section:
            sec = data.overdue_section
            sec_heading_esc = html.escape(sec.heading_name)
            rows_html = []
            for it in sec.items:
                title_esc = html.escape(it.title)
                cls_esc = html.escape(it.cls) if it.cls else ""
                cls_span = (
                    f'<span style="color:#6A6682;font-size:12px;margin-left:6px;font-weight:normal;">({cls_esc})</span>'
                    if cls_esc
                    else ""
                )
                status_esc = html.escape(it.status_label)
                rows_html.append(f"""
                <tr>
                  <td style="padding:10px 0;border-bottom:1px solid #ECE8F4;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="vertical-align:middle;font-size:14px;color:#1E1B2E;line-height:1.4;">
                          <strong style="color:#1E1B2E;font-weight:600;">• {title_esc}</strong>{cls_span}
                        </td>
                        <td align="right" style="vertical-align:middle;white-space:nowrap;padding-left:12px;">
                          <span style="display:inline-block;color:#842029;background-color:#FFDDE3;font-size:11px;font-weight:700;padding:3px 8px;border-radius:12px;border:1px solid #F8B4C0;">⚠️ {status_esc}</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                """)

            if sec.has_more > 0:
                rows_html.append(f"""
                <tr>
                  <td style="padding:10px 0 2px 0;font-size:12px;color:#6A6682;font-style:italic;">
                    +{sec.has_more} more
                  </td>
                </tr>
                """)

            content_cards.append(f"""
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;background-color:#FFFFFF;border:1px solid #ECE8F4;border-left:5px solid #F2546F;border-radius:12px;padding:16px 20px;">
              <tr>
                <td style="padding-bottom:12px;">
                  <span style="display:inline-block;background-color:#FFDDE3;color:#842029;font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;letter-spacing:0.3px;">
                    ⚠️ {sec_heading_esc} · {sec.count}
                  </span>
                </td>
              </tr>
              {"".join(rows_html)}
            </table>
            """)

    cards_markup = "\n".join(content_cards)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>{subject_esc}</title>
</head>
<body style="margin:0;padding:0;background-color:#F4F3F9;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;color:#1E1B2E;">
  <!-- Preheader text for inbox preview -->
  <div style="display:none;font-size:1px;color:#ffffff;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;mso-hide:all;">
    {preheader_esc}
  </div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#F4F3F9;padding:24px 12px;">
    <tr>
      <td align="center">
        <!-- Center constrained container table (fluid up to 600px) -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;margin:0 auto;background-color:#FFFFFF;border-radius:16px;box-shadow:0 4px 16px rgba(0,0,0,0.04);overflow:hidden;">
          
          <!-- Top Header Strip: Teal #14645B with White text and Yellow #FFC53D accent -->
          <tr>
            <td style="background-color:#14645B;padding:24px 28px;color:#FFFFFF;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <h1 style="margin:0;font-size:24px;font-weight:700;color:#FFFFFF;letter-spacing:-0.4px;">
                      DueSync<span style="display:inline-block;width:8px;height:8px;background-color:#FFC53D;border-radius:50%;margin-left:6px;vertical-align:middle;"></span>
                    </h1>
                    <p style="margin:4px 0 0 0;font-size:13px;color:#D3F6E6;letter-spacing:0.2px;">
                      Stay ahead of every deadline.
                    </p>
                  </td>
                  <td align="right" style="vertical-align:middle;font-size:13px;color:#D3F6E6;font-weight:500;">
                    {date_display_esc}
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Content Section Area -->
          <tr>
            <td style="padding:24px 24px 8px 24px;background-color:#FFFFFF;">
              {cards_markup}
            </td>
          </tr>

          <!-- Footer Area -->
          <tr>
            <td style="background-color:#FBFBFE;border-top:1px solid #ECE8F4;padding:18px 24px;text-align:center;">
              <p style="margin:0;font-size:12px;color:#6A6682;line-height:1.5;">
                Sent by duelist · {data.active_count} active, {data.completed_count} completed
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def render_email_package(data: DigestData) -> Tuple[str, str, str]:
    """Return complete triple (subject, plain_text, html)."""
    subject = render_subject(data)
    text = render_plain_text(data)
    html_body = render_html(data)
    return subject, text, html_body
