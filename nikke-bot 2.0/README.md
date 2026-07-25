# NIKKE 装备管理机器人 v2.1

基于 NoneBot2 的 NIKKE（胜利女神：妮姬）T10 装备词条管理 QQ 机器人。

## 功能

- 📸 上传装备截图 → OCR 自动识别 → 保存装备
- 🔍 按角色/类型/部位/词条多维度查询装备
- 📊 装备评分与词条阶级计算
- 🔒 装备锁定保护，防止误删
- 👥 群共享装备库
- 📥 Excel 导出
- 🖼 装备卡片图片渲染

## 技术栈

- Python 3.12+
- NoneBot2 + OneBot v11
- SQLite + aiosqlite
- Pydantic v2
- PaddleOCR / DeepSeek Vision
- Pillow 图片渲染
- Repository + Service 分层架构

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

可选 OCR 引擎：

```bash
# 本地 PaddleOCR（推荐）
pip install paddleocr paddlepaddle

# DeepSeek Vision 兜底
pip install openai
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入实际配置
```

必填配置：

| 变量 | 说明 |
|------|------|
| `BOT_SUPERUSERS` | 管理员 QQ 号列表 |
| `OCR_ENGINE` | OCR 引擎: paddle / deepseek / auto |

可选（使用 DeepSeek 时需要）：

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | API 地址 |
| `DEEPSEEK_MODEL` | 模型名称 |

### 3. 启动

```bash
python bot.py
```

### 4. 连接 QQ

使用 Lagrange / NapCat 等 OneBot v11 客户端连接。

## 命令列表

| 命令 | 说明 |
|------|------|
| `/装备录入` | 发送装备截图 + 此命令录入装备 |
| `/我的装备 [页]` | 查看已录入装备 |
| `/查询词条 <名>` | 按词条搜索装备 |
| `/锁定装备 <ID>` | 锁定装备防止误删 |
| `/解锁装备 <ID>` | 解除锁定 |
| `/删除装备 <ID>` | 删除装备 |
| `/装备详情 <ID>` | 查看装备详情 |
| `/装备统计` | 个人装备统计 |
| `/导出装备` | 导出到 Excel |
| `/红莲装备` | 查询指定角色装备 |
| `/帮助` | 显示帮助 |

## 项目结构

```
nikke-bot 2.0/
├── bot.py                  # 启动入口
├── data/                   # 静态配置（角色库、模板、阶级、别名）
├── src/
│   ├── config.py           # 全局配置管理
│   ├── bot/plugins/        # NoneBot Handler 插件
│   ├── models/             # Pydantic 数据模型
│   ├── database/           # 数据库层（连接、迁移、Repository）
│   ├── services/           # 业务服务层
│   ├── ocr/                # OCR 引擎（可替换）
│   ├── renderer/           # 图片渲染器
│   ├── state/              # 会话状态管理
│   └── utils/              # 工具函数
├── tests/                  # 测试
├── assets/                 # 字体等静态资源
└── database/               # SQLite 数据库文件
```

## 运行测试

```bash
pytest tests/ -v
```

## 数据文件说明

| 文件 | 说明 |
|------|------|
| `data/characters.json` | 角色库（名称、别名、属性） |
| `data/equipment_templates.json` | 装备模板（60 个模板） |
| `data/tier.json` | 词条阶级定义（数值→阶级映射） |
| `data/alias.json` | OCR 别名映射（识别文本→规范名称） |
| `data/affix_names.json` | 合法词条名称列表 |
