import streamlit as st
import pandas as pd
import re

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
with c2:
    # 画像でもテキストでも対応できるよう入力を受け付け
    odds_raw = st.text_area("【3】出馬表をコピペしてください", height=200, placeholder="人気 枠 馬番 馬名 単勝... の順で貼り付け")

if odds_raw and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_logic(prev_list, total_n)
        
        rows = []
        for line in odds_raw.split('\n'):
            line = line.strip()
            # 数値をすべて抽出
            nums = re.findall(r"\d+\.\d+|\d+", line)
            if len(nums) < 4: continue
            
            # 画像[image_03e7bb.png]の並びに準拠：
            # nums[0]=人気, nums[1]=枠, nums[2]=馬番, nums[3]=単勝オッズ(小数)
            # もしnums[3]が整数なら、小数が見つかるまでスライド
            floats = [n for n in nums if "." in n]
            if not floats: continue
            
            tan_odds = float(floats[0])
            # 単勝オッズ(floats[0])のインデックスを探し、その2つ前が「馬番」
            f_idx = nums.index(floats[0])
            horse_num = int(nums[f_idx - 1])
            
            # 漢字（騎手名）の抽出
            kanji = re.findall(r"([一-龠]{2,})", line)
            ignore = ["船橋","浦和","大井","川崎","単勝","複勝"]
            kisyu_cand = [k for k in kanji if k not in ignore]
            kisyu = kisyu_cand[-1] if kisyu_cand else "不明"
            
            rows.append({"馬番": horse_num, "騎手": kisyu, "単勝": tan_odds})

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")
        
        if not df.empty:
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))

            st.subheader("📊 解析告知テーブル")
            # indexを隠し、列幅を固定する table 形式で出力
            st.table(df[['馬番', '騎手', '単勝', '判定', '根拠']].reset_index(drop=True))

            # --- 3. 推奨馬券（三連単マルチ工夫版） ---
            st.divider()
            jiku = df.iloc[0]['馬番'] # 人気1位を軸（例:3番）
            
            # 相手：2, 11, 12番を抽出
            # 12頭立てなら 11番(逆2), 12番(逆1)
            target_opponents = [2, total_n, total_n-1]
            multi_opponents = [n for n in target_opponents if n <= total_n and n != jiku]

            st.subheader("🎫 推奨馬券告知")
            
            # 三連複1頭軸流し
            fuku_opps = sorted(list(set([1, 2, 10, 11, 12])))
            fuku_opps = [n for n in fuku_opps if n <= total_n and n != jiku]
            st.success(f"**三連複 1頭軸流し**")
            st.write(f"軸：{jiku} ―― 相手：{', '.join(map(str, fuku_opps))}")

            # 三連単 軸1頭マルチ
            st.info(f"**三連単 軸1頭マルチ（構造核心）**")
            st.write(f"軸：**{jiku}番**")
            st.write(f"相手：**{', '.join(map(str, multi_opponents))}番**")
            st.caption(f"※単勝断層および正逆2番・逆1番の波動を重視した3点マルチ構成。")

    except Exception as e:
        st.error(f"解析エラー: {e}")
