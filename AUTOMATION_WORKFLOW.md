# Electric Two-Wheeler Outreach Automation

## Daily Flow

Two active Codex recurring tasks run in the Asia/Shanghai timezone:

| Time | Task |
| --- | --- |
| 11:00 | Research up to 20 new companies for the day's market, verify public business contacts, deduplicate, and prepare individualized email previews plus a send queue. |
| 19:30 | Process only that day's eligible queue through the local Zoho sender, with randomized intervals between messages. |

The market rotation is Monday Netherlands, Tuesday Germany, Wednesday Indonesia, Thursday off, Friday Brazil, Saturday Iran, Sunday off. Off days produce no search or email.

Research uses publicly available company information. A company is not counted as qualified unless its website, business fit, and public business email can be supported by sources. Fewer than 20 verified companies is an acceptable result.

## Sending Rules

The 11:00 task writes separate research and eligible-send CSVs. A send queue entry must include:

- `send_eligible=yes`
- `contact_legal_basis`
- `contact_legal_source`
- `personalization_source`
- The sender's required recipient, template, and company-specific personalization fields

Germany requires recorded prior email-marketing consent before a recipient can enter the send queue. Iran remains research-only until a human completes applicable sanctions, payment, shipping, and contact-compliance review. For other markets, unresolved contact-law questions also keep a company out of the queue. The 19:30 task never substitutes another list if the daily queue is missing or empty.

The scheduled sender uses `send_ev_development_emails.py --send --scheduled-auto-send`. The special flag skips the interactive `SEND` prompt only for this explicitly authorized local schedule. It requires documented eligibility fields, rechecks the suppression list and send log, limits each run to 20 messages, uses a locally encrypted credential for the current Windows account, and does not prompt for a password. Missing credentials, failed SMTP authentication, or invalid queue data stop the run. Processed or failed addresses are not automatically retried.

The sender uses randomized 360-680 second gaps between messages. The intended sending window is 19:30-23:30 China time. SMTP status `sent` means Zoho accepted the submission; it does not confirm inbox delivery or reading. The current sender does not track opens.

## Local Data

Research output, generated previews, and task logs are stored under:

```text
%LOCALAPPDATA%\ElectricTwoWheelerOutreach\daily_runs\YYYY-MM-DD\
```

The prospect queue, contact details, HTML previews, sender logs, suppression list, and credentials must remain local. The project-level `leads.csv`, `unsubscribed.txt`, and `send_log.csv` are also local state and are excluded from Git.

Zoho credentials are encrypted for the current Windows account and must be entered again on another computer. Codex recurring task definitions are stored by the Codex app outside this repository; cloning the repository does not recreate them. Recreate both recurring tasks in Codex and save a local Zoho credential on a new computer before enabling scheduled sending.

## Current Verification Boundary

The scheduled tasks are enabled and the sender contains the evidence-gated unattended-send path. A complete unattended run from automated research through delayed SMTP submission has not yet been verified. The first scheduled run depends on Codex automation running locally, the current Windows account being available, the encrypted Zoho credential decrypting, and Zoho SMTP authentication succeeding.
