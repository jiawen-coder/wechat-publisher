# 📝 微信公众号文章发布助手

一键将 Markdown、文字、语音、文件转换为精美的微信公众号文章，并发布到草稿箱。

## ✨ 功能特点

- 🎨 **15+ 排版风格** - 商务、科技、文艺、极简等多种预设风格
- 🤖 **AI 自定义风格** - 描述你想要的风格，AI 帮你生成
- 🖼️ **AI 封面生成** - 根据文章内容智能生成封面图
- 🎤 **语音输入** - 支持语音转文字，边说边写
- 📁 **多格式支持** - txt、md、docx、pdf 文件上传
- 📱 **响应式设计** - 电脑、手机完美适配
- 🚀 **一键发布** - 直接发布到微信公众号草稿箱

## 📂 项目结构

```
gongzhonghao/
├── app.py                  # 🚀 主应用入口
├── requirements.txt        # 📦 依赖包
├── backend/                # 🔧 后端代码
│   ├── __init__.py
│   ├── config.py           # ⚙️ 配置文件（API Key、主题等）
│   ├── api/                # 🌐 API 路由
│   │   └── __init__.py
│   ├── services/           # 💼 业务服务
│   │   ├── __init__.py
│   │   ├── converter.py    # Markdown 转换器
│   │   ├── cover_generator.py  # 封面图生成器
│   │   ├── image_uploader.py   # 图片上传器
│   │   └── wechat_publisher.py # 微信发布器
│   └── utils/              # 🛠️ 工具函数
│       └── __init__.py
├── frontend/               # 🎨 前端代码
│   ├── templates/          # 📄 HTML 模板
│   │   └── index.html
│   └── static/             # 📁 静态资源
├── data/                   # 💾 数据文件
│   ├── user_config.json    # 用户配置
│   ├── temp/               # 临时文件（封面图等）
│   └── uploads/            # 上传文件
├── docs/                   # 📚 文档
│   ├── example.md          # 示例文章
│   └── CHANGELOG.md        # 更新日志
└── vercel.json             # ☁️ Vercel 部署配置
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

### 3. 访问应用

打开浏览器访问 http://localhost:5000

### 4. 配置 API

点击右上角 ⚙️ 设置，配置以下 API Key：

| 配置项 | 用途 | 获取方式 |
|--------|------|----------|
| 微信 AppID | 发布文章 | [微信公众平台](https://mp.weixin.qq.com/) |
| 微信 AppSecret | 发布文章 | 微信公众平台后台 |
| ImgBB API Key | 图片上传 | [ImgBB](https://api.imgbb.com/) |
| Poe API Key | 封面图生成 | [Poe](https://poe.com/api_key) |
| 心流 API Key | AI 对话 | [心流](https://platform.iflow.cn/) |

## 📋 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/config` | GET/POST | 获取/保存配置 |
| `/api/parse` | POST | 解析内容元数据 |
| `/api/convert` | POST | Markdown 转 HTML |
| `/api/convert-custom` | POST | 自定义风格转换 |
| `/api/themes` | GET | 获取主题列表 |
| `/api/generate-cover` | POST | 生成封面图 |
| `/api/publish` | POST | 发布到草稿箱 |
| `/api/upload` | POST | 上传文件 |
| `/api/chat` | POST | AI 对话 |
| `/api/speech-to-text` | POST | 语音转文字 |

## ☁️ 部署

### Vercel 部署

1. Fork 本项目到 GitHub
2. 登录 [Vercel](https://vercel.com/)
3. Import 项目
4. 部署完成

### 注意事项

- 微信公众号 API 需要配置 **IP 白名单**
- Vercel 部署后，需要将 Vercel 服务器 IP 加入白名单
- 建议使用服务号（订阅号功能受限）

## 📝 更新日志

查看 [CHANGELOG.md](docs/CHANGELOG.md)

## 👨‍💻 开发者

联系开发者：**jeveinzhai**

## 📄 License

MIT License
