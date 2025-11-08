import streamlit as st
import sqlite3
import requests
import json
from datetime import datetime
import os

# --------------------------
# 关键修改1：适配 secrets.toml 路径（project/streamlit/secrets.toml）
# --------------------------
# Streamlit 会自动识别 project/streamlit/ 为配置文件夹，无需手动指定路径
# 直接读取即可（确保 secrets.toml 中 [github] 节点和 token 字段正确）
try:
    GITHUB_TOKEN = st.secrets["github"]["token"]
    # 可选：测试 Token 是否读取成功（运行后在页面顶部显示“Token配置成功”）
    # st.success("Token 配置成功！")
except KeyError:
    st.error("未找到 GitHub Token！请检查 project/streamlit/secrets.toml 文件配置")
    st.stop()  # 配置错误时停止运行

# --------------------------
# 关键修改2：修正数据库文件路径（适配 project/ 子文件夹）
# --------------------------
def get_db():
    # 获取当前代码文件（app.py）所在目录（project/ 文件夹）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接数据库路径：project/herbs(1).db（与 app.py 同目录）
    db_path = os.path.join(current_dir, "herbs(1).db")
    # 验证路径是否存在（方便调试）
    if not os.path.exists(db_path):
        st.error(f"数据库文件未找到！实际查找路径：{db_path}")
    return sqlite3.connect(db_path)

# --------------------------
# GitHub 其他配置（保持不变）
# --------------------------
GITHUB_USER = "1849083010n-cell"
GITHUB_REPO = "herb-pending-suggestions"
PENDING_FILE_PATH = "pending.json"

# --------------------------
# GitHub API 相关函数（保持不变，增加错误捕获）
# --------------------------
def get_pending_from_github():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{PENDING_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            content = response.json()
            import base64
            return json.loads(base64.b64decode(content["content"]).decode())
        else:
            st.warning(f"读取GitHub建议失败，状态码：{response.status_code}（可能是仓库或文件不存在）")
            return []
    except Exception as e:
        st.error(f"GitHub连接错误：{str(e)}（可能是Token无效或网络问题）")
        return []

def update_pending_to_github(new_suggestion):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{PENDING_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        # 获取当前文件SHA（更新文件必需）
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code not in [200, 404]:
            st.error(f"获取文件信息失败，状态码：{response.status_code}")
            return False
        
        current_content = get_pending_from_github()
        current_content.append(new_suggestion)
        
        # 编码新内容（indent=2 让 JSON 格式更清晰）
        import base64
        new_content = base64.b64encode(json.dumps(current_content, ensure_ascii=False, indent=2).encode()).decode()
        
        # 构建请求数据（文件不存在时 SHA 为 None）
        data = {
            "message": f"Add new suggestion: {new_suggestion['药材名']}",
            "content": new_content,
            "sha": response.json()["sha"] if response.status_code == 200 else None
        }
        
        # 发送更新请求
        response = requests.put(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return True
        else:
            st.error(f"提交建议失败，状态码：{response.status_code}，响应：{response.text}")
            return False
    except Exception as e:
        st.error(f"提交建议失败：{str(e)}")
        return False

# --------------------------
# 页面展示（修正SQL查询字段名）
# --------------------------
st.title("中药材数据库（带持续更新建议功能）")

# 1. 查询功能（按名称搜）
st.subheader("查药材")
name = st.text_input("输入名称（如当归）")
if st.button("查询"):
    db = get_db()
    cursor = db.cursor()
    try:
        # 关键：字段名改为 "name"（对应数据库表结构，若实际是中文"药材名称"则修改）
        cursor.execute("SELECT * FROM herbs WHERE name LIKE ?", (f'%{name}%',))
        res = cursor.fetchall()
        
        if res:
            for item in res:
                st.write(f"ID: {item[0]} | 名称: {item[1]} | 功效: {item[2]} | 对应脏腑: {item[3]}")
        else:
            st.info("未找到匹配的药材")
    except sqlite3.OperationalError as e:
        st.error(f"查询失败：{str(e)}")
        st.info("解决方案：1. 检查 herbs 表中'药材名称'字段名（是 name 还是 药材名称）；2. 确认数据库文件路径正确")
    finally:
        db.close()

# 2. 提交建议功能
st.subheader("提建议")
with st.form("suggestion_form"):
    herb_name = st.text_input("药材名")
    suggestion = st.text_area("建议内容（如功效补充、分类修正等）")
    submit = st.form_submit_button("提交建议")
    
    if submit:
        if not herb_name or not suggestion:
            st.error("药材名和建议内容不能为空！")
        else:
            new_suggestion = {
                "药材名": herb_name,
                "建议内容": suggestion,
                "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            success = update_pending_to_github(new_suggestion)
            if success:
                st.success("建议提交成功！已同步到GitHub仓库～")
            else:
                st.error("提交失败，请检查：1. GitHub Token权限；2. 仓库名/用户名是否正确；3. 网络连接")

# 3. 显示历史建议
st.subheader("历史建议（来自GitHub）")
pending_list = get_pending_from_github()
if pending_list:
    for i, item in enumerate(pending_list, 1):
        st.write(f"**{i}. {item['药材名']}**（{item['提交时间']}）")
        st.write(f"建议：{item['建议内容']}")
        st.divider()
else:
    st.info("暂无建议，快来提交第一条吧～")
