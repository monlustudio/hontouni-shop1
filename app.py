import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# 設定頁面寬度與標題
st.set_page_config(
    page_title="紅斗泥大福訂單管理系統", page_icon="🍡", layout="wide"
)

# --- 資料庫初始化與設定 ---
DB_FILE = "hongduni_orders.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  # 訂單表
  c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            items TEXT,
            payment TEXT,
            pickup_date TEXT,
            pickup_time_slot TEXT,
            phone TEXT,
            note TEXT,
            shipped INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
  # 口味設定表
  c.execute("""
        CREATE TABLE IF NOT EXISTS flavors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flavor_name TEXT UNIQUE
        )
    """)
  # 預設口味資料
  c.execute("SELECT COUNT(*) FROM flavors")
  if c.fetchone()[0] == 0:
    default_flavors = [
        "法式奶酥",
        "草莓大福",
        "水蜜桃大福",
        "綠葡萄大福",
        "橘子大福",
        "包種茶大福",
        "泰式奶茶大福",
        "柿子包種茶大福",
    ]
    for f in default_flavors:
      c.execute(
          "INSERT OR IGNORE INTO flavors (flavor_name) VALUES (?)", (f,)
      )
  conn.commit()
  conn.close()


init_db()


def get_flavors():
  conn = sqlite3.connect(DB_FILE)
  df = pd.read_sql("SELECT flavor_name FROM flavors ORDER BY id", conn)
  conn.close()
  return df["flavor_name"].tolist()


def add_flavor_to_db(flavor_name):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  try:
    c.execute("INSERT INTO flavors (flavor_name) VALUES (?)", (flavor_name,))
    conn.commit()
    success = True
  except:
    success = False
  conn.close()
  return success


def delete_flavor_from_db(flavor_name):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute("DELETE FROM flavors WHERE flavor_name = ?", (flavor_name,))
  conn.commit()
  conn.close()


def get_orders_by_date(date_str):
  conn = sqlite3.connect(DB_FILE)
  df = pd.read_sql(
      "SELECT * FROM orders WHERE pickup_date = ? ORDER BY id DESC",
      conn,
      params=(date_str,),
  )
  conn.close()
  return df


def add_order(
    name, items_str, payment, pickup_date, time_slot, phone, note
):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute(
      """
        INSERT INTO orders (name, items, payment, pickup_date, pickup_time_slot, phone, note, shipped, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
    """,
      (
          name,
          items_str,
          payment,
          str(pickup_date),
          time_slot,
          phone,
          note,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      ),
  )
  conn.commit()
  conn.close()


def update_order_shipped(order_id, shipped_val):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute(
      "UPDATE orders SET shipped = ? WHERE id = ?", (1 if shipped_val else 0, order_id)
  )
  conn.commit()
  conn.close()


def delete_order(order_id):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
  conn.commit()
  conn.close()


def update_order_full(
    order_id, name, items_str, payment, pickup_date, time_slot, phone, note
):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute(
      """
        UPDATE orders 
        SET name=?, items=?, payment=?, pickup_date=?, pickup_time_slot=?, phone=?, note=?
        WHERE id=?
    """,
      (
          name,
          items_str,
          payment,
          str(pickup_date),
          time_slot,
          phone,
          note,
          order_id,
      ),
  )
  conn.commit()
  conn.close()


# --- 初始化 Session State 日期 ---
if "selected_date" not in st.session_state:
  st.session_state["selected_date"] = datetime.now().date()

# --- 側邊欄：口味設定與資料匯出 ---
with st.sidebar:
  st.header("⚙️ 系統與後台設定")
  st.subheader("🍡 管理下拉選單口味")
  flavors_list = get_flavors()

  new_flavor = st.text_input("新增口味名稱")
  if st.button("➕ 新增口味選項"):
    if new_flavor.strip():
      if add_flavor_to_db(new_flavor.strip()):
        st.success(f"已新增：{new_flavor}")
        st.rerun()
      else:
        st.warning("該口味已存在")

  st.write("目前現有口味：")
  for f in flavors_list:
    c1, c2 = st.columns([4, 1])
    c1.text(f)
    if c2.button("🗑️", key=f"del_flav_{f}"):
      delete_flavor_from_db(f)
      st.rerun()

  st.divider()
  st.subheader("📊 資料備份")
  if st.button("📥 下載完整訂單資料 (CSV)"):
    conn = sqlite3.connect(DB_FILE)
    df_all = pd.read_sql("SELECT * FROM orders", conn)
    conn.close()
    st.download_button(
        "點此下載 CSV 檔案",
        df_all.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"hongduni_orders_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

# --- 主畫面標題 ---
st.title("🍡 紅斗泥大福 — 取貨與訂單管理系統")

# ==========================================
# 1. 最上方：【日曆播報器與日期切換器】
# ==========================================
cur_date = st.session_state["selected_date"]
orders_df = get_orders_by_date(str(cur_date))

col_prev, col_date_picker, col_next, col_today, col_summary = st.columns(
    [1, 2, 1, 1, 4]
)

with col_prev:
  if st.button("◀ 前一天", use_container_width=True):
    st.session_state["selected_date"] = cur_date - timedelta(days=1)
    st.rerun()

with col_date_picker:
  selected_date_input = st.date_input(
      "選擇檢視日期", value=cur_date, label_visibility="collapsed"
  )
  if selected_date_input != cur_date:
    st.session_state["selected_date"] = selected_date_input
    st.rerun()

with col_next:
  if st.button("後一天 ▶", use_container_width=True):
    st.session_state["selected_date"] = cur_date + timedelta(days=1)
    st.rerun()

with col_today:
  if st.button("🏠 回到今天", use_container_width=True):
    st.session_state["selected_date"] = datetime.now().date()
    st.rerun()

# 統計今日各口味數量
flavor_summary_dict = {}
total_orders_count = len(orders_df)
for _, row in orders_df.iterrows():
  items_text = row["items"]
  parts = items_text.split(",")
  for p in parts:
    p = p.strip()
    if "x" in p:
      sub_parts = p.split("x")
      f_name = sub_parts[0].strip()
      try:
        f_qty = int(sub_parts[1].strip())
      except:
        f_qty = 1
      flavor_summary_dict[f_name] = (
          flavor_summary_dict.get(f_name, 0) + f_qty
      )

summary_str_list = [f"{k} × {v}" for k, v in flavor_summary_dict.items()]
summary_text_joined = (
    "、".join(summary_str_list) if summary_str_list else "無訂單"
)

with col_summary:
  st.info(
      f"📅 **【{cur_date} 播報摘要】** 共 **{total_orders_count}** 筆訂單"
      f" ｜ 總計需備貨：**{summary_text_joined}**"
  )

st.divider()

# ==========================================
# 2. 版面切換：左側新增訂單 / 右側訂單管理
# ==========================================
left_col, right_col = st.columns([1.2, 1.8], gap="large")

with left_col:
  st.subheader("➕ 快速新增訂單")

  name = st.text_input("客戶姓名 / 稱呼 *", placeholder="例：陳小美")
  phone = st.text_input("聯絡電話 (選填)", placeholder="例：0912-345-678")

  st.markdown("##### 🛒 訂購內容（可新增多種口味）")

  flavor_options = get_flavors()
  num_rows = st.number_input(
      "品項種類數量",
      min_value=1,
      max_value=10,
      value=1,
      help="如果客人口味買 1 種就填 1，買 2 種就填 2",
  )

  selected_items_list = []
  for i in range(num_rows):
    c_f, c_q = st.columns([2, 1])
    f_sel = c_f.selectbox(f"口味 #{i+1}", flavor_options, key=f"f_{i}")
    q_sel = c_q.number_input(
        f"數量 #{i+1}", min_value=1, max_value=50, value=1, key=f"q_{i}"
    )
    selected_items_list.append(f"{f_sel} x {q_sel}")

  items_combined_str = ", ".join(selected_items_list)

  col_pay, col_date = st.columns(2)
  with col_pay:
    payment = st.radio("付款方式", ["已匯款", "現場付"], horizontal=True)

  with col_date:
    pickup_date = st.date_input("預定取貨日期", value=cur_date)

  time_slot = st.radio("取貨時段", ["中午", "下午", "無指定"], horizontal=True)
  note = st.text_area("備註 (選填)", placeholder="例：要保冷袋、不要附餐具")

  if st.button("✅ 送出並建立訂單", use_container_width=True):
    if not name.strip():
      st.error("請輸入客戶姓名！")
    else:
      add_order(
          name,
          items_combined_str,
          payment,
          pickup_date,
          time_slot,
          phone,
          note,
      )
      st.success(f"已成功新增 {name} 的訂單！")
      st.rerun()

with right_col:
  st.subheader(f"📋 【{cur_date}】取貨與出貨一覽表")

  if orders_df.empty:
    st.warning("這天目前沒有訂單紀錄。")
  else:
    for idx, row in orders_df.iterrows():
      order_id = row["id"]
      is_shipped = bool(row["shipped"])

      with st.expander(
          f"{'✅ [已出貨]' if is_shipped else '⏳ [未出貨]'} {row['pickup_time_slot']}｜"
          f" {row['name']} ｜ {row['items']}  ({row['payment']})",
          expanded=not is_shipped,
      ):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
          st.write(f"**客戶姓名：** {row['name']}")
          st.write(f"**聯絡電話：** {row['phone'] if row['phone'] else '未填'}")
          st.write(f"**付款狀態：** {row['payment']}")
        with c2:
          st.write(f"**訂購品項：** {row['items']}")
          st.write(f"**取貨時段：** {row['pickup_time_slot']}")
          st.write(f"**備註：** {row['note'] if row['note'] else '無'}")
        with c3:
          shipped_toggle = st.checkbox(
              "已出貨", value=is_shipped, key=f"ship_{order_id}"
          )
          if shipped_toggle != is_shipped:
            update_order_shipped(order_id, shipped_toggle)
            st.rerun()

          if st.button("🗑️ 刪除訂單", key=f"del_{order_id}"):
            delete_order(order_id)
            st.rerun()

        with st.popover("✏️ 編輯此訂單"):
          with st.form(key=f"edit_form_{order_id}"):
            e_name = st.text_input("客戶姓名", value=row["name"])
            e_phone = st.text_input(
                "聯絡電話", value=row["phone"] if row["phone"] else ""
            )
            e_items = st.text_input(
                "訂購品項 (例: 法式奶酥 x 2)", value=row["items"]
            )
            e_payment = st.radio(
                "付款方式",
                ["已匯款", "現場付"],
                index=0 if row["payment"] == "已匯款" else 1,
                horizontal=True,
            )
            e_date = st.date_input(
                "預定取貨日期",
                value=datetime.strptime(row["pickup_date"], "%Y-%m-%d").date(),
            )
            e_slot = st.radio(
                "取貨時段",
                ["中午", "下午", "無指定"],
                index=["中午", "下午", "無指定"].index(row["pickup_time_slot"])
                if row["pickup_time_slot"] in ["中午", "下午", "無指定"]
                else 2,
                horizontal=True,
            )
            e_note = st.text_area(
                "備註", value=row["note"] if row["note"] else ""
            )

            if st.form_submit_button("💾 儲存修改"):
              update_order_full(
                  order_id,
                  e_name,
                  e_items,
                  e_payment,
                  e_date,
                  e_slot,
                  e_phone,
                  e_note,
              )
              st.success("已更新訂單！")
              st.rerun()
