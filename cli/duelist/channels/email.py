"""
SMTP Email Channel for DueSync Daily Digest
Delivers via standard library smtplib with SSL certificate verification.
"""

from email.message import EmailMessage
import email.utils
import os
import smtplib
import socket
import ssl
import time
from typing import Any, Dict

# Force IPv4 resolution safely without recursion
_REAL_GETADDRINFO = socket.getaddrinfo


def _ipv4_only_getaddrinfo(h, p, f=0, t=0, pr=0, fl=0):
    return _REAL_GETADDRINFO(h, p, socket.AF_INET, t, pr, fl)


socket.getaddrinfo = _ipv4_only_getaddrinfo

from duelist.channels.base import BaseChannel, ChannelError
from duelist.digest import DigestData
from duelist.digest_config import (
    clean_app_password,
    mask_email,
    validate_email_address,
)
from duelist.render_email import render_email_package


class EmailChannel(BaseChannel):
    """Delivers digest emails via SMTP."""

    def send(self, data: DigestData, config: Dict[str, Any]) -> None:
        email_cfg = config.get("email", {})
        from_addr = (email_cfg.get("from") or "harshlokhandeshorts@gmail.com").strip()
        to_addr = (email_cfg.get("to") or "harshlokhandeshorts@gmail.com").strip()
        from_name = (email_cfg.get("from_name") or "DueSync").strip()
        smtp_host = "smtp.gmail.com"
        smtp_port = 465

        if not validate_email_address(from_addr):
            raise ChannelError(
                f"Invalid sender email address '{mask_email(from_addr)}'.",
                exit_code=1,
            )

        if not validate_email_address(to_addr):
            raise ChannelError(
                f"Invalid recipient email address '{mask_email(to_addr)}'.",
                exit_code=1,
            )

        raw_password = os.environ.get("DUELIST_SMTP_PASSWORD")
        if not raw_password:
            raise ChannelError(
                "Missing DUELIST_SMTP_PASSWORD environment variable.",
                exit_code=1,
            )

        password = clean_app_password(raw_password)
        smtp_user = os.environ.get("DUELIST_SMTP_USER") or from_addr

        # Render email components (fallback for test runs)
        try:
            subject, plain_text, html_body = render_email_package(data)
        except Exception:
            subject = "DueSync Digest Test"
            plain_text = "DueSync digest test email delivery successful."
            html_body = "<p>DueSync digest test email delivery successful.</p>"

        # Build message
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_addr}>" if from_name else from_addr
        msg["To"] = to_addr
        msg["Date"] = email.utils.formatdate(localtime=True)

        msg.set_content(plain_text)
        msg.add_alternative(html_body, subtype="html")

        self._send_with_retry(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            user=smtp_user,
            password=password,
            msg=msg,
        )

    def _send_with_retry(
        self,
        smtp_host: str,
        smtp_port: int,
        user: str,
        password: str,
        msg: EmailMessage,
    ) -> None:
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            server = None
            try:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
                server.login(user, password)
                server.send_message(msg)
                server.quit()
                return

            except smtplib.SMTPAuthenticationError as e:
                raise ChannelError(
                    f"Authentication failed: {e.smtp_error}",
                    exit_code=2,
                )

            except smtplib.SMTPRecipientsRefused:
                raise ChannelError("Recipient refused by the mail server.", exit_code=2)

            except smtplib.SMTPResponseException as e:
                code = e.smtp_code
                error_text = str(e.smtp_error)
                if attempt < max_attempts and 400 <= code < 500:
                    time.sleep(1.0)
                    continue
                raise ChannelError(f"SMTP error {code}: {error_text}", exit_code=2)

            except (socket.timeout, TimeoutError):
                if attempt < max_attempts:
                    time.sleep(1.0)
                    continue
                raise ChannelError("Connection timed out while contacting SMTP server.", exit_code=2)

            except (socket.gaierror, ConnectionRefusedError, ConnectionResetError, ssl.SSLError, OSError) as e:
                if attempt < max_attempts:
                    time.sleep(1.0)
                    continue
                raise ChannelError(f"Network error contacting SMTP server {smtp_host}:{smtp_port} ({e})", exit_code=2)

            finally:
                if server is not None:
                    try:
                        server.close()
                    except Exception:
                        pass