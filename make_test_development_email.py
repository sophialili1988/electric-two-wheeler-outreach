#!/usr/bin/env python3
"""Prepare and optionally send a compressed, image-rich EV test email."""

from __future__ import annotations

import argparse
import base64
import mimetypes
import smtplib
import ssl
import sys
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import formataddr
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "开发信内容"
OUTPUT = ROOT / "开发信成品" / "测试邮件_多品类电动车"
EMAIL_FILE = OUTPUT / "TEST_多品类电动车开发信.eml"
PREVIEW_FILE = OUTPUT / "TEST_多品类电动车开发信.html"
SENDER = "leo@chengcangtrading.com"
SENDER_NAME = "Leo"
RECIPIENT = "molisourcing@gmail.com"
MAX_MESSAGE_BYTES = 1_000_000
IMAGES = [
    ("Electric Two-Wheeler Series Showcase.png", "01_two_wheeler.jpg", "Electric two-wheeler series"),
    ("Electric Tricycle Showcase Banner.png", "02_tricycle.jpg", "Electric tricycle series"),
    ("展厅.png", "03_showroom.jpg", "Showroom and production overview"),
    ("名片.png", "04_business_card.jpg", "Leo business card"),
]


def compress_images() -> list[tuple[Path, str]]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    for index, (source_name, output_name, alt) in enumerate(IMAGES):
        source_path = SOURCE / source_name
        if not source_path.is_file():
            raise FileNotFoundError(f"Required image is missing: {source_path}")
        width = 1200 if index < 2 else 1100 if index == 2 else 690
        quality = 76 if index < 2 else 72 if index == 2 else 82
        with Image.open(source_path) as original:
            image = ImageOps.exif_transpose(original).convert("RGB")
            if image.width > width:
                height = round(image.height * width / image.width)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            destination = OUTPUT / output_name
            image.save(destination, format="JPEG", quality=quality, optimize=True, progressive=True)
        results.append((destination, alt))
    return results


def create_email(images: list[tuple[Path, str]]) -> tuple[EmailMessage, str, str]:
    company = "Test Company"
    market = "Test Market"
    subject = f"TEST - {company}: electric vehicle supply options for {market}"
    paragraphs = [
        "Hi Alex,",
        "I'm Leo from the overseas sales department of an electric vehicle manufacturer in Shandong, China.",
        "Our main product categories are electric two-wheelers and cargo and passenger tricycles. As the manufacturer, we offer competitive factory pricing and dependable production lead times.",
        "The images below show our electric two-wheeler and tricycle ranges, along with a showroom and production overview.",
        "We can discuss OEM/ODM requirements based on your target specifications and order volume.",
        "If you are reviewing electric two-wheelers or cargo and passenger tricycles, send me your target specifications, expected quantity, and destination. I can provide a competitive factory quotation and confirm the production lead time for your requirements.",
        "Best regards,\nLeo | Sales Manager\nLIEDE CHENGCANG TRADING (GUANGDONG) CO., LTD.\nGuangzhou, China | leo@chengcangtrading.com | WhatsApp: +86 130 3366 9180",
    ]
    plain = "\n\n".join(paragraphs)
    html_parts = [
        '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>',
        '<body style="margin:0;background:#f3f5f7;color:#202a33;font-family:Arial,Helvetica,sans-serif">',
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f5f7"><tr><td align="center" style="padding:18px 10px">',
        '<table role="presentation" width="640" cellspacing="0" cellpadding="0" style="width:100%;max-width:640px;background:#fff"><tr><td style="padding:26px 24px">',
        f'<p style="margin:0 0 18px;line-height:1.6">{paragraphs[0]}</p>',
        f'<p style="margin:0 0 16px;line-height:1.6">{paragraphs[1]}</p>',
        f'<p style="margin:0 0 16px;line-height:1.6">{paragraphs[2]}</p>',
    ]
    image_cids = [
        "ev-product-two-wheeler@chengcangtrading.com",
        "ev-product-tricycle@chengcangtrading.com",
        "ev-showroom@chengcangtrading.com",
        "ev-business-card@chengcangtrading.com",
    ]
    for index in range(3):
        if index == 2:
            html_parts.append(f'<p style="margin:0 0 16px;line-height:1.6">{paragraphs[3]}</p><p style="margin:0 0 16px;line-height:1.6">{paragraphs[4]}</p>')
        html_parts.append(
            f'<img src="cid:{image_cids[index]}" alt="{images[index][1]}" '
            'style="display:block;width:100%;height:auto;border:0;margin:0 0 18px">'
        )
    html_parts.extend([
        f'<p style="margin:0 0 18px;line-height:1.6">{paragraphs[5]}</p>',
        '<p style="margin:0 0 16px;line-height:1.55">Best regards,<br>Leo | Sales Manager<br>',
        'LIEDE CHENGCANG TRADING (GUANGDONG) CO., LTD.<br>Guangzhou, China<br>',
        '<a href="mailto:leo@chengcangtrading.com" style="color:#155a8a">leo@chengcangtrading.com</a> | WhatsApp: +86 130 3366 9180</p>',
        f'<img src="cid:{image_cids[3]}" alt="{images[3][1]}" style="display:block;width:100%;height:auto;border:0;margin:8px 0 0">',
        '</td></tr></table></td></tr></table></body></html>',
    ])
    html_body = "".join(html_parts)

    message = EmailMessage(policy=policy.SMTP)
    message["From"] = formataddr((SENDER_NAME, SENDER))
    message["To"] = RECIPIENT
    message["Subject"] = subject
    message["Reply-To"] = SENDER
    message.set_content(plain)
    message.add_alternative(html_body, subtype="html")
    html_part = message.get_payload()[-1]
    for (image_path, _alt), cid in zip(images, image_cids):
        html_part.add_related(
            image_path.read_bytes(),
            maintype="image",
            subtype="jpeg",
            cid=f"<{cid}>",
            filename=image_path.name,
            disposition="inline",
        )
    return message, subject, html_body


def write_artifacts(message: EmailMessage, html_body: str, images: list[tuple[Path, str]]) -> bytes:
    raw_message = message.as_bytes(policy=policy.SMTP)
    if len(raw_message) > MAX_MESSAGE_BYTES:
        raise ValueError(f"Serialized email is {len(raw_message):,} bytes, above the 1,000,000-byte limit.")
    EMAIL_FILE.write_bytes(raw_message)
    preview_body = html_body
    for (image_path, _alt), cid in zip(images, [
        "ev-product-two-wheeler@chengcangtrading.com",
        "ev-product-tricycle@chengcangtrading.com",
        "ev-showroom@chengcangtrading.com",
        "ev-business-card@chengcangtrading.com",
    ]):
        mime, _ = mimetypes.guess_type(image_path.name)
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        preview_body = preview_body.replace(f"cid:{cid}", f"data:{mime};base64,{encoded}")
    PREVIEW_FILE.write_text(preview_body, encoding="utf-8")
    return raw_message


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a compact EV outreach test email and optionally send it")
    parser.add_argument("--send", action="store_true", help="Send the prepared email using a password read from stdin")
    args = parser.parse_args()
    try:
        images = compress_images()
        message, subject, html_body = create_email(images)
        raw_message = write_artifacts(message, html_body, images)
        print(f"To: {RECIPIENT}")
        print(f"Subject: {subject}")
        print(f"Inline images: {len(images)}")
        print(f"Serialized MIME size: {len(raw_message):,} bytes (limit: {MAX_MESSAGE_BYTES:,})")
        print(f"Preview: {PREVIEW_FILE}")
        print(f"Email: {EMAIL_FILE}")
    except (OSError, ValueError) as exc:
        print(f"Cannot prepare test email: {exc}", file=sys.stderr)
        return 2

    if not args.send:
        print("Prepared only. No email sent.")
        return 0

    password = sys.stdin.readline().rstrip("\r\n")
    if not password:
        print("No password received on the local input pipe.", file=sys.stderr)
        return 2
    message = BytesParser(policy=policy.SMTP).parsebytes(raw_message)
    client = None
    try:
        context = ssl.create_default_context()
        client = smtplib.SMTP("smtp.zoho.com", 587, timeout=30)
        client.ehlo()
        client.starttls(context=context)
        client.ehlo()
        client.login(SENDER, "".join(password.split()))
        client.send_message(message)
        print(f"Sent test development email to {RECIPIENT}.")
        return 0
    except (OSError, smtplib.SMTPException) as exc:
        print(f"Test development email failed: {exc}", file=sys.stderr)
        return 1
    finally:
        password = ""
        if client is not None:
            try:
                client.quit()
            except (OSError, smtplib.SMTPException):
                client.close()


if __name__ == "__main__":
    raise SystemExit(main())
