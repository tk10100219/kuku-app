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
    df = df.sort_values(by="タイム(秒)").head(10)
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

st.title("⚡ 九九 10問正解タイムアタック ⚡")

# --- 設定画面 ---
if st.session_state.game_status == "config":
    user_name = st.text_input("なまえを入力してね", "ともえ")
    level = st.radio("レベルをえらんでね", ["Level 1 (だんごと特訓)", "Level 2 (ランダム)", "Level 3 (むしくい)"])
    
    dan = 1
    if level == "Level 1 (だんごと特訓)":
        dan = st.number_input("何のだん？", 1, 9, 2)

    if st.button("スタート！"):
        st.session_state.current_idx = 0
        st.session_state.game_status = "playing"
        st.session_state.start_time = time.time()
        st.session_state.user_name = user_name
        st.session_state.level_name = level
        st.session_state.dan_choice = dan
        st.session_state.current_question = None # 最初の問題生成用
        st.rerun()

# --- プレイ画面 ---
elif st.session_state.game_status == "playing":
    # プログレスバーの表示
    st.progress(st.session_state.current_idx * 10)
    st.write(f"### 現在の正解数: {st.session_state.current_idx} / 10 問")

    # 新しい問題を作る（まだ作っていない、または正解して次に行く場合）
    if st.session_state.current_question is None:
        if st.session_state.level_name == "Level 1 (だんごと特訓)":
            st.session_state.current_question = (st.session_state.dan_choice, random.randint(1, 9))
        else:
            st.session_state.current_question = (random.randint(1, 9), random.randint(1, 9))
    
    a, b = st.session_state.current_question
    
    # 問題文の作成
    if st.session_state.level_name == "Level 3 (むしくい)":
        # 虫食いロジック（固定されないよう工夫）
        if 'mushikui_type' not in st.session_state or st.session_state.current_question_changed:
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

    # 入力フォーム
    with st.form(key=f"q_form_{st.session_state.current_idx}", clear_on_submit=True):
        user_ans = st.number_input(ans_label, value=None, step=1, placeholder="答えを入力してね")
        submit = st.form_submit_button("決定！")
        
        if submit:
            if user_ans == correct_ans:
                st.success(random.choice(["せいかい！", "すごい！", "天才！", "そのちょうし！"]))
                st.session_state.current_idx += 1
                st.session_state.current_question = None # 問題をリセットして次へ
                st.session_state.current_question_changed = True
                time.sleep(0.5)
                
                if st.session_state.current_idx >= 10:
                    st.session_state.game_status = "finished"
                    st.session_state.end_time = time.time()
                st.rerun()
            else:
                st.error(f"ざんねん！ 正解は {correct_ans} でした。もう一度同じ問題に挑戦！")
                # 正解するまで current_question は None にしない（同じ問題が続く）

# --- 結果・ランキング画面 ---
elif st.session_state.game_status == "finished":
    total_time = st.session_state.end_time - st.session_state.start_time
    st.balloons()
    st.success(f"10問正解達成！おめでとう！ タイム: {total_time:.2f} 秒")
    
    save_ranking(st.session_state.user_name, st.session_state.level_name, total_time)
    
    st.subheader("🏆 ランキング (TOP 10)")
    st.table(load_ranking())
    
    if st.button("もういちど あそぶ"):
        st.session_state.game_status = "config"
        st.session_state.current_idx = 0
        st.rerun()
