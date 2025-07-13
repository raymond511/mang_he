import streamlit as st
import random
import re
from typing import List, Set

st.set_page_config(page_title="随机数字生成器", page_icon="🎲", layout="centered")

st.title("🎲 随机数字生成器")

# ----- Session State -----
if "history" not in st.session_state:
    st.session_state["history"] = []

# ----- Helper Functions -----

def parse_numbers(raw: str) -> Set[int]:
    """
    Parse a string such as '1,3 5-7' into a set of positive integers.
    Accepts comma, space, and dash-separated tokens. Dash indicates a range.
    """
    nums: Set[int] = set()
    for token in re.split(r"[,\s]+", raw.strip()):
        if not token:
            continue
        if "-" in token:
            try:
                a, b = map(int, token.split("-", 1))
                if a > 0 and b > 0:
                    start, end = sorted((a, b))
                    nums.update(range(start, end + 1))
            except ValueError:
                pass
        else:
            if token.isdigit():
                n = int(token)
                if n > 0:
                    nums.add(n)
    return nums


@st.cache_data(show_spinner=False)
def build_candidates(start: int, end: int, mode: str, filter_raw: str) -> List[int]:
    """
    Return the list of candidate numbers after applying either
    the '排定' (include-only) or '排除' (exclude) filter.
    """
    base = list(range(start, end + 1))
    filters = parse_numbers(filter_raw)

    if mode == "排定":
        return [n for n in base if n in filters] if filters else []
    if mode == "排除":
        return [n for n in base if n not in filters]
    return base


# ----- UI: Range Selection -----
with st.expander("① 选择随机范围 (包括端点)", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        start_val = st.number_input(
            "开始", min_value=1, value=1, step=1, key="range_start"
        )
    with col2:
        end_val = st.number_input(
            "结束", min_value=start_val, value=max(10, start_val), step=1, key="range_end"
        )
    with col3:
        if st.button("🗑️ 清除范围"):
            st.session_state["range_start"] = 1
            st.session_state["range_end"] = 10

# ----- UI: Filter Selection -----
with st.expander("② 过滤规则 (二选一)", expanded=True):
    mode = st.radio("选择模式", ["排定", "排除"], horizontal=True, key="filter_mode")

    filter_key = "include_raw" if mode == "排定" else "exclude_raw"
    filter_raw = st.text_input(
        "输入数字或范围 (如 1,3 5-7)",
        value=st.session_state.get(filter_key, ""),
        key=filter_key,
        placeholder="1,3 5-7",
    )

    clear_label = "🗑️ 清除排定列表" if mode == "排定" else "🗑️ 清除排除列表"
    if st.button(clear_label):
        st.session_state[filter_key] = ""

# ----- Generate Button -----
candidates = build_candidates(start_val, end_val, mode, filter_raw)

st.markdown(f"**可选数字数量：** {len(candidates)}")

generate_col, clear_hist_col = st.columns([1, 1])
with generate_col:
    if st.button("🎰 生成随机数字"):
        if not candidates:
            st.error("⚠️ 没有可用数字可供选择，请检查输入。")
        else:
            pick = random.choice(candidates)
            st.success(f"🎉 生成的数字： **{pick}**")
            st.session_state.history.append(pick)

with clear_hist_col:
    if st.button("🗑️ 清除历史"):
        st.session_state.history.clear()

# ----- History -----
if st.session_state.history:
    st.subheader("历史记录")
    st.write(st.session_state.history)
