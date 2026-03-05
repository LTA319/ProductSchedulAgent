# 生产排程智能体

基于约束规划的自动化生产排程系统，用于解决机加工车间的生产计划优化问题。

## 功能特性

- 📊 **数据导入**：支持从 Excel 文件导入订单、工艺路线和设备数据
- 🧮 **智能排程**：使用 Google OR-Tools CP-SAT 求解器进行约束优化
- 📈 **可视化展示**：通过甘特图直观展示排程结果
- 📉 **指标分析**：计算设备利用率、交期达成率、瓶颈设备等关键指标
- 🌐 **Web 界面**：基于 Streamlit 的友好交互界面
- 💾 **结果导出**：支持导出排程结果为 Excel 或 CSV 格式

## 项目结构

```
ProductSchedulAgent/
├── data_layer/          # 数据层：数据解析、验证和模型
│   ├── __init__.py
│   ├── models.py        # 数据模型定义
│   ├── parser.py        # Excel 数据解析器
│   └── validator.py     # 数据验证器
├── business_logic/      # 业务逻辑层：排程算法和分析
│   ├── __init__.py
│   ├── scheduler.py     # 排程引擎
│   ├── metrics.py       # 指标计算器
│   └── visualizer.py    # 可视化生成器
├── ui/                  # UI层：Streamlit Web界面
│   ├── __init__.py
│   └── app.py           # 主应用程序
├── tests/               # 测试模块
│   ├── __init__.py
│   ├── test_parser.py   # 数据解析测试
│   ├── test_scheduler.py # 排程算法测试
│   └── property_tests/  # 属性测试
├── docs/                # 文档和示例数据
├── .kiro/               # Kiro 规范文档
│   └── specs/
│       └── production-scheduling-agent/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
├── requirements.txt     # Python 依赖包
└── README.md           # 项目说明文档
```

## 技术栈

- **Python 3.8+**：主要开发语言
- **OR-Tools**：Google 开源的约束规划和优化库
- **Streamlit**：快速构建 Web 界面的 Python 框架
- **Pandas**：数据处理和 Excel 文件读写
- **Plotly**：交互式图表可视化
- **Hypothesis**：基于属性的测试框架
- **Pytest**：单元测试框架

## 安装说明

### 1. 克隆项目

```bash
git clone <repository-url>
cd ProductSchedulAgent
```

### 2. 创建虚拟环境

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用指南

### 启动 Web 界面

```bash
streamlit run ui/app.py
```

浏览器会自动打开 `http://localhost:8501`

### 数据格式要求

#### 订单数据 (orders.xlsx)

| 订单号 | 产品编码 | 数量 | 交期 | 优先级 |
|--------|----------|------|------|--------|
| ORD001 | PROD001  | 10   | 2026-03-15 | 5 |

#### 工艺路线数据 (processes.xlsx)

| 产品编码 | 工序编号 | 工序名称 | 工序顺序 | 标准工时(h) | 所需设备类型 | 前置工序 |
|----------|----------|----------|----------|-------------|--------------|----------|
| PROD001  | OP001    | 粗加工   | 1        | 2.0         | 车床         | -        |

#### 设备数据 (equipment.xlsx)

| 设备编号 | 设备类型 | 可用开始时间 | 可用结束时间 | 产能上限(h/天) | 换产时间(h) |
|----------|----------|--------------|--------------|----------------|-------------|
| EQ001    | 车床     | 2026-03-01 08:00 | 2026-03-31 18:00 | 8 | 0.5 |

### 使用流程

1. **上传数据文件**：在侧边栏上传订单、工艺路线和设备数据文件
2. **数据预览**：系统会自动解析并显示数据预览
3. **开始排程**：点击"开始排程"按钮执行优化计算
4. **查看结果**：
   - 甘特图：查看详细的时间安排
   - 指标看板：查看关键性能指标
   - 详细数据：查看排程结果表格
5. **导出结果**：下载排程结果为 Excel 或 CSV 格式

## 运行测试

### 运行所有测试

```bash
pytest tests/
```

### 运行属性测试

```bash
pytest tests/property_tests/ -v
```

### 查看测试覆盖率

```bash
pytest --cov=data_layer --cov=business_logic --cov=ui tests/
```

## 开发指南

### 添加新功能

1. 在相应的层级目录中创建新模块
2. 遵循现有的代码结构和命名规范
3. 编写单元测试和属性测试
4. 更新文档

### 代码规范

- 使用 Python 类型注解
- 遵循 PEP 8 代码风格
- 为所有公共函数编写 docstring
- 保持函数简洁，单一职责

## 约束和限制

- 当前版本不支持动态插单和实时调整
- 求解器对大规模问题（50+ 订单）可能需要较长时间
- 不支持班次和日历约束
- 不考虑物料齐套和人员技能约束

## 扩展方向

- 动态排程和实时调整
- 多目标优化（交期、成本、利用率）
- 高级约束（物料、人员、班次）
- 智能推荐和异常预警
- 历史数据分析和参数优化

## 许可证

[待定]

## 联系方式

[待定]

## 致谢

本项目使用了以下开源项目：
- [Google OR-Tools](https://developers.google.com/optimization)
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/)
