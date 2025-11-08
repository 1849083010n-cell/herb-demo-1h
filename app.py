import streamlit as st
import sqlite3

# 连接数据库（指定为herbs(1).db）
def get_db():
    # 关键修改：将数据库文件名改为herbs(1).db
    return sqlite3.connect("herbs(1).db")

st.title("1小时测试版")

# 1. 查询功能（按名称搜）
st.subheader("查药材")
name = st.text_input("输入名称（如当归）")
if st.button("查询"):
    db = get_db()
    # 注意：SQL语句中的字段名需与数据库表结构一致
    # 若表中字段是“name”而非“名称”，需修改为SELECT * FROM herbs WHERE name LIKE ?
    res = db.execute("SELECT * FROM herbs WHERE 名称 LIKE ?", (f'%{name}%',)).fetchall()
    
    # 优化显示：如果有结果，按行展示；无结果提示
    if res:
        for item in res:
            st.write(f"ID: {item[0]} | 名称: {item[1]} | 功效: {item[2]} | 对应脏腑: {item[3]}")
    else:
        st.info("未找到匹配的药材")
    
    db.close()

# 2. 提交功能（确保数据库中存在pending表，若不存在需先创建）
st.subheader("提建议")
with st.form("f"):
    n = st.text_input("药材名")
    c = st.text_input("建议内容")
    if st.form_submit_button("提交"):
        try:
            db = get_db()
            # 插入建议到pending表
            db.execute("INSERT INTO pending (名称, 内容) VALUES (?,?)", (n, c))
            db.commit()
            st.success("提交成功！")
        except sqlite3.OperationalError:
            # 若pending表不存在，提示创建
            st.error("提交失败：未找到pending表，请先创建该表")
        finally:
            db.close()

