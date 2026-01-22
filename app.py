import streamlit as st
import pandas as pd
import re

def get_10_layers(horse_list, total_n):
    waves = set()
    for h in horse_list:
        rev = total_n - h + 1
        for i in range(10):
            waves.add(h + (i * total_n))
            waves.add(rev + (i * total_n))
    return waves

st.set_page_config(page_title="波動×断層 穴馬解析", layout="wide")
st.title("🎯 地方競馬 波動・断層解析")

col1, col2 = st.columns(2)
with col1:
    prev_res = st.text_input("【1】前レース確定着順 (例: 7, 6, 9)", "")
    total_n = st.number_input("【2】今レースの頭数", min_value=1, value=12)
with col2:
    odds_data = st.text_area("【3】オッズ表(単複)をコピペ", height=150)

if odds_data and prev_res:
    try:
        prev_list = [int(x.strip()) for x in prev_res.split(",")]
        wave_nums = get_10_layers(prev_list, total_n)
        
        pattern = r"(\d+)\s+[\s\S]+?\s+(\d+\.\d+)\s+(\d+\.\d+)-"
        matches = re.findall(pattern, odds_data)
        df = pd.DataFrame(matches, columns=['馬番', '単勝', '複勝下限']).astype(float)
        
        # 馬番を整数にし、人気順ではなく馬番順に並べる
        df['馬番'] = df['馬番'].astype(int)
        df = df.sort_values('馬番').reset_index(drop=True)
        
        # 断層計算（単勝人気順での比較が必要なため一時的にソート）
        df_sorted = df.sort_values('単勝')
        df_sorted['断層'] = (df_sorted['単勝'].shift(-1) / df_sorted['単勝']).fillna(1.0)
        df = df.merge(df_sorted[['馬番', '断層']], on='馬番')
        
        def judge(row):
            h = int(row['馬番'])
            res = []
            if h in wave_nums: res.append("🔥波動")
            if row['断層'] > 1.5: res.append("⚡断層")
            if 50 < row['単勝'] < 130: res.append("🕵️仕込")
            return " ".join(res)

        df['判定'] = df.apply(judge, axis=1)
        
        # --- 見やすさの改良 ---
        # 1. インデックスを1番からにする
        df.index = df.index + 1
        
        st.subheader("📊 解析スコア（馬番順）")
        
        # 2. 注目馬だけ色をつけるスタイル設定
        def highlight_picks(s):
            return ['background-color: #ffff00; color: black; font-weight: bold' if '🔥' in str(v) and '🕵️' in str(v) else '' for v in s]

        st.table(df.style.format({'単勝': '{:.1f}', '複勝下限': '{:.1f}', '断層': '{:.2f}'}))
        
        # 3. 結論をはっきり出す
        picks = df[df['判定'].str.contains("🔥") & df['判定'].str.contains("🕵️")]
        if not picks.empty:
            st.error(f"🚀 【激熱の穴馬】 馬番: {', '.join(picks['馬番'].astype(str).tolist())} が波動×仕込みに合致！")
        
    except Exception as e:
        st.error(f"入力形式を確認してください: {e}")
