import streamlit as st
import time
import random
import pandas as pd
import os

# --- 設定とデータ準備 ---
RANKING_FILE = "kuku_ranking.csv"

def load_ranking():
    if os.path.exists(RANKING_FILE):
        return pd.read_csv(RANKING_FILE)
    else:
        return pd.DataFrame(columns=["名前", "レベル", "タイム(秒)"])

def save_ranking(name, level, score):
    df = load_ranking()
    new_data = pd.DataFrame([[name, level, round(score, 2)]], columns=["名前", "レベル", "タイム(秒)"])
    df = pd.concat([df, new_data], ignore_index=True)
    
    # 【修正】重複データを削除し、全体をタイム順に並べ替えて保存
    df = df.drop_duplicates()
    df = df.sort_values(by="タイム(秒)")
    df.to_csv(RANKING_FILE, index=False)

# --- セッション状態の初期化 ---
if 'game_status' not in st.session_state:
    st.session_state.game_status = "config"
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'ranking_saved' not in st.session_state:
    st.session_state.ranking_saved = False # 保存済みチェック用

st.set_page_config(page_title="九九タイムアタック", layout="centered")
st.title("⚡ 九九 10問正解タイムアタック ⚡")

# --- ①＆② サイドバーにランキングを表示 ---
st.sidebar.header("🏆 記録をみてみよう！")
ranking_data = load_ranking()

# ユーザーがレベルを切り替えて見られるようにする
target_level = st.sidebar.selectbox(
    "レベルをえらんでね", 
    ["Level 1 (だんごと特訓)", "Level 2 (ランダム)", "Level 3 (むしくい)"],
    key="sidebar_level"
)

if not ranking_data.empty:
    # 選択されたレベルでフィルタリングして、TOP10を表示
    filtered_ranking = ranking_data[ranking_data["レベル"] == target_level].sort_values(by="タイム(秒)").head(10)
    
    if not filtered_ranking.empty:
        # インデックスを1から始まる順位として表示
        filtered_ranking.index = range(1, len(filtered_ranking) + 1)
        st.sidebar.table(filtered_ranking)
    else:
        st.sidebar.info(f"{target_level} の記録はまだないよ！")
else:
    st.sidebar.write("ランキングはまだありません。")

# --- 設定画面 ---
if st.session_state.game_status == "config":
    # ③ デフォルトを空にする
    user_name = st.text_input("なまえを入力してね", value="", placeholder="ここに名前をかいてね")
    level = st.radio("レベルをえらんでね", ["Level 1 (だんごと特訓)", "Level 2 (ランダム)", "Level 3 (むしくい)"])
    
    dan = 1
    if level == "Level 1 (だんごと特訓)":
        dan = st.number_input("何のだん？", 1, 9, 2)

    if st.button("スタート！"):
        # ③ 名前が空の場合のチェック
        if user_name.strip() == "":
            st.warning("⚠️ 「名前をかいてね」")
        else:
            st.session_state.current_idx = 0
            st.session_state.game_status = "playing"
            st.session_state.start_time = time.time()
            st.session_state.user_name = user_name
            st.session_state.level_name = level
            st.session_state.dan_choice = dan
            st.session_state.current_question = None
            st.session_state.ranking_saved = False # 新しいゲーム開始時にリセット
            st.rerun()

# --- プレイ画面 ---
elif st.session_state.game_status == "playing":
    st.progress(st.session_state.current_idx * 10)
    st.write(f"### 現在の正解数: {st.session_state.current_idx} / 10 問")

    if st.session_state.current_question is None:
        if st.session_state.level_name == "Level 1 (だんごと特訓)":
            st.session_state.current_question = (st.session_state.dan_choice, random.randint(1, 9))
        else:
            st.session_state.current_question = (random.randint(1, 9), random.randint(1, 9))
    
    a, b = st.session_state.current_question
    
    # むしくい問題のロジック
    if st.session_state.level_name == "Level 3 (むしくい)":
        if 'mushikui_type' not in st.session_state or getattr(st.session_state, 'current_question_changed', True):
             st.session_state.mushikui_type = random.choice(["a", "b", "c"])
             st.session_state.current_question_changed = False
        
        m_type = st.session_state.mushikui_type
        if m_type == "a":
            ans_label, correct_ans = f"□ × {b} = {a*b}", a
        elif m_type == "b":
            ans_label, correct_ans = f"{a} × □ = {a*b}", b
        else:
            ans_label, correct_ans = f"{a} × {b} = □", a*b
    else:
        ans_label, correct_ans = f"{a} × {b} = ", a*b

    with st.form(key=f"q_form_{st.session_state.current_idx}", clear_on_submit=True):
        user_ans = st.number_input(ans_label, value=None, step=1, placeholder="答えを入力してね")
        submit = st.form_submit_button("決定！")
        
        if submit:
            if user_ans == correct_ans:
                st.success(random.choice(["せいかい！", "すごい！", "天才！", "そのちょうし！"]))
                st.session_state.current_idx += 1
                st.session_state.current_question = None 
                st.session_state.current_question_changed = True
                time.sleep(0.5)
                
                if st.session_state.current_idx >= 10:
                    st.session_state.game_status = "finished"
                    st.session_state.end_time = time.time()
                st.rerun()
            else:
                st.error(f"ざんねん！ 正解は {correct_ans} でした。もう一度挑戦！")

# --- 結果・ランキング画面 ---
elif st.session_state.game_status == "finished":
    total_time = st.session_state.end_time - st.session_state.start_time
    st.balloons()
    st.success(f"10問正解達成！おめでとう！ タイム: {total_time:.2f} 秒")
    
    # 保存済みでなければ保存
    if not st.session_state.ranking_saved:
        save_ranking(st.session_state.user_name, st.session_state.level_name, total_time)
        st.session_state.ranking_saved = True
    
    st.subheader(f"🏆 {st.session_state.level_name} のランキング")
    current_ranking = load_ranking()
    display_df = current_ranking[current_ranking["レベル"] == st.session_state.level_name].sort_values(by="タイム(秒)").head(10)
    display_df.index = range(1, len(display_df) + 1)
    st.table(display_df)
    
    if st.button("もういちど あそぶ"):
        st.session_state.game_status = "config"
        st.session_state.current_idx = 0
        st.session_state.ranking_saved = False
        st.rerun()
