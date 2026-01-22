import streamlit as st
import pandas as pd
import re

def get_wave_logic(prev_list, total_n):
    # 正逆1, 10は連続構造として固定
    targets = {1, total_n, 10, (total_n - 9 if total_n >= 10 else 0)}
    wave_details = {1: ["正1"], total_n: ["逆1"], 10: ["正10"], (total_n-9): ["逆10"]}
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

st.set_page_config(page_title="構造告知：三連単マルチ版", layout="wide")
st.title("🛡️ 構造告知：出目構造×オッズ解析")

c1, c2 = st.columns([1, 2])
with c1:
    prev_raw = st.text_input("【1】前走確定着順", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
with c2:
    odds_raw = st.text_area("【3】オッズ表コピペ", height=200)

if odds_raw and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_logic(prev_list, total_n)
        
        # --- データ抽出 ---
        rows = []
        for line in odds_raw.split('\n'):
            floats = re.findall(r"\d+\.\d+", line)
            if not floats: continue
            prefix = line.split(floats[0])[0]
            ints = re.findall(r"\b\d+\b", prefix)
            if ints:
                horse_num = int(ints[-1])
                names = re.findall(r"([一-龠]{2,})", re.sub(r"\(.*?\)", "", line))
                kisyu = [n for n in names if n not in ["船橋","浦和","大井","川崎","単勝","複勝"]][-1] if names else "不明"
                rows.append({"馬番": horse_num, "単勝": float(floats[0]), "複下": float(floats[1]) if len(floats)>1 else 0.0, "騎手": kisyu})

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")
        df['単順'] = range(1, len(df) + 1)
        df['複順'] = df['複下'].rank(method='min')
        df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)

        if not df.empty:
            st.subheader("📊 解析告知テーブル")
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))
            st.table(df[['馬番', '騎手', '単勝', '判定', '異常', '根拠']].reset_index(drop=True))

            # --- 有力馬選定 ---
            jiku_num = df.iloc[0]['馬番'] # ◎ 3番想定
            
            # 裏（対角）のオッズ選別
            strong_set = [6, 7, 2, total_n-1] # 本日強い数字と正逆2番
            selected_maru = []
            for n in strong_set:
                if n <= total_n and n != jiku_num:
                    row = df[df['馬番'] == n]
                    if not row.empty and (row.iloc[0]['異常'] == "🚨" or row.iloc[0]['単勝'] <= 15.0):
                        selected_maru.append(n)
            
            ana_nums = [1, total_n, 10, (total_n-9 if total_n >= 10 else 0)]
            ana_nums = [n for n in ana_nums if n > 0 and n != jiku_num]

            st.divider()
            st.subheader("🐴 有力馬番")
            st.write(f"◎ **{jiku_num}番** （軸：支持の壁）")
            st.write(f"◯ **{', '.join(map(str, selected_maru))}番** （構造＋オッズ裏付け：不要な対角は除外済）")
            st.write(f"▲ **{', '.join(map(str, [1, total_n]))}番** （連続構造：正逆1）")
            st.write(f"△ **{', '.join(map(str, [n for n in ana_nums if n not in [1, total_n]]))[:2]}番** （連続構造：正逆10）")

            # --- 推奨馬券（三連複・三連単マルチ） ---
            st.subheader("🎫 推奨馬券告知")
            
            # 三連複相手
            fuku_opponents = sorted(list(set(selected_maru + ana_nums)))
            st.success(f"**三連複 1頭軸流し**")
            st.write(f"軸：{jiku_num} ―― 相手：{', '.join(map(str, fuku_opponents))}")

            # 三連単マルチ（オッズ解析を反映）
            # 軸3番、相手に異常(🚨)や強構造の2, 11, 12等を優先
            multi_opponents = [n for n in [2, total_n-1, total_n] if n <= total_n and n != jiku_num]
            
            st.info(f"**三連単 軸1頭マルチ（工夫枠）**")
            st.write(f"軸：{jiku_num} ―― 相手：{', '.join(map(str, multi_opponents))}")
            st.caption(f"※オッズ乖離(🚨)および正逆構造から、高配当の使者として {', '.join(map(str, multi_opponents))} 番を相手に抜擢。")
            
    except Exception as e:
        st.error(f"解析エラー: {e}")
