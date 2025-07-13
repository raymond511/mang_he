import streamlit as st
import random
import re
from typing import List, Set

st.set_page_config(page_title="随机数字生成器", page_icon="🎲", layout="centered")

st.title("🎲 随机数字生成器")

# -----------------------------------------------------------------------------
# 🗄️  Session‑state defaults & util helpers
# -----------------------------------------------------------------------------
DEFAULTS = {
    "range_start": 1,
    "range_end": 20,
    "filter_mode": "未选择",  # none selected
    "include_raw": "",
    "exclude_raw": "",
    "history": [],
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------------------------------------------------------
# 🔍 Parsing helpers
# -----------------------------------------------------------------------------

def parse_numbers(raw: str) -> Set[int]:
    """Turn something like '1,3 5-7' into a set {1,3,5,6,7}."""
    nums: Set[int] = set()
    for tok in re.split(r"[,\s]+", raw.strip()):
        if not tok:
            continue
        if "-" in tok:
            try:
                a, b = map(int, tok.split("-", 1))
                if a > 0 and b > 0:
                    lo, hi = sorted((a, b))
                    nums.update(range(lo, hi + 1))
            except ValueError:
                pass  # ignore malformed
        else:
            if tok.isdigit():
                n = int(tok)
                if n > 0:
                    nums.add(n)
    return nums


def _apply_addition(num: int) -> None:
    """Handle the ➕ button logic: update include/exclude fields appropriately."""
    mode = st.session_state.get("filter_mode", "未选择")

    if mode == "排定":  # inclusion list active ➜ remove number if present
        include_set = parse_numbers(st.session_state.get("include_raw", ""))
        if num in include_set:
            include_set.remove(num)
            st.session_state["include_raw"] = ",".join(map(str, sorted(include_set)))
    else:  # 默认或排除模式 ➜ add to exclusion list
        exclude_set = parse_numbers(st.session_state.get("exclude_raw", ""))
        if num not in exclude_set:
            exclude_set.add(num)
            st.session_state["exclude_raw"] = ",".join(map(str, sorted(exclude_set)))


# Handle deferred additions (so we mutate *before* widgets instantiate)
if "pending_add" in st.session_state:
    _apply_addition(st.session_state.pop("pending_add"))

# -----------------------------------------------------------------------------
# 🛠️  Core builder (cached)
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def build_candidates(start: int, end: int, mode: str, filter_raw: str) -> List[int]:
    base = list(range(start, end + 1))
    if mode == "未选择":
        return base

    filt = parse_numbers(filter_raw)
    if mode == "排定":
        return [n for n in base if n in filt] if filt else []
    if mode == "排除":
        return [n for n in base if n not in filt]
    return base

# -----------------------------------------------------------------------------
# 🧹 Global clear‑all
# -----------------------------------------------------------------------------

def clear_all():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

if st.button("🗑️ 全部清除", use_container_width=True):
    clear_all()
    st.rerun()

# -----------------------------------------------------------------------------
# ① Range selection
# -----------------------------------------------------------------------------
with st.expander("① 选择随机范围 (包括端点)", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input(
            "开始",
            min_value=1,
            value=st.session_state["range_start"],
            step=1,
            key="range_start",
        )
    with c2:
        st.number_input(
            "结束",
            min_value=max(1, st.session_state["range_start"]),
            value=st.session_state["range_end"],
            step=1,
            key="range_end",
        )

# -----------------------------------------------------------------------------
# ② Filter selection
# -----------------------------------------------------------------------------
with st.expander("② 过滤规则 (二选一)", expanded=True):
    MODE_OPTS = ["未选择", "排定", "排除"]
    st.radio(
        "选择模式",
        MODE_OPTS,
        horizontal=True,
        index=MODE_OPTS.index(st.session_state["filter_mode"]),
        key="filter_mode",
    )

    filter_key = "include_raw" if st.session_state["filter_mode"] == "排定" else "exclude_raw"
    st.text_input(
        "输入数字或范围 (如 1,3 5-7)",
        value=st.session_state.get(filter_key, ""),
        key=filter_key,
        placeholder="1,3 5-7",
        disabled=(st.session_state["filter_mode"] == "未选择"),
    )

# -----------------------------------------------------------------------------
# 🎰 Generate
# -----------------------------------------------------------------------------
try:
    filter_raw_current = st.session_state.get(filter_key, "")
    candidates = build_candidates(
        st.session_state["range_start"],
        st.session_state["range_end"],
        st.session_state["filter_mode"],
        filter_raw_current,
    )

    st.markdown(f"**可选数字数量：** {len(candidates)}")

    if st.button("🎰 生成随机数字", type="primary"):
        if not candidates:
            st.warning("⚠️ 没有可用数字可供选择，请检查输入。")
        else:
            pick = random.choice(candidates)
            st.success(f"🎉 生成的数字： **{pick}**")
            st.session_state.history.append(pick)

except Exception as exc:
    st.error(f"发生错误：{exc}")
    st.exception(exc)

# -----------------------------------------------------------------------------
# 📝 History with ➕ buttons on the **LEFT** of each number
# -----------------------------------------------------------------------------
if st.session_state.history:
    st.subheader("历史记录 (点击 ➕ 将其排除)")
    for idx, num in enumerate(reversed(st.session_state.history)):
        btn_col, num_col = st.columns([1, 4])  # button first, then number
        if btn_col.button("➕", key=f"add_{idx}"):
            # Defer mutation until next run to avoid widget‑state mutation errors
            st.session_state["pending_add"] = num
            st.rerun()
        num_col.write(num)
