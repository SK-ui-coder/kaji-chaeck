import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="清掃・管理チェックリスト",
    page_icon="🧹",
    layout="wide",
)

# 写真の「実施予定」をそのままデータ化
SCHEDULE = {
    "洗濯":       ["月曜日", "水曜日", "金曜日"],
    "トイレ・洗面": ["火曜日", "木曜日", "土曜日"],
    "床":         ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"],
    "玄関":       ["土曜日"],
    "壁・窓":     ["月曜日", "金曜日"],
    "排水溝":     ["火曜日", "水曜日"],
    "加湿器":     ["木曜日", "日曜日"],
    "皿・台所":   ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"],
    "在庫管理":   ["金曜日", "土曜日", "日曜日"],
    "価格調査":   ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"],
}

DAYS = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

# セッション中はチェック状態を保持
if "checked" not in st.session_state:
    st.session_state.checked = {}

today = datetime.now()
today_name = DAYS[today.weekday()]

st.title("🧹 清掃・管理チェックリスト")
st.caption(f"今日は {today.strftime('%Y年%m月%d日')}（{today_name}）")

# 今日の予定
today_tasks = [task for task, days in SCHEDULE.items() if today_name in days]

st.subheader(f"📋 今日の実施予定（{len(today_tasks)}項目）")

if today_tasks:
    for task in today_tasks:
        key = f"{today.date()}_{task}"
        st.session_state.checked.setdefault(key, False)
        st.checkbox(task, key=key)

    done = sum(st.session_state.checked[f"{today.date()}_{task}"] for task in today_tasks)
    total = len(today_tasks)
    st.progress(done / total if total else 0)
    st.write(f"**進捗：{done} / {total} 完了**")

    if done == total:
        st.success("🎉 今日の予定はすべて完了です！")
else:
    st.info("今日は実施予定がありません。")

if st.button("今日のチェックをリセット"):
    for task in today_tasks:
        st.session_state.checked[f"{today.date()}_{task}"] = False
    st.rerun()

st.divider()

# 週間予定表
st.subheader("📅 週間実施予定")

header = st.columns([1.5] + [1] * 7)
header[0].markdown("**種類**")
for col, day in zip(header[1:], DAYS):
    col.markdown(f"**{day[:1]}**")

for task, scheduled_days in SCHEDULE.items():
    cols = st.columns([1.5] + [1] * 7)
    cols[0].write(task)
    for i, day in enumerate(DAYS):
        if day in scheduled_days:
            cols[i + 1].markdown("⭕")
        else:
            cols[i + 1].markdown("—")

st.divider()

# 今日以外も確認できる詳細
st.subheader("🔎 曜日別の予定")
selected_day = st.selectbox("確認する曜日", DAYS, index=today.weekday())
selected_tasks = [task for task, days in SCHEDULE.items() if selected_day in days]

for task in selected_tasks:
    st.write(f"☑️ {task}")

st.caption("※ チェック状態は、このブラウザで開いているセッション中に保持されます。")