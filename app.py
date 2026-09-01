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
from pathlib import Path
import tempfile

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

DETAILS = {
    "洗濯": ["洗濯機掃除", "フィルター清掃", "洗剤補充"],
    "トイレ・洗面": ["便器", "洗面台", "鏡", "排水溝"],
    "床": ["掃除機", "床拭き", "モップ洗浄"],
    "玄関": ["たたき掃除", "靴整理"],
    "壁・窓": ["窓拭き", "壁拭き"],
    "排水溝": ["排水溝ブラシ", "漂白剤投入"],
    "加湿器": ["フィルター掃除", "水交換"],
    "皿・台所": ["皿洗い", "台拭き", "排水溝掃除"],
    "在庫管理": ["棚整理", "在庫確認"],
    "価格調査": ["ネット価格調査", "店舗価格調査"],
}

ORDER_UNIT = {
    "床シート1": 10,
    "床シート2": 10,
    "ロール": 3,
    "洗濯洗剤": 1,
    "洗濯柔軟剤": 1,
    "風呂用洗剤": 1,
    "トイレ洗剤": 1,
    "トイレ芳香剤": 1,
    "漂白剤": 1,
    "住宅洗剤": 1,
    "フローリングウェットシート": 10,
    "流せるトイレクリーナー": 1,
    "消臭ビーズ無香料詰替え": 1,
    "ソフトパックティッシュ": 1,
    "食器用泡スプレー": 1,
    "バスタブタレンジング HARD": 1,
    "2倍巻トイレットペーパー": 1,
    "黒リング綿棒2個組": 1,
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
    ["床シート1",1,0,100,False],
    ["床シート2",1,0,100,False],
    ["ロール",1,0,100,False],
    ["フローリングウェットシート",3,0,59,False],
    ["流せるトイレクリーナー",1,0,198,False],
    ["消臭ビーズ無香料詰替え",1,0,298,False],
    ["ソフトパックティッシュ",1,0,598,False],
    ["食器用泡スプレー",1,0,398,False],
    ["バスタブタレンジング HARD",2,0,498,False],
    ["2倍巻トイレットペーパー",1,0,678,False],
    ["黒リング綿棒2個組",1,0,298,False],
]

# ---------------- 初期化 ----------------
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        INITIAL_INVENTORY,
        columns=["商品名","仕入数","出庫数","容量","発注"]
    )

if "clean_status" not in st.session_state:
    st.session_state.clean_status = {task: False for task in SCHEDULE}

if "clean_details" not in st.session_state:
    st.session_state.clean_details = {
        task: {d: False for d in DETAILS.get(task, [])}
        for task in SCHEDULE
    }

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

    data = [["商品名","現在庫","容量","発注単位"]]
    for _, r in order_df.iterrows():
        unit = ORDER_UNIT.get(r["商品名"], 1)
        data.append([
            str(r["商品名"]),
            str(int(r["理論在庫数"])),
            str(int(r["容量"])),
            str(unit),
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

now = datetime.now()
today_full = FULL_DAYS[now.weekday()]

st.title("🧹 清掃・在庫管理")
st.caption(f"{now:%Y年%m月%d日}（{today_full}）")

tab1, tab2 = st.tabs(["🧹 チェックリスト", "📦 在庫・発注"])

# =========================================================
# チェックリスト
# =========================================================
with tab1:
    st.subheader("今日・曜日別の実施予定")

    col_day = st.columns(7)
    selected_day = st.session_state.get("selected_day", today_full)
    for i, d in enumerate(FULL_DAYS):
        label = DAYS[i]
        if col_day[i].button(label, use_container_width=True):
            selected_day = d
            st.session_state.selected_day = d

    target_day = selected_day
    st.caption(f"表示中の曜日：{target_day}")

    today_tasks = [task for task, days in SCHEDULE.items() if target_day in days]

    if st.button("🔄 この曜日のチェックを全部リセット", use_container_width=True):
        for task in today_tasks:
            st.session_state.clean_status[task] = False
            for det in st.session_state.clean_details.get(task, {}):
                st.session_state.clean_details[task][det] = False
        st.session_state.clean_reset_no += 1
        st.rerun()

    today_df = pd.DataFrame({
        "項目": today_tasks,
        "完了": [st.session_state.clean_status.get(task, False) for task in today_tasks]
    })

    edited = st.data_editor(
        today_df,
        hide_index=True,
        use_container_width=True,
        disabled=["項目"],
        key=f"clean_editor_{st.session_state.clean_reset_no}_{target_day}",
        column_config={
            "項目": st.column_config.TextColumn("項目", width="large"),
            "完了": st.column_config.CheckboxColumn("☑ 完了", default=False),
        }
    )

    for _, row in edited.iterrows():
        st.session_state.clean_status[row["項目"]] = bool(row["完了"])

    done = int(edited["完了"].sum()) if len(edited) else 0
    total = len(edited)

    a,b,c = st.columns(3)
    a.metric("この曜日の予定", total)
    b.metric("完了", done)
    c.metric("残り", total-done)

    st.progress(done/total if total else 0)

    st.divider()
    st.subheader("🧩 詳細チェック")

    for task in today_tasks:
        with st.expander(f"{task} の詳細チェック", expanded=False):
            details = DETAILS.get(task, [])
            if not details:
                st.caption("詳細項目は登録されていません。")
            else:
                cols = st.columns(len(details))
                for i, det in enumerate(details):
                    key = f"detail_{task}_{det}"
                    current = st.session_state.clean_details[task].get(det, False)
                    new_val = cols[i].checkbox(det, value=current, key=key)
                    st.session_state.clean_details[task][det] = new_val

    st.divider()
    st.subheader("📅 週間予定表")

    rows = []
    for task, days in SCHEDULE.items():
        rows.append({
            "項目": task,
            "月": "⭕" if "月曜日" in days else "—",
            "火": "⭕" if "火曜日" in days else "—",
            "水": "⭕" if "水曜日" in days else "—",
            "木": "⭕" if "木曜日" in days else "—",
            "金": "⭕" if "金曜日" in days else "—",
            "土": "⭕" if "土曜日" in days else "—",
            "日": "⭕" if "日曜日" in days else "—",
        })

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
        column_config={"項目": st.column_config.TextColumn("項目", width="large")}
    )

# =========================================================
# 在庫・発注
# =========================================================
with tab2:
    st.subheader("📦 在庫管理表")

    df = inventory_view()
    order_df = df[df["発注"]].copy()
    zero_df = df[df["理論在庫数"] <= 0]

    a,b,c = st.columns(3)
    a.metric("商品数", len(df))
    b.metric("在庫合計", int(df["理論在庫数"].sum()))
    c.metric("発注商品", len(order_df))

    if len(order_df):
        st.warning("🛒 発注対象：" + "、".join(order_df["商品名"].tolist()))
    if len(zero_df):
        st.error("⚠️ 在庫0：" + "、".join(zero_df["商品名"].tolist()))

    st.markdown("### 📋 商品一覧")
    edited_inv = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "商品名": st.column_config.TextColumn("商品名", width="large", required=True),
            "仕入数": st.column_config.NumberColumn("仕入数", min_value=0, step=1, width="small"),
            "出庫数": st.column_config.NumberColumn("出庫数", min_value=0, step=1, width="small"),
            "理論在庫数": st.column_config.NumberColumn("理論在庫数", width="small", disabled=True),
            "容量": st.column_config.NumberColumn("容量", min_value=0, step=1, width="small"),
            "発注": st.column_config.CheckboxColumn("🛒 発注", width="small"),
        },
        disabled=["理論在庫数"],
        key=f"inventory_editor_{st.session_state.inventory_reset_no}"
    )

    base = edited_inv[["商品名","仕入数","出庫数","容量","発注"]].copy()
    for col in ["仕入数","出庫数","容量"]:
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0).astype(int)
    base["発注"] = base["発注"].fillna(False).astype(bool)
    st.session_state.inventory = base.reset_index(drop=True)

    st.divider()
    st.subheader("🛒 発注リスト")

    current = inventory_view()
    current_orders = current[current["発注"]].copy()

    if len(current_orders):
        order_display = current_orders[["商品名","理論在庫数","容量"]].copy()
        order_display.insert(3, "発注単位", [
            ORDER_UNIT.get(n, 1) for n in order_display["商品名"]
        ])
        st.dataframe(order_display, hide_index=True, use_container_width=True)

        if st.button("🖨️ 発注リストをPDF記録", use_container_width=True):
            filename = f"発注リスト_{datetime.now():%Y%m%d_%H%M%S}.pdf"
            pdf_path = make_order_pdf(current_orders, filename)

            st.session_state.order_history.append({
                "日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "商品数": len(current_orders),
                "商品": "、".join(current_orders["商品名"].tolist()),
                "ファイル": filename
            })

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ PDFを保存",
                    data=f.read(),
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            st.success("PDFの発注記録を作成しました。")
    else:
        st.info("発注にチェックした商品はありません。")

    st.markdown("### 🗂️ 発注記録")
    if st.session_state.order_history:
        st.dataframe(
            pd.DataFrame(st.session_state.order_history),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.caption("まだ発注記録はありません。")

    st.divider()
    st.subheader("➕ 商品追加")
    with st.form("add_product"):
        name = st.text_input("商品名")
        a,b = st.columns(2)
        cap = a.number_input("容量", min_value=0, step=1, value=500)
        qty = b.number_input("初期仕入数", min_value=0, step=1, value=0)
        if st.form_submit_button("商品を追加", use_container_width=True):
            if name.strip():
                new = pd.DataFrame([[name.strip(),int(qty),0,int(cap),False]],
                                   columns=["商品名","仕入数","出庫数","容量","発注"])
                st.session_state.inventory = pd.concat(
                    [st.session_state.inventory, new], ignore_index=True
                )
                st.session_state.inventory_reset_no += 1
                st.rerun()
            else:
                st.error("商品名を入力してください。")

    if st.button("🔄 在庫表を初期状態に戻す", use_container_width=True):
        st.session_state.inventory = pd.DataFrame(
            INITIAL_INVENTORY,
            columns=["商品名","仕入数","出庫数","容量","発注"]
        )
        st.session_state.inventory_reset_no += 1
        st.rerun()

st.divider()
st.caption("※表を直接編集できます。スマホでは横スクロールできます。")
