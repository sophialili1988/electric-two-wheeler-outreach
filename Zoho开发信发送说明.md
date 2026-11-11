# 电动车 Zoho 开发信发送

发件邮箱固定为 `leo@chengcangtrading.com`，默认使用 Zoho SMTP `smtp.zoho.com:587` 和 STARTTLS。脚本使用 Python 标准库，不需要额外安装邮件包。

## 四种客户模板

`commuter` 面向通勤电动两轮车进口商和零售商；`motorcycle` 面向较高功率电摩进口商和经销商；`tricycle` 面向货运/客运三轮车经销商及车队；`multi_category` 面向多品类进口商和 OEM/贴牌渠道。

每封邮件会附上对应的产品图和 `开发信内容/名片.png`。正文、规格和措辞沿用主稿中的信息；价格、交期、认证和目的地法规应在报价前按具体配置核实。

## 准备客户名单

编辑 `leads_template.csv`，每行一家公司。必填列：`email`、`first_name`、`company`、`country`、`template_type`、`personalization_hook`。`personalization_hook` 写该公司网站上的具体观察，例如 `your dealer network focuses on urban commuter scooters`。`focus_product` 用于多品类模板；`subject_line` 可覆盖系统生成的主题。`do_not_contact` 填 `yes` 可跳过该地址。

## 预览与测试

在此目录打开 PowerShell，先预览名单及生成的 HTML：

```powershell
python .\send_ev_development_emails.py --csv .\leads_template.csv
```

HTML 预览保存在 `邮件预览`。预览不会连接邮箱，也不会发送邮件。测试连接只验证 Zoho 登录，不发邮件：

也可以双击 `打开Zoho测试开发信窗口.cmd`，使用本地表单预览并发送一封开发信。密码框默认遮蔽输入；勾选“记住密码”或点击“仅保存密码”时，会保存为当前 Windows 账户专属的 DPAPI 加密文件 `.zoho_app_password.secure`。

命令行批量发送工具首次使用时，可把应用专用密码保存为加密文件。在本机隐藏提示中输入两遍密码：

```powershell
python .\send_ev_development_emails.py --save-password
```

脚本会创建 `.zoho_app_password.dpapi`，其中只有加密内容；之后连接检查和发送会自动读取它，不再提示输入密码。该文件绑定当前 Windows 用户，不适合作为跨设备备份。

```powershell
python .\send_ev_development_emails.py --check-connection
```

命令行给自己的测试邮箱发送某一个完整开发信模板时，需要客户细分、用于个性化的观察、测试公司和测试市场。脚本会先显示收件人、主题和正文，输入 `SEND` 后才读取加密凭据或出现隐藏密码提示：

```powershell
python .\send_ev_development_emails.py --test-recipient "你的测试邮箱地址" --test-template commuter --test-company "Test Company" --test-country "Test Market" --test-observation "your retailer network focuses on commuter scooters" --test-first-name "Alex"
```

若没有保存加密凭据，脚本会在需要登录时通过本机隐藏提示临时询问。专用密码不要发在聊天里，也不要保存到脚本、名单、命令行参数或日志中。

## 正式发送

确认预览并检查名单、退订地址后，显式加 `--send`：

```powershell
python .\send_ev_development_emails.py --csv .\leads_template.csv --send --max-emails 10 --delay 60
```

正式发送前同样会显示本次邮件并要求输入 `SEND`。`unsubscribed.txt` 中的地址、CSV 中标记 `do_not_contact` 的地址、重复地址和 `send_log.csv` 中已处理的地址会被跳过。测试发送单独记录在 `test_send_log.csv`。

## 定时自动发送

Codex 的电动车定时任务在上午生成当天名单和发送队列，并于北京时间 19:30 启动发送。自动发送只处理当天 `send_queue.csv` 中有明确联系依据的条目，必须提供 `send_eligible=yes`、`contact_legal_basis`、`contact_legal_source` 和 `personalization_source`。未保存本机加密凭据、SMTP 登录失败、退订或重复地址都会停止或跳过；无人值守时不会弹出密码提示。发送记录中的 `sent` 只表示 SMTP 接受了提交，不代表客户已收到或打开邮件。失败或结果不确定的地址不会自动重试。

定时模式使用 `--scheduled-auto-send` 跳过交互确认。它必须和 `--send` 一起使用，只用于已经授权的本机定时队列；不要用于普通名单或测试邮件。随机间隔应在四小时窗口内完成。
