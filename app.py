import streamlit as st
import pandas as pd
import re

def get_wave_logic(prev_list, total_n):
    # 正逆1, 正逆10は「連続出現数字」として固定
    targets = {1, total_n, 10, (total_n - 10 + 1)}
    wave_details = {
        1: ["正1(連続構造)"], 
        total_n: ["逆1(連続構造)"], 
        10: ["正10(連続構造)"], 
        (total_n - 10 + 1): ["逆10(連続構造)"]
    }
    
    # 前走からの3巡（エネルギー移動）を追加
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

st.set_page_config(page_title="構造告知：穴馬炙り出し", layout="wide")
st.title("🛡️ オッズ・出目解析：構造核心告知")

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
        
        # --- 鉄壁のデータ抽出（カラム崩れ完全防止） ---
        lines = odds_raw.split('\n')
        rows = []
        for line in lines:
            floats = re.findall(r"\d+\.\d+", line)
            if len(floats) >= 2:
                # 単勝オッズ(floats[0])の左側にある「一番近い整数」を馬番と定義
                parts = line.split(floats[0])[0].split()
                horse_num = int(re.sub(r"\D", "", parts[-1])) if parts else 0
                
                # 騎手名の抽出（カッコ付きデータ等を排除）
                names = re.findall(r"([一-龠]{2,})", re.sub(r"\(.*?\)", "", line))
                kisyu = [n for n in names if n not in ["船橋","浦和","大井","川崎","単勝","複勝","確定"]][-1]
                
                rows.append({"馬番": horse_num, "単勝": float(floats[0]), "複下": float(floats[1]), "騎手": kisyu})

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")

        if not df.empty:
            # --- 1. オッズ・出目解析 ---
            st.subheader("📊 オッズ・出目解析（告知）")
            st.info(f"【オッズ解析】 上位人気の単複バランスから軸馬を安定評価。")
            st.error(f"【連続出現数字】 現在「正逆1番・正逆10番」が強力に連動中。穴馬はここから炙り出します。")

            # --- 2. 解析テーブル ---
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))
            df['単順'] = range(1, len(df) + 1)
            df['複順'] = df['複下'].rank(method='min')
            df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)
            
            st.table(df[['馬番', '騎手', '単勝', '判定', '異常', '根拠']])

            # --- 3. 最終結論 ---
            st.divider()
            st.subheader("🐴 有力馬番")
            st.caption("※穴馬はオッズに関わらず、連続出現している構造的数字（正逆1, 10）から無慈悲に選定します。")

            # 有力馬選定
            y_jiku = df.iloc[0]['馬番']  # ◎
            y_fuku = df.iloc[1]['馬番'] if len(df) > 1 else 0 # ◯
            
            # 正逆1, 10を確実に確保（穴馬候補）
            segyaku_target = {1, total_n, 10, (total_n - 9 if total_n >= 10 else 0)}
            ana_candidates = [n for n in segyaku_target if n != y_jiku and n != y_fuku and n != 0]

            st.write(f"◎ **{y_jiku}番** （人気馬：オッズ断層および支持の壁）")
            st.write(f"◯ **{y_fuku}番** （人気馬：本日の構造の裏付け）")
            st.write(f"▲ **{', '.join(map(str, [1, total_n]))}番** （核心：連続出現中の正逆1）")
            st.write(f"△ **{', '.join(map(str, [n for n in ana_candidates if n not in [1, total_n]]))[:2]}番** （核心：連続出現中の正逆10）")

            st.subheader("🎫 推奨馬券")
            st.success(f"ワイド：{y_jiku}-{y_fuku}（本線） / {y_jiku}-1, {y_jiku}-{total_n}（構造穴への流し）")
            st.info(f"三連複：{y_jiku}-{y_fuku}-1, {y_jiku}-{y_fuku}-{total_n}（構造核心決着）")

    except Exception as e:
        st.error(f"解析待機中... データを貼り付けてください。")
