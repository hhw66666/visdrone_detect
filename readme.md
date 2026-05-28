# 科大巡弋 - 智能航拍目标检测系统

基于 YOLOv8 的智能航拍目标检测系统，提供 Web 界面进行图片、视频和批量检测。

---

## 功能特性

- **图片检测**：支持 JPG、PNG、BMP 等格式
- **视频检测**：上传视频文件，自动逐帧检测
- **目标识别**：可识别 10 类目标（小汽车、摩托车、人群、行人、带篷三轮车、三轮车、自行车、卡车、面包车、公交车）
- **历史记录**：保存所有检测记录，随时查看
- **AI 客服**：小科助手随时解答疑问，支持天气查询、地点搜索等地图功能
- **聊天历史**：支持保存和管理对话记录

---

## 环境要求

- Python 3.9+ （推荐 Python 3.11）
- Windows / Linux / macOS

---

## 第一步：安装 Python

如果没有安装 Python，推荐到官网下载：

**下载地址**：https://www.python.org/downloads/

安装时记得勾选 **"Add Python to PATH"**（添加到环境变量）。

安装完成后，打开命令行验证：

```bash
python --version
```

---

## 第二步：安装依赖

进入项目目录，安装所需的 Python 包：

```bash
cd d:\visdrone_detect

pip install django ultralytics opencv-python pillow numpy
```

或者一行命令安装所有依赖：

```bash
pip install django==5.2.13 ultralytics opencv-python pillow numpy xmltodict
```

---

## 第三步：下载 YOLO 模型（如果还没有）

将训练好的模型文件（.pt）放到项目根目录的 `models/` 文件夹下。

默认配置使用 `models/v8-best.pt`。

可以在 `config.xml` 中修改模型路径：

```xml
<detection>
    <model_path>models/v8-best.pt</model_path>
</detection>
```

---

## 第四步：运行服务器

进入项目目录，运行：

```bash
cd d:\visdrone_detect

python manage.py runserver
```

看到以下输出说明启动成功：

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### 关闭服务器

在运行服务器的命令行窗口中按 `Ctrl+Break`（或 `Ctrl+C`）即可关闭。

或者在另一个命令行窗口中执行：

```bash
taskkill //F //IM python.exe
```

---

## 第五步：打开浏览器使用

在浏览器中打开：**http://127.0.0.1:8000/**

首页展示了系统介绍、功能说明和联系方式。点击右上角"登录"按钮或页面中央的"立即体验"按钮，弹出登录框进行登录。

首次使用需要注册账号，然后登录即可使用全部功能。

---

## 页面说明

| 页面 | URL | 说明 |
|------|-----|------|
| 首页/登录 | `/` | 展示系统介绍，点击登录后弹出登录框 |
| 登录后首页 | `/home/` | 个人中心，显示检测统计和最近记录 |
| 检测页面 | `/detect/` | 上传图片或视频进行目标检测 |
| 历史记录 | `/history/` | 查看所有检测历史 |
| 小科客服 | `/xiaoyu/` | AI 客服聊天界面 |
| 聊天记录 | `/chat-history/` | 管理保存的对话记录 |
| 个人资料 | `/profile/` | 修改头像和个人信息 |

---

## 项目结构

```
d:\visdrone_detect\
├── manage.py                 # Django 入口，运行服务器
├── config.xml                # 配置文件（模型路径、API 配置等）
│
├── detect_system/            # Django 项目配置
│   ├── settings.py           # Django 设置
│   ├── urls.py               # 路由配置
│   └── config_loader.py      # 配置文件加载
│
├── detection/                 # Django 应用
│   ├── views.py              # 视图函数
│   ├── models.py             # 数据模型
│   └── templates/             # HTML 模板
│       └── detection/
│           ├── home.html     # 登录后首页
│           ├── login.html     # 登录页面（含弹窗登录）
│           ├── detect.html    # 检测页面
│           ├── history.html   # 历史记录
│           ├── profile.html   # 个人资料
│           ├── xiaoyu.html    # 小科客服聊天页面
│           └── chat_history.html  # 聊天记录管理
│
├── ai_services/              # AI 服务模块
│   ├── agents/               # Agent 模块
│   │   ├── base.py          # Agent 基类
│   │   └── xiaoyu.py        # 小科客服实现
│   ├── tools/                # 工具模块
│   │   ├── setup.py         # 工具注册
│   │   └── predefined.py    # 预定义工具工厂
│   ├── mcp/                  # MCP 工具模块
│   │   └── modelscope_client.py  # ModelScope MCP 连接器
│   └── prompts/              # AI 提示词
│       └── xiaoyu_prompts.py
│
└── static/                   # 静态资源
    ├── css/base.css          # 样式文件
    └── js/common.js          # JavaScript 公共函数
```

---

## 常见问题

### 1. 启动报错 "ModuleNotFoundError"

说明有 Python 包没装全，运行：

```bash
pip install django ultralytics opencv-python pillow numpy xmltodict
```

### 2. 页面显示异常或 CSS 没有加载

确保在项目根目录运行 `python manage.py runserver`。

### 3. 检测没有结果

检查 `config.xml` 中的模型路径是否正确，以及模型文件是否存在。

### 4. 小科客服无法回复

检查 `config.xml` 中的 MiniMax API 配置是否正确。

### 5. 小科无法查询天气/地图

检查 `config.xml` 中的 ModelScope MCP 配置是否正确。

---

## 后续扩展

项目采用模块化设计，方便扩展：

- **接入 RAG**：在 `config.xml` 中启用 RAG 配置，添加知识库
- **接入 MCP**：在 `ai_services/mcp/modelscope_client.py` 中注册新的工具
- **接入 LangChain**：在 `ai_services/chains/` 中扩展链式调用

---

## 技术栈

- **后端**：Django 5.2
- **前端**：HTML + CSS + JavaScript
- **AI 模型**：YOLOv8 (Ultralytics)
- **客服 API**：MiniMax M2.7
- **地图工具**：ModelScope MCP (高德地图/天气)



github.com:hhw66666