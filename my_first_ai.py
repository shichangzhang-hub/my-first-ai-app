import requests
import json

# ================= 你的配置区 =================
# 换成你的真实 API Key
API_KEY = "sk-ddb352b28cba41d09dea8883663f2b4f" 
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" 
# ============================================

# 1. 初始化对话历史（这就是让 AI "拥有记忆" 的秘诀）
# 我们在这里给它设定一个专业的垂直领域人设
messages_history = [
    {"role": "system", "content": "你是一个严谨的医疗科技业务助理。你的回答必须专业、精炼，且符合商业落地规范。"}
]

print("=========================================")
print("  🤖 专业业务助理已启动 (输入 'quit' 退出)")
print("=========================================")

# 2. 开启无限循环，打造交互式工具
while True:
    # 接收用户在键盘的输入
    user_input = input("\n👨‍💻 你的问题: ")
    
    # 设置一个退出机关
    if user_input.lower() in ['quit', 'exit', '退出']:
        print("👋 助理已下线，再见！")
        break
        
    # 如果用户直接按了回车没打字，就跳过这次循环
    if not user_input.strip():
        continue

    # 3. 将用户的新问题加入到对话历史中
    messages_history.append({"role": "user", "content": user_input})

    # 准备打包发送的数据
    payload = {
        "model": "qwen-turbo", 
        "messages": messages_history, # 注意这里：我们发送的是整个历史记录！
        "temperature": 0.7 
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    # 4. 发送请求并处理结果
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200: 
            result = response.json()
            ai_reply = result["choices"][0]["message"]["content"]
            
            # 打印 AI 的回复
            print(f"🤖 助理回复: {ai_reply}")
            
            # 5. 【关键步】把 AI 的回复也存进历史记录里，形成完整的记忆闭环
            messages_history.append({"role": "assistant", "content": ai_reply})
            
        else:
            print(f"\n❌ 出错了！错误代码: {response.status_code}")
            print(response.text)
            # 如果出错，把刚才加进去的问题弹出来，免得破坏历史记录
            messages_history.pop() 
            
    except Exception as e:
        print(f"网络请求发生异常: {e}")