import streamlit as st
import pandas as pd
import re

def get_wave_logic(prev_list, total_n):
    # 基本の構造核心（正逆1, 10）
    targets = {1, total_n, 10, (total_n - 9 if total_n >= 10 else 0)}
    wave_details = {
        1: ["正1(連続構造)"], 
        total_n: ["逆1(連続構造)"], 
        10: ["正10(連続構造)"], 
        (total_n - 9 if total_n >= 10 else 0): ["逆10(連続構造)"]
    }
    # 前走3巡エネルギー
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

st.set_page_config(page_title="構造核心・オッズ選別告知", layout="wide")
st.title("🛡️ 構造核心告知：オッズ選別エディション")

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
        
        lines = [l.strip() for l in odds_raw.split('\n') if l.strip()]
        rows = []
        for line in lines:
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
            st.subheader("📊 解析告知")
            
            # --- ◯の選定と「裏」の判定ロジック ---
            ◎_num = df.iloc[0]['馬番']
            
            # 本日の強い候補（例として6, 7）
            strong_candidates = [6, 7, total_n-5, total_n-6]
            selected_maru = []
            maru_reasons = []

            for c in strong_candidates:
                if c <= total_n and c != ◎_num:
                    target_row = df[df['馬番'] == c]
                    if not target_row.empty:
                        # オッズ解析：単複乖離(🚨)がある、もしくは人気10位以内なら採用
                        if target_row.iloc[0]['異常'] == "🚨" or target_row.iloc[0]['単順'] <= 10:
                            selected_maru.append(c)
                            maru_reasons.append(f"{c}番(構造優先)")
                        else:
                            # 裏を含めない理由の生成
                            st.caption(f"※{c}番（{target_row.iloc[0]['馬番']}の裏）はオッズ乖離・支持が弱いため除外。")

            st.table(df[['馬番', '騎手', '単勝', '判定', '異常', '根拠']].reset_index(drop=True))

            st.divider()
            st.subheader("🐴 有力馬番")
            
            # 確定印
            ▲ = [1, total_n]
            △ = [10, (total_n-9 if total_n >= 10 else 0)]
            
            st.write(f"◎ **{◎_num}番** （人気馬：銀行評価）")
            st.write(f"◯ **{', '.join(map(str, selected_maru[:2]))}番** （本日強い構造＋オッズ裏付けあり）")
            st.write(f"▲ **{', '.join(map(str, ▲))}番** （連続構造：正逆1）")
            st.write(f"△ **{', '.join(map(str, △))}番** （連続構造：正逆10）")

            # --- 推奨馬券（三連複1頭軸・三連単） ---
            st.subheader("🎫 推奨馬券")
            # 1, 2, 3, 11, 12等の核心馬を統合
            target_all = sorted(list(set([◎_num] + selected_maru + ▲ + △)))
            opponents = [n for n in target_all if n != ◎_num]
            
            st.success(f"**三連複 1頭軸流し**")
            st.write(f"軸：{◎_num} ―― 相手：{', '.join(map(str, opponents))}")

            st.info(f"**三連単 推奨フォーメーション**")
            st.write(f"1着：{◎_num}")
            st.write(f"2着：{', '.join(map(str, selected_maru[:2])) if selected_maru else '構造上位'}")
            st.write(f"3着：{', '.join(map(str, opponents))}")

    except Exception as e:
        st.error(f"解析待機中...")
