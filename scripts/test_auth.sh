#!/bin/bash

# 用户认证API测试脚本

API_URL="http://127.0.0.1:8000/api"

echo "======================================"
echo "  用户认证API测试"
echo "======================================"
echo ""

# 测试1: 注册用户
echo "测试1: 注册新用户"
echo "--------------------------------------"
REGISTER_RESPONSE=$(curl -s -X POST "${API_URL}/auth/register" \
  -F "username=testuser" \
  -F "email=test@example.com" \
  -F "password=123456" \
  -F "full_name=测试用户")

echo "响应: $REGISTER_RESPONSE"
echo ""

# 测试2: 登录
echo "测试2: 用户登录"
echo "--------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -F "username=testuser" \
  -F "password=123456")

echo "响应: $LOGIN_RESPONSE"

# 提取token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Token: $TOKEN"
echo ""

# 测试3: 获取当前用户信息
if [ ! -z "$TOKEN" ]; then
  echo "测试3: 获取当前用户信息"
  echo "--------------------------------------"
  ME_RESPONSE=$(curl -s -X GET "${API_URL}/auth/me" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "响应: $ME_RESPONSE"
  echo ""
  
  # 测试4: 登出
  echo "测试4: 用户登出"
  echo "--------------------------------------"
  LOGOUT_RESPONSE=$(curl -s -X POST "${API_URL}/auth/logout" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "响应: $LOGOUT_RESPONSE"
  echo ""
fi

echo "======================================"
echo "  测试完成"
echo "======================================"
