# 测试数据说明

本目录包含用于测试和演示生产排程系统的数据文件和生成器。

## 文件说明

### 1. example_data.xlsx
示例数据文件，包含完整的生产排程数据：
- **订单表**: 12个订单，涵盖8种产品
- **工艺路线表**: 27道工序，定义了每个产品的加工流程
- **设备表**: 8台设备，包括车床、铣床、钻床、磨床等

该文件可直接用于：
- 系统功能演示
- 手动测试
- 验证排程算法正确性

### 2. create_example_data.py
示例数据生成脚本，用于创建 example_data.xlsx 文件。

运行方式：
```bash
python tests/create_example_data.py
```

### 3. data_generators.py
测试数据生成器模块，提供以下功能：

#### 随机数据生成函数
- `generate_random_orders()`: 生成随机订单数据
- `generate_random_processes()`: 生成随机工艺路线数据
- `generate_random_equipment()`: 生成随机设备数据
- `generate_complete_dataset()`: 生成完整的数据集（确保引用完整性）

#### 预定义数据集
- `generate_simple_dataset()`: 简单数据集（3订单，2产品，3设备）
- `generate_large_dataset()`: 大规模数据集（50订单，20产品，15设备）

#### Hypothesis 策略
用于属性测试的数据生成策略：
- `order_strategy()`: 订单对象生成策略
- `process_strategy()`: 工艺路线对象生成策略
- `equipment_strategy()`: 设备对象生成策略

### 4. test_generators.py
数据生成器的单元测试，验证生成器的正确性。

运行方式：
```bash
python tests/test_generators.py
```

### 5. test_hypothesis_strategies.py
Hypothesis 策略的测试，验证策略生成的数据符合业务规则。

运行方式：
```bash
python tests/test_hypothesis_strategies.py
```

### 6. verify_example_data.py
示例数据验证脚本，验证 example_data.xlsx 文件的完整性和正确性。

运行方式：
```bash
python tests/verify_example_data.py
```

## 使用示例

### 在属性测试中使用数据生成器

```python
from tests.data_generators import generate_complete_dataset
from hypothesis import given, strategies as st

# 使用预定义数据集
def test_with_simple_dataset():
    orders, processes, equipment = generate_simple_dataset()
    # 执行测试...

# 使用 Hypothesis 策略
from tests.data_generators import order_strategy

@given(order_strategy())
def test_order_property(order):
    assert order.quantity > 0
    # 更多断言...
```

### 生成自定义规模的数据集

```python
from tests.data_generators import generate_complete_dataset

# 生成自定义规模的数据集
orders, processes, equipment = generate_complete_dataset(
    num_orders=20,
    num_products=10,
    num_equipment=12,
    min_operations_per_product=2,
    max_operations_per_product=6
)
```

## 数据格式说明

### 订单数据格式
- 订单号: 唯一标识符
- 产品编码: 关联到工艺路线
- 生产数量: 正整数
- 承诺交期: 日期时间
- 优先级: 1-5（1最高）
- 是否急单: 布尔值

### 工艺路线数据格式
- 产品编码: 关联到订单
- 工序号: 唯一标识符
- 工序名称: 描述性名称
- 工序顺序: 正整数，定义执行顺序
- 单件标准工时: 小时数（浮点数）
- 可使用设备编号: 关联到设备表
- 前置工序: 可选，定义工序依赖关系

### 设备数据格式
- 设备编号: 唯一标识符
- 设备类型: 设备分类
- 可用开始时间: 日期时间
- 可用结束时间: 日期时间
- 产能上限: 每日工作小时数
- 换产时间: 小时数（浮点数）

## 注意事项

1. **引用完整性**: 使用 `generate_complete_dataset()` 确保订单中的产品在工艺路线中存在，工艺路线中的设备在设备列表中存在。

2. **工序顺序**: 工艺路线生成器自动维护工序顺序和前置工序关系。

3. **数据规模**: 大规模数据集可能导致排程求解时间较长，建议根据测试需求选择合适的数据规模。

4. **随机性**: 数据生成器使用随机数，每次运行结果可能不同。如需可重复的测试，可以设置随机种子：
   ```python
   import random
   random.seed(42)
   ```
