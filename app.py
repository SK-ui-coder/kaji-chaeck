import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from pathlib import Path          # ←★★★ 追加 ★★★
import tempfile                   # ←★★★ PDF保存用 ★★★

st.set_page_config(page_title="清掃・在庫管理", page_icon="🧹", layout="wide")

DAYS = ["月","火","水","木","金","土","日"]
FULL_DAYS = ["月曜日","火曜日","水曜日","木曜日","金曜日","土曜日","日曜日"]

SCHEDULE = {
    "洗濯": ["月曜日","水曜日","金曜日"],
    "トイレ・洗面": ["火曜日","木曜日","土曜日"],
    "床": FULL_DAYS,
    "玄関": ["土曜日"],
    "壁・窓": ["月曜日","金曜日"],
    "排水溝": ["火曜日","水曜日"],
    "加湿器": ["木曜日","日曜日"],
    "皿・台所": FULL_DAYS,
    "在庫管理": ["金曜日","土曜日","日曜日"],
    "価格調査": FULL_DAYS,
}

INITIAL_INVENTORY = [
    ["風呂用洗剤",1,0,500,False],
    ["トイレ洗剤",1,0,500,False],
    ["トイレ芳香剤",1,0,500,False],
    ["洗濯洗剤",1,0,500,False],
    ["洗濯柔軟剤",1,0,500,False],
    ["トイレ漂白剤",1,0,500,False],
    ["漂白剤",1,0,500,False],
    ["住宅洗剤",1,0,500,False],
    ["床シート1",1,0,100,True],
    ["床シート2",1,0,100,True],
    ["ロール",1,0,100,True],
]

# ---------------- 初期化 ----------------
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        INITIAL_INVENTORY,
        columns=["商品名","仕入数","出庫数","容量","発注"]
    )

if "clean_status" not in st.session_state:
    st.session_state.clean_status = {task: False for task in SCHEDULE}

if "clean_reset_no" not in st.session_state:
    st.session_state.clean_reset_no = 0

if "inventory_reset_no" not in st.session_state:
    st.session_state.inventory_reset_no = 0

if "order_history" not in st.session_state:
    st.session_state.order_history = []

def inventory_view():
    df = st.session_state.inventory.copy()
    for col in ["仕入数","出庫数","容量"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["理論在庫数"] = (df["仕入数"] - df["出庫数"]).clip(lower=0)
    return df[["商品名","仕入数","出庫数","理論在庫数","容量","発注"]]

# ---------------- PDF作成（修正版） ----------------
def make_order_pdf(order_df, filename):
    font_candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    ]
    font_path = next((p for p in font_candidates if Path(p).exists()), None)

    if font_path:
        pdfmetrics.registerFont(TTFont("Japanese", font_path))
        font_name = "Japanese"
    else:
        font_name = "Helvetica"

    # ★★★ Streamlit Cloud でも確実に動く一時ファイル保存 ★★★
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    path = tmp.name

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.fontName = font_name
    title_style.alignment = TA_CENTER

    normal = styles["Normal"]
    normal.fontName = font_name

    story = [
        Paragraph("発注リスト", title_style),
        Spacer(1, 8),
        Paragraph(f"発注日：{datetime.now():%Y年%m月%d日 %H:%M}", normal),
        Spacer(1, 12),
    ]

    data = [["商品名","現在庫","容量","発注数"]]
    for _, r in order_df.iterrows():
        data.append([
            str(r["商品名"]),
            str(int(r["理論在庫数"])),
            str(int(r["容量"])),
            "1"
        ])

    table = Table(data, colWidths=[230,80,80,80], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),font_name),
        ("FONTSIZE",(0,0),(-1,-1),10),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("ALIGN",(1,1),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),7),
    ]))
    story.append(table)
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"合計 {len(order_df)} 商品", normal))
    doc.build(story)

    return path

# ---------------- 以下は元コードそのまま ----------------
