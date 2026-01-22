import streamlit as st
import pandas as pd
import re

# 正逆10巡目の計算ロジック
def get_wave_details(horse_list, total_n):
    wave_map = {} # 数字：どの馬から来たか
    for h in horse_list:
        rev = total_n - h + 1
        for i in range(10):
            # 正巡と逆巡の計算
            for val in [h + (i * total_n), rev + (i * total_n)]:
                if val not in wave_map:
                    wave_map[val] = []
                wave_map[val].append(h)
    return wave_map

st.set_page_config(page_title="出目波動・断層解析", layout="wide")
st.title("🎯 波動継承・穴馬狙撃システム")

col1, col2 = st.columns(2)
with col1:
    prev_res_raw = st.text_input("【1】前走3着以内馬番 (例: 7, 6, 9)", "")
    total_n = st.number_input("【2】今レースの頭数", min_value=1, value=12)
with col2:
    odds_data = st.text_area("【3】オッズ表(単複)をコピペ", height=150)

if odds_data and prev_res_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_res_raw.split(",")]
        # 全10巡目までの「波動数字」を算出
        wave_dict = get_wave_details(prev_list, total_n)
        
        # オッズ抽出
        pattern = r"(\d+)\s+[\s\S]+?\s+(\d+\.\d+)\s+(\d+\.\d+)-"
        matches = re.findall(pattern, odds_data)
        df = pd.DataFrame(matches, columns=['馬番', '単勝', '複勝下限']).astype(float)
        df['馬番'] = df['馬番'].astype(int)
        
        # 単勝人気順での断層計算
        df = df.sort_values('単勝')
        df['断層'] = (df['単勝'].shift(-1) / df['単勝']).fillna(1.0)
        
        # 波動判定：今レースの馬番が、10巡目波動のいずれかに合致するか
        def check_wave(row):
            h = int(row['馬番'])
            # 今レースの馬番が波動リストにあるかチェック
            if h in wave_dict:
                return f"🔥継承元:{wave_dict[h]}"
            return ""

        df['波動'] = df.apply(check_wave, axis=1)
        df['仕込'] = df.apply(lambda r: "🕵️" if 50 < r['単勝'] < 130 else "", axis=1)
        
        # 馬番順に戻して表示
        df = df.sort_values('馬番').reset_index(drop=True)
        df.index = df.index + 1
        
        st.subheader("📊 波動・オッズ解析表")
        st.table(df[['馬番', '単勝', '波動', '仕込', '断層']].style.format({'単勝': '{:.1f}', '断層': '{:.2f}'}))
        
        # 結論：波動 × 仕込みの重複
        picks = df[(df['波動'] != "") & (df['仕込'] != "")]
        if not picks.empty:
            st.error(f"🚀 【波動継承の穴馬】 馬番: {', '.join(picks['馬番'].astype(str).tolist())}")
            st.info("※前レースの着順馬から『10巡目以内』にこの馬番が隠れていました。")
        else:
            st.warning("波動と仕込みが一致する馬はいませんでした。")

    except Exception as e:
        st.error(f"解析エラー: {e}")
