import streamlit as st
import pandas as pd
import re

def get_wave_3_layers(prev_list, total_n):
    # 正逆3巡目まで、かつ枠内に収まる数字のみを抽出
    targets = {1, total_n} # 正逆1は固定
    wave_details = {}
    
    for h in prev_list:
        rev = total_n - h + 1
        # 正3巡・逆3巡の計算
        for i in range(3):
            p = h + (i * total_n)
            r = rev + (i * total_n)
            for v in [p, r]:
                # 3巡目までの計算結果が頭数以内なら採用
                if 1 <= v <= total_n:
                    targets.add(v)
                    if v not in wave_details: wave_details[v] = []
                    wave_details[v].append(f"{h}番の{'正' if v==p else '逆'}{i+1}巡")
    return sorted(list(targets)), wave_details

st.set_page_config(page_title="波動構造解析", layout="wide")
st.title("🛡️ 構造告知：正逆3巡フォーカス")

c1, c2 = st.columns([1, 2])
with c1:
    prev_raw = st.text_input("【1】前走着順", "7, 6, 9")
    total_n = st.number_input("【2】頭数", min_value=1, value=12)
with c2:
    odds_raw = st.text_area("【3】オッズ表コピペ", height=200)

if odds_raw and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_3_layers(prev_list, total_n)
        
        # データ抽出：性別(牝/牡/セ)を無視して騎手名を拾う
        pattern = r"(\d+)\s+[\s\S]*?(\d+\.\d+)\s+(\d+\.\d+)-[\s\S]*?(?:牝|牡|セ)\d+\s+\([+-]?\d+\)\s+\d+\.\d+\s+([一-龠ぁ-んァ-ヶ]+)"
        matches = re.findall(pattern, odds_raw)
        
        rows = []
        for m in matches:
            rows.append({"馬番": int(m[0]), "単勝": float(m[1]), "複下": float(m[2]), "騎手": m[3]})
        
        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("馬番")

        if not df.empty:
            # --- 告知エリア ---
            st.subheader("📢 構造告知アラート")
            st.error(f"🔥 【現在の核心】 正逆1番 および 前走{prev_list}からの「正逆3巡以内」が連動中。")
            
            # 異常投票の算出（単勝人気と複勝人気の乖離）
            df['単順'] = df['単勝'].rank()
            df['複順'] = df['複下'].rank()
            df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)
            
            # テーブル構成
            df['核心'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: ", ".join(wave_map.get(x, [])))

            st.table(df[['馬番', '騎手', '単勝', '核心', '異常', '根拠']])

            # 指示
            st.subheader("🚀 構造上の狙い目")
            targets = df[(df['核心'] != "") & (df['単勝'] > 20)]
            if not targets.empty:
                for _, row in targets.iterrows():
                    st.success(f"馬番 {row['馬番']}（{row['騎手']}）：3巡目以内の波動に合致。穴馬としての構造的根拠あり。")
        else:
            st.warning("データ形式が合いません。表の「馬番」から「騎手」までをコピーしてください。")

    except Exception as e:
        st.error(f"解析待機中...")
