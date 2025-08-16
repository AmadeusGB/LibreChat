# LibreChat 品牌定制指南

## 🎯 修改应用标题

### 📋 步骤总结

我们刚刚成功将 LibreChat 的标题从 "LibreChat v0.8.0-rc2 - Every AI for Everyone" 改为 "Corust.ai"。

### 🔧 具体操作步骤

#### 1. 修改环境变量
```bash
# 在 .env 文件中修改 APP_TITLE
sed -i '' 's/APP_TITLE=LibreChat/APP_TITLE=Corust.ai/' .env
```

#### 2. 验证修改
```bash
grep "APP_TITLE" .env
# 输出: APP_TITLE=Corust.ai
```

#### 3. 重启服务
```bash
# 停止当前服务
pkill -f "node api/server/index.js"

# 重新启动
npm run backend
```

#### 4. 验证生效
```bash
# 检查API配置
curl -s http://localhost:3080/api/config | jq '.appTitle'
# 输出: "Corust.ai"
```

### 🎨 效果展示

修改后的效果：
- ✅ **页面标题**: 浏览器标签页显示 "Corust.ai"
- ✅ **登录页面**: 显示 "Corust.ai" 而不是 "LibreChat"
- ✅ **应用内标题**: 所有引用应用名称的地方都会显示 "Corust.ai"

### 📁 相关文件说明

#### 后端配置文件
- **`.env`** - 环境变量配置，包含 `APP_TITLE`
- **`api/server/routes/config.js`** - 读取 APP_TITLE 并返回给前端

#### 前端使用位置
- **`client/src/routes/Layouts/Startup.tsx`** - 设置页面标题
- **`client/src/hooks/Config/useAppStartup.ts`** - 应用启动时的标题设置
- **`client/src/components/Auth/AuthLayout.tsx`** - 登录页面的logo alt文本

### 🚀 其他品牌定制选项

#### 修改Logo
```bash
# 替换 logo 文件
cp your-logo.svg client/public/assets/logo.svg
```

#### 修改Favicon
```bash
# 替换 favicon 文件
cp your-favicon.ico client/public/favicon.ico
```

#### 修改主题色彩
编辑 `client/src/index.css` 或相关的 Tailwind 配置文件。

### 🔄 完整的品牌定制流程

1. **准备资源**
   - 新的应用名称
   - Logo文件 (SVG格式推荐)
   - Favicon文件
   - 品牌色彩方案

2. **修改配置**
   ```bash
   # 修改应用标题
   sed -i '' 's/APP_TITLE=LibreChat/APP_TITLE=YourBrandName/' .env
   
   # 替换logo
   cp your-logo.svg client/public/assets/logo.svg
   
   # 替换favicon
   cp your-favicon.ico client/public/favicon.ico
   ```

3. **重启服务**
   ```bash
   pkill -f "node api/server/index.js"
   npm run backend
   ```

4. **验证效果**
   - 访问 http://localhost:3080/login
   - 检查浏览器标签页标题
   - 确认logo和favicon显示正确

### 💡 注意事项

1. **环境变量优先级**: `APP_TITLE` 环境变量会覆盖代码中的默认值
2. **缓存清理**: 修改后建议清除浏览器缓存以确保看到最新效果
3. **生产部署**: 在生产环境中也需要设置相同的环境变量

### 🎯 下一步可以定制的内容

- 🎨 **主题色彩** - 修改CSS变量和Tailwind配置
- 📝 **文案内容** - 修改多语言文件
- 🖼️ **图标资源** - 替换各种尺寸的图标文件
- 🔗 **链接地址** - 修改帮助文档、条款等链接

---

*通过这个简单的修改，我们成功将 LibreChat 品牌化为 Corust.ai！*