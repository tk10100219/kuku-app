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
    df = df.sort_values(by="タイム(秒)").head(10) # 上位10位まで保存
    df.to_csv(RANKING_FILE, index=False)

# --- セッション状態の初期化 ---
if 'game_status' not in st.session_state:
    st.session_state.game_status = "config" # config, playing, finished
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0

st.title("⚡ 九九タイムアタック ⚡")

# --- 設定画面 ---
if st.session_state.game_status == "config":
    user_name = st.text_input("なまえを入力してね", "ともえ")
    level = st.radio("レベルをえらんでね", ["Level 1 (だんごと特訓)", "Level 2 (ランダム)", "Level 3 (むしくい)"])
    
    dan = 1
    if level == "Level 1 (だんごと特訓)":
        dan = st.number_input("何のだん？", 1, 9, 2)

    if st.button("スタート！"):
        # 問題作成
        qs = []
        if level == "Level 1 (だんごと特訓)":
            base = [(dan, i) for i in range(1, 10)]
            qs = random.sample(base * 2, 10) # 10問にする
        else:
            for _ in range(10):
                qs.append((random.randint(1, 9), random.randint(1, 9)))
        
        st.session_state.questions = qs
        st.session_state.current_idx = 0
        st.session_state.game_status = "playing"
        st.session_state.start_time = time.time()
        st.session_state.user_name = user_name
        st.session_state.level_name = level
        st.rerun()

# --- プレイ画面 ---
elif st.session_state.game_status == "playing":
    q_idx = st.session_state.current_idx
    a, b = st.session_state.questions[q_idx]
    
    st.subheader(f"だい {q_idx + 1} もん / 10")
    
    # レベルごとの表示切り替え
    if st.session_state.level_name == "Level 3 (むしくい)":
        target = random.choice(["a", "b", "c"])
        if target == "a":
            ans_label = f"□ × {b} = {a*b}"
            correct_ans = a
        elif target == "b":
            ans_label = f"{a} × □ = {a*b}"
            correct_ans = b
        else:
            ans_label = f"{a} × {b} = □"
            correct_ans = a*b
    else:
        ans_label = f"{a} × {b} = "
        correct_ans = a*b

    with st.form(key=f"q_{q_idx}"):
        user_ans = st.number_input(ans_label, value=0, step=1)
        submit = st.form_submit_button("決定！")
        
        if submit:
            if user_ans == correct_ans:
                st.session_state.current_idx += 1
                if st.session_state.current_idx >= 10:
                    st.session_state.game_status = "finished"
                    st.session_state.end_time = time.time()
                st.rerun()
            else:
                st.error("おしい！もういちど！")

# --- 結果・ランキング画面 ---
elif st.session_state.game_status == "finished":
    total_time = st.session_state.end_time - st.session_state.start_time
    st.balloons()
    st.success(f"クリア！ タイム: {total_time:.2f} びょう")
    
    save_ranking(st.session_state.user_name, st.session_state.level_name, total_time)
    
    st.subheader("🏆 ランキング (TOP 10)")
    st.table(load_ranking())
    
    if st.button("もういちど あそぶ"):
        st.session_state.game_status = "config"
        st.rerun()
