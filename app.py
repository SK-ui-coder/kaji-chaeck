import streamlit as st
from datetime import datetime

st.set_page_config(page_title="清掃・在庫チェック", page_icon="🧹", layout="centered")

DAYS = ["月曜日","火曜日","水曜日","木曜日","金曜日","土曜日","日曜日"]

SCHEDULE = {
    "洗濯":["月曜日","水曜日","金曜日"],
    "トイレ・洗面":["火曜日","木曜日","土曜日"],
    "床":DAYS,
    "玄関":["土曜日"],
    "壁・窓":["月曜日","金曜日"],
    "排水溝":["火曜日","水曜日"],
    "加湿器":["木曜日","日曜日"],
    "皿・台所":DAYS,
    "在庫管理":["金曜日","土曜日","日曜日"],
    "価格調査":DAYS,
}

INITIAL_INVENTORY = [
    {"商品名":"風呂用洗剤","仕入数":1,"出庫数":0,"容量":500,"発注":False},
    {"商品名":"トイレ洗剤","仕入数":1,"出庫数":0,"容量":500,"発注":False},
    {"商品名":"トイレ芳香剤","仕入数":1,"出庫数":0,"容量":500,"発注":False},
    {"商品名":"洗濯洗剤","仕入数":1,"出庫数":0,"容量":500,"発注":False},
    {"商品名":"洗濯柔軟剤","仕入数":1,"出庫数":0,"容量":500,"発注":False},
    {"商品名":"トイレ漂白剤","仕入数":1,"出庫数":0,"容量":500,"発注":False},
    {"商品名":"漂白剤","仕入数":1,"出庫数":0,"容量":500,"発注":False},
    {"商品名":"住宅洗剤","仕入数":1,"出庫数":0,"容量":500,"発注":False},
    {"商品名":"床シート1","仕入数":1,"出庫数":0,"容量":100,"発注":True},
    {"商品名":"床シート2","仕入数":1,"出庫数":0,"容量":100,"発注":True},
    {"商品名":"ロール","仕入数":1,"出庫数":0,"容量":100,"発注":True},
]

if "inventory" not in st.session_state:
    st.session_state.inventory = [x.copy() for x in INITIAL_INVENTORY]
if "checked" not in st.session_state:
    st.session_state.checked = {}

now = datetime.now()
today = DAYS[now.weekday()]
st.title("🧹 清掃・在庫チェック")
st.caption(f"{now:%Y年%m月%d日}（{today}）")

tab1, tab2 = st.tabs(["🧹 清掃チェック","📦 在庫管理"])

with tab1:
    tasks = [x for x,d in SCHEDULE.items() if today in d]
    st.subheader(f"今日の実施予定　{len(tasks)}項目")
    done = 0
    for task in tasks:
        key = f"{now.date()}_{task}"
        st.session_state.checked.setdefault(key, False)
        if st.checkbox(task, key=key):
            done += 1
    st.progress(done/len(tasks) if tasks else 0)
    st.write(f"**進捗：{done} / {len(tasks)} 完了**")
    if tasks and done == len(tasks):
        st.success("🎉 今日の予定はすべて完了！")
    if st.button("🔄 今日のチェックをリセット", use_container_width=True):
        for task in tasks:
            st.session_state.checked[f"{now.date()}_{task}"] = False
        st.rerun()

    st.divider()
    st.subheader("📅 週間予定")
    st.caption("月　火　水　木　金　土　日")
    for task, days in SCHEDULE.items():
        marks = " ".join("⭕" if d in days else "・" for d in DAYS)
        st.write(f"**{task}**　{marks}")

with tab2:
    st.subheader("📦 在庫管理")
    low = []
    orders = []
    total = 0
    for x in st.session_state.inventory:
        stock = max(0, x["仕入数"] - x["出庫数"])
        total += stock
        if stock == 0: low.append(x["商品名"])
        if x["発注"]: orders.append(x["商品名"])

    a,b,c = st.columns(3)
    a.metric("商品数", len(st.session_state.inventory))
    b.metric("在庫合計", total)
    c.metric("発注", len(orders))

    if orders:
        st.warning("🛒 発注対象：" + "、".join(orders))
    if low:
        st.error("⚠️ 在庫0：" + "、".join(low))
    st.caption("理論在庫数 ＝ 仕入数 − 出庫数")

    for i,x in enumerate(st.session_state.inventory):
        stock = max(0, x["仕入数"] - x["出庫数"])
        with st.container(border=True):
            title = f"### 📦 {x['商品名']}"
            if x["発注"]: title += "　🛒 発注"
            if stock == 0: title += "　⚠️ 在庫0"
            st.markdown(title)

            p,q = st.columns(2)
            x["仕入数"] = p.number_input("仕入数", min_value=0, step=1, value=int(x["仕入数"]), key=f"p{i}")
            x["出庫数"] = q.number_input("出庫数", min_value=0, step=1, value=int(x["出庫数"]), key=f"q{i}")

            r,s = st.columns(2)
            r.metric("理論在庫数", max(0, x["仕入数"]-x["出庫数"]))
            s.metric("容量", f"{x['容量']}")

            x["発注"] = st.checkbox("🛒 発注する", value=bool(x["発注"]), key=f"o{i}")

    st.divider()
    st.subheader("➕ 商品を追加")
    with st.form("add"):
        name = st.text_input("商品名")
        a,b = st.columns(2)
        cap = a.number_input("容量", min_value=0, step=1, value=500)
        qty = b.number_input("初期仕入数", min_value=0, step=1, value=0)
        if st.form_submit_button("商品を追加", use_container_width=True):
            if name.strip():
                st.session_state.inventory.append({"商品名":name.strip(),"仕入数":int(qty),"出庫数":0,"容量":int(cap),"発注":False})
                st.rerun()
            else:
                st.error("商品名を入力してください。")

    if st.button("🔄 在庫を初期状態に戻す", use_container_width=True):
        st.session_state.inventory = [x.copy() for x in INITIAL_INVENTORY]
        st.rerun()

st.divider()
st.caption("※現在はブラウザのセッション中に入力内容を保持します。")
