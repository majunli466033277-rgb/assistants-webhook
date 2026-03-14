#!/usr/bin/env python3
"""
飞书机器人Webhook服务
三个独立机器人的统一处理中心
"""

from flask import Flask, request, jsonify
import json
import hashlib
import hmac
import base64
import time
from datetime import datetime

app = Flask(__name__)

# 三个机器人的配置
ASSISTANTS = {
    "cli_a9264cea0eb8dbb6": {  # 鹰眼
        "name": "鹰眼",
        "emoji": "🦅",
        "secret": "djEEBGrkYc9oPQE8HTYaObnkQeFSsta6",
        "type": "金融助手"
    },
    "cli_a9250b6444381cb5": {  # 骆驼
        "name": "骆驼",
        "emoji": "🐫",
        "secret": "W5NbFpbQQrZi7gt88PsbQewVjo0yU5lr",
        "type": "跨境助手"
    },
    "cli_a93a7cb952389cb5": {  # 灵狐
        "name": "灵狐",
        "emoji": "🦊",
        "secret": "7aXGEJgtMp3vgDF5HG4q2gFwskLXi276",
        "type": "日常助手"
    }
}

# Webhook验证token（需要在飞书平台设置）
VERIFICATION_TOKEN = "assistants_webhook_token_2026"

def verify_signature(timestamp, nonce, signature):
    """验证飞书Webhook签名"""
    string_to_sign = f"{timestamp}\n{nonce}\n{VERIFICATION_TOKEN}".encode('utf-8')
    expected_signature = base64.b64encode(
        hmac.new(VERIFICATION_TOKEN.encode('utf-8'), string_to_sign, hashlib.sha256).digest()
    ).decode('utf-8')
    return hmac.compare_digest(signature, expected_signature)

def get_access_token(app_id, app_secret):
    """获取机器人的访问令牌"""
    import requests
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = {"app_id": app_id, "app_secret": app_secret}
    
    response = requests.post(url, headers=headers, json=data, timeout=10)
    result = response.json()
    
    if result.get("code") == 0:
        return result["tenant_access_token"]
    else:
        print(f"获取令牌失败: {result.get('msg')}")
        return None

def send_reply(app_id, app_secret, chat_id, reply_text):
    """发送回复消息"""
    import requests
    import json as json_lib
    
    token = get_access_token(app_id, app_secret)
    if not token:
        return False
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    data = {
        "receive_id": chat_id,
        "receive_id_type": "chat_id",
        "msg_type": "text",
        "content": json_lib.dumps({"text": reply_text})
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()
        return result.get("code") == 0
    except Exception as e:
        print(f"发送消息失败: {str(e)}")
        return False

def generate_assistant_reply(assistant_config, message_text):
    """根据助手身份生成回复"""
    name = assistant_config["name"]
    emoji = assistant_config["emoji"]
    
    if name == "鹰眼":
        return f"{emoji} {name}分析：收到金融相关问题，正在分析市场数据，稍后给您详细报告。"
    elif name == "骆驼":
        return f"{emoji} {name}调研：收到跨境相关问题，正在调研国际市场和物流方案。"
    elif name == "灵狐":
        return f"{emoji} {name}安排：收到日程安排需求，正在为您优化时间规划。"
    else:
        return f"收到消息，正在处理中..."

@app.route('/webhook', methods=['POST'])
def webhook():
    """处理飞书Webhook请求"""
    try:
        data = request.json
        
        # 验证请求
        timestamp = request.headers.get('X-Lark-Request-Timestamp', '')
        nonce = request.headers.get('X-Lark-Request-Nonce', '')
        signature = request.headers.get('X-Lark-Signature', '')
        
        if not verify_signature(timestamp, nonce, signature):
            return jsonify({"error": "签名验证失败"}), 403
        
        # 处理挑战请求（URL验证）
        if data.get("type") == "url_verification":
            return jsonify({"challenge": data.get("challenge")})
        
        # 处理消息事件
        if data.get("type") == "event_callback":
            event = data.get("event", {})
            
            # 识别是哪个机器人
            app_id = event.get("app_id")
            if app_id not in ASSISTANTS:
                return jsonify({"error": "未知机器人"}), 400
            
            assistant = ASSISTANTS[app_id]
            
            # 处理消息
            if event.get("type") == "message":
                message = event.get("message", {})
                message_id = message.get("message_id")
                chat_id = message.get("chat_id")
                message_type = message.get("message_type")
                
                if message_type == "text":
                    content = json.loads(message.get("content", "{}")).get("text", "")
                    
                    print(f"[{datetime.now()}] 收到{assistant['name']}消息: {content[:50]}...")
                    
                    # 生成回复
                    reply = generate_assistant_reply(assistant, content)
                    
                    # 发送回复
                    success = send_reply(app_id, assistant["secret"], chat_id, reply)
                    
                    if success:
                        print(f"  回复发送成功: {reply[:50]}...")
                        return jsonify({"status": "success"})
                    else:
                        print("  回复发送失败")
                        return jsonify({"error": "发送失败"}), 500
        
        return jsonify({"status": "ignored"})
        
    except Exception as e:
        print(f"Webhook处理异常: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "assistants": list(ASSISTANTS.keys())
    })

if __name__ == '__main__':
    print("飞书机器人Webhook服务启动")
    print(f"支持的助手: {', '.join([a['name'] for a in ASSISTANTS.values()])}")
    app.run(host='0.0.0.0', port=3000, debug=True)
