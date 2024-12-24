import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# データベース接続
conn = sqlite3.connect("expenses.db")
c = conn.cursor()

# 新しいテーブルを作成（もし存在しない場合）
c.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    category TEXT,
    product TEXT,
    cost INTEGER
)
""")
conn.commit()

# カテゴリテーブルを作成（もし存在しない場合）
c.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    category_name TEXT
)
""")
conn.commit()

# ヘルパー関数
def add_expense(category, product, cost):
    c.execute("INSERT INTO expenses (category, product, cost) VALUES (?, ?, ?)", (category, product, cost))
    conn.commit()

def get_expenses():
    c.execute("SELECT id, category, product, cost FROM expenses")
    return c.fetchall()

def delete_expenses(expense_ids):
    for expense_id in expense_ids:
        c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()

def add_category(category_name):
    c.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
    conn.commit()

def get_categories():
    c.execute("SELECT category_name FROM categories")
    return [row[0] for row in c.fetchall()]

def delete_category(category_name):
    c.execute("DELETE FROM categories WHERE category_name = ?", (category_name,))
    conn.commit()

# タイトル
st.title("費用管理アプリ")

# サイドバーでカテゴリーを選択し、商品名と費用を一括入力
st.sidebar.header("費用の一括入力")

# 既存カテゴリを取得
categories = get_categories()
categories = categories if categories else ["家賃", "食費", "交通費", "趣味"]  # カテゴリがない場合のデフォルト

category = st.sidebar.selectbox("カテゴリーを選択", categories)
with st.sidebar.form("expense_form"):
    products = st.text_area("商品名（カンマ区切り）", placeholder="例: 家賃, 食費, 交通費")
    costs = st.text_area("費用（カンマ区切り）", placeholder="例: 50000, 30000, 10000")
    submitted = st.form_submit_button("一括追加")
    if submitted:
        try:
            # 入力された商品名と費用を処理
            product_list = products.split(",")
            cost_list = [int(cost.strip()) for cost in costs.split(",")]
            if len(product_list) == len(cost_list):
                for product, cost in zip(product_list, cost_list):
                    add_expense(category, product.strip(), cost)
                st.sidebar.success("データを一括追加しました！")
            else:
                st.sidebar.error("商品名と費用の数が一致していません。")
        except ValueError:
            st.sidebar.error("費用には数値を入力してください。")

# FIREページ
st.header("FIRE (Financial Independence, Retire Early) 目標")

# 年収と目標設定
st.sidebar.header("目標設定")

# ユーザーの年収を入力
annual_income = st.sidebar.number_input("現在の年収 (万円)", min_value=0, step=100, format="%d")

# 予測年収変化率を入力
income_growth_rate = st.sidebar.number_input("年収の予測変化率 (%)", min_value=-100.0, max_value=100.0, step=0.1)

# 株価（または投資金額）を入力
current_stock_value = st.sidebar.number_input("現在の株価または投資額 (万円)", min_value=0, step=100, format="%d")

# 予測株価変化率を入力
stock_growth_rate = st.sidebar.number_input("株価の予測変化率 (%)", min_value=-100.0, max_value=100.0, step=0.1)

# 予測年収計算
years = st.sidebar.number_input("予測する年数", min_value=1, max_value=50, value=10, step=1)

# 予測年収を計算
future_annual_income = annual_income * (1 + income_growth_rate / 100) ** years

# 予測株価を計算
future_stock_value = current_stock_value * (1 + stock_growth_rate / 100) ** years

# 結果表示
st.sidebar.write(f"{years} 年後の年収予測: {future_annual_income}万円")
st.sidebar.write(f"{years} 年後の株価予測: {future_stock_value}万円")

# 予測変化をグラフ化
years_range = list(range(0, years + 1))
income_values = [annual_income * (1 + income_growth_rate / 100) ** year for year in years_range]
stock_values = [current_stock_value * (1 + stock_growth_rate / 100) ** year for year in years_range]

# グラフ表示
fig, ax = plt.subplots()
ax.plot(years_range, income_values, label="年収予測", color='blue', marker='o')
ax.plot(years_range, stock_values, label="株価予測", color='orange', marker='x')
ax.set_xlabel("年数")
ax.set_ylabel("金額 (万円)")
ax.set_title("年収および株価の予測変化")
ax.legend()

# グラフを表示
st.pyplot(fig)

# ダウンロードボタンの追加
def to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')s
    return output.getvalue()
s
def to_json(df):
    return df.to_json(orient="records", lines=True).encode('utf-8')

# 費用一覧の表示（DataFrameとして表示）
expenses = get_expenses()
if expenses:
    st.subheader("費用一覧")
    
    # DataFrameに変換
    expenses_df = pd.DataFrame(expenses, columns=["ID", "カテゴリー", "商品名", "費用"])
    
    # 表を表示
    st.dataframe(expenses_df.drop("ID", axis=1))  # IDは表示しない
    
    # チェックボックスを表示する
    selected_ids_to_delete = []
    for index, row in expenses_df.iterrows():
        expense_id = row['ID']
        product_name = row['商品名']  # 商品名を表示
        checkbox = st.checkbox(f"削除: {product_name}", key=f"delete_{expense_id}")
        if checkbox:
            selected_ids_to_delete.append(expense_id)

    # 削除ボタン
    if st.button("選択した項目を削除"):
        if selected_ids_to_delete:
            delete_expenses(selected_ids_to_delete)
            st.success(f"{len(selected_ids_to_delete)} 項目が削除されました。")
            st.rerun()  # ページを再読み込みして最新のデータを表示
        else:
            st.warning("削除する項目を選択してください。")
    
    # ダウンロードオプション
    st.subheader("データダウンロード")
    
    # CSVとしてダウンロード
    csv = to_csv(expenses_df)
    st.download_button(
        label="CSVとしてダウンロード",
        data=csv,
        file_name="expenses.csv",
        mime="text/csv"
    )
    
    # Excelとしてダウンロード
    excel = to_excel(expenses_df)
    st.download_button(
        label="Excelとしてダウンロード",
        data=excel,
        file_name="expenses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # JSONとしてダウンロード
    json = to_json(expenses_df)
    st.download_button(
        label="JSONとしてダウンロード",
        data=json,
        file_name="expenses.json",
        mime="application/json"
    )
else:
    st.write("まだ費用が入力されていません。サイドバーから入力してください。")

# アプリ終了時の接続クローズ
st.sidebar.write("アプリを閉じるとデータベースの接続が自動で切れます。")
