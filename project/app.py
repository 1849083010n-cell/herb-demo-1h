import streamlit as st
import sqlite3
import requests
import json
from datetime import datetime

# 配置GitHub信息（替换为你的仓库信息）
GITHUB_USER = "1849083010n-cell"
GITHUB_REPO = "herb-pending-suggestions"  # 如 herb-database
GITHUB_TOKEN = st.secrets["github"]["token"]  # 建议用Streamlit Secrets存储Token
PENDING_FILE_PATH = "pending.json"  # 仓库中存储建议的文件路径

# 连接本地数据库（herbs(1).db）
def get_db():
    return sqlite3.connect("herbs(1).db")

# 通过GitHub API获取当前pending.json内容
def get_pending_from_github():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{PENDING_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        import base64
        return json.loads(base64.b64decode(content["content"]).decode())
    else:
        return []  # 若文件不存在，返回空列表

# 通过GitHub API更新pending.json
def update_pending_to_github(new_suggestion):
    # 获取当前文件内容和SHA（用于更新）
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{PENDING_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    current_content = get_pending_from_github()
    current_content.append(new_suggestion)  # 添加新建议

    # 编码新内容
    import base64
    new_content = base64.b64encode(json.dumps(current_content, ensure_ascii=False).encode()).decode()

    # 构建更新请求
    data = {
        "message": f"Add new suggestion: {new_suggestion['药材名']}",  # 提交信息
        "content": new_content,
        "sha": response.json()["sha"] if response.status_code == 200 else None  # 若文件存在，需传入当前SHA
    }

    # 发送更新请求
    response = requests.put(url, headers=headers, json=data)
    return response.status_code == 200

# 页面标题
st.title("中药材数据库（带持续更新建议功能）")

# 1. 查询功能（按名称搜）
st.subheader("查药材")
name = st.text_input("输入名称（如当归）")
if st.button("查询"):
    db = get_db()
    # 注意：字段名需与herbs(1).db中的表结构一致（若表中是name则改WHERE name LIKE ?）
    res = db.execute("SELECT * FROM herbs WHERE 名称 LIKE ?", (f'%{name}%',)).fetchall()
    if res:
        for item in res:
            st.write(f"ID: {item[0]} | 名称: {item[1]} | 功效: {item[2]} | 对应脏腑: {item[3]}")
    else:
        st.info("未找到匹配的药材")
    db.close()

# 2. 提交建议功能（同步到GitHub）
st.subheader("提建议")
with st.form("suggestion_form"):
    herb_name = st.text_input("药材名")
    suggestion = st.text_area("建议内容（如功效补充、分类修正等）")
    submit = st.form_submit_button("提交建议")
    
    if submit:
        if not herb_name or not suggestion:
            st.error("药材名和建议内容不能为空！")
        else:
            # 构建建议数据（含时间戳）
            new_suggestion = {
                "药材名": herb_name,
                "建议内容": suggestion,
                "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # 提交到GitHub
            success = update_pending_to_github(new_suggestion)
            if success:
                st.success("建议提交成功！已同步到GitHub仓库～")
            else:
                st.error("提交失败，请检查GitHub配置或网络！")

# 3. 显示当前所有建议（从GitHub读取）
st.subheader("历史建议（来自GitHub）")
pending_list = get_pending_from_github()
if pending_list:
    for i, item in enumerate(pending_list, 1):
        st.write(f"**{i}. {item['药材名']}**（{item['提交时间']}）")
        st.write(f"建议：{item['建议内容']}")
        st.divider()
else:
    st.info("暂无建议，快来提交第一条吧～")
