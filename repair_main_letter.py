from io import BytesIO
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from PIL import Image

ROOT = Path.cwd()
SOURCE_DIR = next(
    folder for folder in ROOT.iterdir()
    if folder.is_dir() and any(file.suffix.lower() == ".docx" for file in folder.iterdir())
)
TARGET = min(SOURCE_DIR.glob("*.docx"), key=lambda file: file.stat().st_size)


def cropped_jpeg(path, box, width=1500):
    with Image.open(path) as image:
        image = image.crop(box)
        image.thumbnail((width, 500))
        output = BytesIO()
        image.save(output, format="JPEG", quality=86, optimize=True)
        output.seek(0)
        return output


two_path = SOURCE_DIR / "Electric Two-Wheeler Series Showcase.png"
trike_path = SOURCE_DIR / "Electric Tricycle Showcase Banner.png"
collage_path = next(
    path for path in SOURCE_DIR.glob("*.png")
    if Image.open(path).size == (1448, 1086)
)
card_path = next(
    path for path in SOURCE_DIR.glob("*.png")
    if Image.open(path).size == (690, 446)
)

with Image.open(two_path) as im:
    two_image = cropped_jpeg(two_path, (0, 285, im.width, 690))
with Image.open(trike_path) as im:
    trike_image = cropped_jpeg(trike_path, (0, 245, im.width, 715))
with Image.open(collage_path) as im:
    collage_image = cropped_jpeg(collage_path, (0, 0, im.width, im.height), 1100)
with Image.open(card_path) as im:
    card_image = cropped_jpeg(card_path, (0, 0, im.width, im.height), 1000)


def format_run(run, size=10.5, color="293B4A", bold=False, font="Arial"):
    run.font.name = font
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), font)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), font)
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    run.bold = bold


def paragraph(doc, text, *, size=10.3, color="293B4A", bold=False, after=6, font="Arial"):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.08
    format_run(p.add_run(text), size=size, color=color, bold=bold, font=font)
    return p


def add_inline_image(doc, stream, width=6.1, alt="Product illustration"):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(6)
    shape = p.add_run().add_picture(stream, width=Inches(width))
    shape._inline.docPr.set("descr", alt)


def add_email(doc, heading, audience, subject, body, image=None, alt="Product illustration"):
    h = doc.add_paragraph()
    h.paragraph_format.space_after = Pt(2)
    format_run(h.add_run(heading), size=14, color="174A6E", bold=True, font="Arial")
    paragraph(doc, audience, size=9.2, color="687B89", after=7)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    format_run(p.add_run("Subject: "), size=10.5, color="174A6E", bold=True)
    format_run(p.add_run(subject), size=10.5, color="293B4A", bold=True)
    for i, text in enumerate(body):
        paragraph(doc, text)
        if image is not None and i == 1:
            add_inline_image(doc, image, alt=alt)
    paragraph(doc, "Best regards,", size=10.3, after=1)
    paragraph(doc, "Leo | Sales Manager", size=9.6, after=1)
    paragraph(doc, "LIEDE CHENGCANG TRADING (GUANGDONG) CO., LTD.", size=9.6, after=1)
    paragraph(doc, "Guangzhou, China | leo@chengcangtrading.com | WhatsApp: +86 130 3366 9180", size=9.2, color="526879", after=3)


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.62)
section.bottom_margin = Inches(0.62)
section.left_margin = Inches(0.72)
section.right_margin = Inches(0.72)
normal = doc.styles["Normal"]
normal.font.name = "Arial"
normal.font.size = Pt(10.3)
normal.font.color.rgb = RGBColor(41, 59, 74)
normal.paragraph_format.space_after = Pt(6)

p = doc.add_paragraph(style="Title")
p.paragraph_format.space_after = Pt(3)
format_run(p.add_run("Targeted Electric Vehicle Outreach"), size=20, color="153B5B", bold=True)
paragraph(doc, "按潜在客户类型区分的英文开发信 | 发送前请按客户主营品类和目标市场修改方括号内容。", size=9.5, color="586D7D", font="Microsoft YaHei", after=5)
paragraph(doc, "统一公司介绍采用贸易公司身份；型号、价格、交期和认证信息需按具体订单与目的地再次确认。", size=9.2, color="586D7D", font="Microsoft YaHei", after=12)

add_email(
    doc,
    "01  Commuter electric two-wheeler importers and retailers",
    "适用客户：电动自行车/踏板车进口商、批发商及零售渠道",
    "Commuter e-scooter options for [Company Name]'s urban mobility range",
    [
        "Hi [First Name],",
        "I saw that [Company Name] serves [specific customer segment or retail channel] in [market]. We are a China-based export trading company in Guangzhou, coordinating electric vehicle supply with factories in Shandong. I thought our commuter two-wheeler range may be relevant to your portfolio.",
        "Our catalogue includes 350W, 48V models with 12Ah or 20Ah battery configurations. Lead-acid and lithium options are available on selected models. We can shortlist models around your preferred retail price, battery type, and local requirements.",
        "Would a short model shortlist be useful? If you share your target models and trial order quantity, I can send current EXW quotations and lead times for matching configurations.",
    ],
    two_image,
    "Electric two-wheeler model selection",
)

doc.add_page_break()
add_email(
    doc,
    "02  Electric motorcycle importers and distributors",
    "适用客户：电动摩托车进口商、区域经销商及品牌渠道",
    "60V/72V electric motorcycle options for [Company Name]'s lineup",
    [
        "Hi [First Name],",
        "I noticed [specific motorcycle models, brands, or customer channel] on [Company Name]'s website. We are a China-based trading company coordinating export orders with factories in Shandong, and can help source higher-power electric two-wheelers for your lineup.",
        "Our catalogue includes models from 1,000W to 3,000W and 60V/72V configurations, with battery choices varying by model. We can check the requested configuration against your market's vehicle classification and road-use rules before preparing a quotation.",
        "Which power class and battery type are you currently sourcing? With your target quantity, I can send a focused model selection with current EXW price and lead time.",
    ],
)

doc.add_page_break()
add_email(
    doc,
    "03  Cargo and passenger electric tricycle buyers",
    "适用客户：配送车辆经销商、货运运营商、客运及多用途车辆渠道",
    "Cargo and passenger e-tricycles for [Company Name]'s commercial customers",
    [
        "Hi [First Name],",
        "I saw that [Company Name] supplies [delivery operators, cargo users, or passenger-transport businesses] in [market]. We also coordinate cargo and passenger electric tricycle supply for commercial use.",
        "The range covers different cargo and passenger layouts. To recommend a suitable model, it would help to know the intended use, expected payload or passenger capacity, operating conditions, and local vehicle requirements.",
        "Are you currently sourcing electric tricycles for resale or fleet use? If you share the application and expected quantity, I can send the relevant model details and a current EXW quotation for review.",
    ],
    trike_image,
    "Cargo and passenger electric tricycle models",
)

doc.add_page_break()
add_email(
    doc,
    "04  Multi-category importers and OEM/private-label channels",
    "适用客户：同时经营多类电动车、寻求新供应渠道或 OEM/ODM 配套的进口商",
    "A China export supply option for [Company Name]'s electric vehicle portfolio",
    [
        "Hi [First Name],",
        "I saw that [Company Name] carries several electric vehicle categories in [market]. We are LIEDE CHENGCANG TRADING (GUANGDONG) CO., LTD., a China-based export trading company with an international sales team in Guangzhou and production resources in Shandong.",
        "We coordinate supply across electric two-wheelers and cargo or passenger tricycles, with model, battery, and appearance options depending on the product. OEM/ODM requests can be reviewed against the selected factory and order requirements.",
        "If you are reviewing suppliers for [specific category], send me your target specification, expected quantity, and destination. I can check a focused selection and prepare current pricing and lead-time details.",
    ],
    collage_image,
    "Electric vehicles and supply overview",
)

paragraph(doc, "Contact card for signature or follow-up", size=10.2, color="174A6E", bold=True, after=3)
add_inline_image(doc, card_image, width=5.8, alt="Leo business contact card")

doc.core_properties.title = "Targeted Electric Vehicle Outreach"
doc.core_properties.subject = "Four segmented English email drafts with four inline illustrations"
doc.core_properties.author = "LIEDE CHENGCANG TRADING (GUANGDONG) CO., LTD."
doc.save(TARGET)
print(TARGET)
