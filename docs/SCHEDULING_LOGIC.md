# 排程逻辑详解

## 概述

本系统是一个基于**约束规划 (Constraint Programming)** 的生产排程系统，使用 Google OR-Tools 的 CP-SAT 求解器来解决**作业车间调度问题 (Job Shop Scheduling Problem, JSSP)**。

系统的核心目标是：在满足所有约束条件的前提下，找到使总完工时间（makespan）最小的排程方案。

---

## 问题定义

### 输入数据

1. **订单 (Orders)**
   - 订单号、产品编码、数量、交期、优先级

2. **工艺路线 (Processes)**
   - 产品编码、工序号、工序名称、工序顺序
   - 单件标准工时（分钟）、所需设备、前置工序

3. **设备 (Equipment)**
   - 设备编号、状态、效率系数
   - 每日工作时长（小时）、可用时间窗口

### 输出结果

- 每个工序的开始时间、结束时间、分配设备
- 总完工时间（makespan）
- 设备利用率、交期达成率、瓶颈设备

---

## 核心流程

### 1. 数据预处理 (`_preprocess_data`)

#### 目的
将原始数据转换为求解器可用的结构，构建索引以提高查询效率。

#### 构建的数据结构

```python
# 产品到工艺路线的映射
product_to_processes: Dict[str, List[Process]]
# 例如: {"P01": [工序1, 工序2, 工序3]}

# 设备组到设备列表的映射
equipment_group_to_equipment: Dict[str, List[Equipment]]
# 例如: {"M01,M02": [设备M01, 设备M02]}

# 设备每日工作时长（分钟）
equipment_daily_capacity: Dict[str, float]
# 例如: {"M01": 480.0}  # 8小时 = 480分钟

# 所有需要排程的(订单, 工序)对
job_operations: List[Tuple[Order, Process]]
```

#### 时间范围估算

```python
# 计算总工作量
total_work_minutes = Σ(订单数量 × 单件工时)

# 估算需要的天数（添加2倍缓冲）
estimated_days = (total_work_minutes / 平均每日产能) × 2
estimated_days = max(estimated_days, 30)  # 至少30天

# 计算时间范围（horizon）
horizon = estimated_days × 24小时 × 60分钟
```

**说明**：horizon 是求解器搜索空间的上界，设置得太小可能无解，太大会影响求解效率。

---

### 2. 构建优化模型 (`build_model`)

#### 决策变量

对每个工序 `(订单i, 工序j)` 创建以下变量：

| 变量类型　　　　　　 | 说明　　　　　　　| 取值范围　　　　　　　 |
| ----------------------| -------------------| ------------------------|
| ----rt_var`　　　　　| 开始时间　　　　　| [0, horizon] 分钟　　　|
| `end_------ 结束时间 | [0, horizon] 分钟 | 　　　　　　　　　　　 |
| --resence_var`　　　 | 是否在设备k上执行 | {0, 1} 布尔值　　　　　|
| -----rval_var`　　　 | 时间区间　　　　　| [start, duration, end] |

##--------制

如果一个工序可以在多台设备上执行（例如 "M01,M02"），系统会：

1. 为每台可用设备创建一个 `presence_var` 和 `interval_var`
2. 添加约束：`sum(presence_vars) == 1`（必须选择恰好一台设备）
3. 求解器自动选择最优的设备分配

**示例**：
```python
工序: 车削, 可用设备: [M01, M02]

变量:
- presence_M01: 是否在M01上执行
- presence_M02: 是否在M02上执行
- interval_M01: 在M01上的时间区间（可选）
- interval_M02: 在M02上的时间区间（可选）

约束:
- presence_M01 + presence_M02 = 1
```

#### 工序持续时间计算

```python
duration = 单件标准工时 × 订单数量
```

**示例**：
- 单件工时：5分钟
- 订单数量：100件
- 持续时间：500分钟

---

### 3. 添加约束 (`add_constraints`)

#### 约束1：工艺顺序约束

**规则**：工序必须按照工艺路线的顺序执行

```python
# 对于同一订单的连续工序
工序i的结束时间 <= 工序i+1的开始时间

# 对于有显式前置工序的情况
前置工序的结束时间 <= 当前工序的开始时间
```

**示例**：
```
订单SO001的工艺路线：车削 → 铣削 → 检验

约束：
- 车削.end_time <= 铣削.start_time
- 铣削.end_time <= 检验.start_time
```

#### 约束2：设备互斥约束

**规则**：同一台设备不能同时执行多个工序

```python
model.AddNoOverlap(设备k的所有区间变量)
```

这个约束确保分配到同一设备的所有工序在时间上不重叠。

**示例**：
```
设备M01上的工序：
- 订单1的车削: [0, 500]
- 订单2的车削: [500, 1000]  ✓ 不重叠
- 订单3的车削: [450, 950]   ✗ 与订单2重叠，不允许
```

#### 约束3：时间约束

**规则**：结束时间 = 开始时间 + 持续时间

```python
end_time = start_time + (单件工时 × 订单数量)
```

#### 约束4：时间窗口约束

**规则**：所有工序的开始时间必须非负

```python
start_time >= 0
```

**扩展**：可以根据设备的 `available_start` 和 `available_end` 添加更复杂的时间窗口约束。

---

### 4. 设置优化目标 (`set_objective`)

#### 目标函数

**最小化总完工时间（makespan）**

```python
makespan = max(所有工序的结束时间)
minimize(makespan)
```

#### 目标变量

```python
# 创建makespan变量
makespan_var = model.NewIntVar(0, horizon, 'makespan')

# 添加约束：makespan >= 所有工序的结束时间
for each operation:
    model.Add(makespan_var >= operation.end_time)

# 设置优化目标
model.Minimize(makespan_var)
```

#### 其他可能的优化目标

虽然当前系统使用 makespan 作为目标，但也可以考虑：

- 最小化总延期时间
- 最小化设备切换次数
- 最大化设备利用率
- 多目标优化（加权组合）

---

### 5. 求解 (`solve`)

#### 求解流程

```python
1. 构建模型 (build_model)
2. 添加约束 (add_constraints)
3. 设置优化目标 (set_objective)
4. 创建求解器
5. 设置求解器参数
6. 执行求解
7. 提取结果
```

#### 求解器参数

```python
solver.parameters.max_time_in_seconds = 60.0  # 最大求解时间60秒
```

#### 求解状态

| 状态　　　　　 | 说明　　　　　　　　　　　 |     |
| ----------------| ----------------------------| -----|
| ` ---MAL`　　　| 找到最优解，并证明了最优性 |     |
| `F---　　 E`　 | 找到可行解，但未证明最优　 |     |
| -----　　IBLE` | 无可行解（约束冲突）　　　 |     |
| OWN`　　　　　 | 求解超时或其他原因　　　　 |     |

####　　 | 　　　

1. **约束过于严格**
   - 交期太紧
   - 设备产能不足
   - 工艺路线冲突

2. **数据错误**
   - 工序顺序错误
   - 设备类型不匹配
   - 时间估算不合理

---

### 6. 提取结果 (`extract_solution`)

#### 步骤1：获取工序时间

从求解器获取每个工序的开始和结束时间（工作分钟）：

```python
start_time = solver.Value(start_var)  # 例如: 0
end_time = solver.Value(end_var)      # 例如: 500
duration = end_time - start_time      # 例如: 500分钟
```

#### 步骤2：确定分配的设备

检查哪个 `presence_var` 的值为 1：

```python
for equipment in available_equipment:
    if solver.Value(presence_var[equipment]) == 1:
        assigned_equipment = equipment
        break
```

#### 步骤3：转换为日历时间

**核心函数**：`_work_minutes_to_datetime`

**转换逻辑**：

```python
# 输入：工作分钟数（连续时间）
# 输出：日历datetime（考虑每日工作时长）

# 1. 计算是第几个工作日
work_day = 工作分钟 // 每日工作分钟

# 2. 计算当天的工作分钟数
minutes_in_day = 工作分钟 % 每日工作分钟

# 3. 计算实际日期时间
result_date = 基准日期 + work_day天
result_datetime = result_date的8:00 + minutes_in_day
```

**示例**：

```python
设备M01每日工作: 480分钟（8小时）
基准日期: 2024-03-06 08:00

工作分钟 = 1000
work_day = 1000 // 480 = 2（第2天）
minutes_in_day = 1000 % 480 = 40

result_datetime = 2024-03-08 08:40
```

**为什么需要转换？**

- 求解器使用连续时间（工作分钟）进行优化
- 用户需要看到实际的日历时间（考虑每天的工作时间）
- 转换确保结果符合实际生产场景

#### 步骤4：计算 makespan

```python
# 找到最早开始和最晚结束
min_start_time = min(op.start_time for op in operations)
max_end_time = max(op.end_time for op in operations)

# 计算日历时间跨度（小时）
makespan = (max_end_time - min_start_time).total_seconds() / 3600.0
```

---

## 算法特性

### ✅ 优势

1. **全局最优**
   - CP-SAT 求解器能找到全局最优解（在时间限制内）
   - 不会陷入局部最优

2. **灵活的设备分配**
   - 自动选择最优设备
   - 实现负载均衡
   - 支持设备组概念

3. **严格的约束保证**
   - 100% 遵守工艺顺序
   - 绝对不会出现设备冲突
   - 保证所有约束条件

4. **考虑实际工作时间**
   - 每台设备独立的工作时长
   - 自动跳过非工作时间
   - 结果以日历时间呈现

5. **批量生产支持**
   - 正确处理订单数量
   - 工时 = 单件工时 × 数量

### ⚠️ 局限性

1. **求解时间**
   - 大规模问题可能需要较长时间
   - 当前限制：60秒

2. **简化假设**
   - 假设设备从时间0开始可用
   - 未考虑设备故障、维护
   - 未考虑人员限制

3. **优化目标单一**
   - 仅优化 makespan
   - 未考虑成本、能耗等因素

---

## 完整示例

### 输入数据

**订单**：
```
订单号: SO001
产品: P01
数量: 100件
交期: 2024-03-10
```

**工艺路线**（产品P01）：
```
1. 车削: 单件5分钟, 设备: M01,M02
2. 铣削: 单件3分钟, 设备: M03
3. 检验: 单件1分钟, 设备: M04
```

**设备**：
```
M01: 车床, 每日8小时
M02: 车床, 每日8小时
M03: 铣床, 每日8小时
M04: 检验台, 每日8小时
```

### 求解过程

#### 1. 数据预处理

```python
job_operations = [
    (SO001, 车削),
    (SO001, 铣削),
    (SO001, 检验)
]

总工作量 = (5 + 3 + 1) × 100 = 900分钟
```

#### 2. 构建模型

```python
# 为车削工序创建变量
start_车削 = IntVar(0, horizon)
end_车削 = IntVar(0, horizon)
duration_车削 = 5 × 100 = 500分钟

presence_M01 = BoolVar()
presence_M02 = BoolVar()

约束: presence_M01 + presence_M02 = 1
```

#### 3. 添加约束

```python
# 工艺顺序
end_车削 <= start_铣削
end_铣削 <= start_检验

# 设备互斥
AddNoOverlap(M01的所有区间)
AddNoOverlap(M02的所有区间)
...

# 时间约束
end_车削 = start_车削 + 500
end_铣削 = start_铣削 + 300
end_检验 = start_检验 + 100
```

#### 4. 求解

```python
求解器找到最优解:
- 车削在M01上执行: 0-500分钟
- 铣削在M03上执行: 500-800分钟
- 检验在M04上执行: 800-900分钟
```

#### 5. 转换为日历时间

```python
基准日期: 2024-03-06 08:00
M01每日工作: 480分钟

车削:
  start: 0分钟 → 2024-03-06 08:00
  end: 500分钟 → 2024-03-07 08:20
  (第1天: 0-480, 第2天: 480-500)

铣削:
  start: 500分钟 → 2024-03-07 08:20
  end: 800分钟 → 2024-03-08 09:40

检验:
  start: 800分钟 → 2024-03-08 09:40
  end: 900分钟 → 2024-03-08 11:20
```

### 输出结果

```
订单: SO001
总完工时间: 51.33小时（2天3小时20分）

工序详情:
┌────────┬──────┬─────────────────┬─────────────────┬──────────┐
│ 工序   │ 设备 │ 开始时间        │ 结束时间        │ 工时(h)  │
├────────┼──────┼─────────────────┼─────────────────┼──────────┤
│ 车削   │ M01  │ 03-06 08:00     │ 03-07 08:20     │ 8.33     │
│ 铣削   │ M03  │ 03-07 08:20     │ 03-08 09:40     │ 5.00     │
│ 检验   │ M04  │ 03-08 09:40     │ 03-08 11:20     │ 1.67     │
└────────┴──────┴─────────────────┴─────────────────┴──────────┘

设备利用率:
- M01: 16.2%
- M02: 0%
- M03: 9.7%
- M04: 3.2%

交期达成: ✓ (完工时间 < 交期)
```

---

## 扩展方向

### 1. 多目标优化

```python
# 加权目标函数
objective = w1 × makespan + w2 × 延期惩罚 + w3 × 设备切换成本
```

### 2. 动态排程

- 支持插单、急单
- 实时调整排程
- 考虑在制品状态

### 3. 高级约束

- 设备维护时间窗口
- 人员技能匹配
- 物料可用性
- 能源消耗限制

### 4. 启发式算法

对于超大规模问题，可以结合：
- 遗传算法
- 模拟退火
- 禁忌搜索

### 5. 机器学习

- 学习历史数据预测工时
- 智能调整优先级
- 预测瓶颈设备

---

## 参考资料

- [Google OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
- [Job Shop Scheduling Problem](https://en.wikipedia.org/wiki/Job-shop_scheduling)
- [Constraint Programming](https://en.wikipedia.org/wiki/Constraint_programming)

---

## 总结

本排程系统通过约束规划技术，将复杂的生产排程问题转化为数学优化问题，由求解器自动找到最优解。系统的核心优势在于：

1. **自动化**：无需手动编写复杂的调度规则
2. **最优性**：在时间限制内找到全局最优解
3. **灵活性**：易于添加新的约束和目标
4. **可靠性**：保证所有约束条件得到满足

这使得系统能够高效地处理实际生产中的复杂排程问题。
　　　　　　　　　　 |     |