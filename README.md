# 智能助手联盟 - Webhook服务

## 🎯 功能
统一处理三个飞书机器人的Webhook请求：
- 🦅 鹰眼（金融助手）
- 🐫 骆驼（跨境助手）
- 🦊 灵狐（日常助手）

## 🚀 部署到Railway
1. Railway中选这个仓库
2. 自动部署
3. 获取公网URL

## 🔧 配置飞书Webhook
对每个机器人：
1. 事件订阅 → 配置请求地址
2. 填写：`https://你的-railway-url/webhook`
3. 设置Verification Token：`assistants_webhook_token_2026`
4. 订阅事件：`im:message`
