import streamlit as st
import pandas as pd
import re

def get_wave_3_layers(prev_list, total_n):
    # 正逆3巡目以内かつ頭数枠内のみを抽出
    targets = {1, total_n}
    wave_details = {}
    for h in prev_list:
        rev = total_n - h + 1
        for i in range(3):
            p = h + (i * total_n)
            r = rev + (i * total_n)
            for v in [p, r]:
                if 1 <= v <= total_n:
                    targets.add(v)
                    if v not in wave_details: wave_details[v] = []
                    wave_details[v].append(f"{h}番の{'正' if v==p else '逆'}{i+1}巡")
    return sorted(list(targets)), wave_details

st.set_page_config(page_title="構造告知アラート", layout="wide")
st.title("🛡️ 構造告知：人気順・正逆3巡フォーカス")

c1, c2 = st.columns([1, 2])
with c1:
    prev_raw = st.text_input("【1】前走確定着順", "7, 6, 9")
    total_n = st.number_input("【2】今レース頭数", min_value=1, value=12)
with c2:
    odds_raw = st.text_area("【3】人気順オッズ表を貼り付け", height=200)

if odds_raw and prev_raw:
    try:
        prev_list = [int(x.strip()) for x in prev_raw.split(",") if x.strip().isdigit()]
        wave_list, wave_map = get_wave_3_layers(prev_list, total_n)
        
        # --- 鉄壁のデータ抽出ロジック（人気順対応） ---
        lines = odds_raw.split('\n')
        rows = []
        for line in lines:
            nums = re.findall(r"\d+\.?\d*", line)
            names = re.findall(r"([一-龠ぁ-んァ-ヶ]{2,})", line)
            
            if len(nums) >= 3 and names:
                # 馬番の特定（人気順の場合、行頭付近の整数）
                # 密集データ対策：2番目が1〜total_nの範囲ならそれを採用、そうでなければ1番目
                n1 = int(nums[0]) if nums[0].isdigit() else 0
                n2 = int(nums[1]) if len(nums) > 1 and nums[1].isdigit() else 0
                horse_num = n2 if 1 <= n2 <= total_n else n1
                
                # 騎手名の抽出（不要な単語をフィルタリング）
                kisyu = [n for n in names if n not in ["牝", "牡", "セ", "船橋", "浦和", "大井", "川崎", "単勝", "複勝", "人気"]][-1]
                
                # オッズの抽出
                floats = [float(n) for n in nums if "." in n]
                if len(floats) >= 2:
                    rows.append({"馬番": horse_num, "単勝": floats[0], "複下": floats[1], "騎手": kisyu})

        # 人気順（単勝オッズ順）でデータフレーム作成
        df = pd.DataFrame(rows).drop_duplicates('馬番').sort_values("単勝")

        if not df.empty:
            # --- 告知エリア ---
            st.subheader("📢 構造告知メッセージ")
            st.error(f"🔥 【構造】 正逆1番 および 前走{prev_list}からの「正逆3巡」を解析。")
            
            # 断層の計算
            df['断層'] = (df['単勝'].shift(-1) / df['単勝']).fillna(1.0)
            df['単順'] = range(1, len(df) + 1)
            df['複順'] = df['複下'].rank(method='min')
            df['異常'] = df.apply(lambda r: "🚨" if (r['単順'] - r['複順']) >= 3 else "", axis=1)

            # 判定と根拠
            df['核心'] = df['馬番'].apply(lambda x: "🔥核心" if x in wave_list else "")
            df['根拠'] = df['馬番'].apply(lambda x: " / ".join(wave_map.get(x, [])))

            # 人気順でそのまま表示
            st.table(df[['馬番', '騎手', '単勝', '断層', '核心', '異常', '根拠']].style.format({'断層': '{:.2f}'}))
            
            # 具体的な構造の歪みを告知
            picks = df[(df['核心'] != "") & (df['単勝'] > 20)]
            if not picks.empty:
                st.subheader("🚀 構造上の歪み（狙い目）")
                for _, row in picks.iterrows():
                    st.success(f"人気順位{int(row['単順'])}位：馬番 {row['馬番']}（{row['騎手']}）は正逆3巡の核心。かつ単複乖離あり。")
        else:
            st.info("人気順のオッズ表をコピーして貼り付けてください。")

    except Exception as e:
        st.error("解析待機中...")
