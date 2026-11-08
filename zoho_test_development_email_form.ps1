Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$root = $PSScriptRoot
$imageRoot = Join-Path $root '开发信内容'
$credentialFile = Join-Path $root '.zoho_app_password.secure'
$sender = 'leo@chengcangtrading.com'
$senderName = 'Leo'
$senderCompany = 'LIEDE CHENGCANG TRADING (GUANGDONG) CO., LTD.'
$senderPhone = '+86 130 3366 9180'

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Zoho 测试开发信'
$form.StartPosition = 'CenterScreen'
$form.Size = [System.Drawing.Size]::new(780, 760)
$form.MinimumSize = [System.Drawing.Size]::new(780, 760)
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false

function Add-Label($text, $x, $y, $width = 130) {
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $text
    $label.Location = [System.Drawing.Point]::new($x, $y + 4)
    $label.Size = [System.Drawing.Size]::new($width, 22)
    $form.Controls.Add($label)
}

function Add-TextBox($x, $y, $width, $height = 26, $multiline = $false) {
    $box = New-Object System.Windows.Forms.TextBox
    $box.Location = [System.Drawing.Point]::new($x, $y)
    $box.Size = [System.Drawing.Size]::new($width, $height)
    $box.Multiline = $multiline
    if ($multiline) { $box.ScrollBars = 'Vertical' }
    $form.Controls.Add($box)
    return $box
}

Add-Label 'Zoho 发件邮箱' 18 18
$senderBox = Add-TextBox 150 16 250
$senderBox.Text = $sender
$senderBox.ReadOnly = $true
Add-Label '测试收件邮箱' 416 18 115
$recipientBox = Add-TextBox 530 16 220
$recipientBox.Text = 'molisourcing@gmail.com'

Add-Label '客户联系人' 18 56
$firstNameBox = Add-TextBox 150 54 250
$firstNameBox.Text = 'Alex'
Add-Label '客户公司' 416 56 115
$companyBox = Add-TextBox 530 54 220
$companyBox.Text = 'Test Company'

Add-Label '国家/市场' 18 94
$countryBox = Add-TextBox 150 92 250
$countryBox.Text = 'Test Market'
Add-Label '产品模板' 416 94 115
$templateBox = New-Object System.Windows.Forms.ComboBox
$templateBox.Location = [System.Drawing.Point]::new(530, 92)
$templateBox.Size = [System.Drawing.Size]::new(220, 26)
$templateBox.DropDownStyle = 'DropDownList'
[void]$templateBox.Items.AddRange([object[]]@(
    '通勤电动两轮车 / commuter',
    '电动摩托车 / motorcycle',
    '货运或客运三轮车 / tricycle',
    '多品类及 OEM / multi_category'
))
$templateBox.SelectedIndex = 0
$form.Controls.Add($templateBox)

Add-Label '客户网站观察点' 18 134 130
$observationBox = Add-TextBox 150 132 600 48 $true
$observationBox.Text = 'your team is reviewing commuter electric scooters for its sourcing portfolio'
Add-Label '重点产品' 18 190 130
$focusBox = Add-TextBox 150 188 600 26
$focusBox.Text = 'commuter electric scooters'

Add-Label '邮件主题' 18 228
$subjectBox = Add-TextBox 150 226 600 26
Add-Label '应用专用密码' 18 266 130
$passwordBox = Add-TextBox 150 264 400 26
$passwordBox.UseSystemPasswordChar = $true
$rememberBox = New-Object System.Windows.Forms.CheckBox
$rememberBox.Text = '记住密码（仅此 Windows 账户可解密）'
$rememberBox.Location = [System.Drawing.Point]::new(555, 264)
$rememberBox.Size = [System.Drawing.Size]::new(205, 30)
$form.Controls.Add($rememberBox)

$hint = New-Object System.Windows.Forms.Label
$hint.Text = '密码框会遮蔽输入；可选择本机 DPAPI 加密保存。请检查下面预览，再点击发送。'
$hint.Location = [System.Drawing.Point]::new(18, 300)
$hint.Size = [System.Drawing.Size]::new(720, 24)
$form.Controls.Add($hint)

$preview = New-Object System.Windows.Forms.TextBox
$preview.Location = [System.Drawing.Point]::new(18, 328)
$preview.Size = [System.Drawing.Size]::new(732, 330)
$preview.Multiline = $true
$preview.ReadOnly = $true
$preview.ScrollBars = 'Vertical'
$preview.Font = [System.Drawing.Font]::new('Consolas', 9)
$form.Controls.Add($preview)

$status = New-Object System.Windows.Forms.Label
$status.Text = '准备就绪。此窗口只发送一封测试开发信。'
$status.Location = [System.Drawing.Point]::new(18, 665)
$status.Size = [System.Drawing.Size]::new(470, 24)
$form.Controls.Add($status)

$saveButton = New-Object System.Windows.Forms.Button
$saveButton.Text = '仅保存密码'
$saveButton.Location = [System.Drawing.Point]::new(492, 690)
$saveButton.Size = [System.Drawing.Size]::new(112, 30)
$form.Controls.Add($saveButton)
$sendButton = New-Object System.Windows.Forms.Button
$sendButton.Text = '发送测试开发信'
$sendButton.Location = [System.Drawing.Point]::new(610, 690)
$sendButton.Size = [System.Drawing.Size]::new(140, 30)
$form.Controls.Add($sendButton)
$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Text = '取消'
$cancelButton.Location = [System.Drawing.Point]::new(18, 690)
$cancelButton.Size = [System.Drawing.Size]::new(80, 30)
$cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancelButton)
$form.CancelButton = $cancelButton

function Get-SelectedTemplate {
    switch ($templateBox.SelectedIndex) {
        0 { 'commuter' }
        1 { 'motorcycle' }
        2 { 'tricycle' }
        3 { 'multi_category' }
        default { 'commuter' }
    }
}

function Get-EmailDraft {
    $first = $firstNameBox.Text.Trim()
    $company = $companyBox.Text.Trim()
    $country = $countryBox.Text.Trim()
    $observation = $observationBox.Text.Trim()
    $focus = $focusBox.Text.Trim()
    switch (Get-SelectedTemplate) {
        'commuter' {
            $subject = "${company}: commuter e-scooters for $country"
            $body = @"
Hi $first,

I noticed this on your website: $observation. We are a China-based export trading company in Guangzhou, coordinating electric vehicle supply with factories in Shandong. I thought our commuter two-wheeler range may be relevant to your portfolio in $country.

Our catalogue includes 350W, 48V models with 12Ah or 20Ah battery configurations. Lead-acid and lithium options are available on selected models. We can shortlist models around your preferred retail price, battery type, and local requirements.

Would a short model shortlist be useful? If you share your target models and trial order quantity, I can send current EXW quotations and lead times for matching configurations.

Best regards,
$senderName | Sales Manager
$senderCompany
Guangzhou, China | $sender | WhatsApp: $senderPhone
"@
            $productImage = 'Electric Two-Wheeler Series Showcase.png'
        }
        'motorcycle' {
            $subject = "${company}: 60V/72V electric motorcycles for $country"
            $body = @"
Hi $first,

I noticed this on your website: $observation. We are a China-based trading company coordinating export orders with factories in Shandong, and can help source higher-power electric two-wheelers for your lineup in $country.

Our catalogue includes models from 1,000W to 3,000W and 60V/72V configurations, with battery choices varying by model. We can check the requested configuration against your market's vehicle classification and road-use rules before preparing a quotation.

Which power class and battery type are you currently sourcing? With your target quantity, I can send a focused model selection with current EXW price and lead time.

Best regards,
$senderName | Sales Manager
$senderCompany
Guangzhou, China | $sender | WhatsApp: $senderPhone
"@
            $productImage = 'Electric Two-Wheeler Series Showcase.png'
        }
        'tricycle' {
            $subject = "${company}: cargo and passenger e-tricycles for $country"
            $body = @"
Hi $first,

I noticed this on your website: $observation. We also coordinate cargo and passenger electric tricycle supply for commercial use in $country.

The range covers different cargo and passenger layouts. To recommend a suitable model, it would help to know the intended use, expected payload or passenger capacity, operating conditions, and local vehicle requirements.

Are you currently sourcing electric tricycles for resale or fleet use? If you share the application and expected quantity, I can send the relevant model details and a current EXW quotation for review.

Best regards,
$senderName | Sales Manager
$senderCompany
Guangzhou, China | $sender | WhatsApp: $senderPhone
"@
            $productImage = 'Electric Tricycle Showcase Banner.png'
        }
        default {
            if (-not $focus) { $focus = 'electric two-wheelers and tricycles' }
            $subject = "${company}: electric vehicle supply for $country"
            $body = @"
Hi $first,

I noticed this on your website: $observation. We are $senderCompany, a China-based export trading company with an international sales team in Guangzhou and production resources in Shandong.

We coordinate supply across electric two-wheelers and cargo or passenger tricycles, with model, battery, and appearance options depending on the product. OEM/ODM requests can be reviewed against the selected factory and order requirements.

If you are reviewing suppliers for $focus, send me your target specification, expected quantity, and destination. I can check a focused selection and prepare current pricing and lead-time details.

Best regards,
$senderName | Sales Manager
$senderCompany
Guangzhou, China | $sender | WhatsApp: $senderPhone
"@
            $productImage = '电车2.png'
        }
    }
    return @{ Subject = $subject; Body = $body.Trim(); ProductImage = $productImage }
}

function Update-Preview {
    $draft = Get-EmailDraft
    $subjectBox.Text = $draft.Subject
    $preview.Text = "To: $($recipientBox.Text.Trim())`r`nSubject: $($draft.Subject)`r`n`r`n$($draft.Body)`r`n`r`n[Inline image: $($draft.ProductImage)]`r`n[Inline image: 名片.png]"
}

foreach ($control in @($recipientBox, $firstNameBox, $companyBox, $countryBox, $observationBox, $focusBox)) {
    $control.Add_TextChanged({ Update-Preview })
}
$templateBox.Add_SelectedIndexChanged({ Update-Preview })

if (Test-Path -LiteralPath $credentialFile) {
    try {
        $encrypted = (Get-Content -LiteralPath $credentialFile -Raw).Trim()
        $secure = ConvertTo-SecureString -String $encrypted
        $passwordBox.Text = [System.Net.NetworkCredential]::new('', $secure).Password
        $rememberBox.Checked = $true
    } catch {
        [System.Windows.Forms.MessageBox]::Show($form, '已保存的密码无法由当前 Windows 账户解密。请手动输入并重新保存。', '凭据不可用') | Out-Null
    }
}
Update-Preview

$saveButton.Add_Click({
    if ([string]::IsNullOrWhiteSpace($passwordBox.Text)) {
        [System.Windows.Forms.MessageBox]::Show($form, '请先输入 Zoho 应用专用密码。', '尚未填写密码') | Out-Null
        return
    }
    try {
        $secure = ConvertTo-SecureString -String $passwordBox.Text -AsPlainText -Force
        ConvertFrom-SecureString -SecureString $secure | Set-Content -LiteralPath $credentialFile -Encoding ASCII
        $rememberBox.Checked = $true
        $status.Text = '密码已使用 Windows DPAPI 加密保存。'
        [System.Windows.Forms.MessageBox]::Show($form, '已保存加密凭据；明文密码没有写入文件。', '保存完成') | Out-Null
    } catch {
        [System.Windows.Forms.MessageBox]::Show($form, $_.Exception.Message, '保存失败') | Out-Null
    }
})

$sendButton.Add_Click({
    $to = $recipientBox.Text.Trim()
    $password = $passwordBox.Text
    $draft = Get-EmailDraft
    if ($to -notmatch '^[^\s@]+@[^\s@]+\.[^\s@]+$' -or
        [string]::IsNullOrWhiteSpace($firstNameBox.Text) -or
        [string]::IsNullOrWhiteSpace($companyBox.Text) -or
        [string]::IsNullOrWhiteSpace($countryBox.Text) -or
        [string]::IsNullOrWhiteSpace($observationBox.Text) -or
        [string]::IsNullOrWhiteSpace($password)) {
        [System.Windows.Forms.MessageBox]::Show($form, '请填写有效收件邮箱、客户信息和应用专用密码。', '信息不完整') | Out-Null
        return
    }
    $confirm = [System.Windows.Forms.MessageBox]::Show($form, "确认发送一封开发信到：`r`n$to`r`n`r`n主题：$($draft.Subject)", '确认发送', [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
    if ($confirm -ne [System.Windows.Forms.DialogResult]::Yes) { return }

    $sendButton.Enabled = $false
    $saveButton.Enabled = $false
    $status.Text = '正在连接 Zoho 并发送……'
    $form.Refresh()
    $message = $null
    $client = $null
    $views = @()
    $resources = @()
    try {
        if ($rememberBox.Checked) {
            $secure = ConvertTo-SecureString -String $password -AsPlainText -Force
            ConvertFrom-SecureString -SecureString $secure | Set-Content -LiteralPath $credentialFile -Encoding ASCII
        } elseif (Test-Path -LiteralPath $credentialFile) {
            Remove-Item -LiteralPath $credentialFile -Force
        }

        $message = [System.Net.Mail.MailMessage]::new()
        $message.From = [System.Net.Mail.MailAddress]::new($sender, $senderName)
        $message.To.Add($to)
        $message.Subject = $draft.Subject
        $message.SubjectEncoding = [System.Text.Encoding]::UTF8
        $message.BodyEncoding = [System.Text.Encoding]::UTF8
        $message.ReplyToList.Add($sender)
        $plainView = [System.Net.Mail.AlternateView]::CreateAlternateViewFromString($draft.Body, [System.Text.Encoding]::UTF8, 'text/plain')
        $htmlBody = '<html><body style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:#222">'
        $paragraphs = $draft.Body -split '(?:\r?\n){2}'
        foreach ($paragraph in $paragraphs) { $htmlBody += '<p>' + [System.Net.WebUtility]::HtmlEncode($paragraph).Replace("`r`n", '<br>').Replace("`n", '<br>') + '</p>' }
        $htmlBody += '<p><img src="cid:ev-product" alt="Product showcase" style="display:block;max-width:640px;width:100%;height:auto;margin:18px 0"></p>'
        $htmlBody += '<p><img src="cid:ev-business-card" alt="Business card" style="display:block;max-width:640px;width:100%;height:auto;margin:18px 0"></p>'
        $htmlBody += '</body></html>'
        $htmlView = [System.Net.Mail.AlternateView]::CreateAlternateViewFromString($htmlBody, [System.Text.Encoding]::UTF8, 'text/html')
        $productPath = Join-Path $imageRoot $draft.ProductImage
        $cardPath = Join-Path $imageRoot '名片.png'
        foreach ($path in @($productPath, $cardPath)) {
            if (-not (Test-Path -LiteralPath $path)) { throw "Inline image not found: $path" }
        }
        foreach ($spec in @(@{ Path = $productPath; Cid = 'ev-product' }, @{ Path = $cardPath; Cid = 'ev-business-card' })) {
            $resource = [System.Net.Mail.LinkedResource]::new($spec.Path, 'image/png')
            $resource.ContentId = $spec.Cid
            $resource.TransferEncoding = [System.Net.Mime.TransferEncoding]::Base64
            [void]$htmlView.LinkedResources.Add($resource)
            $resources += $resource
        }
        [void]$message.AlternateViews.Add($plainView)
        [void]$message.AlternateViews.Add($htmlView)
        $views += $plainView, $htmlView

        $client = [System.Net.Mail.SmtpClient]::new('smtp.zoho.com', 587)
        $client.EnableSsl = $true
        $client.Timeout = 30000
        $client.Credentials = [System.Net.NetworkCredential]::new($sender, $password)
        $client.Send($message)

        $passwordBox.Clear()
        $status.Text = "测试开发信已发送到 $to。"
        [System.Windows.Forms.MessageBox]::Show($form, "测试开发信已发送到 $to。", '发送成功', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information) | Out-Null
    } catch {
        $passwordBox.Clear()
        $status.Text = '发送失败。请确认 Zoho SMTP 设置和应用专用密码。'
        [System.Windows.Forms.MessageBox]::Show($form, $_.Exception.Message, '发送失败', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
    } finally {
        if ($message) { $message.Dispose() }
        foreach ($view in $views) { $view.Dispose() }
        foreach ($resource in $resources) { $resource.Dispose() }
        if ($client) { $client.Dispose() }
        $password = $null
        $sendButton.Enabled = $true
        $saveButton.Enabled = $true
    }
})

$form.Add_FormClosing({ $passwordBox.Clear() })
[void]$form.ShowDialog()
