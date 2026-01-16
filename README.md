# 多模型协同的PPT智能优化与自动生成网页系统

## 项目简介

这是一个基于多个大模型协同工作的智能PPT优化系统,实现了从PPT上传、多模型并行分析、跨模型迭代修正到自动生成优化后PPT的完整流程。

### 核心功能

- **PPT智能解析**: 自动解析PPT内容、版式、样式等信息
- **多模型协同**: 集成讯飞星火、文心一言、通义千问、腾讯混元四大模型
- **迭代修正机制**: 模型间差异化分工,交叉修正,确保优化建议的准确性
- **冲突智能调和**: 自动检测并调和模型建议冲突,支持人工干预
- **自动生成PPT**: 基于最终优化方案自动生成新的PPT文件

### 技术架构

- **前端**: Vue3 + Element Plus
- **后端**: Python + FastAPI
- **PPT处理**: python-pptx
- **模型对接**: 异步并行调用多个大模型API

## 项目结构

```
ppt-ai-optimizer/
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── components/   # Vue组件
│   │   ├── views/        # 页面视图
│   │   ├── api/          # API接口
│   │   └── utils/        # 工具函数
│   └── package.json
├── backend/              # 后端代码
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务逻辑
│   │   │   ├── ppt_parser.py        # PPT解析器
│   │   │   ├── model_engine.py      # 模型调用引擎
│   │   │   ├── iteration_corrector.py # 迭代修正器
│   │   │   └── ppt_generator.py     # PPT生成器
│   │   └── utils/        # 工具函数
│   ├── config/           # 配置文件
│   ├── logs/             # 日志目录
│   ├── uploads/          # 上传文件目录
│   ├── requirements.txt  # Python依赖
│   └── main.py           # 应用入口
├── docs/                 # 文档
│   └── 需求文档.md
├── .gitignore
└── README.md
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- 4个大模型的API Key

### 后端安装与启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置API Key (复制配置模板并填写)
cp config/config.example.yaml config/config.yaml
# 编辑 config/config.yaml 填写各模型的API Key

# 启动后端服务
python main.py
```

### 前端安装与启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## API Key 申请指南

### 1. 讯飞星火PPT智能助手
- 官网: https://www.xfyun.cn
- 文档: https://www.xfyun.cn/doc/spark/ppt-assistant.html
- 申请流程: 注册账号 → 创建应用 → 获取 APPID、APIKey、APISecret

### 2. 百度文心一言PPT优化模块
- 官网: https://yiyan.baidu.com
- 文档: https://yiyan.baidu.com/developer/docs/ppt-optimize
- 申请流程: 登录百度账号 → 开通服务 → 获取 API Key 和 Secret Key

### 3. 阿里云通义千问PPT生成器
- 官网: https://www.aliyun.com/product/dashscope
- 文档: https://help.aliyun.com/document_detail/2511236.html
- 申请流程: 登录阿里云 → 开通服务 → 创建 API Key

### 4. 腾讯混元PPT智能分析模型
- 官网: https://cloud.tencent.com/product/hunyuan
- 文档: https://cloud.tencent.com/document/product/1729/95224
- 申请流程: 登录腾讯云 → 开通混元服务 → 获取 SecretId 和 SecretKey

## 核心功能说明

### 1. PPT解析
系统使用 `python-pptx` 库解析上传的PPT文件,提取:
- 每页幻灯片的版式类型
- 文本内容及样式
- 图片和图表信息
- 配色方案

### 2. 多模型并行调用
系统会同时调用4个大模型,各模型侧重点:
- **讯飞星火**: 场景化适配、行业定制
- **文心一言**: 排版设计、配色优化
- **通义千问**: 内容逻辑、图表可视化
- **腾讯混元**: 多建议融合、冲突调和

### 3. 迭代修正流程
```
讯飞星火(全维度建议)
  ↓
文心一言(修正layout/color)
  ↓
通义千问(修正logic/chart)
  ↓
腾讯混元(融合所有建议,调和冲突)
  ↓
最终优化方案
```

### 4. 冲突检测与调和
- 自动检测模型建议冲突(同一位置不同建议)
- 冲突率 < 5%: 自动调和
- 冲突率 5%-10%: 模型仲裁
- 冲突率 > 10%: 提示用户手动选择

## 配置说明

配置文件位于 `backend/config/config.yaml`:

```yaml
# 模型配置
models:
  xunfei:
    enabled: true
    api_key: "your_api_key"
    timeout: 30

  wenxin:
    enabled: true
    api_key: "your_api_key"
    secret_key: "your_secret_key"
    timeout: 30

  qianwen:
    enabled: true
    api_key: "your_api_key"
    timeout: 30

  hunyuan:
    enabled: true
    secret_id: "your_secret_id"
    secret_key: "your_secret_key"
    timeout: 30

# 迭代修正配置
iteration:
  max_rounds: 2              # 最大迭代轮次
  conflict_threshold: 0.05   # 冲突率阈值(5%)
  manual_threshold: 0.10     # 人工干预阈值(10%)

# 上传配置
upload:
  max_size: 50  # MB
  allowed_extensions: [".pptx"]
```

## 扩展指南

### 新增模型

1. 在 `backend/app/services/model_engine.py` 中新增模型接口类
2. 实现标准化输入输出转换
3. 在配置文件中添加模型配置
4. 更新迭代修正流程中的模型角色分配

详见: `docs/扩展指南.md`

## 测试

```bash
# 后端单元测试
cd backend
pytest tests/

# 前端测试
cd frontend
npm run test

# 端到端测试
npm run test:e2e
```

## 日志说明

系统日志存储在 `backend/logs/` 目录:
- `app.log`: 应用主日志
- `model_calls.log`: 模型调用日志
- `iteration.log`: 迭代修正日志
- `conflicts.log`: 冲突检测与调和日志

每个日志都关联 `ppt_id`,便于追溯完整处理流程。

## 常见问题

### Q: 某个模型调用失败怎么办?
A: 系统有自动降级机制,会跳过失败的模型继续使用其他模型完成分析。

### Q: 如何调整迭代轮次?
A: 修改 `config/config.yaml` 中的 `iteration.max_rounds` 参数。

### Q: 支持哪些PPT格式?
A: 目前仅支持 .pptx 格式(Office 2007及以上版本)。

## 许可证

MIT License

## 联系方式

- 项目作者: lilywang
- 邮箱: lilywang@lexin.com
- GitHub: https://github.com/lilywang-lx

## 致谢

感谢讯飞星火、文心一言、通义千问、腾讯混元提供的大模型API支持。
