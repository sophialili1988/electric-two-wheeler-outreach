# Electric Two-Wheeler Outreach

Local Zoho SMTP sender and personalized email materials for electric two-wheelers and electric tricycles.

## Requirements

- Windows 10 or later
- Python 3.10 or later for the command-line sender; it uses only the Python standard library
- PowerShell 7 (`pwsh.exe`) for the graphical test-email form
- Internet access to `smtp.zoho.com:587`

## First run on a new computer

1. Keep the `开发信内容` directory beside the scripts.
2. For the graphical sender, double-click `打开Zoho测试开发信窗口.cmd` and enter the Zoho app-specific password locally.
3. For the command-line sender, open PowerShell in this directory and run `python .\send_ev_development_emails.py --save-password` to store a credential encrypted for the current Windows account.
4. Run `python .\send_ev_development_emails.py --check-connection` to verify SMTP authentication without sending.
5. Preview a reviewed prospect CSV before using `--send`.

The graphical form and command-line sender use separate DPAPI credential files. Credentials cannot be moved between Windows accounts or computers; enter the password again on each computer. Never commit either credential file.

## Files

- `send_ev_development_emails.py`: preview, SMTP connection check, test send, and controlled CSV sending
- `zoho_test_development_email_form.ps1` and `打开Zoho测试开发信窗口.cmd`: local graphical test sender
- `leads_template.csv`: blank prospect-list template
- `Zoho开发信发送说明.md`: detailed sender instructions
- `开发信内容/`: email source document and inline product/business-card images

Keep real prospect lists, suppression lists, send logs, previews, and credentials local. The product price list and generated email drafts are intentionally not part of this deployment repository.
