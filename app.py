import streamlit as st
import pandas as pd
import re

# 過去の連動パターンを解析するロジック
def analyze_structure(prev_results, total_n):
    # 前走の着順（正・逆）をすべて書き出し
    patterns = []
    for h in prev_results:
        patterns.append(f"正{h}")
        patterns.append(f"逆{total_n - h + 1}")
    return patterns

def get_wave_logic(prev_winners, total_n):
    # 自動的に「正逆1」と「正逆10巡目」をベースに全候補を算出
    focus_nums = {1, total_n}
    details = {}
    for h in prev_winners:
        rev = total_n - h + 1
        for i in range(10):
            for v in [h + (i * total_n), rev + (i * total_n)]:
                target = v if v <= total_n else (v % total_n if v % total_n != 0 else total_n)
                focus_nums.add(target)
                if target not in details: details[target] = []
                details[target].append(f"{h}の{i+1}巡")
    return sorted(list(focus_nums)), details

st.set_page_config(page_title="構造解析・波動告知システム", layout="wide")
st.title("🛡️ 構造解析型・波動告知システム")

col1, col2 = st.columns([1, 2])
with col1:
    prev_res_raw = st.text_input("【1】前走確定着順 (例: 7, 6, 9)", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
with col2:
    odds_input = st.text_area("【3】オッズ表をコピペ", height=200)

if odds_input and prev_res_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_res_raw.split(",") if x.strip().isdigit()]
        
        # --- 【核心】馬券構造の告知ロジック ---
        st.subheader("📢 解析官からの構造告知")
        patterns = analyze_structure(prev_list, total_n)
        
        # 構造の告知例：前走の結果から「今の連動性」を言語化
        st.error(f"⚠️ 【現在の馬券構造】 正逆1 vs 正逆10巡目 がワイド圏内で対峙中。")
        st.warning(f"🔄 【エネルギー移動】 前走 {prev_list[0]}番(1着)・{prev_list[1]}番(2着) から、今レースの端（1・{total_n}）および10巡目への転写を感知。")
        
        # データ抽出
        pattern = r"(\d+)\s+[\s\S]*?(\d+\.\d+)\s+(\d+\.\d+)-[\s\S]*?([一-龠ぁ-んァ-ヶ]+)"
        matches = re.findall(pattern, odds_input)
        parsed_data = []
        for m in matches:
            num = int(m[0])
            if 1 <= num <= total_n:
                parsed_data.append({"馬番": num, "単勝": float(m[1]), "複下": float(m[2]), "騎手": m[3]})
        
        df = pd.DataFrame(parsed_data).drop_duplicates('馬番').sort_values("馬番")
        
        wave_list, wave_map = get_wave_logic(prev_list, total_n)

        if not df.empty:
            df['核心'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['注釈'] = df['馬番'].apply(lambda x: ", ".join(list(set(wave_map.get(x, [])))))
            df['単順'] = df['単勝'].rank()
            df['複順'] = df['複下'].rank()
            df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)

            st.table(df[['馬番', '騎手', '単勝', '核心', '異常', '注釈']])

            # 具体的な買い目告知
            hot_horses = df[(df['核心'] != "") & (df['単勝'] > 30)]
            if not hot_horses.empty:
                st.subheader("🚀 告知：狙い撃ち馬番")
                for _, row in hot_horses.iterrows():
                    st.write(f"👉 **馬番 {row['馬番']}（{row['騎手']}）**: 構造上の核心に位置し、単勝{row['単勝']}倍の異常値。ワイド・三連複の軸候補。")

    except Exception as e:
        st.error(f"解析待機中... データを貼り付けてください。")
