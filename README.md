# 清掃・在庫管理 v4

Streamlit Cloudで発生していた `st.dataframe()` の TypeError を修正した版です。

主な機能:
- 清掃チェックリスト
- チェックリストの確実なリセット
- CSV風の在庫一覧表
- 仕入数・出庫数・容量・発注を表から直接編集
- 理論在庫数の自動計算
- 発注対象から発注リストを作成
- 発注リストPDF作成・印刷
- 発注記録

## Streamlit Cloud
GitHubの `app.py` と `requirements.txt` をこの版に置き換えてください。
`requirements.txt` に `reportlab` を入れているのでPDF機能も動作します。
