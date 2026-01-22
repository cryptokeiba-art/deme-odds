import streamlit as st
import pandas as pd
import re

def get_wave_logic(prev_list, total_n):
    # 正逆1, 10は連続構造として固定
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
st.title("🛡️ 構造核心告知：出馬表完全解析版")

c1, c2 = st.columns([1, 2])
with c1:
    prev_raw = st.text_input("【1】前走確定着順", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
with c2:
    odds_raw = st.text_area("【3】オッズ表をコピペ（枠・馬番・オッズ・騎手を含む範囲）", height=200)

if odds_raw and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_logic(prev_list, total_n)
        
        # --- 堅牢なデータ抽出ロジック ---
        rows = []
        for line in odds_raw.split('\n'):
            line = line.strip()
            # 1. 小数（単勝・複勝オッズ）をすべて見つける
            floats = re.findall(r"\d+\.\d+", line)
            if len(floats) < 1: continue
            
            # 2. 単勝オッズの左側の文字列から「馬番」を特定
            # 単勝オッズの直前にある整数が馬番であるという物理的規則を利用
            prefix = line.split(floats[0])[0].strip()
            all_ints = re.findall(r"\d+", prefix)
            if not all_ints: continue
            horse_num = int(all_ints[-1]) # 最も右にある整数が馬番
            
            # 3. 騎手名（2文字以上の漢字）
            names = re.findall(r"([一-龠]{2,})", line)
            # 場所名などを除外
            kisyu = [n for n in names if n not in ["船橋","浦和","大井","川崎","門別","高知","佐賀"]][-1] if names else "不明"
            
            rows.append({
                "馬番": horse_num,
                "単勝": float(floats[0]),
                "複下": float(floats[1]) if len(floats) > 1 else 0.0,
                "騎手": kisyu
            })

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")
        df['単順'] = range(1, len(df) + 1)
        df['複順'] = df['複下'].rank(method='min')
        df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)

        if not df.empty:
            st.subheader("📊 解析告知テーブル")
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))
            # インデックスを隠して馬番を主役にする
            st.dataframe(df[['馬番', '騎手', '単勝', '判定', '異常', '根拠']], use_container_width=True, hide_index=True)

            # --- 有力馬選定 ---
            jiku = df.iloc[0]['馬番'] # ◎ 3番想定
            
            # ◯：構造(2, 11, 6, 7)かつオッズ支持(15倍以内)
            maru_candidates = [n for n in [2, total_n-1, 6, 7] if n <= total_n and n != jiku]
            selected_maru = [n for n in maru_candidates if not df[df['馬番']==n].empty and df[df['馬番']==n].iloc[0]['単勝'] <= 15.0]

            st.divider()
            st.subheader("🐴 核心告知")
            st.write(f"◎ **{jiku}番** （軸：支持の壁）")
            st.write(f"◯ **{', '.join(map(str, selected_maru)) if selected_maru else 'なし'}番** （構造＋オッズ支持）")
            st.write(f"▲ **{', '.join(map(str, [1, total_n]))}番** （連続構造：正逆1）")
            st.write(f"△ **{', '.join(map(str, [10, max(1, total_n-9)]))}番** （連続構造：正逆10）")

            # --- 推奨馬券 ---
            st.subheader("🎫 推奨馬券")
            
            # 三連複1頭軸流し
            opponents = sorted(list(set(selected_maru + [1, total_n, 10, max(1, total_n-9)])))
            opponents = [n for n in opponents if n != jiku]
            
            st.success(f"**三連複 1頭軸流し**")
            st.write(f"軸：{jiku} ―― 相手：{', '.join(map(str, opponents))}")

            # 三連単 軸1頭マルチ
            # 相手を異常🚨馬や強構造馬（2, 11, 12番等）に絞って工夫
            multi_opponents = [n for n in [2, total_n-1, total_n] if n <= total_n and n != jiku]
            
            st.info(f"**三連単 軸1頭マルチ（特選）**")
            st.write(f"軸：{jiku} ―― 相手：{', '.join(map(str, multi_opponents))}")
            st.caption(f"※構造上の端（{total_n}番）と、オッズ乖離の可能性がある正逆2番を相手に指名。")
            
    except Exception as e:
        st.error(f"解析中... 正しいフォーマットで貼り付けてください。")
