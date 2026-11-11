#!/usr/bin/env python3
"""Send personalized electric-vehicle outreach through Zoho SMTP."""

from __future__ import annotations

import argparse
import base64
import csv
import ctypes
import getpass
import html
import mimetypes
import os
import random
import re
import smtplib
import ssl
import subprocess
import sys
import time
from ctypes import wintypes
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "开发信内容"
PASSWORD_FILE = ROOT / ".zoho_app_password.dpapi"
POWERSHELL_PASSWORD_FILE = ROOT / ".zoho_app_password.secure"
DPAPI_ENTROPY = b"chengcang-ev-zoho-smtp-v1"
SENDER_EMAIL = "leo@chengcangtrading.com"
SENDER_NAME = "Leo"
COMPANY = "LIEDE CHENGCANG TRADING (GUANGDONG) CO., LTD."
PHONE = "+86 130 3366 9180"
MAX_MESSAGE_BYTES = 1_000_000
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
REQUIRED_FIELDS = {"email", "first_name", "company", "country", "template_type", "personalization_hook"}
INLINE_IMAGE_SOURCES = [
    ("Electric Two-Wheeler Series Showcase.png", "01_two_wheeler.jpg", 1200, 76),
    ("Electric Tricycle Showcase Banner.png", "02_tricycle.jpg", 1200, 76),
    ("展厅.png", "03_showroom.jpg", 1100, 72),
    ("名片.png", "04_business_card.jpg", 690, 82),
]
COMPRESSED_IMAGE_DIR = ROOT / "开发信成品" / "邮件图片"

TEMPLATES = {
    "commuter": {
        "label": "Commuter electric two-wheeler importers and retailers",
        "category": "commuter electric two-wheelers",
        "subject": "{company}: commuter e-scooters for {market}",
        "body": """Hi {first_name},

I am Leo from the overseas sales team of an electric vehicle manufacturer in Shandong, China. I noticed this on your website: {personalization_hook}. We manufacture electric two-wheelers and cargo and passenger electric tricycles. Our experience covers commuter, delivery, and utility models, with competitive factory pricing and production lead times confirmed for each configuration and order. I thought our commuter range may be relevant to your portfolio in {country}.

Our catalogue includes 350W, 48V models with 12Ah or 20Ah battery configurations. Lead-acid and lithium options are available on selected models. We can shortlist models around your preferred retail price, battery type, and local requirements.

Would a short model shortlist be useful? If you share your target models and trial order quantity, I can send current EXW quotations and lead times for matching configurations.

If this message is not relevant to your business, I apologize for the interruption. Please reply "No further emails" and I will make sure you do not receive another outreach email from me.

Best regards,
{sender_name} | Sales Manager
{sender_company}
Guangzhou, China | {sender_email} | WhatsApp: {sender_phone}""",
    },
    "motorcycle": {
        "label": "Electric motorcycle importers and distributors",
        "category": "electric motorcycles",
        "subject": "{company}: 60V/72V electric motorcycles for {market}",
        "body": """Hi {first_name},

I am Leo from the overseas sales team of an electric vehicle manufacturer in Shandong, China. I noticed this on your website: {personalization_hook}. We manufacture electric two-wheelers and cargo and passenger electric tricycles. Our experience includes higher-power electric motorcycles, with competitive factory pricing and production lead times confirmed for each configuration and order. I thought our motorcycle range may complement your portfolio in {country}.

Our catalogue includes models from 1,000W to 3,000W and 60V/72V configurations, with battery choices varying by model. We can check the requested configuration against your market's vehicle classification and road-use rules before preparing a quotation.

Which power class and battery type are you currently sourcing? With your target quantity, I can send a focused model selection with current EXW price and lead time.

If this message is not relevant to your business, I apologize for the interruption. Please reply "No further emails" and I will make sure you do not receive another outreach email from me.

Best regards,
{sender_name} | Sales Manager
{sender_company}
Guangzhou, China | {sender_email} | WhatsApp: {sender_phone}""",
    },
    "tricycle": {
        "label": "Cargo and passenger electric tricycle buyers",
        "category": "cargo and passenger electric tricycles",
        "subject": "{company}: cargo and passenger e-tricycles for {market}",
        "body": """Hi {first_name},

I am Leo from the overseas sales team of an electric vehicle manufacturer in Shandong, China. I noticed this on your website: {personalization_hook}. We manufacture cargo and passenger electric tricycles as well as electric two-wheelers. Our experience covers different utility layouts, with competitive factory pricing and production lead times confirmed for each configuration and order.

The range covers different cargo and passenger layouts. To recommend a suitable model, it would help to know the intended use, expected payload or passenger capacity, operating conditions, and local vehicle requirements.

Are you currently sourcing electric tricycles for resale or fleet use? If you share the application and expected quantity, I can send the relevant model details and a current EXW quotation for review.

If this message is not relevant to your business, I apologize for the interruption. Please reply "No further emails" and I will make sure you do not receive another outreach email from me.

Best regards,
{sender_name} | Sales Manager
{sender_company}
Guangzhou, China | {sender_email} | WhatsApp: {sender_phone}""",
    },
    "multi_category": {
        "label": "Multi-category importers and OEM/private-label channels",
        "category": "electric vehicle portfolio",
        "subject": "{company}: an electric vehicle supply option for {market}",
        "body": """Hi {first_name},

I am Leo from the overseas sales team of an electric vehicle manufacturer in Shandong, China. I noticed this on your website: {personalization_hook}. We manufacture electric two-wheelers and cargo and passenger electric tricycles. Our experience covers commuter, delivery, and utility models, with competitive factory pricing and production lead times confirmed for each configuration and order.

We coordinate supply across electric two-wheelers and cargo or passenger tricycles, with model, battery, and appearance options depending on the product. OEM/ODM requests can be reviewed against the selected factory and order requirements.

If you are reviewing suppliers for {focus_product}, send me your target specification, expected quantity, and destination. I can check a focused selection and confirm the matching factory price and production schedule.

If this message is not relevant to your business, I apologize for the interruption. Please reply "No further emails" and I will make sure you do not receive another outreach email from me.

Best regards,
{sender_name} | Sales Manager
{sender_company}
Guangzhou, China | {sender_email} | WhatsApp: {sender_phone}""",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError("CSV is missing columns: " + ", ".join(sorted(missing)))
        rows = []
        for line, item in enumerate(reader, start=2):
            row = {key: (value or "").strip() for key, value in item.items() if key}
            if not row.get("email") or not EMAIL_RE.match(row["email"]):
                print(f"Skip row {line}: invalid email address")
                continue
            if row.get("template_type") not in TEMPLATES:
                raise ValueError(f"Row {line}: template_type must be one of {', '.join(TEMPLATES)}")
            missing_values = [key for key in REQUIRED_FIELDS if not row.get(key)]
            if missing_values:
                raise ValueError(f"Row {line}: fill in {', '.join(sorted(missing_values))}")
            rows.append(row)
        return rows


def prepare(row: dict[str, str]) -> tuple[str, str, list[Path]]:
    template = TEMPLATES[row["template_type"]]
    focus = row.get("focus_product", "").strip() or template["category"]
    values = {
        "first_name": row["first_name"],
        "company": row["company"],
        "country": row["country"],
        "market": row["country"],
        "focus_product": focus,
        "personalization_hook": row["personalization_hook"],
        "sender_name": "Leo",
        "sender_company": COMPANY,
        "sender_email": SENDER_EMAIL,
        "sender_phone": PHONE,
    }
    subject = row.get("subject_line", "").strip() or template["subject"].format_map(values)
    body = template["body"].format_map(values)
    COMPRESSED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for source_name, output_name, max_width, quality in INLINE_IMAGE_SOURCES:
        source = CONTENT_DIR / source_name
        destination = COMPRESSED_IMAGE_DIR / output_name
        if not source.is_file():
            raise ValueError(f"Inline image not found: {source}")
        if not destination.is_file() or destination.stat().st_mtime < source.stat().st_mtime:
            with Image.open(source) as original:
                image = ImageOps.exif_transpose(original).convert("RGB")
                if image.width > max_width:
                    height = round(image.height * max_width / image.width)
                    image = image.resize((max_width, height), Image.Resampling.LANCZOS)
                image.save(destination, format="JPEG", quality=quality, optimize=True, progressive=True)
        paths.append(destination)
    return subject, body, paths


def image_part(path: Path, cid: str) -> tuple[bytes, str, str]:
    mime, _ = mimetypes.guess_type(path.name)
    if not mime or not mime.startswith("image/"):
        raise ValueError(f"Unsupported image file: {path.name}")
    maintype, subtype = mime.split("/", 1)
    return path.read_bytes(), maintype, subtype


def make_message(address: str, subject: str, body: str, images: list[Path]) -> EmailMessage:
    message = EmailMessage()
    message["From"] = formataddr((SENDER_NAME, SENDER_EMAIL))
    message["To"] = address
    message["Subject"] = subject
    message["Reply-To"] = SENDER_EMAIL
    message["Auto-Submitted"] = "auto-generated"
    message.set_content(body)
    paragraphs = body.split("\n\n")
    html_body = "<html><body style=\"font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:#222\">"
    html_body += "".join(f"<p>{html.escape(line)}</p>" for line in paragraphs[:3])
    html_body += "<p>Our product ranges and showroom are pictured below.</p>"
    for index, path in enumerate(images[:3]):
        html_body += f'<p><img src="cid:outreach-image-{index}" alt="{html.escape(path.stem)}" style="display:block;max-width:640px;width:100%;height:auto;margin:18px 0"></p>'
    html_body += "".join(f"<p>{html.escape(line)}</p>" for line in paragraphs[3:])
    if len(images) > 3:
        html_body += f'<p><img src="cid:outreach-image-3" alt="{html.escape(images[3].stem)}" style="display:block;max-width:640px;width:100%;height:auto;margin:18px 0"></p>'
    html_body += "</body></html>"
    message.add_alternative(html_body, subtype="html")
    html_part = message.get_payload()[-1]
    for index, path in enumerate(images):
        data, maintype, subtype = image_part(path, f"outreach-image-{index}")
        html_part.add_related(
            data,
            maintype=maintype,
            subtype=subtype,
            cid=f"<outreach-image-{index}>",
            filename=path.name,
            disposition="inline",
        )
    if len(message.as_bytes()) > MAX_MESSAGE_BYTES:
        raise ValueError(f"Email for {address} exceeds the 1,000,000-byte size limit")
    return message


def save_preview(row: dict[str, str], subject: str, body: str, images: list[Path], output_dir: Path) -> Path:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", row["company"]).strip("._-") or "prospect"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{safe_name}_{row['template_type']}.html"
    parts = [f"<h2>{html.escape(subject)}</h2>", f"<p>To: {html.escape(row['email'])}</p>"]
    paragraphs = body.split("\n\n")
    parts.append("<div style=\"font-family:Arial,sans-serif;line-height:1.6\">")
    parts.extend(f"<p>{html.escape(paragraph)}</p>" for paragraph in paragraphs[:3])
    parts.append("<p>Our product ranges and showroom are pictured below.</p>")
    for path in images[:3]:
        data, maintype, subtype = image_part(path, "")
        parts.append(f'<p><img style="display:block;max-width:640px;width:100%;height:auto" alt="{html.escape(path.stem)}" src="data:{maintype}/{subtype};base64,{base64.b64encode(data).decode("ascii")}"></p>')
    parts.extend(f"<p>{html.escape(paragraph)}</p>" for paragraph in paragraphs[3:])
    if len(images) > 3:
        path = images[3]
        data, maintype, subtype = image_part(path, "")
        parts.append(f'<p><img style="display:block;max-width:640px;width:100%;height:auto" alt="{html.escape(path.stem)}" src="data:{maintype}/{subtype};base64,{base64.b64encode(data).decode("ascii")}"></p>')
    parts.append("</div>")
    output.write_text("\n".join(parts), encoding="utf-8")
    return output


def append_log(path: Path, row: dict[str, str], status: str, detail: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        if not exists:
            writer.writerow(["timestamp_utc", "email", "company", "status", "detail"])
        writer.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), row["email"], row.get("company", ""), status, detail[:300]])


def connect(host: str, port: int, password: str) -> smtplib.SMTP:
    context = ssl.create_default_context()
    if port == 465:
        client: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=30, context=context)
        client.ehlo()
    else:
        client = smtplib.SMTP(host, port, timeout=30)
        client.ehlo()
        client.starttls(context=context)
        client.ehlo()
    client.login(SENDER_EMAIL, "".join(password.split()))
    return client


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _dpapi(data: bytes | bytearray, protect: bool) -> bytes:
    if os.name != "nt":
        raise RuntimeError("Encrypted password storage is available only on Windows.")
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    if protect:
        crypt.argtypes = [ctypes.POINTER(DATA_BLOB), wintypes.LPCWSTR, ctypes.POINTER(DATA_BLOB), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB)]
    else:
        crypt.argtypes = [ctypes.POINTER(DATA_BLOB), ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(DATA_BLOB), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB)]
    crypt.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    source_buffer = (ctypes.c_byte * max(1, len(data))).from_buffer_copy(data)
    entropy_buffer = (ctypes.c_byte * len(DPAPI_ENTROPY)).from_buffer_copy(DPAPI_ENTROPY)
    source = DATA_BLOB(len(data), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_byte)))
    entropy = DATA_BLOB(len(DPAPI_ENTROPY), ctypes.cast(entropy_buffer, ctypes.POINTER(ctypes.c_byte)))
    output = DATA_BLOB()
    description = wintypes.LPWSTR()
    try:
        if protect:
            ok = crypt(ctypes.byref(source), "Chengcang Zoho SMTP", ctypes.byref(entropy), None, None, 0x1, ctypes.byref(output))
        else:
            ok = crypt(ctypes.byref(source), ctypes.byref(description), ctypes.byref(entropy), None, None, 0x1, ctypes.byref(output))
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.memset(ctypes.addressof(source_buffer), 0, max(1, len(data)))
        if output.pbData:
            if not protect and output.cbData:
                ctypes.memset(output.pbData, 0, output.cbData)
            kernel32.LocalFree(output.pbData)
        if description:
            kernel32.LocalFree(description)


def save_password() -> None:
    if PASSWORD_FILE.exists() and input("A saved password exists. Type REPLACE to replace it: ").strip() != "REPLACE":
        print("Kept the existing encrypted credential.")
        return
    password = getpass.getpass("Zoho app-specific password (input hidden): ")
    if not password:
        raise ValueError("Password cannot be empty.")
    confirmation = getpass.getpass("Enter it once more to confirm (input hidden): ")
    if password != confirmation:
        raise ValueError("The two entries did not match; nothing was saved.")
    protected = _dpapi(password.encode("utf-8"), protect=True)
    PASSWORD_FILE.write_bytes(b"EV-ZOHO-DPAPI-1\n" + base64.b64encode(protected) + b"\n")
    print(f"Saved a Windows-user-encrypted credential to {PASSWORD_FILE}. The password itself is not stored as text.")


def get_password(allow_prompt: bool = True) -> str:
    if PASSWORD_FILE.exists():
        content = PASSWORD_FILE.read_bytes().splitlines()
        if len(content) != 2 or content[0] != b"EV-ZOHO-DPAPI-1":
            raise ValueError("Saved credential file is invalid. Recreate it with --save-password.")
        try:
            encrypted = base64.b64decode(content[1], validate=True)
            return _dpapi(encrypted, protect=False).decode("utf-8")
        except (ValueError, UnicodeDecodeError, OSError) as exc:
            raise ValueError("Could not decrypt saved credential for this Windows account. Recreate it with --save-password.") from exc
    if POWERSHELL_PASSWORD_FILE.exists():
        path = str(POWERSHELL_PASSWORD_FILE).replace("'", "''")
        script = (
            "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); "
            f"$secure=ConvertTo-SecureString -String (Get-Content -Raw -LiteralPath '{path}').Trim(); "
            "$password=[System.Net.NetworkCredential]::new('', $secure).Password; "
            "[Console]::Out.Write($password)"
        )
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        try:
            result = subprocess.run(
                ["pwsh.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as exc:
            raise RuntimeError("Could not read the locally encrypted PowerShell credential.") from exc
        if result.returncode != 0 or not result.stdout:
            raise RuntimeError("Could not decrypt the locally saved Zoho credential for this Windows account.")
        return result.stdout.rstrip("\r\n")
    if not allow_prompt:
        raise RuntimeError("No local encrypted Zoho credential is available; save it interactively before scheduled sending.")
    return getpass.getpass("Zoho app-specific password (input hidden): ")


def confirm_send() -> bool:
    try:
        return input("Type SEND to authorize this email: ").strip() == "SEND"
    except EOFError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Personalized electric-vehicle outreach via Zoho SMTP")
    parser.add_argument("--csv", type=Path, default=ROOT / "leads_template.csv", help="Prospect CSV")
    parser.add_argument("--preview-dir", type=Path, default=ROOT / "邮件预览")
    parser.add_argument("--suppression", type=Path, default=ROOT / "unsubscribed.txt")
    parser.add_argument("--log", type=Path, default=ROOT / "send_log.csv")
    parser.add_argument("--test-log", type=Path, default=ROOT / "test_send_log.csv")
    parser.add_argument("--sender-email", default=SENDER_EMAIL, help="Zoho mailbox (default: leo@chengcangtrading.com)")
    parser.add_argument("--smtp-host", default="smtp.zoho.com")
    parser.add_argument("--smtp-port", type=int, default=587)
    parser.add_argument("--check-connection", action="store_true", help="Authenticate without sending")
    parser.add_argument("--save-password", action="store_true", help="Save the Zoho app password encrypted for this Windows user")
    parser.add_argument("--test-recipient", help="Send one selected development-email template to a test mailbox")
    parser.add_argument("--test-template", choices=sorted(TEMPLATES), help="Required with --test-recipient")
    parser.add_argument("--test-company", help="Test company name")
    parser.add_argument("--test-country", help="Test destination market")
    parser.add_argument("--test-observation", help="Company-specific observation used in the message")
    parser.add_argument("--test-focus", help="Product focus for the test message")
    parser.add_argument("--test-first-name", default="Alex", help="Greeting name in the test message")
    parser.add_argument("--send", action="store_true", help="Send eligible CSV rows after explicit confirmation")
    parser.add_argument("--max-emails", type=int, default=10, help="Maximum sends per run (1-50)")
    parser.add_argument("--delay", type=int, default=60, help="Seconds between messages")
    parser.add_argument("--random-delay-min", type=int, help="Randomized minimum seconds between messages")
    parser.add_argument("--random-delay-max", type=int, help="Randomized maximum seconds between messages")
    parser.add_argument(
        "--scheduled-auto-send",
        action="store_true",
        help="Skip interactive confirmation for a pre-authorized scheduled send; requires --send and explicit eligibility evidence in every row",
    )
    args = parser.parse_args()

    if args.sender_email != SENDER_EMAIL:
        parser.error("This sender is configured for leo@chengcangtrading.com; change SENDER_EMAIL in the script only if needed")
    if args.max_emails < 1 or args.max_emails > 50 or args.delay < 0:
        parser.error("--max-emails must be 1-50 and --delay cannot be negative")
    if (args.random_delay_min is None) != (args.random_delay_max is None):
        parser.error("--random-delay-min and --random-delay-max must be used together")
    if args.random_delay_min is not None and (args.random_delay_min < 0 or args.random_delay_max < args.random_delay_min):
        parser.error("Random delay bounds must be nonnegative and max must be at least min")
    if sum([args.check_connection, args.save_password, bool(args.test_recipient), args.send]) > 1:
        parser.error("Use only one of --save-password, --check-connection, --test-recipient, or --send")
    if args.scheduled_auto_send and not args.send:
        parser.error("--scheduled-auto-send requires --send")

    if args.save_password:
        try:
            save_password()
            return 0
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"Could not save encrypted credential: {exc}", file=sys.stderr)
            return 1

    if args.check_connection:
        try:
            with connect(args.smtp_host, args.smtp_port, get_password()):
                print(f"Zoho SMTP authentication succeeded ({args.smtp_host}:{args.smtp_port}). No email sent.")
            return 0
        except (OSError, RuntimeError, ValueError, smtplib.SMTPException) as exc:
            print(f"Zoho SMTP connection failed: {exc}", file=sys.stderr)
            return 1

    if args.test_recipient:
        if not EMAIL_RE.match(args.test_recipient.strip()):
            parser.error("--test-recipient must be a valid email address")
        if not all([args.test_template, args.test_company, args.test_country, args.test_observation]):
            parser.error("--test-recipient requires --test-template, --test-company, --test-country, and --test-observation")
        row = {
            "email": args.test_recipient.strip().lower(),
            "first_name": args.test_first_name.strip(),
            "company": args.test_company.strip(),
            "country": args.test_country.strip(),
            "template_type": args.test_template,
            "personalization_hook": args.test_observation.strip(),
            "focus_product": (args.test_focus or "").strip(),
        }
        try:
            subject, body, images = prepare(row)
        except (OSError, ValueError) as exc:
            print(f"Cannot prepare test email: {exc}", file=sys.stderr)
            return 2
        print(f"To: {row['email']}\nSubject: {subject}\n\n{body}\n\nInline images: {', '.join(path.name for path in images)}")
        if not confirm_send():
            print("Cancelled. No email sent.")
            return 0
        try:
            with connect(args.smtp_host, args.smtp_port, get_password()) as client:
                client.send_message(make_message(row["email"], subject, body, images))
            append_log(args.test_log, row, "sent")
            print(f"Test development email sent to {row['email']}.")
            return 0
        except (OSError, RuntimeError, ValueError, smtplib.SMTPException) as exc:
            append_log(args.test_log, row, "failed", str(exc))
            print(f"Test send failed: {exc}", file=sys.stderr)
            return 1

    try:
        rows = read_csv(args.csv)
        suppressed = {line.strip().lower() for line in args.suppression.read_text(encoding="utf-8-sig").splitlines() if line.strip() and not line.lstrip().startswith("#")} if args.suppression.exists() else set()
        already_processed = set()
        if args.log.exists():
            with args.log.open("r", encoding="utf-8-sig", newline="") as stream:
                already_processed = {
                    (r.get("email") or "").strip().lower()
                    for r in csv.DictReader(stream)
                    if (r.get("status") or "").strip().lower() in {"sent", "failed"}
                }
        prepared = []
        seen = set()
        for row in rows:
            address = row["email"].lower()
            if address in seen or address in suppressed or address in already_processed or row.get("do_not_contact", "").lower() in {"yes", "true", "1", "y"}:
                print("Skipped duplicate, suppressed, previously processed, or opted-out address.")
                continue
            if args.scheduled_auto_send:
                documented = all(row.get(key, "").strip() for key in ("send_eligible", "contact_legal_basis", "contact_legal_source", "personalization_source"))
                eligible = row.get("send_eligible", "").strip().lower() in {"yes", "true", "1", "y"}
                if not documented or not eligible:
                    print("Skipped scheduled recipient without documented contact eligibility and personalization sources.")
                    continue
            seen.add(address)
            subject, body, images = prepare(row)
            prepared.append((row, subject, body, images))
        selected = prepared[:args.max_emails]
        if not selected:
            print("No eligible recipients.")
            return 0
        if args.random_delay_min is not None:
            worst_case_seconds = (len(selected) - 1) * args.random_delay_max + len(selected) * 35 + 30
            if worst_case_seconds > 14400:
                parser.error("Selected emails and maximum random delay could exceed the four-hour window")
        for row, subject, body, images in selected:
            preview_path = save_preview(row, subject, body, images, args.preview_dir)
            if args.scheduled_auto_send:
                print("Local scheduled email preview saved.")
            else:
                print(f"\nTo: {row['email']}\nSubject: {subject}\n\n{body}\nInline images: {', '.join(path.name for path in images)}")
                print(f"HTML preview: {preview_path}")
    except (OSError, ValueError) as exc:
        print(f"Cannot prepare email list: {exc}", file=sys.stderr)
        return 2

    if not args.send:
        print("Preview only. No email was sent.")
        return 0
    if not args.scheduled_auto_send and not confirm_send():
        print("Cancelled. No email sent.")
        return 0
    sent = 0
    try:
        password = get_password(allow_prompt=not args.scheduled_auto_send)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Could not read the local Zoho credential: {exc}", file=sys.stderr)
        return 1
    try:
        if args.scheduled_auto_send:
            try:
                with connect(args.smtp_host, args.smtp_port, password):
                    pass
            except (OSError, RuntimeError, ValueError, smtplib.SMTPException) as exc:
                print(f"Scheduled send stopped because Zoho authentication failed: {exc}", file=sys.stderr)
                return 1
        for index, (row, subject, body, images) in enumerate(selected):
            try:
                with connect(args.smtp_host, args.smtp_port, password) as client:
                    client.send_message(make_message(row["email"], subject, body, images))
                append_log(args.log, row, "sent")
                sent += 1
                print("Sent one scheduled email." if args.scheduled_auto_send else f"Sent: {row['email']}")
            except (OSError, RuntimeError, ValueError, smtplib.SMTPException) as exc:
                append_log(args.log, row, "failed", str(exc))
                print(f"Scheduled email failed: {exc}" if args.scheduled_auto_send else f"Failed: {row['email']}: {exc}", file=sys.stderr)
                if args.scheduled_auto_send:
                    return 1
            if index + 1 < len(selected):
                delay = random.randint(args.random_delay_min, args.random_delay_max) if args.random_delay_min is not None else args.delay
                if delay:
                    print(f"Next message in {delay} seconds.")
                    time.sleep(delay)
    finally:
        password = ""
    print(f"Finished. Sent {sent} of {len(selected)} selected emails.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
