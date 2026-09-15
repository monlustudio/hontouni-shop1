import datetime
import json
import os
import streamlit as st

# 設定網頁標題與寬螢幕版面
st.set_page_config(
    page_title="紅斗泥大福訂單管理系統", page_type="wide", layout="wide"
)

# 預設的口味清單（您可以隨時在這裡新增或修改）
DEFAULT_FLAVORS = [
    "柿子包種茶大福",
    "法式奶酥大福",
    "草莓大福",
    "水蜜桃大福",
    "綠葡萄大福",
    "橘子大福",
    "泰式奶茶大福",
]

DATA_FILE = "orders.json"


# 載入與儲存資料的輔助函數
def load_orders():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      return []
  return []


def save_orders(orders):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(orders, f, ensure_ascii=False, indent=2)


# 初始化 Session State
if "orders" not in st.session_state:
  st.session_state["orders"] = load_orders()

if "selected_date" not in st.session_state:
  st.session_state["selected_date"] = datetime.date.today()

# 確保 URL 參數或狀態有被正確追蹤
orders = st.session_state["orders"]

# --- 1. 最上方：【日曆播報器與日期切換器】 ---
st.title("🍡 紅斗泥大福訂單與取貨管理系統")

col_prev, col_date, col_next, col_today, col_voice = st.columns(
    [1, 2.5, 1, 1, 1.5]
)

with col_prev:
  if st.button("◀ 前一天", use_container_width=True):
    st.session_state["selected_date"] -= datetime.timedelta(days=1)
    st.rerun()

with col_date:
  selected_date = st.date_input(
      "選擇查看日期",
      value=st.session_state["selected_date"],
      label_visibility="collapsed",
  )
  st.session_state["selected_date"] = selected_date

with col_next:
  if st.button("後一天 ▶", use_container_width=True):
    st.session_state["selected_date"] += datetime.timedelta(days=1)
    st.rerun()

with col_today:
  if st.button("📅 回到今天", use_container_width=True):
    st.session_state["selected_date"] = datetime.date.today()
    st.rerun()

# 篩選出當天訂單
date_str = st.session_state["selected_date"].strftime("%Y-%m-%d")
day_orders = [o for o in orders if o.get("pickup_date") == date_str]

# 計算今日各口味總量統計
flavor_summary = {}
for o in day_orders:
  for item in o.get("items", []):
    f_name = item.get("flavor")
    f_qty = item.get("qty", 0)
    flavor_summary[f_name] = flavor_summary.get(f_name, 0) + f_qty

summary_text = (
    "、".join([f"{k} × {v}個" for k, v in flavor_summary.items()])
    if flavor_summary
    .items() else "今日尚無訂單"
)

with col_voice:
  # 生成網頁端文字轉語音按鈕
  summary_sentence = (
      f"今天是 {date_str}，共有 {len(day_orders)} 筆訂單。總計需備貨："
      f" {summary_text}"
  )
  voice_html = f"""
    <button onclick="
        const utterance = new SpeechSynthesisUtterance('{summary_sentence}');
        utterance.lang = 'zh-TW';
        window.speechSynthesis.speak(utterance);
    " style="width:100%; height:42px; background-color:#ff4b4b; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">
        🔊 語音播報今日訂單
    </button>
    """
  st.markdown(voice_html, unsafe_allow_html=True)

# 顯示今日摘要卡片
st.info(
    f"📅 **【{date_str} 訂單摘要】** ｜ 共 **{len(day_orders)}** 筆訂單 ｜ 總計需備貨：**{summary_text}**"
)

st.divider()

# --- 主畫面雙欄設計：左側輸入 / 右側清單 ---
left_col, right_col = st.columns([1.2, 1.8], gap="large")

# --- 2. 左側：快速新增訂單區 ---
with left_col:
  st.subheader("➕ 快速新增訂單")

  with st.form("new_order_form", clear_submit=True):
    c_name = st.text_input("客戶姓名", placeholder="例：陳小美")
    c_phone = st.text_input("聯絡電話（選填）", placeholder="例：0912-345-678")

    st.markdown("##### 🛒 訂購內容")

    # 使用 session 管理動態多口味列
    if "form_items" not in st.session_state:
      st.session_state["form_items"] = [{"flavor": DEFAULT_FLAVORS[0], "qty": 1}]

    # 簡單用固定的 3 組欄位讓使用者快速點選口味與數量
    order_items_input = []
    col_f1, col_f2 = st.columns([2, 1])

    item_1_flavor = col_f1.selectbox(
        "口味 1", DEFAULT_FLAVORS, key="f1", label_visibility="collapsed"
    )
    item_1_qty = col_f2.number_input(
        "數量 1", min_value=1, max_value=100, value=1, key="q1"
    )

    item_2_flavor = col_f1.selectbox(
        "口味 2（選填）",
        ["無"] + DEFAULT_FLAVORS,
        key="f2",
        label_visibility="collapsed",
    )
    item_2_qty = col_f2.number_input(
        "數量 2", min_value=0, max_value=100, value=0, key="q2"
    )

    item_3_flavor = col_f1.selectbox(
        "口味 3（選填）",
        ["無"] + DEFAULT_FLAVORS,
        key="f3",
        label_visibility="collapsed",
    )
    item_3_qty = col_f2.number_input(
        "數量 3", min_value=0, max_value=100, value=0, key="q3"
    )

    st.markdown("---")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
      payment_status = st.selectbox(
          "付款狀態", ["已匯款", "現場付"], index=0
      )
    with col_p2:
      time_slot = st.selectbox("取貨時段", ["中午", "下午", "無指定"], index=1)

    pickup_date_input = st.date_input(
        "預定取貨日期", value=st.session_state["selected_date"]
    )
    memo = st.text_input("備註", placeholder="例：裝保冷袋、不附餐具")

    submitted = st.form_submit_button("✅ 送出訂單", use_container_width=True)

    if submitted:
      if not c_name.strip():
        st.error("請輸入客戶姓名！")
      else:
        # 整理訂購品項
        collected_items = []
        collected_items.append({"flavor": item_1_flavor, "qty": item_1_qty})
        if item_2_flavor != "无" and item_2_flavor != "無" and item_2_qty > 0:
          collected_items.append({"flavor": item_2_flavor, "qty": item_2_qty})
        if item_3_flavor != "无" and item_3_flavor != "無" and item_3_qty > 0:
          collected_items.append({"flavor": item_3_flavor, "qty": item_3_qty})

        new_order = {
            "id": datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "name": c_name,
            "phone": c_phone,
            "pickup_date": pickup_date_input.strftime("%Y-%m-%d"),
            "time_slot": time_slot,
            "payment": payment_status,
            "items": collected_items,
            "memo": memo,
            "shipped": False,
        }

        orders.append(new_order)
        st.session_state["orders"] = orders
        save_orders(orders)
        st.success(f"已成功為【{c_name}】建立訂單！")
        st.rerun()

# --- 3. 右側：該日訂單清單與管理區 ---
with right_col:
  st.subheader(f"📋 {date_str} 訂單清單（共 {len(day_orders)} 筆）")

  if not day_orders:
    st.info("這一天目前還沒有訂單，請從左側新增。")
  else:
    for idx, ord_item in enumerate(day_orders):
      with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.2, 2.5, 1.2, 1.3])

        with c1:
          # 已出貨勾選框
          shipped_status = st.checkbox(
              "已出貨",
              value=ord_item.get("shipped", False),
              key=f"shipped_{ord_item['id']}",
          )
          if shipped_status != ord_item.get("shipped", False):
            ord_item["shipped"] = shipped_status
            save_orders(orders)
            st.rerun()

          st.markdown(
              f"**{ord_item['name']}**"
              if not shipped_status
              else f"~~**{ord_item['name']}**~~ (已出貨)"
          )
          if ord_item.get("phone"):
            st.caption(f"📞 {ord_item['phone']}")

        with c2:
          items_str = ", ".join(
              [
                  f"{it['flavor']} × {it['qty']}"
                  for it in ord_item.get("items", [])
              ]
          )
          st.markdown(f"**訂購內容**：{items_str}")
          if ord_item.get("memo"):
            st.caption(f"📝 備註：{ord_item['memo']}")

        with c3:
          pay_badge = (
              "🟢 已匯款"
              if ord_item["payment"] == "已匯款"
              else "🟡 現場付"
          )
          st.markdown(f"**付款**：{pay_badge}")
          st.markdown(f"**時段**：⏰ {ord_item['time_slot']}")

        with c4:
          # 編輯與刪除按鈕
          with st.popover("✏️ 編輯訂單", use_container_width=True):
            with st.form(f"edit_form_{ord_item['id']}"):
              edit_name = st.text_input("客戶姓名", value=ord_item["name"])
              edit_phone = st.text_input("電話", value=ord_item.get("phone", ""))
              edit_payment = st.selectbox(
                  "付款方式",
                  ["已匯款", "現場付"],
                  index=0 if ord_item["payment"] == "已匯款" else 1,
              )
              edit_slot = st.selectbox(
                  "取貨時段",
                  ["中午", "下午", "無指定"],
                  index=["中午", "下午", "無指定"].index(
                      ord_item.get("time_slot", "下午")
                  ),
              )
              edit_memo = st.text_input("備註", value=ord_item.get("memo", ""))

              save_edit = st.form_submit_button("💾 儲存修改")
              if save_edit:
                ord_item["name"] = edit_name
                ord_item["phone"] = edit_phone
                ord_item["payment"] = edit_payment
                ord_item["time_slot"] = edit_slot
                ord_item["memo"] = edit_memo
                save_orders(orders)
                st.success("已更新訂單！")
                st.rerun()

          if st.button(
              "🗑️ 刪除", key=f"del_{ord_item['id']}", use_container_width=True
          ):
            orders = [o for o in orders if o["id"] != ord_item["id"]]
            st.session_state["orders"] = orders
            save_orders(orders)
            st.rerun()
