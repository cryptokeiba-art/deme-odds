import streamlit as st
import pandas as pd
import re

def get_wave_logic(prev_list, total_n):
    # 正逆1, 10を最優先の連続構造として固定
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

st.set_page_config(page_title="構造核心告知システム", layout="wide")

# --- 最上部：連続出現数字の目立つ告知 ---
st.error("🔥 【核心構造：連続出現数字】 🔥")
st.markdown("### **正逆 1番・10番・12番・3番**（現在このラインが連動中。穴馬はここから炙り出します）")

st.divider()

c1, c2 = st.columns([1, 2])
with c1:
    prev_raw = st.text_input("【1】前走確定着順", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
with c2:
    odds_raw = st.text_area("【3】オッズ表をコピペ", height=200)

if odds_raw and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_logic(prev_list, total_n)
        
        # --- 超堅牢なデータ抽出ロジック（フォーマット崩れ対策） ---
        rows = []
        for line in odds_raw.split('\n'):
            line = line.strip()
            # 1. 小数（オッズ）を探す
            floats = re.findall(r"\d+\.\d+", line)
            if not floats: continue
            
            # 2. 単勝オッズ（最初の小数）の左側を解析して馬番を特定
            left_part = line.split(floats[0])[0].strip()
            ints_left = re.findall(r"\d+", left_part)
            horse_num = int(ints_left[-1]) if ints_left else 0
            
            # 3. 行全体から漢字（騎手名）を特定
            # 2文字以上の漢字を抽出
            kanji_names = re.findall(r"([一-龠]{2,})", line)
            # 特定の場所名を除外して最後の漢字を騎手名とする
            ignore_list = ["船橋","浦和","大井","川崎","門別","高知","佐賀"]
            kisyu_list = [k for k in kanji_names if k not in ignore_list]
            kisyu = kisyu_list[-1] if kisyu_list else "不明"
            
            if horse_num > 0:
                rows.append({
                    "馬番": horse_num,
                    "騎手": kisyu,
                    "単勝": float(floats[0]),
                    "複下": float(floats[1]) if len(floats) > 1 else 0.0
                })

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")
        
        if not df.empty:
            df['単順'] = range(1, len(df) + 1)
            df['複順'] = df['複下'].rank(method='min')
            df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))

            # --- テーブル表示（カラム崩れを許さない表示形式） ---
            st.subheader("📊 解析告知テーブル")
            # st.table を使い、全データを固定幅で表示
            st.table(df[['馬番', '騎手', '単勝', '判定', '異常', '根拠']].reset_index(drop=True))

            # --- 推奨馬券セクション ---
            st.divider()
            jiku = df.iloc[0]['馬番']
            
            # 相手候補の整理
            ana_nums = [1, total_n, 10, max(1, total_n-9)]
            opponents = sorted(list(set(ana_nums + [2, total_n-1]))) # 2, 11番等も追加
            opponents = [n for n in opponents if n != jiku and n <= total_n]

            st.subheader("🎫 推奨馬券告知")
            st.success(f"**三連複 1頭軸流し**")
            st.write(f"軸：{jiku} ―― 相手：{', '.join(map(str, opponents))}")

            st.info(f"**三連単 軸1頭マルチ（工夫枠）**")
            # オッズ解析で🚨や上位人気の馬を相手に優先
            multi_opponents = [n for n in [2, total_n-1, total_n] if n <= total_n and n != jiku]
            st.write(f"軸：{jiku} ―― 相手：{', '.join(map(str, multi_opponents))}")
            st.caption(f"※連続構造の端（{total_n}番）と、オッズ乖離の可能性がある正逆2番を厚めに。")

    except Exception as e:
        st.error(f"解析待機中... データを貼り付けてください。")
