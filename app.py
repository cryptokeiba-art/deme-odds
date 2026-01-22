import streamlit as st
import pandas as pd
import re
from PIL import Image

# --- 1. 構造計算ロジック ---
def get_wave_logic(prev_list, total_n):
    targets = {1, total_n, 10, (max(1, total_n - 9))}
    wave_details = {1: ["正1"], total_n: ["逆1"], 10: ["正10"], (max(1, total_n-9)): ["逆10"]}
    for h in prev_list:
        rev = total_n - h + 1
        for i in range(3):
            p, r = h + (i * total_n), rev + (i * total_n)
            for v in [p, r]:
                if 1 <= v <= total_n:
                    targets.add(v)
                    if v not in wave_details: wave_details[v] = []
                    wave_details[v].append(f"{h}の{'正' if v==p else '逆'}{i+1}巡")
    return sorted(list(targets)), wave_details

st.set_page_config(page_title="構造核心告知", layout="wide")

# --- 2. 連続出現数字の告知（最上部固定） ---
st.error("🔥 【核心構造：連続出現数字】 🔥")
st.markdown("### **正逆 1番・10番・12番・3番**（現在このラインが連動中）")

st.divider()

c1, c2 = st.columns([1, 2])
with c1:
    prev_raw = st.text_input("【1】前走確定着順", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
    
    # --- 画像アップロード用ボタンをここに追加 ---
    uploaded_image = st.file_uploader("📷 ここに画像をアップロードしてください", type=["png", "jpg", "jpeg"])

with c2:
    # 従来通りテキストでも貼り付け可能
    odds_raw = st.text_area("【3】または、出馬表をテキストでコピペ（Ctrl+V）", height=250)

# --- 3. 解析処理 ---
if (odds_raw or uploaded_image) and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_logic(prev_list, total_n)
        
        # ※本来はここでOCRライブラリを使い画像から文字を読み取りますが、
        # Streamlit Cloud環境で確実に動かすため、貼り付けられたデータの物理位置を優先して処理します。
        
        input_data = odds_raw # 現状はテキスト解析をメインに据えています
        
        rows = []
        for line in input_data.split('\n'):
            line = line.strip()
            nums = re.findall(r"\d+\.\d+|\d+", line)
            if len(nums) < 3: continue
            
            floats = [n for n in nums if "." in n]
            if not floats: continue
            tan_odds = float(floats[0])
            
            f_idx = nums.index(floats[0])
            horse_num = 0
            for offset in [1, 2]:
                check_idx = f_idx - offset
                if check_idx >= 0:
                    val = int(nums[check_idx])
                    if 1 <= val <= total_n:
                        horse_num = val
                        break
            
            kanji = re.findall(r"([一-龠]{2,})", line)
            ignore = ["船橋","浦和","大井","川崎","単勝","複勝"]
            kisyu_cand = [k for k in kanji if k not in ignore]
            kisyu = kisyu_cand[-1] if kisyu_cand else "不明"
            
            if horse_num > 0:
                rows.append({"馬番": horse_num, "騎手": kisyu, "単勝": tan_odds})

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")
        
        if not df.empty:
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))

            st.subheader("📊 解析告知テーブル")
            st.table(df[['馬番', '騎手', '単勝', '判定', '根拠']].reset_index(drop=True))

            # --- 推奨馬券告知 ---
            st.divider()
            jiku = df.iloc[0]['馬番']
            target_opponents = [2, total_n, total_n-1]
            multi_opponents = [n for n in target_opponents if n <= total_n and n != jiku]

            st.subheader("🎫 推奨馬券告知")
            st.success(f"**三連複 1頭軸流し**： 軸 {jiku} ―― 相手 {', '.join(map(str, [1, 2, 10, 11, 12] if total_n >=12 else [1, 2, total_n]))}")
            st.info(f"**三連単 軸1頭マルチ（3点）**： 軸 {jiku} ―― 相手 {', '.join(map(str, multi_opponents))}")

    except Exception as e:
        st.error(f"解析エラー: {e}")
