# 🚀 LibreChat (Corust.ai) 部署指南

## 🎉 标题修改完成！

我已经成功将应用标题从 "LibreChat" 修改为 "Corust.ai"：

### ✅ 修改内容
1. **环境变量**: `.env` 文件中 `APP_TITLE=Corust.ai`
2. **页面标题**: 浏览器标签页现在显示 "Corust.ai"
3. **页面底部**: Footer 现在显示 "Corust.ai v0.8.0-rc2"
4. **Logo Alt文本**: 已使用动态配置

### 🔄 修改的文件
- `.env` - 环境变量配置
- `client/src/components/Chat/Footer.tsx` - 页面底部文本

---

## 🏗️ 当前运行方式分析

### 当前开发环境
你目前使用的是**开发模式**运行：

```bash
# 后端服务
npm run backend  # 运行在 http://localhost:3080

# 前端服务  
npm run frontend # 开发服务器 (Vite)
```

### 架构组成
- **前端**: React + Vite (开发服务器)
- **后端**: Node.js + Express
- **数据库**: MongoDB (本地或Docker)
- **搜索**: MeiliSearch
- **文件存储**: 本地文件系统
- **向量数据库**: PostgreSQL + pgvector (RAG功能)

---

## 🌐 生产部署方案

### 方案1: Docker Compose (推荐 ⭐)

**优点**: 
- ✅ 简单易用，一键部署
- ✅ 包含所有依赖服务
- ✅ 适合中小型部署
- ✅ 支持自动重启和健康检查

**部署步骤**:
```bash
# 1. 克隆项目
git clone https://github.com/danny-avila/LibreChat.git
cd LibreChat

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要的配置

# 3. 使用 Docker Compose 部署
docker-compose up -d

# 或使用生产配置
docker-compose -f deploy-compose.yml up -d
```

**适用场景**: 
- VPS/云服务器部署
- 内网企业部署
- 开发/测试环境

---

### 方案2: Kubernetes + Helm

**优点**:
- ✅ 企业级容器编排
- ✅ 自动扩缩容
- ✅ 高可用性
- ✅ 滚动更新

**部署步骤**:
```bash
# 1. 添加 Helm 仓库
helm repo add librechat https://danny-avila.github.io/LibreChat/

# 2. 安装 LibreChat
helm install librechat librechat/librechat \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=your-domain.com

# 3. 配置 Ingress 和 TLS
```

**适用场景**:
- 大型企业部署
- 需要高可用的生产环境
- 多租户环境

---

### 方案3: 传统服务器部署

**优点**:
- ✅ 完全控制
- ✅ 性能最优
- ✅ 自定义程度高

**部署步骤**:
```bash
# 1. 安装依赖
npm install

# 2. 构建前端
npm run frontend:build

# 3. 启动生产服务
npm run backend:prod

# 4. 配置 Nginx 反向代理
```

---

## ❌ Vercel 不适用的原因

### 为什么 Vercel 不行？

1. **🚫 后端限制**: Vercel 主要支持 Serverless Functions，不支持长时间运行的 Node.js 服务器
2. **🚫 数据库**: LibreChat 需要 MongoDB、MeiliSearch、PostgreSQL，Vercel 无法提供
3. **🚫 文件存储**: 需要持久化文件存储，Vercel 是无状态的
4. **🚫 WebSocket**: 需要实时通信支持
5. **🚫 复杂架构**: LibreChat 是全栈应用，不是静态站点

---

## 🌟 推荐的云部署方案

### 1. Railway (最简单 ⭐⭐⭐)

**为什么推荐**:
- ✅ 支持 Docker 部署
- ✅ 自动 HTTPS
- ✅ 简单的环境变量管理
- ✅ 内置数据库服务

**部署步骤**:
```bash
# 1. 连接 GitHub 仓库到 Railway
# 2. 选择 Docker 部署
# 3. 添加 MongoDB 服务
# 4. 配置环境变量
```

**费用**: ~$5-20/月

---

### 2. DigitalOcean App Platform

**优点**:
- ✅ 支持 Docker Compose
- ✅ 托管数据库
- ✅ 自动扩缩容
- ✅ 简单配置

**部署方式**:
- 使用 Docker Compose 配置
- 连接托管 MongoDB
- 配置域名和 SSL

**费用**: ~$12-25/月

---

### 3. AWS/GCP/Azure (企业级)

**AWS 方案**:
- **ECS Fargate**: 容器化部署
- **RDS**: MongoDB Atlas 或 DocumentDB
- **S3**: 文件存储
- **CloudFront**: CDN 加速

**GCP 方案**:
- **Cloud Run**: 容器部署
- **MongoDB Atlas**: 托管数据库
- **Cloud Storage**: 文件存储

**费用**: ~$30-100+/月

---

### 4. VPS 自建 (性价比最高 ⭐⭐)

**推荐服务商**:
- **Hetzner**: €4.15/月 (2vCPU, 4GB RAM)
- **Vultr**: $6/月 (1vCPU, 2GB RAM)
- **DigitalOcean**: $12/月 (2vCPU, 2GB RAM)

**部署方式**:
```bash
# 1. 购买 VPS (推荐 Ubuntu 22.04)
# 2. 安装 Docker 和 Docker Compose
# 3. 克隆项目并配置
# 4. 使用 Docker Compose 部署
# 5. 配置 Nginx 和 SSL (Let's Encrypt)
```

---

## 🛠️ 快速部署脚本

我为你创建了一个一键部署脚本：

```bash
#!/bin/bash
# 一键部署 Corust.ai 到 VPS

# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. 安装 Docker Compose
sudo apt install docker-compose-plugin -y

# 4. 克隆项目
git clone https://github.com/danny-avila/LibreChat.git
cd LibreChat

# 5. 配置环境变量
cp .env.example .env
sed -i 's/APP_TITLE=LibreChat/APP_TITLE=Corust.ai/' .env

# 6. 启动服务
sudo docker compose -f deploy-compose.yml up -d

# 7. 配置 Nginx (可选)
echo "部署完成！访问 http://your-server-ip:3080"
```

---

## 📊 方案对比

| 方案 | 难度 | 费用/月 | 性能 | 可控性 | 推荐度 |
|------|------|---------|------|--------|--------|
| Railway | ⭐ | $5-20 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| VPS自建 | ⭐⭐ | $4-12 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| DigitalOcean | ⭐⭐ | $12-25 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| AWS/GCP | ⭐⭐⭐ | $30+ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Kubernetes | ⭐⭐⭐⭐ | $50+ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## 🎯 我的建议

对于你的 Corust.ai 项目，我推荐：

1. **开发/测试**: 继续使用当前的 `npm run` 方式
2. **小规模生产**: Railway 或 VPS + Docker Compose
3. **企业级**: AWS ECS + RDS + S3

需要我帮你设置具体的部署方案吗？