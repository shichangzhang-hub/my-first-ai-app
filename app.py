import streamlit as st
import requests
import json
import numpy as np

# ================= 1. 基础配置与页面初始化 =================
st.set_page_config(page_title="Coyote-X1 智能助理", layout="wide")

# 请在这里填入你的真实 API Key
API_KEY = "sk-ddb352b28cba41d09dea8883663f2b4f" 
CHAT_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
EMBED_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

# --- 核心算法函数（保持不变） ---
def get_embedding(text):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "text-embedding-v2", "input": text}
    response = requests.post(EMBED_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    return []

def calculate_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# ================= 2. 侧边栏控制面板 (Sidebar) =================
with st.sidebar:
    st.title("⚙️ 控制面板")
    st.info("📂 知识库状态：medical_kb.txt 已加载")
    
    # 让面试官可以动态挑选模型和调节阈值，尽显工程专业度
    model_choice = st.selectbox("选择模型层", ["qwen-turbo", "qwen-plus"])
    threshold = st.slider("架构护栏阈值 (Similarity Threshold)", 0.1, 1.0, 0.3, step=0.05)
    
    st.markdown("""
    **护栏机制说明：**
    当用户提问与本地知识库的最高匹配度**低于**设定的阈值时，系统将自动拦截并触发合规回复，彻底杜绝大模型幻觉。
    """)

# ================= 3. 读取知识库与缓存 =================
@st.cache_resource # Streamlit 缓存机制，确保不用每次刷新都重新读取和计算向量
def init_knowledge_base():
    with open("medical_kb.txt", "r", encoding="utf-8") as f:
        document = f.read()
    chunks = [c.strip() for c in document.split('\n') if c.strip()]
    chunk_embeddings = [get_embedding(chunk) for chunk in chunks]
    return chunks, chunk_embeddings

try:
    chunks, chunk_embeddings = init_knowledge_base()
except Exception as e:
    st.error(f"知识库加载失败，请检查桌面是否存在 medical_kb.txt 文件。错误: {e}")
    st.stop()

# ================= 4. 对话历史状态管理 =================
# Streamlit 是脚本流运行，必须用 session_state 来维持历史记忆
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是卡尤迪 Coyote-X1 医疗设备的专属业务助理，请问有什么可以帮您？"}
    ]

# 在网页上渲染出历史聊天气泡
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ================= 5. 核心交互流（等待用户输入） =================
if user_question := st.chat_input("请输入您的问题..."):
    
    # 1. 展现用户输入的气泡
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.messages.append({"role": "user", "content": user_question})

    # 2. 检索逻辑与后台日志展示
    question_embedding = get_embedding(user_question)
    scores = [calculate_similarity(question_embedding, ce) for ce in chunk_embeddings]
    best_index = np.argmax(scores)
    best_score = scores[best_index]
    best_chunk = chunks[best_index]

    # 在网页上拉起一个漂亮的折叠日志栏
    with st.expander("🔍 RAG 向量检索后台实时日志"):
        st.write(f"**命中最高片段：** `{best_chunk}`")
        st.write(f"**语义相关性得分：** `{best_score:.4f}` (当前拦截阈值: `{threshold}`)")

    # 3. 架构护栏拦截校验
    if best_score < threshold:
        reply = "抱歉，内部知识库中未找到相关业务合规规范。为确保医疗设备操作安全，系统拒绝回答该问题。"
    else:
        # 4. 生成组装 Prompt 喂给大模型
        final_prompt = f"请仅仅根据私有知识回答问题。私有知识：{best_chunk}。问题：{user_question}"
        
        payload = {
            "model": model_choice,
            "messages": [{"role": "user", "content": final_prompt}],
            "temperature": 0.1
        }
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        
        with st.spinner("大模型正在组织严谨语言..."):
            response = requests.post(CHAT_URL, headers=headers, json=payload)
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
            else:
                reply = "服务器通信异常，请稍后再试。"

    # 5. 展现 AI 的回复气泡并存入记忆
    with st.chat_message("assistant"):
        st.write(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})