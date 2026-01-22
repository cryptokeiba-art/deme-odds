import streamlit as st
import pandas as pd
import re

def get_wave_details(horse_list, total_n):
    wave_map = {}
    all_numbers = set()
    for h in horse_list:
        rev = total_n - h + 1
        for i in range(10):
            for val in [h + (i * total_n), rev + (i * total_n)]:
                if val <= total_n:
                    if val not in wave_map: wave_map[val] = []
                    wave_map[val].append(h)
                    all_numbers.add(val)
    return wave_map, sorted(list(all_numbers))

st.set_page_config(page_title="究極・地方競馬解析", layout="wide")
st.title("🏇 波動×断層×異常投票 解析システム")

col1, col2 = st.columns(2)
with col1:
    prev_res_raw = st.text_input("【1】前走確定着順 (例: 7, 6, 9)", "")
    total_n = st.number_input("【2】今レースの頭数", min_value=1, value=12)
with col2:
    odds_data = st.text_area("【3】オッズ表をコピペ", height=150)

if odds_data and prev_res_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_res_raw.split(",")]
        wave_dict, wave_list = get_wave_details(prev_list, total_n)
        
        # オッズ解析
        pattern = r"(\d+)\s+[\s\S]+?\s+(\d+\.\d+)\s+(\d+\.\d+)-"
        matches = re.findall(pattern, odds_data)
        df = pd.DataFrame(matches, columns=['馬番', '単勝', '複勝下限']).astype(float)
        df['馬番'] = df['馬番'].astype(int)
        
        # 複勝売れランク（異常投票チェック）
        df['複勝順位'] = df['複勝下限'].rank(method='min')
        df['単勝順位'] = df['単勝'].rank(method='min')
        df['異常'] = df.apply(lambda r: "🚨" if (r['単勝順位'] - r['複勝順位']) >= 3 else "", axis=1)

        # 断層計算
        df = df.sort_values('単勝')
        df['断層'] = (df['単勝'].shift(-1) / df['単勝']).fillna(1.0)
        
        # 判定
        df['波動'] = df['馬番'].apply(lambda x: f"🔥継承:{wave_dict[x]}" if x in wave_dict else "")
        df['判定'] = df.apply(lambda r: "🚩有力" if 50 < r['単勝'] < 150 else ("⭐次点" if r['馬番'] in [1, total_n] else ""), axis=1)
        
        df = df.sort_values('馬番').reset_index(drop=True)
        df.index = df.index + 1

        # --- 表示 ---
        st.subheader("📋 連続出現（波動）数字リスト")
        st.success(f"今回の波動馬番： {', '.join(map(str, wave_list))}")

        st.subheader("📊 総合解析データ")
        st.table(df[['馬番', '単勝', '波動', '判定', '異常', '断層']].style.format({'単勝': '{:.1f}', '断層': '{:.2f}'}))
        
        # --- 親切なアドバイス ---
        st.subheader("🕵️ 解析官の親切コメント")
        
        # 銀行判定
        top_fav = df.loc[df['単勝順位'] == 1].iloc[0]
        if top_fav['単勝'] < 2.0 and top_fav['断層'] > 2.0:
            st.write("💎 **【銀行レース】** 1番人気が盤石です。紐荒れを狙いましょう。")
        else:
            st.write("💥 **【波乱含み】** 絶対的な軸が不在。高配当のチャンスです。")

        # 異常投票の解説
        abnormal = df[df['異常'] == "🚨"]
        if not abnormal.empty:
            st.error(f"⚠️ **【異常投票あり】** 馬番 {', '.join(abnormal['馬番'].astype(str).tolist())} は複勝が異常に売れています。仕込まれている可能性があります！")

        # 12Rのような特殊ケースへの言及
        if total_n in wave_list:
            st.warning(f"💡 **【正逆の法則】** 大外の {total_n}番に波動が出ています。今日の船橋は外枠の波動が強い傾向にあります。12番は要チェックです。")

    except Exception as e:
        st.error(f"解析エラー: {e}")
