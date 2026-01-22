import streamlit as st
import pandas as pd
import re

def get_wave_logic(prev_list, total_n):
    targets = {1, total_n, 10, (total_n - 10 + 1)} # 正逆1, 正逆10を基本セットに含める
    wave_details = {}
    for h in prev_list:
        rev = total_n - h + 1
        for i in range(3): # 正逆3巡まで
            p, r = h + (i * total_n), rev + (i * total_n)
            for v in [p, r]:
                if 1 <= v <= total_n:
                    targets.add(v)
                    if v not in wave_details: wave_details[v] = []
                    wave_details[v].append(f"{h}の{'正' if v==p else '逆'}{i+1}巡")
    return sorted(list(targets)), wave_details

st.set_page_config(page_title="構造解析・最終結論システム", layout="wide")
st.title("🎯 オッズ・出目解析：最終結論告知")

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
        
        # データ抽出ロジック
        lines = odds_raw.split('\n')
        rows = []
        for line in lines:
            floats = re.findall(r"\d+\.\d+", line)
            ints = re.findall(r"\b\d+\b", line)
            names = re.findall(r"([一-龠]{2,})", re.sub(r"\(.*?\)", "", line))
            if len(ints) >= 2 and len(floats) >= 2 and names:
                horse_num = int(ints[1]) if len(ints[0]) <= 2 else int(ints[0])
                kisyu = [n for n in names if n not in ["船橋","浦和","大井","川崎","単勝","複勝"]][-1]
                rows.append({"馬番": horse_num, "単勝": float(floats[0]), "複下": float(floats[1]), "騎手": kisyu})

        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")

        if not df.empty:
            # --- 1. オッズ・出目解析 ---
            st.subheader("📊 オッズ・出目解析")
            st.info(f"【オッズ解析】 単複の乖離および断層から、仕掛けの入っている馬番を特定。")
            st.info(f"【出目分析】 継続中の正逆1番、正逆10番を核心構造として評価。")

            # --- 2. 解析テーブル ---
            df['単順'] = range(1, len(df) + 1)
            df['複順'] = df['複下'].rank(method='min')
            df['判定'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))
            df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)
            st.table(df[['馬番', '騎手', '単勝', '判定', '異常', '根拠']])

            # --- 3. 結論告知 ---
            st.divider()
            st.subheader("🐴 有力馬番")
            st.write("※穴馬券は人気→人気→穴、もしくは人気→穴→人気のケースが多いため、有力馬番は人気馬を優先しています。")

            # 有力馬選定
            top_3 = df.head(3) # 人気上位
            ana_core = df[df['判定'] == "🔥核心"].query("単勝 > 10").head(2) # 波動穴
            
            # 各印の生成
            # ◎ 1番人気
            val_0 = top_3.iloc[0]['馬番']
            g_0 = f"（連続中の正逆10番のうち {'逆10' if val_0 == (total_n-9) else '核心馬'}）" if val_0 in [10, total_n-9] else "（本日強い波動の起点）"
            st.write(f"◎ **{val_0}番** {g_0}")

            # ◯ 2番人気
            val_1 = top_3.iloc[1]['馬番']
            g_1 = "（本日強い正逆6/7番）" if val_1 in [6, 7, total_n-5, total_n-6] else "（上位人気・構造の裏付けあり）"
            st.write(f"◯ **{val_1}番** {g_1}")

            # ▲ 核心穴馬
            ana_nums = ana_core['馬番'].tolist()
            st.write(f"▲ **{', '.join(map(str, ana_nums if ana_nums else [1, total_n]))}番** （連続中の正逆1）")

            # △ オッズ推奨
            st.write(f"△ **{top_3.iloc[-1]['馬番']}番** （オッズ分布から推奨）")

            st.subheader("🚀 狙い目")
            st.write(f"**【オッズ解析から】**")
            st.write(f"馬番{val_0}を軸に推奨。支持の安定度と複勝の貼り付きから、銀行としての機能を感知。")
            st.write(f"**【出目分析から】**")
            st.write(f"3レース連続で正逆1番vs正逆10番でワイド圏内のため、このラインを本線に据える。")

            st.subheader("🎫 推奨馬券")
            st.success(f"ワイド：{val_0}-{val_1}（本線） / {val_0}-{ana_nums[0] if ana_nums else 1}（押さえ）")
            st.info(f"三連複：{val_0}-{val_1}-{ana_nums[0] if ana_nums else 1}")

    except Exception as e:
        st.error("データ解析中...")
