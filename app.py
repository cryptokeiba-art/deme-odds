import streamlit as st
import pandas as pd
import re

def get_wave_focus(prev_winners, total_n):
    # 正逆1と正逆10（10巡目）にフォーカスした波動抽出
    focus_nums = {1, total_n} # 正逆1は常にフォーカス
    wave_details = {}
    
    for h in prev_winners:
        rev = total_n - h + 1
        # 10巡目までの波動を計算
        for i in range(10):
            for val in [h + (i * total_n), rev + (i * total_n)]:
                if 1 <= val <= total_n:
                    focus_nums.add(val)
                    if val not in wave_details: wave_details[val] = []
                    wave_details[val].append(f"{h}({i+1}巡)")
    return focus_nums, wave_details

st.set_page_config(page_title="正逆1vs10 核心解析", layout="wide")
st.title("🎯 波動核心フォーカス：正逆1 vs 正逆10")

# 入力セクション
col1, col2 = st.columns(2)
with col1:
    prev_res = st.text_input("【1】前走確定（例: 7, 6, 9）", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
with col2:
    odds_input = st.text_area("【3】オッズ・騎手・馬体重データを全コピー", height=200)

if odds_input and prev_res:
    try:
        # 改良版データ抽出：枠、馬番、馬名、単勝、複勝、性齢、体重、重、騎手を抽出
        pattern = r"(\d)\s+(\d+)\s+(.+?)\s+(\d+\.\d+)\s+(\d+\.\d+)-(\d+\.\d+)\s+(\w\d)\s+(\d+)\D+(\d+)\D+\s+(\d+\.\d+)\s+([^\s]+)"
        matches = re.findall(pattern, odds_input)
        
        data = []
        for m in matches:
            data.append({
                "枠": int(m[0]), "馬番": int(m[1]), "馬名": m[2],
                "単勝": float(m[3]), "複下限": float(m[4]), "騎手": m[10], "体重": int(m[7])
            })
        
        df = pd.DataFrame(data).sort_values("馬番")
        
        # 波動解析
        prev_list = [int(x.strip()) for x in prev_res.split(",")]
        focus_set, wave_map = get_wave_focus(prev_list, total_n)
        
        # 核心フラグ
        df['波動核心'] = df['馬番'].apply(lambda x: "🔥" if x in focus_set else "")
        df['詳細'] = df['馬番'].apply(lambda x: wave_map.get(x, ""))
        
        # 異常投票(単複乖離)
        df['複順'] = df['複下限'].rank()
        df['単順'] = df['単勝'].rank()
        df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)

        # 表示
        st.subheader(f"🔍 解析結果：正逆1 vs 正逆10（出現候補: {sorted(list(focus_set))}）")
        
        # テーブル表示
        st.table(df[['枠', '馬番', '騎手', '単勝', '波動核心', '異常', '詳細']])
        
        # 核心アドバイス
        st.subheader("💡 核心的フォーカス・アドバイス")
        target_12 = df[df['馬番'] == total_n].iloc[0]
        if target_12['馬番'] in focus_set:
            st.error(f"⚠️ 核心合致：大外{total_n}番（{target_12['騎手']}）に前走からの波動が直撃しています。正逆1の起点として最重要。")
            
        if any(df['異常'] == "🚨"):
            ab_horses = df[df['異常'] == "🚨"]['馬番'].tolist()
            st.warning(f"📢 異常投票：馬番 {ab_horses} は、単勝人気に比して複勝が異常に買われています。銀行レース崩しの刺客です。")

    except Exception as e:
        st.error("データの抽出に失敗しました。サイトの表を「枠」から「騎手」まで横に長くコピーしてください。")
