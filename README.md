
课程设计选题：题目二-校园二手交易平台

# 校园拾光集（Campus Loop Market）

SK3017《Python Web企业级项目开发》课程设计。项目使用 Flask + MySQL + Jinja2 实现校园二手交易平台，覆盖商品发布、浏览、搜索、分页、收藏、留言与卖家回复、个人中心管理。

> GitHub 源码仓库：https://github.com/Zonyon-Zky/sk3017-campus-market

## 功能清单

- 商品发布：标题、描述、分类、价格、1-3 张图片
- 图片校验：仅 JPG/JPEG/PNG，单张 ≤2MB，UUID 重命名保存
- 首页：最新商品、分类筛选、标题/描述模糊搜索、每页 10 条分页
- 商品详情：多图切换、卖家信息、收藏、留言板
- 收藏：判重并友好提示；个人中心可查看收藏
- 留言：登录用户留言，商品卖家回复
- 个人中心：我发布的、我的收藏、我收到的留言
- 商品状态：在售 / 已售 / 已下架，卖家可切换或删除
- 搜索特殊字符：`'` 通过参数化查询处理，`%`、`_` 通过 `LIKE ... ESCAPE '='` 按字面匹配

## 技术栈

- Python 3.11+（本次运行环境 Python 3.14）
- Flask 3.1
- PyMySQL
- MySQL 8
- Jinja2 + 原生 HTML/CSS/JavaScript
- pytest（10 个 HTTP 层测试）

## 目录结构

```text
campus-market/
├── app/
│   ├── auth.py
│   ├── market.py
│   ├── db.py
│   ├── templates/
│   └── static/
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── init.sql
├── docs/
│   ├── DEVELOPMENT_LOG.md
│   ├── DEBUG_LOG.md
│   ├── AI协作记录.md
│   ├── 课程设计报告.docx
│   └── 课程设计报告.pdf
├── screenshots/
├── tests/
├── requirements.txt
├── .env.example
└── run.py
```

## 快速运行

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

初始化数据库：

```bash
mysql -u root -p < database/init.sql
```

也可以使用 Navicat / MySQL Workbench 执行 `database/init.sql`。

复制 `.env.example` 为 `.env`：

```text
FLASK_SECRET_KEY=change-me
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=campus_market
```

启动：

```bash
python run.py
```

访问 `http://127.0.0.1:5000`。

## 测试账号

| 用户名 | 密码 | 用途 |
|---|---|---|
| demo | 123456 | 卖家账号，有多件发布商品与留言 |
| buyer | 123456 | 买家账号，可收藏、留言、发布商品 |

## 测试数据

`database/seed.sql` 由项目自行造数，包含：

- 2 个测试用户
- 5 个商品分类
- 24 件商品，覆盖 5 个分类、3 种状态
- 12 张本地商品示意图
- 收藏记录与带卖家回复的留言
- 含 `100%`、`O'Reilly` 等特殊搜索样例

## 测试

测试使用独立数据库 `campus_market_test`，请先确保 MySQL 可连接：

```bash
pytest -q
```

当前共 10 个测试，覆盖：

- 首页分页与 10 条限制
- `%`、`'` 特殊字符搜索
- 非法页码、分类与过长关键词
- 注册、登录、未登录访问
- 图片缺失、超大图片、错误格式
- 商品发布与图片落盘
- 重复收藏判重
- 留言与卖家回复权限
- 商品状态修改与删除权限
- 个人中心三类数据

## 工程纪律与精简策略

本项目应用了两个外部 skill 的核心约束：

- `mattpocock/skills` 的 `tdd`：先固定 HTTP seam，再按核心业务切片测试；测试验证外部行为，不依赖内部实现。
- `DietrichGebert/ponytail`：不引入 ORM、前端框架或额外中间件；使用标准库/PyMySQL/原生模板完成必要功能；只保留任务真实需要的抽象。

## 主要页面

- `/`：市场首页
- `/products/<id>`：商品详情与留言
- `/publish`：发布商品
- `/profile?tab=published|favorites|messages`：个人中心
- `/auth/login`、`/auth/register`：账号入口
