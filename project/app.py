import streamlit as st
import sqlite3
import requests
import json
from datetime import datetime
import os
from streamlit.components.v1 import html  # 改用 components.v1.html 更稳定

# 带 JavaScript 交互的开关 HTML 代码
interactive_toggle_html = """
<!-- 开关容器：绑定点击事件 -->
<div id="toggleSwitch" data-show-ax-label="true" data-state="On" 
     style="width: 64px; padding: 2px; background: #34C759; overflow: hidden; border-radius: 100px; 
     justify-content: space-between; align-items: center; display: inline-flex; cursor: pointer;">
  <!-- 关闭状态的竖线（默认隐藏） -->
  <div data-svg-wrapper id="offLine" style="display: none;">
    <svg width="21" height="10" viewBox="0 0 21 10" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="10" width="1" height="10" fill="white"/>
    </svg>
  </div>
  <!-- 开关滑块 -->
  <div data-svg-wrapper id="toggleKnob" style="position: relative; transition: transform 0.3s ease;">
    <svg width="39" height="24" viewBox="0 0 39 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="39" height="24" rx="12" fill="white"/>
    </svg>
  </div>
</div>

<!-- 状态显示文本 -->
<div id="toggleStatus" style="margin-top: 10px; font-size: 16px; font-family: Inter; color: #333;">
  状态：开启（On）
</div>

<!-- JavaScript 交互逻辑 -->
<script>
// 获取开关元素
const toggleSwitch = document.getElementById('toggleSwitch');
const toggleKnob = document.getElementById('toggleKnob');
const offLine = document.getElementById('offLine');
const toggleStatus = document.getElementById('toggleStatus');

// 绑定点击事件（兼容不同浏览器）
if (toggleSwitch.addEventListener) {
  toggleSwitch.addEventListener('click', toggleState);
} else if (toggleSwitch.attachEvent) {  // 兼容旧版IE（可选）
  toggleSwitch.attachEvent('onclick', toggleState);
}

// 状态切换函数
function toggleState() {
  const currentState = toggleSwitch.getAttribute('data-state');
  
  if (currentState === 'On') {
    // 切换到 Off 状态
    toggleSwitch.setAttribute('data-state', 'Off');
    toggleSwitch.style.background = '#D9D9D9';
    toggleKnob.style.transform = 'translateX(-25px)';
    offLine.style.display = 'block';
    toggleStatus.textContent = '状态：关闭（Off）';
  } else {
    // 切换到 On 状态
    toggleSwitch.setAttribute('data-state', 'On');
    toggleSwitch.style.background = '#34C759';
    toggleKnob.style.transform = 'translateX(0)';
    offLine.style.display = 'none';
    toggleStatus.textContent = '状态：开启（On）';
  }
}
</script>
"""

# Streamlit 页面
st.title("可交互开关插件演示")
st.subheader("点击开关切换 On/Off 状态")

# 嵌入交互开关（改用 components.v1.html，参数更稳定）
html(
    interactive_toggle_html,  # 直接传HTML字符串（位置参数，避免关键字参数问题）
    width=100,
    height=80,
    scrolling=False
)


try:
    GITHUB_TOKEN = st.secrets["github"]["token"]
except KeyError:
    st.error("未找到 GitHub Token！请在 Streamlit Cloud 网页端配置 Secrets")
    st.stop()

# --------------------------
# 数据库路径配置（确保正确找到 herbs(1).db）
# --------------------------
def get_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取 app.py 所在目录（project/）
    db_path = os.path.join(current_dir, "herbs(1).db")
    if not os.path.exists(db_path):
        st.error(f"数据库文件未找到！路径：{db_path}")
        st.info("请确认 herbs(1).db 已放在 project/ 文件夹下")
    return sqlite3.connect(db_path)

# --------------------------
# GitHub 仓库配置（确认正确性）
# --------------------------
GITHUB_USER = "1849083010n-cell"  # 你的 GitHub 用户名（必须完全一致）
GITHUB_REPO = "herb-pending-suggestions"  # 仓库名（必须与 GitHub 上一致）
PENDING_FILE_PATH = "pending.json"  # 建议存储文件

# --------------------------
# GitHub API 函数（修复权限相关问题）
# --------------------------
def get_pending_from_github():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{PENDING_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Streamlit-App"  # 增加 User-Agent 避免 401 错误
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            content = response.json()
            import base64
            return json.loads(base64.b64decode(content["content"]).decode())
        elif response.status_code == 401:
            st.error("GitHub 权限不足！请检查 Token 是否勾选 repo 权限")
            return []
        elif response.status_code == 404:
            st.warning("pending.json 文件不存在，将自动创建")
            return []
        else:
            st.warning(f"读取失败，状态码：{response.status_code}")
            return []
    except Exception as e:
        st.error(f"GitHub 连接错误：{str(e)}")
        return []

def update_pending_to_github(new_suggestion):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{PENDING_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Streamlit-App"  # 增加 User-Agent
    }
    try:
        # 获取当前文件信息（用于更新）
        response = requests.get(url, headers=headers, timeout=10)
        current_content = get_pending_from_github()
        current_content.append(new_suggestion)
        
        # 编码新内容
        import base64
        new_content = base64.b64encode(
            json.dumps(current_content, ensure_ascii=False, indent=2).encode()
        ).decode()
        
        # 构建更新数据
        data = {
            "message": f"Add suggestion: {new_suggestion['药材名']}",
            "content": new_content,
            "sha": response.json()["sha"] if response.status_code == 200 else None
        }
        
        # 发送更新请求
        response = requests.put(url, headers=headers, json=data, timeout=10)
        if response.status_code == 201:  # 201 表示创建成功（文件不存在时）
            return True
        elif response.status_code == 200:  # 200 表示更新成功（文件已存在时）
            return True
        else:
            st.error(f"提交失败，状态码：{response.status_code}，原因：{response.text}")
            return False
    except Exception as e:
        st.error(f"提交失败：{str(e)}")
        return False

# --------------------------
# 页面展示（修复数据库查询字段）
# --------------------------
st.title("中药材数据库（带持续更新建议功能）")

# 1. 查询功能（修正字段名为中文“名称”）
st.subheader("查药材")
name = st.text_input("输入名称（如当归）")
if st.button("查询"):
    db = get_db()
    cursor = db.cursor()
    try:
        # 关键修改：将字段名从 "name" 改为中文 "名称"（适配你的数据库表结构）
        cursor.execute("SELECT * FROM herbs WHERE 名称 LIKE ?", (f'%{name}%',))
        res = cursor.fetchall()
        
        if res:
            for item in res:
                st.write(f"ID: {item[0]} | 名称: {item[1]} | 功效: {item[2]} | 对应脏腑: {item[3]}")
        else:
            st.info("未找到匹配的药材")
    except sqlite3.OperationalError as e:
        st.error(f"查询失败：{str(e)}")
        st.info("若提示 'no such column: 名称'，请将代码中 '名称' 改为数据库实际字段名（如 '药材名称'）")
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
