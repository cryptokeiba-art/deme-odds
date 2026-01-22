import streamlit as st
import pandas as pd
import re

def get_wave_logic(prev_list, total_n):
    # 正逆1, 正逆10を「連続構造」として固定選定
    targets = {1, total_n, 10, (total_n - 9 if total_n >= 10 else 0)}
    wave_details = {
        1: ["正1(連続構造)"], 
        total_n: ["逆1(連続構造)"], 
        10: ["正10(連続構造)"], 
        (total_n - 9 if total_n >= 10 else 0): ["逆10(連続構造)"]
    }
    # 前走エネルギーの転写
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
st.title("🛡️ 構造核心告知：出目優先解析")

c1, c2 = st.columns([1, 2])
with c1:
    prev_raw = st.text_input("【1】前走確定着順", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
with c2:
    odds_raw = st.text_area("【3】オッズ表を貼り付け", height=200, placeholder="ここにコピーした表を貼り付けてください")

if odds_raw and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_logic(prev_list, total_n)
        
        lines = [l.strip() for l in odds_raw.split('\n') if l.strip()]
        rows = []
        
        for line in lines:
            # 1. 小数（単勝オッズ等）を抽出
            floats = re.findall(r"\d+\.\d+", line)
            if not floats: continue
            
            # 2. 単勝オッズ(floats[0])より左側のテキストを解析
            prefix_text = line.split(floats[0])[0]
            ints = re.findall(r"\b\d+\b", prefix_text)
            
            if len(ints) >= 1:
                # 密集形式（人気 枠 馬番）に対応：単勝オッズの直前の整数が「馬番」
                horse_num = int(ints[-1])
                
                # 3. 騎手名（2文字以上の漢字）
                names = re.findall(r"([一-龠]{2,})", re.sub(r"\(.*?\)", "", line))
                kisyu = [n for n in names if n not in ["船橋","浦和","大井","川崎","単勝","複勝","確定"]][-1] if names else "不明"
                
                rows.append({
                    "馬番": horse_num,
                    "単勝": float(floats[0]),
                    "複下": float(floats[1]) if len(floats) > 1 else 0.0,
                    "騎手": kisyu
                })

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")

        if not df.empty:
            st.subheader("📊 解析告知")
            st.error(f"🔥 【核心構造】 現在「正逆1番・正逆10番」が連動中。穴馬はオッズ不問でここから炙り出します。")

            # テーブル作成
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))
            st.table(df[['馬番', '騎手', '単勝', '判定', '根拠']])

            # 最終結論
            st.divider()
            st.subheader("🐴 有力馬番")
            st.caption("※穴馬はオッズに関わらず、連続出現している構造的数字（正逆1, 10）から無慈悲に選定します。")

            y_jiku = df.iloc[0]['馬番']
            y_fuku = df.iloc[1]['馬番'] if len(df) > 1 else 0
            
            # 穴馬選定（連続構造）
            se_1 = [1, total_n]
            se_10 = [n for n in [10, total_n-9] if n > 0]

            st.write(f"◎ **{y_jiku}番** （人気馬：銀行評価）")
            st.write(f"◯ **{y_fuku}番** （人気馬：本日強い正逆6/7番等の裏付け）")
            st.write(f"▲ **{', '.join(map(str, se_1))}番** （連続構造の核心：正逆1）")
            st.write(f"△ **{', '.join(map(str, se_10))}番** （連続構造の核心：正逆10）")

            st.subheader("🎫 推奨馬券")
            st.success(f"ワイド：{y_jiku}-{y_fuku}（本線） / {y_jiku}-{se_1[0]}, {y_jiku}-{se_1[1]}（構造穴：正逆1流し）")
            st.info(f"三連複：{y_jiku}-{y_fuku}-{se_1[0]}, {y_jiku}-{y_fuku}-{se_1[1]}（構造核心決着）")
        else:
            st.warning("データの抽出に失敗しました。サイトの表を「枠」から「騎手」まで横に長くコピーしてください。")

    except Exception as e:
        st.error(f"解析エラー: {e}")
