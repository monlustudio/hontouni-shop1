import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit_sortables import sort_items  # 引入拖曳排序套件

# 設定頁面寬度與標題
st.set_page_config(
    page_title="紅斗泥大福訂單管理系統", page_icon="🍡", layout="wide"
)

# --- 自訂 CSS 主題樣式 ---
st.markdown("""
<style>
    /* 全體背景與主色調 */
    .stApp {
        background-color: #cd9e97;
        color: #ffffff;
    }
    
    /* 主畫面標題與文字顏色保持白色 */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #ffffff !important;
    }

    /* 側邊欄 (Sidebar) 背景與文字 */
    section[data-testid="stSidebar"] {
        background-color: #7d544f !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span {
        color: #ffffff !important;
    }

    /* 按鈕樣式: 背景 #946660, 字體白色 */
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #946660 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100%;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #5e3f3b !important;
        color: #ffffff !important;
    }

    /* 下拉選單 (Selectbox) 白底黑字 */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="select"] input, div[data-baseweb="select"] div {
        color: #000000 !important;
    }

    /* 容器與卡片微調 */
    div.stExpander, div.stContainer {
        background-color: rgba(255, 255, 255, 0.12);
        border-radius: 10px;
        padding: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 資料庫初始化 ---
DB_FILE = "hongduni_orders.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
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
  c.execute("""
        CREATE TABLE IF NOT EXISTS flavors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flavor_name TEXT UNIQUE,
            sort_order INTEGER DEFAULT 0
        )
    """)
  try:
    c.execute("ALTER TABLE flavors ADD COLUMN sort_order INTEGER DEFAULT 0")
  except:
    pass

  c.execute("SELECT COUNT(*) FROM flavors")
  if c.fetchone()[0] == 0:
    default_flavors = [
        "綠桔雙拼水果大福",
        "法式奶酥桔大福",
        "奶油綠豆桔大福",
        "紅豆桔大福",
        "綠葡萄法式奶酥大福",
        "綠葡萄奶油綠豆大福",
        "法式奶酥柿大福",
        "台灣包種柿大福",
        "靜岡抹茶柿大福",
        "奶油綠豆柿大福",
        "紅豆柿大福",
        "水果雙拼茶韻大福",
        "乳酪綜合大福",
        "芋頭奶凍大福",
        "法式奶酥紅豆大福",
        "法式奶酥抹茶大福",
        "台灣包種茶大福",
        "法式奶酥包種茶大福",
        "豆綜合大福",
        "豆大福紅豆",
        "奶油綠豆大福",
        "芋頭豆大福",
        "重乳酪紅豆大福",
        "抹茶紅豆乳酪大福",
        "可可乳酪大福",
    ]
    for idx, f in enumerate(default_flavors):
      c.execute(
          "INSERT OR IGNORE INTO flavors (flavor_name, sort_order) VALUES (?,"
          " ?)",
          (f, idx),
      )
  conn.commit()
  conn.close()


init_db()


def get_flavors():
  conn = sqlite3.connect(DB_FILE)
  df = pd.read_sql(
      "SELECT flavor_name FROM flavors ORDER BY sort_order ASC, id ASC", conn
  )
  conn.close()
  return df["flavor_name"].tolist()


def get_flavor_records():
  conn = sqlite3.connect(DB_FILE)
  df = pd.read_sql(
      "SELECT id, flavor_name, sort_order FROM flavors ORDER BY sort_order ASC,"
      " id ASC",
      conn,
  )
  conn.close()
  return df


def update_flavor_name(flavor_id, new_name):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  try:
    c.execute(
        "UPDATE flavors SET flavor_name = ? WHERE id = ?", (new_name, flavor_id)
    )
    conn.commit()
    success = True
  except:
    success = False
  conn.close()
  return success


def save_new_flavor_order(sorted_names):
  """透過拖曳後的完整清單順序重新寫入資料庫排序"""
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  for idx, name in enumerate(sorted_names):
    c.execute("UPDATE flavors SET sort_order = ? WHERE flavor_name = ?", (idx, name))
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


# --- 初始化 Session State ---
if "selected_date" not in st.session_state:
  st.session_state["selected_date"] = datetime.now().date()

if "item_count" not in st.session_state:
  st.session_state["item_count"] = 1

if "form_reset_counter" not in st.session_state:
  st.session_state["form_reset_counter"] = 0

# ==========================================
# 左側導覽列：頁面切換
# ==========================================
st.sidebar.title("🍡 紅斗泥管理選單")
app_mode = st.sidebar.radio("選擇功能頁面", ["📋 訂單與取貨主頁", "⚙️ 編輯口味清單"])

# ==========================================
# 頁面一：編輯口味清單 (支援拖曳排序、修改名稱、刪除)
# ==========================================
if app_mode == "⚙️ 編輯口味清單":
  st.title("⚙️ 編輯與管理下拉選單口味")
  st.write(
      "在這裡您可以新增口味、修改名稱，或直接**用滑鼠按住項目上下拖曳**來調整選單順序："
  )

  # 新增口味區
  with st.container():
    new_flavor_input = st.text_input("輸入新口味名稱")
    if st.button("➕ 新增口味"):
      if new_flavor_input.strip():
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
          c.execute("SELECT MAX(sort_order) FROM flavors")
          max_order = c.fetchone()[0]
          next_order = 0 if max_order is None else max_order + 1

          c.execute(
              "INSERT INTO flavors (flavor_name, sort_order) VALUES (?, ?)",
              (new_flavor_input.strip(), next_order),
          )
          conn.commit()
          st.success(f"已成功新增口味：{new_flavor_input}")
          st.rerun()
        except:
          st.warning("該口味已經存在選單中了！")
        conn.close()

  st.divider()
  st.subheader("📋 拖曳排序清單")
  st.info("提示：直接用滑鼠拖曳下方清單中的項目即可調整順序！")

  current_flavors = get_flavors()

  # 呼叫 sort_items 建立拖曳互動介面
  sorted_flavors = sort_items(current_flavors, key="flavor_sort_list")

  # 如果使用者拖曳改變了順序，自動儲存
  if sorted_flavors != current_flavors:
    save_new_flavor_order(sorted_flavors)
    st.rerun()

  st.divider()
  st.subheader("✏️ 修改名稱或刪除特定口味")
  flavors_df = get_flavor_records()
  for idx, row in flavors_df.iterrows():
    f_id = row["id"]
    f_name = row["flavor_name"]

    with st.container():
      c_name, c_edit, c_del = st.columns([3, 1.5, 1])
      with c_name:
        st.markdown(f"**{f_name}**")
      with c_edit:
        with st.popover("✏️ 編輯名稱"):
          edit_name_input = st.text_input(
              "修改名稱", value=f_name, key=f"edit_input_{f_id}"
          )
          if st.button("💾 儲存", key=f"save_edit_{f_id}"):
            if edit_name_input.strip():
              if update_flavor_name(f_id, edit_name_input.strip()):
                st.success("修改成功！")
                st.rerun()
              else:
                st.error("修改失敗，該名稱可能已存在！")
      with c_del:
        if st.button("🗑️ 刪除", key=f"del_flav_{f_id}"):
          conn = sqlite3.connect(DB_FILE)
          c = conn.cursor()
          c.execute("DELETE FROM flavors WHERE id = ?", (f_id,))
          conn.commit()
          conn.close()
          st.rerun()

# ==========================================
# 頁面二：訂單與取貨主頁
# ==========================================
elif app_mode == "📋 訂單與取貨主頁":
  st.title("🍡 紅斗泥大福 — 取貨與訂單管理系統")

  # 1. 快速新增訂單區 (置於最上方)
  st.subheader("➕ 快速新增訂單")

  with st.container():
    f_key = st.session_state["form_reset_counter"]

    col_n1, col_n2 = st.columns(2)
    with col_n1:
      name = st.text_input(
          "客戶姓名 / 稱呼 *",
          placeholder="例：陳小美",
          key=f"input_name_{f_key}",
      )
    with col_n2:
      phone = st.text_input(
          "聯絡電話 (選填)",
          placeholder="例：0912-345-678",
          key=f"input_phone_{f_key}",
      )

    st.markdown("##### 🛒 訂購品項")
    flavor_options = get_flavors()

    selected_items_list = []
    for i in range(st.session_state.item_count):
      c_f, c_q, _ = st.columns([2.5, 1, 0.5])
      f_sel = c_f.selectbox(
          f"口味 #{i+1}",
          flavor_options,
          key=f"f_new_{f_key}_{i}",
      )
      q_sel = c_q.number_input(
          f"數量 #{i+1}",
          min_value=1,
          max_value=50,
          value=1,
          key=f"q_new_{f_key}_{i}",
      )
      selected_items_list.append(f"{f_sel} x {q_sel}")

    if st.button("➕ 增加一個口味"):
      st.session_state.item_count += 1
      st.rerun()

    items_combined_str = ", ".join(selected_items_list)

    col_pay, col_date_col, col_slot = st.columns(3)
    with col_pay:
      payment = st.radio(
          "付款方式",
          ["已匯款", "現場付"],
          horizontal=True,
          key=f"pay_new_{f_key}",
      )

    with col_date_col:
      pickup_date = st.date_input(
          "預定取貨日期",
          value=st.session_state["selected_date"],
          key=f"date_new_{f_key}",
      )

    with col_slot:
      time_slot = st.radio(
          "取貨時段",
          ["中午", "下午", "無指定"],
          horizontal=True,
          key=f"slot_new_{f_key}",
      )

    note = st.text_input(
        "備註 (選填)", placeholder="例：要保冷袋", key=f"note_new_{f_key}"
    )

    if st.button("✅ 儲存送出訂單", use_container_width=True, type="primary"):
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
        st.session_state.item_count = 1
        st.session_state["form_reset_counter"] += 1
        st.success(f"🎉 新增成功！已建立 {name} 的訂單。")
        st.rerun()

  st.divider()

  # 2. 日曆播報器與日期切換
  cur_date = st.session_state["selected_date"]
  orders_df = get_orders_by_date(str(cur_date))

  col_prev, col_date_picker, col_next, col_today = st.columns(
      [1.2, 1.8, 1.2, 1.2]
  )
  with col_prev:
    if st.button("◀ 前一天", use_container_width=True):
      st.session_state["selected_date"] = cur_date - timedelta(days=1)
      st.rerun()
  with col_date_picker:
    selected_date_input = st.date_input(
        "選擇日期", value=cur_date, label_visibility="collapsed"
    )
    if selected_date_input != cur_date:
      st.session_state["selected_date"] = selected_date_input
      st.rerun()
  with col_next:
    if st.button("後一天 ▶", use_container_width=True):
      st.session_state["selected_date"] = cur_date + timedelta(days=1)
      st.rerun()
  with col_today:
    if st.button("🏠 今天", use_container_width=True):
      st.session_state["selected_date"] = datetime.now().date()
      st.rerun()

  # 統計當日口味需求
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
      "、".join(summary_str_list) if summary_str_list else "目前尚無訂單"
  )

  st.info(
      f"📢 **【{cur_date} 每日播報摘要】** 共 **{total_orders_count}** 筆訂單"
      f" ｜ 總計需備貨：**{summary_text_joined}**"
  )

  # 3. 下半部：取貨清單管理
  st.subheader(f"📋 【{cur_date}】取貨與出貨清單")

  if orders_df.empty:
    st.warning("這天目前沒有訂單紀錄。")
  else:
    for idx, row in orders_df.iterrows():
      order_id = row["id"]
      is_shipped = bool(row["shipped"])

      with st.container():
        rc1, rc2, rc3, rc4 = st.columns([1.2, 2.5, 1.5, 1])

        with rc1:
          st.markdown(
              f"**{'✅ 已出貨' if is_shipped else '⏳ 未出貨'}**<br>`{row['pickup_time_slot']}`",
              unsafe_allow_html=True,
          )

        with rc2:
          st.markdown(
              f"**{row['name']}** ({row['payment']})<br><span"
              f" style='color: #ffe6e2;'>{row['items']}</span>",
              unsafe_allow_html=True,
          )

        with rc3:
          phone_txt = row["phone"] if row["phone"] else "無電話"
          note_txt = f" / 備註: {row['note']}" if row["note"] else ""
          st.markdown(
              f"<small>{phone_txt}{note_txt}</small>", unsafe_allow_html=True
          )

        with rc4:
          shipped_toggle = st.checkbox(
              "已出貨", value=is_shipped, key=f"ship_{order_id}"
          )
          if shipped_toggle != is_shipped:
            update_order_shipped(order_id, shipped_toggle)
            st.rerun()

        # 編輯與刪除
        with st.expander("⚙️ 編輯 / 刪除訂單"):
          with st.form(key=f"edit_form_{order_id}"):
            e_name = st.text_input("客戶姓名", value=row["name"])
            e_phone = st.text_input(
                "聯絡電話", value=row["phone"] if row["phone"] else ""
            )
            e_items = st.text_input(
                "訂購品項 (例: 芋見奶凍大福 x 2)", value=row["items"]
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

            col_save, col_del = st.columns(2)
            if col_save.form_submit_button("💾 儲存修改"):
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
              st.success("已更新！")
              st.rerun()

          if st.button("🗑️ 刪除此筆訂單", key=f"del_{order_id}"):
            delete_order(order_id)
            st.rerun()
