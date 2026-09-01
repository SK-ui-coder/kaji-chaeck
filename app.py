import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title='清掃・在庫管理', page_icon='🧹', layout='wide')
DAYS=['月','火','水','木','金','土','日']
FULL=['月曜日','火曜日','水曜日','木曜日','金曜日','土曜日','日曜日']
SCHEDULE={'洗濯':['月曜日','水曜日','金曜日'],'トイレ・洗面':['火曜日','木曜日','土曜日'],'床':FULL,'玄関':['土曜日'],'壁・窓':['月曜日','金曜日'],'排水溝':['火曜日','水曜日'],'加湿器':['木曜日','日曜日'],'皿・台所':FULL,'在庫管理':['金曜日','土曜日','日曜日'],'価格調査':FULL}
INITIAL=[['風呂用洗剤',1,0,500,False],['トイレ洗剤',1,0,500,False],['トイレ芳香剤',1,0,500,False],['洗濯洗剤',1,0,500,False],['洗濯柔軟剤',1,0,500,False],['トイレ漂白剤',1,0,500,False],['漂白剤',1,0,500,False],['住宅洗剤',1,0,500,False],['床シート1',1,0,100,True],['床シート2',1,0,100,True],['ロール',1,0,100,True]]
if 'inv' not in st.session_state: st.session_state.inv=pd.DataFrame(INITIAL,columns=['商品名','仕入数','出庫数','容量','発注'])
if 'clean' not in st.session_state: st.session_state.clean={}
now=datetime.now(); idx=now.weekday(); today=FULL[idx]
st.title('🧹 清掃・在庫管理'); st.caption(f'{now:%Y年%m月%d日}（{today}）')
t1,t2=st.tabs(['🧹 チェックリスト','📦 在庫表'])
with t1:
    tasks=[x for x,d in SCHEDULE.items() if today in d]
    st.subheader('今日のチェック')
    c1,c2,c3=st.columns(3); done=sum(st.session_state.clean.get(x,False) for x in tasks)
    c1.metric('予定',len(tasks)); c2.metric('完了',done); c3.metric('残り',len(tasks)-done)
    todaydf=pd.DataFrame({'項目':tasks,'完了':[st.session_state.clean.get(x,False) for x in tasks]})
    edited=st.data_editor(todaydf,hide_index=True,use_container_width=True,disabled=['項目'],column_config={'項目':st.column_config.TextColumn('項目',width='large'),'完了':st.column_config.CheckboxColumn('☑ 完了')},key='today')
    for _,r in edited.iterrows(): st.session_state.clean[r['項目']]=bool(r['完了'])
    if st.button('🔄 今日のチェックを全部リセット',use_container_width=True):
        for x in tasks: st.session_state.clean[x]=False
        st.session_state.pop('today',None); st.rerun()
    st.divider(); st.subheader('📅 週間予定')
    rows=[]
    for task,days in SCHEDULE.items(): rows.append([task]+['⭕' if d in days else '—' for d in FULL])
    st.dataframe(pd.DataFrame(rows,columns=['項目']+DAYS),hide_index=True,use_container_width=True,column_config={'項目':st.column_config.TextColumn('項目',width='large')})
with t2:
    st.subheader('📦 在庫管理表'); st.caption('理論在庫数 ＝ 仕入数 − 出庫数')
    df=st.session_state.inv.copy(); df['理論在庫数']=(df['仕入数']-df['出庫数']).clip(lower=0)
    orders=df.loc[df['発注'],'商品名'].tolist(); zero=df.loc[df['理論在庫数']==0,'商品名'].tolist()
    a,b,c=st.columns(3); a.metric('商品数',len(df)); b.metric('在庫合計',int(df['理論在庫数'].sum())); c.metric('発注',len(orders))
    if orders: st.warning('🛒 発注対象：'+'、'.join(orders))
    if zero: st.error('⚠️ 在庫0：'+'、'.join(zero))
    edited=st.data_editor(df,hide_index=True,use_container_width=True,num_rows='dynamic',disabled=['理論在庫数'],column_config={'商品名':st.column_config.TextColumn('商品名',width='large'),'仕入数':st.column_config.NumberColumn('仕入数',min_value=0,step=1),'出庫数':st.column_config.NumberColumn('出庫数',min_value=0,step=1),'理論在庫数':st.column_config.NumberColumn('理論在庫数'),'容量':st.column_config.NumberColumn('容量',min_value=0,step=1),'発注':st.column_config.CheckboxColumn('🛒 発注')},key='inventory')
    base=edited[['商品名','仕入数','出庫数','容量','発注']].copy(); base[['仕入数','出庫数','容量']]=base[['仕入数','出庫数','容量']].fillna(0).astype(int); base['発注']=base['発注'].fillna(False).astype(bool); st.session_state.inv=base.reset_index(drop=True)
    if st.button('🔄 在庫表を初期状態に戻す',use_container_width=True):
        st.session_state.inv=pd.DataFrame(INITIAL,columns=['商品名','仕入数','出庫数','容量','発注']); st.session_state.pop('inventory',None); st.rerun()
st.caption('CSVのような一覧表で、スマホでは横スクロールして確認できます。')
