# 设计文档

## 概述

生产排程智能体是一个基于约束规划的自动化排程系统，采用 Python + OR-Tools + Streamlit 技术栈实现。系统通过读取 Excel 格式的生产数据，使用 Google OR-Tools 的 CP-SAT 求解器进行约束优化，生成最优排程方案，并通过 Streamlit Web 界面提供交互式可视化展示。

核心设计理念：
- **最小可用原型**：优先实现核心排程功能，快速验证可行性
- **模块化架构**：数据层、算法层、展示层分离，便于维护和扩展
- **约束驱动**：基于真实生产约束（工艺顺序、设备互斥、时间窗口）进行优化
- **可视化优先**：通过甘特图和指标看板直观展示排程结果

## 架构

系统采用三层架构设计：

```
┌─────────────────────────────────────────┐
│         展示层 (Streamlit UI)            │
│  - 文件上传                              │
│  - 数据预览                              │
│  - 排程触发                              │
│  - 甘特图展示                            │
│  - 指标看板                              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         业务逻辑层                        │
│  - 排程引擎 (Scheduler)                  │
│  - 可视化生成器 (Visualizer)             │
│  - 指标计算器 (Metrics Calculator)       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         数据层                           │
│  - 数据解析器 (Data Parser)              │
│  - 数据验证器 (Data Validator)           │
│  - 数据模型 (Data Models)                │
└─────────────────────────────────────────┘
```

### 技术栈

- **Python 3.8+**：主要开发语言
- **OR-Tools**：Google 开源的约束规划和优化库，用于排程求解
- **Streamlit**：快速构建 Web 界面的 Python 框架
- **Pandas**：数据处理和 Excel 文件读写
- **Plotly/Matplotlib**：甘特图和图表可视化
- **openpyxl**：Excel 文件解析

## 组件和接口

### 1. 数据层组件

#### DataParser（数据解析器）
负责从 Excel 文件中读取和解析生产数据。

```python
class DataParser:
    def parse_orders(file_path: str) -> List[Order]
    def parse_processes(file_path: str) -> List[Process]
    def parse_equipment(file_path: str) -> List[Equipment]
```

**输入**：Excel 文件路径
**输出**：结构化的数据模型对象列表
**职责**：
- 读取 Excel 文件
- 提取关键字段
- 转换为内部数据模型

#### DataValidator（数据验证器）
验证输入数据的完整性和一致性。

```python
class DataValidator:
    def validate_orders(orders: List[Order]) -> ValidationResult
    def validate_processes(processes: List[Process]) -> ValidationResult
    def validate_equipment(equipment: List[Equipment]) -> ValidationResult
    def validate_consistency(orders, processes, equipment) -> ValidationResult
```

**输入**：解析后的数据对象
**输出**：验证结果（成功/失败 + 错误信息）
**职责**：
- 检查必填字段
- 验证数据类型和范围
- 检查引用完整性（如订单中的产品是否在工艺路线中存在）

### 2. 业务逻辑层组件

#### Scheduler（排程引擎）
核心排程算法实现，使用 OR-Tools CP-SAT 求解器。

```python
class Scheduler:
    def __init__(self, orders, processes, equipment)
    def build_model(self) -> cp_model.CpModel
    def add_constraints(self, model: cp_model.CpModel)
    def set_objective(self, model: cp_model.CpModel)
    def solve(self) -> ScheduleResult
    def extract_solution(self, solver: cp_model.CpSolver) -> ScheduleResult
```

**输入**：订单、工艺路线、设备数据
**输出**：排程结果（每个工序的开始/结束时间、分配设备）
**职责**：
- 构建 CP-SAT 优化模型
- 定义决策变量（工序时间、设备分配）
- 添加约束（工艺顺序、设备互斥、时间窗口）
- 设置优化目标（最小化总完工时间）
- 求解并提取结果

#### MetricsCalculator（指标计算器）
计算排程方案的关键性能指标。

```python
class MetricsCalculator:
    def calculate_makespan(schedule: ScheduleResult) -> float
    def calculate_equipment_utilization(schedule: ScheduleResult) -> Dict[str, float]
    def calculate_on_time_delivery(schedule: ScheduleResult, orders: List[Order]) -> float
    def identify_bottleneck(schedule: ScheduleResult) -> str
```

**输入**：排程结果
**输出**：性能指标字典
**职责**：
- 计算总完工时间
- 计算设备利用率
- 计算交期达成率
- 识别瓶颈设备

#### Visualizer（可视化生成器）
生成甘特图和其他可视化图表。

```python
class Visualizer:
    def generate_gantt_chart(schedule: ScheduleResult) -> Figure
    def generate_utilization_chart(metrics: Dict) -> Figure
    def save_gantt_to_file(figure: Figure, file_path: str)
```

**输入**：排程结果和指标数据
**输出**：可视化图表对象
**职责**：
- 生成甘特图（设备-时间视图）
- 生成设备利用率柱状图
- 支持图表保存和导出

### 3. 展示层组件

#### StreamlitApp（Web 界面）
基于 Streamlit 的用户交互界面。

```python
def main():
    st.title("生产排程智能体")
    
    # 文件上传区
    uploaded_files = upload_data_files()
    
    # 数据预览
    if uploaded_files:
        preview_data(uploaded_files)
    
    # 排程计算
    if st.button("开始排程"):
        result = run_scheduling()
        display_results(result)
    
    # 结果展示
    display_gantt_chart()
    display_metrics()
```

**职责**：
- 提供文件上传功能
- 展示数据预览
- 触发排程计算
- 展示甘特图和指标
- 提供结果导出功能

## 数据模型

### Order（订单）
```python
@dataclass
class Order:
    order_id: str          # 订单号
    product_id: str        # 产品编码
    quantity: int          # 数量
    due_date: datetime     # 交期
    priority: int          # 优先级 (1-5, 5最高)
    is_urgent: bool        # 是否紧急
```

### Process（工艺路线）
```python
@dataclass
class Process:
    product_id: str              # 产品编码
    operation_id: str            # 工序编号
    operation_name: str          # 工序名称
    sequence: int                # 工序顺序
    standard_time: float         # 标准工时（小时）
    required_equipment: str      # 所需设备类型
    predecessor: Optional[str]   # 前置工序
```

### Equipment（设备）
```python
@dataclass
class Equipment:
    equipment_id: str           # 设备编号
    equipment_type: str         # 设备类型
    available_start: datetime   # 可用开始时间
    available_end: datetime     # 可用结束时间
    capacity: float             # 产能上限（小时/天）
    changeover_time: float      # 换产时间（小时）
```

### ScheduleResult（排程结果）
```python
@dataclass
class ScheduleResult:
    status: str                           # 求解状态 (OPTIMAL/FEASIBLE/INFEASIBLE)
    makespan: float                       # 总完工时间
    operations: List[ScheduledOperation]  # 已排程工序列表
    solve_time: float                     # 求解耗时（秒）
    
@dataclass
class ScheduledOperation:
    order_id: str          # 订单号
    operation_id: str      # 工序编号
    equipment_id: str      # 分配设备
    start_time: float      # 开始时间（相对时间，单位：小时）
    end_time: float        # 结束时间
    duration: float        # 持续时间
```

### ValidationResult（验证结果）
```python
@dataclass
class ValidationResult:
    is_valid: bool              # 是否通过验证
    errors: List[str]           # 错误信息列表
    warnings: List[str]         # 警告信息列表
```


## 正确性属性

*属性是指在系统所有有效执行过程中都应该保持为真的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性是人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1：数据解析完整性
*对于任何*符合格式要求的 Excel 订单文件，解析后的订单对象列表应该包含所有行的数据，且每个订单对象的所有必填字段（订单号、产品编码、数量、交期、优先级）都应该被正确提取
**验证需求：1.1**

### 属性 2：工艺数据解析正确性
*对于任何*符合格式要求的工艺路线数据，解析后应该正确建立产品到工序的映射关系，且每个工序的标准工时、设备要求、工序顺序都应该与源数据一致
**验证需求：1.2**

### 属性 3：设备数据解析正确性
*对于任何*符合格式要求的设备数据，解析后的设备对象应该包含所有设备，且设备编号、可用时段、产能上限、换产时间等字段都应该被正确提取
**验证需求：1.3**

### 属性 4：无效数据错误检测
*对于任何*包含无效数据的输入（如缺失必填字段、数据类型错误、负数数量等），验证器应该返回失败状态，并在错误信息中明确指出具体的问题字段和错误原因
**验证需求：1.4**

### 属性 5：数据导入往返一致性
*对于任何*成功导入的数据，从内存中读取的数据应该与原始输入数据在所有关键字段上保持一致
**验证需求：1.5**

### 属性 6：工艺顺序约束
*对于任何*排程结果，如果工序 B 的前置工序是 A，那么工序 A 的结束时间必须小于或等于工序 B 的开始时间
**验证需求：2.2**

### 属性 7：设备互斥约束
*对于任何*排程结果和任意设备，该设备上分配的所有工序的时间区间不应该存在重叠（即对于同一设备上的任意两个工序，一个的结束时间应该小于或等于另一个的开始时间）
**验证需求：2.3**

### 属性 8：工序时间计算正确性
*对于任何*排程结果中的工序，其持续时间（结束时间 - 开始时间）应该等于该工序的标准工时
**验证需求：2.4**

### 属性 9：排程结果完整性
*对于任何*成功的排程结果，输入的每个订单的每道工序都应该在结果中有对应的排程记录，且每条记录都包含开始时间、结束时间和分配设备信息
**验证需求：2.5**

### 属性 10：关键指标可计算性
*对于任何*排程结果，系统应该能够成功计算总完工时间（makespan）、每台设备的利用率、交期达成率等关键指标，且这些指标的值应该在合理范围内（如利用率在 0-100% 之间）
**验证需求：3.3**

### 属性 11：甘特图数据完整性
*对于任何*排程结果，生成的甘特图数据应该包含所有已排程的工序，且每个工序条都应该包含订单号、工序名称、开始时间和结束时间信息
**验证需求：4.1, 4.3**

### 属性 12：结果导出往返一致性
*对于任何*排程结果，导出为 Excel/CSV 后再读取，关键信息（订单号、工序、设备、时间）应该与原始结果保持一致
**验证需求：5.5**

### 属性 13：设备工作时间计算正确性
*对于任何*排程结果和任意设备，该设备的总工作时间应该等于分配到该设备的所有工序的持续时间之和
**验证需求：6.1**

### 属性 14：设备利用率计算正确性
*对于任何*设备，其利用率应该等于（总工作时间 / 可用时间）× 100%，且结果应该在 0-100% 范围内
**验证需求：6.2**

### 属性 15：瓶颈设备识别正确性
*对于任何*排程结果，识别出的瓶颈设备应该是所有设备中利用率最高的设备
**验证需求：6.3**

## 错误处理

### 数据层错误处理

1. **文件读取错误**
   - 文件不存在：返回明确错误信息 "文件未找到: {file_path}"
   - 文件格式错误：返回 "不支持的文件格式，请提供 .xlsx 或 .xls 文件"
   - 文件损坏：返回 "文件无法读取，可能已损坏"

2. **数据验证错误**
   - 缺失必填字段：列出所有缺失的字段名称
   - 数据类型错误：指出具体字段和期望类型
   - 数据范围错误：如负数数量、无效日期等
   - 引用完整性错误：如订单中的产品在工艺路线中不存在

3. **数据一致性错误**
   - 工艺路线循环依赖：检测并报告循环的工序链
   - 设备类型不匹配：工序要求的设备类型不存在
   - 时间窗口冲突：设备可用时间不足以完成所有工序

### 业务逻辑层错误处理

1. **排程求解错误**
   - 无可行解：返回 INFEASIBLE 状态，并说明可能的原因（如约束过严、资源不足）
   - 求解超时：返回当前最优解（如果有）或建议简化问题规模
   - 内存不足：建议减少订单数量或工序数量

2. **约束冲突**
   - 交期不可达：列出无法按时完成的订单
   - 设备产能不足：指出瓶颈设备和缺口
   - 工艺路线不完整：指出缺失的工序定义

### 展示层错误处理

1. **用户输入错误**
   - 未上传文件：提示用户上传必需的数据文件
   - 文件格式错误：显示支持的文件格式列表
   - 文件大小超限：提示最大文件大小限制

2. **可视化错误**
   - 数据为空：显示友好提示 "暂无排程数据"
   - 图表生成失败：显示错误信息并提供重试选项

### 错误恢复策略

1. **数据验证失败**：允许用户修正数据后重新上传
2. **排程失败**：提供调整建议（如放宽交期、增加设备）
3. **部分成功**：对于部分订单无法排程的情况，返回已完成的排程并标注失败订单

## 测试策略

### 单元测试

使用 pytest 框架进行单元测试，覆盖各个组件的核心功能：

1. **数据解析测试**
   - 测试正常格式的 Excel 文件解析
   - 测试各种边界情况（空文件、单行数据、大量数据）
   - 测试错误格式的处理

2. **数据验证测试**
   - 测试各种无效数据的检测
   - 测试引用完整性验证
   - 测试边界值验证

3. **排程算法测试**
   - 测试简单场景（单订单、单设备）
   - 测试约束正确性（工艺顺序、设备互斥）
   - 测试优化目标计算

4. **指标计算测试**
   - 测试总完工时间计算
   - 测试设备利用率计算
   - 测试交期达成率计算

5. **可视化测试**
   - 测试甘特图数据生成
   - 测试图表对象创建
   - 测试文件保存功能

### 基于属性的测试

使用 Hypothesis 库进行基于属性的测试，验证系统的通用正确性属性：

**测试框架**：Hypothesis（Python 的属性测试库）
**配置**：每个属性测试至少运行 100 次迭代

1. **属性测试 1：数据解析往返一致性**
   - **功能：production-scheduling-agent，属性 5：数据导入往返一致性**
   - **验证需求：1.5**
   - 生成随机订单数据 → 写入 Excel → 解析 → 验证数据一致性

2. **属性测试 2：工艺顺序约束**
   - **功能：production-scheduling-agent，属性 6：工艺顺序约束**
   - **验证需求：2.2**
   - 生成随机订单和工艺路线 → 执行排程 → 验证所有前置工序在后续工序之前完成

3. **属性测试 3：设备互斥约束**
   - **功能：production-scheduling-agent，属性 7：设备互斥约束**
   - **验证需求：2.3**
   - 生成随机排程问题 → 执行排程 → 验证每台设备上的工序时间不重叠

4. **属性测试 4：工序时间计算**
   - **功能：production-scheduling-agent，属性 8：工序时间计算正确性**
   - **验证需求：2.4**
   - 生成随机排程结果 → 验证每个工序的持续时间等于标准工时

5. **属性测试 5：设备利用率计算**
   - **功能：production-scheduling-agent，属性 14：设备利用率计算正确性**
   - **验证需求：6.2**
   - 生成随机排程结果 → 计算利用率 → 验证公式正确性和范围有效性

6. **属性测试 6：瓶颈设备识别**
   - **功能：production-scheduling-agent，属性 15：瓶颈设备识别正确性**
   - **验证需求：6.3**
   - 生成随机排程结果 → 识别瓶颈 → 验证返回的设备确实是利用率最高的

7. **属性测试 7：无效数据检测**
   - **功能：production-scheduling-agent，属性 4：无效数据错误检测**
   - **验证需求：1.4**
   - 生成各种无效数据（缺失字段、错误类型、负数等）→ 验证系统正确识别并报告错误

### 集成测试

测试端到端的工作流程：

1. **完整排程流程测试**
   - 上传数据 → 解析验证 → 执行排程 → 生成可视化 → 导出结果
   - 使用真实的示例数据进行测试

2. **错误场景测试**
   - 测试各种错误输入的处理流程
   - 验证错误信息的准确性和友好性

3. **性能测试**
   - 测试不同规模问题的求解时间
   - 验证小规模问题（10 订单，5 设备）在 10 秒内完成

### 测试数据

1. **最小测试集**
   - 2-3 个订单
   - 2-3 台设备
   - 3-5 道工序
   - 用于快速验证核心功能

2. **标准测试集**
   - 10-20 个订单
   - 5-8 台设备
   - 5-10 道工序
   - 用于性能和正确性验证

3. **边界测试集**
   - 单订单单设备
   - 大量订单（50+）
   - 复杂工艺路线（10+ 工序）
   - 紧张交期场景

## 实现注意事项

### OR-Tools 使用要点

1. **时间离散化**
   - 将时间转换为整数（如以小时为单位）
   - 定义合理的时间范围（horizon）

2. **变量定义**
   - 为每个工序定义开始时间变量
   - 为每个工序定义结束时间变量
   - 为每个工序定义设备分配变量（可选）

3. **约束添加**
   - 工艺顺序：`model.Add(end_A <= start_B)`
   - 设备互斥：使用 `AddNoOverlap` 约束
   - 时间窗口：`model.Add(start >= available_start)`

4. **目标函数**
   - 定义 makespan 变量
   - 添加约束：`model.Add(makespan >= end_time)` for all operations
   - 最小化：`model.Minimize(makespan)`

### Streamlit 界面设计

1. **布局结构**
   - 侧边栏：文件上传和参数设置
   - 主区域：数据预览、排程按钮、结果展示
   - 使用 tabs 组织不同视图（甘特图、指标、详细数据）

2. **状态管理**
   - 使用 `st.session_state` 保存上传的数据和排程结果
   - 避免重复计算

3. **用户体验**
   - 显示进度条（`st.progress`）
   - 使用 spinner 提示计算中（`st.spinner`）
   - 提供清晰的错误提示

### 性能优化

1. **数据预处理**
   - 在排程前验证和清洗数据
   - 建立高效的数据索引

2. **模型简化**
   - 对于大规模问题，考虑分批排程
   - 使用启发式方法生成初始解

3. **求解器配置**
   - 设置合理的求解时间限制
   - 配置并行求解线程数

## 扩展方向

1. **动态排程**
   - 支持实时插单
   - 设备故障重排
   - 进度反馈和调整

2. **高级约束**
   - 物料齐套约束
   - 人员技能约束
   - 班次和日历约束

3. **多目标优化**
   - 同时优化交期、成本、设备利用率
   - 提供帕累托前沿解集

4. **智能推荐**
   - 基于历史数据的参数推荐
   - 异常预警和瓶颈分析
   - 排程方案对比和评估
