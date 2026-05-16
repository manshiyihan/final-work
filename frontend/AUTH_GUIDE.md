# 用户认证系统使用指南

## 功能概述

系统已添加完整的用户认证功能，包括：
- 用户注册
- 用户登录
- 会话管理
- 自动登出
- 路由守卫

---

## 快速开始

### 1. 启动后端

```bash
# 确保后端API运行
./scripts/run_api.sh
```

后端会自动创建用户表。

### 2. 启动前端

```bash
cd frontend
npm run dev
```

### 3. 访问系统

打开浏览器访问: http://localhost:7860

首次访问会自动跳转到登录页面。

---

## 用户注册

### 注册步骤

1. 在登录页面点击"注册"标签
2. 填写注册信息：
   - 用户名（必填，至少3个字符）
   - 邮箱（必填，格式正确）
   - 姓名（可选）
   - 密码（必填，至少6个字符）
   - 确认密码（必填，需与密码一致）
3. 点击"注册"按钮
4. 注册成功后自动切换到登录标签页

### 注册验证规则

- 用户名：至少3个字符，不能重复
- 邮箱：格式正确，不能重复
- 密码：至少6个字符
- 确认密码：必须与密码一致

---

## 用户登录

### 登录步骤

1. 在登录页面输入用户名和密码
2. 点击"登录"按钮或按Enter键
3. 登录成功后跳转到主页面

### 登录状态

- 登录成功后，token会保存在localStorage中
- 页面右上角显示用户名
- 点击用户名可查看用户信息和退出登录

---

## 会话管理

### Token机制

- 登录成功后获得token（有效期7天）
- Token自动添加到所有API请求头
- Token过期或无效时自动跳转到登录页

### 自动登出

以下情况会自动登出：
- Token过期（7天后）
- Token无效
- 手动点击"退出登录"

---

## API接口

### 注册接口

```
POST /api/auth/register
Content-Type: multipart/form-data

参数:
- username: 用户名
- email: 邮箱
- password: 密码
- full_name: 姓名（可选）

响应:
{
  "ok": true,
  "message": "注册成功，用户ID: 1"
}
```

### 登录接口

```
POST /api/auth/login
Content-Type: multipart/form-data

参数:
- username: 用户名
- password: 密码

响应:
{
  "ok": true,
  "token": "token字符串",
  "user": {
    "id": 1,
    "username": "user1",
    "email": "user@example.com",
    "full_name": "张三",
    "role": "user"
  }
}
```

### 登出接口

```
POST /api/auth/logout
Authorization: Bearer {token}

响应:
{
  "ok": true,
  "message": "登出成功"
}
```

### 获取当前用户

```
GET /api/auth/me
Authorization: Bearer {token}

响应:
{
  "ok": true,
  "user": {
    "id": 1,
    "username": "user1",
    "email": "user@example.com",
    "full_name": "张三",
    "role": "user"
  }
}
```

---

## 数据库结构

### users表

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login TEXT
)
```

### 字段说明

- `id`: 用户ID（主键）
- `username`: 用户名（唯一）
- `email`: 邮箱（唯一）
- `password_hash`: 密码哈希（SHA256）
- `full_name`: 姓名
- `role`: 角色（user/admin）
- `is_active`: 是否激活（1=激活，0=禁用）
- `created_at`: 创建时间
- `last_login`: 最后登录时间

---

## 前端组件

### Login.vue

登录注册页面组件，包含：
- 登录表单
- 注册表单
- 表单验证
- 错误提示

### MainLayout.vue

主布局组件，包含：
- 用户信息显示
- 下拉菜单
- 退出登录功能

---

## 路由守卫

### 自动跳转

- 未登录访问主页 → 跳转到登录页
- 已登录访问登录页 → 跳转到主页
- Token过期 → 自动跳转到登录页

### 路由配置

```javascript
{
  path: '/login',
  meta: { requiresAuth: false }  // 不需要登录
}

{
  path: '/',
  meta: { requiresAuth: true }   // 需要登录
}
```

---

## 安全性

### 密码安全

- 密码使用SHA256哈希存储
- 不存储明文密码
- 密码最少6个字符

### Token安全

- Token使用secrets.token_urlsafe生成
- Token有效期7天
- Token存储在localStorage
- 自动在请求头中添加

### 会话管理

- 服务端维护会话状态
- 会话过期自动清理
- 支持手动登出

---

## 测试账号

首次使用需要注册新账号，系统没有预设账号。

### 注册测试账号

```
用户名: testuser
邮箱: test@example.com
密码: 123456
```

---

## 常见问题

### Q1: 忘记密码怎么办？

A: 当前版本暂不支持密码重置，可以联系管理员或直接在数据库中修改。

### Q2: 如何修改密码？

A: 当前版本暂不支持修改密码功能，后续版本会添加。

### Q3: Token过期后怎么办？

A: Token过期后会自动跳转到登录页，重新登录即可。

### Q4: 可以同时登录多个账号吗？

A: 不可以，每次登录会覆盖之前的token。

### Q5: 如何查看所有用户？

A: 当前版本暂不支持用户管理功能，可以直接查询数据库。

---

## 后续功能规划

- [ ] 密码重置功能
- [ ] 修改密码功能
- [ ] 用户管理界面（管理员）
- [ ] 角色权限管理
- [ ] 登录日志
- [ ] 多设备登录管理
- [ ] 第三方登录（OAuth）

---

## 开发说明

### 添加新的受保护路由

```javascript
{
  path: '/new-page',
  component: NewPage,
  meta: { requiresAuth: true }  // 需要登录
}
```

### 在组件中获取用户信息

```javascript
const user = computed(() => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
})
```

### 调用需要认证的API

```javascript
// API会自动添加token到请求头
import { someApi } from '@/api'

const response = await someApi()
```

---

## 故障排除

### 问题1: 登录后立即跳转到登录页

**原因**: Token未正确保存

**解决**:
1. 检查浏览器localStorage
2. 清除浏览器缓存
3. 检查后端API是否正常

### 问题2: 注册失败

**原因**: 用户名或邮箱已存在

**解决**:
1. 更换用户名
2. 更换邮箱
3. 检查数据库是否有重复数据

### 问题3: 无法访问API

**原因**: 后端未启动或CORS配置问题

**解决**:
1. 确保后端API运行
2. 检查CORS配置
3. 查看浏览器控制台错误

---

## 总结

✅ 完整的用户认证系统
✅ 安全的密码存储
✅ 自动会话管理
✅ 友好的用户界面
✅ 完善的错误处理

**现在可以开始使用了！** 🎉
