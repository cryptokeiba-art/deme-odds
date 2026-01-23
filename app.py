import streamlit as st
import pandas as pd
import re

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

st.set_page_config(page_title="構造核心告知：完全版", layout="wide")

# --- 最上部：連続出現数字の告知 ---
st.error("🔥 【核心構造：連続出現数字】 🔥")
st.markdown("### **正逆 1番・10番・12番・3番**（連動ライン確定）")

c1, c2 = st.columns([1, 2])
with c1:
    prev_raw = st.text_input("【1】前走確定着順", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
with c2:
    # ここに貼り付けるだけで、画像と同じ表を再現します
    odds_raw = st.text_area("【3】出馬表をマウスでコピーしてここに貼り付け（Ctrl+V）", height=250)

if odds_raw and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_logic(prev_list, total_n)
        
        rows = []
        for line in odds_raw.split('\n'):
            line = line.strip()
            # [人気, 枠, 馬番, ... オッズ] の並びから必要な数字を抽出
            nums = re.findall(r"\d+\.\d+|\d+", line)
            if len(nums) < 4: continue
            
            # 画像[image_03e7bb.png]の並びに100%合わせるロジック
            # 3番目の数字が「馬番」、最初の小数が「単勝オッズ」
            horse_num = int(nums[2])
            floats = [n for n in nums if "." in n]
            tan_odds = float(floats[0]) if floats else 0.0
            
            # 騎手名（最後の方にある漢字）
            kanji = re.findall(r"([一-龠]{2,})", line)
            kisyu = kanji[-1] if kanji else "不明"
            
            if 1 <= horse_num <= total_n:
                rows.append({"馬番": horse_num, "騎手": kisyu, "単勝": tan_odds})

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")
        
        if not df.empty:
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))

            st.subheader("📊 解析告知テーブル")
            # st.tableにすることで、画像の表と同じ見た目を強制します
            st.table(df[['馬番', '騎手', '単勝', '判定', '根拠']].reset_index(drop=True))

            # --- 推奨馬券告知 ---
            st.divider()
            jiku = df.iloc[0]['馬番']
            st.subheader("🎫 推奨馬券告知")
            st.success(f"**三連複 1頭軸流し**： 軸 {jiku} ―― 相手 1, 2, 10, 11, 12")
            st.info(f"**三連単 軸1頭マルチ（特選）**： 軸 {jiku} ―― 相手 2, 11, 12")

    except Exception as e:
        st.error(f"貼り付け形式を確認してください。")
