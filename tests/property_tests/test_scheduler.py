"""
排程引擎属性测试

使用 Hypothesis 进行基于属性的测试，验证排程引擎的正确性属性。
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from data_layer.models import Order, Process, Equipment, ScheduleResult
from business_logic.scheduler import Scheduler


# 生成器：生成随机订单
@st.composite
def order_strategy(draw, product_ids=None):
    """生成随机订单"""
    if product_ids is None:
        product_ids = ['P1', 'P2', 'P3']
    
    order_id = f"O{draw(st.integers(min_value=1, max_value=1000))}"
    product_id = draw(st.sampled_from(product_ids))
    quantity = draw(st.integers(min_value=1, max_value=10))
    due_date = datetime.now() + timedelta(days=draw(st.integers(min_value=1, max_value=30)))
    priority = draw(st.integers(min_value=1, max_value=5))
    is_urgent = draw(st.booleans())
    
    return Order(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        due_date=due_date,
        priority=priority,
        is_urgent=is_urgent
    )


# 生成器：生成随机工艺路线
@st.composite
def process_strategy(draw, product_id, sequence, equipment_types=None):
    """生成随机工艺路线"""
    if equipment_types is None:
        equipment_types = ['M1', 'M2', 'M3']
    
    operation_id = f"OP{product_id}_{sequence}"
    operation_name = f"工序{sequence}"
    standard_time = draw(st.integers(min_value=1, max_value=10))
    required_equipment = draw(st.sampled_from(equipment_types))
    
    return Process(
        product_id=product_id,
        operation_id=operation_id,
        operation_name=operation_name,
        sequence=sequence,
        standard_time=float(standard_time),
        required_equipment=required_equipment,
        predecessor=None
    )


# 生成器：生成随机设备
@st.composite
def equipment_strategy(draw, equipment_type, equipment_id):
    """生成随机设备"""
    available_start = datetime.now()
    available_end = available_start + timedelta(days=30)
    capacity = draw(st.floats(min_value=8.0, max_value=24.0))
    changeover_time = draw(st.floats(min_value=0.0, max_value=2.0))
    
    return Equipment(
        equipment_id=equipment_id,
        equipment_type=equipment_type,
        available_start=available_start,
        available_end=available_end,
        capacity=capacity,
        changeover_time=changeover_time
    )


# 生成器：生成完整的排程问题
@st.composite
def scheduling_problem_strategy(draw):
    """生成完整的排程问题（订单、工艺、设备）"""
    # 定义产品和设备类型
    product_ids = ['P1', 'P2']
    equipment_types = ['M1', 'M2']
    
    # 生成订单（1-3个），确保订单ID唯一
    num_orders = draw(st.integers(min_value=1, max_value=3))
    orders = []
    used_order_ids = set()
    for i in range(num_orders):
        order = draw(order_strategy(product_ids=product_ids))
        # 确保订单ID唯一
        while order.order_id in used_order_ids:
            order = draw(order_strategy(product_ids=product_ids))
        used_order_ids.add(order.order_id)
        orders.append(order)
    
    # 为每个产品生成工艺路线（2-3道工序）
    processes = []
    for product_id in product_ids:
        num_operations = draw(st.integers(min_value=2, max_value=3))
        for seq in range(1, num_operations + 1):
            processes.append(draw(process_strategy(product_id, seq, equipment_types)))
    
    # 为每种设备类型生成设备（1-2台）
    equipment = []
    for eq_type in equipment_types:
        num_equipment = draw(st.integers(min_value=1, max_value=2))
        for i in range(num_equipment):
            equipment.append(draw(equipment_strategy(eq_type, f"{eq_type}_{i+1}")))
    
    return orders, processes, equipment


class TestSchedulerProperties:
    """排程引擎属性测试类"""
    
    @given(scheduling_problem_strategy())
    @settings(max_examples=100, deadline=None)
    def test_process_sequence_constraint(self, problem_data):
        """
        **Feature: production-scheduling-agent, Property 6: 工艺顺序约束**
        **Validates: Requirements 2.2**
        
        属性：对于任何排程结果，如果工序 B 的前置工序是 A，
        那么工序 A 的结束时间必须小于或等于工序 B 的开始时间
        """
        orders, processes, equipment = problem_data
        
        # 创建排程引擎
        scheduler = Scheduler(orders, processes, equipment)
        
        # 执行排程
        result = scheduler.solve()
        
        # 如果求解失败，跳过验证（无可行解不是属性违反）
        if result.status == 'INFEASIBLE' or result.status == 'UNKNOWN':
            return
        
        # 构建工序到排程操作的映射
        operation_map = {
            (op.order_id, op.operation_id): op
            for op in result.operations
        }
        
        # 验证工艺顺序约束
        for order in orders:
            if order.product_id not in scheduler.product_to_processes:
                continue
            
            product_processes = scheduler.product_to_processes[order.product_id]
            
            # 检查相邻工序的顺序
            for i in range(len(product_processes) - 1):
                current_process = product_processes[i]
                next_process = product_processes[i + 1]
                
                current_key = (order.order_id, current_process.operation_id)
                next_key = (order.order_id, next_process.operation_id)
                
                if current_key in operation_map and next_key in operation_map:
                    current_op = operation_map[current_key]
                    next_op = operation_map[next_key]
                    
                    # 断言：当前工序的结束时间 <= 下一工序的开始时间
                    assert current_op.end_time <= next_op.start_time, (
                        f"工艺顺序约束违反: 订单 {order.order_id}, "
                        f"工序 {current_process.operation_id} 结束时间 {current_op.end_time} "
                        f"> 工序 {next_process.operation_id} 开始时间 {next_op.start_time}"
                    )

    
    @given(scheduling_problem_strategy())
    @settings(max_examples=100, deadline=None)
    def test_equipment_mutual_exclusion(self, problem_data):
        """
        **Feature: production-scheduling-agent, Property 7: 设备互斥约束**
        **Validates: Requirements 2.3**
        
        属性：对于任何排程结果和任意设备，该设备上分配的所有工序的时间区间不应该存在重叠
        （即对于同一设备上的任意两个工序，一个的结束时间应该小于或等于另一个的开始时间）
        """
        orders, processes, equipment = problem_data
        
        # 创建排程引擎
        scheduler = Scheduler(orders, processes, equipment)
        
        # 执行排程
        result = scheduler.solve()
        
        # 如果求解失败，跳过验证
        if result.status == 'INFEASIBLE' or result.status == 'UNKNOWN':
            return
        
        # 按设备分组工序
        equipment_operations = {}
        for op in result.operations:
            if op.equipment_id not in equipment_operations:
                equipment_operations[op.equipment_id] = []
            equipment_operations[op.equipment_id].append(op)
        
        # 验证每台设备上的工序不重叠
        for equipment_id, ops in equipment_operations.items():
            # 按开始时间排序
            ops_sorted = sorted(ops, key=lambda x: x.start_time)
            
            # 检查相邻工序不重叠
            for i in range(len(ops_sorted) - 1):
                current_op = ops_sorted[i]
                next_op = ops_sorted[i + 1]
                
                # 断言：当前工序的结束时间 <= 下一工序的开始时间
                assert current_op.end_time <= next_op.start_time, (
                    f"设备互斥约束违反: 设备 {equipment_id}, "
                    f"工序 {current_op.order_id}/{current_op.operation_id} "
                    f"结束时间 {current_op.end_time} > "
                    f"工序 {next_op.order_id}/{next_op.operation_id} "
                    f"开始时间 {next_op.start_time}"
                )

    
    @given(scheduling_problem_strategy())
    @settings(max_examples=100, deadline=None)
    def test_operation_time_calculation(self, problem_data):
        """
        **Feature: production-scheduling-agent, Property 8: 工序时间计算正确性**
        **Validates: Requirements 2.4**
        
        属性：对于任何排程结果中的工序，其持续时间（结束时间 - 开始时间）应该等于该工序的标准工时
        """
        orders, processes, equipment = problem_data
        
        # 创建排程引擎
        scheduler = Scheduler(orders, processes, equipment)
        
        # 执行排程
        result = scheduler.solve()
        
        # 如果求解失败，跳过验证
        if result.status == 'INFEASIBLE' or result.status == 'UNKNOWN':
            return
        
        # 构建工序ID到工艺对象的映射
        operation_to_process = {p.operation_id: p for p in processes}
        
        # 验证每个工序的时间计算
        for op in result.operations:
            if op.operation_id in operation_to_process:
                process = operation_to_process[op.operation_id]
                expected_duration = int(process.standard_time)
                actual_duration = op.end_time - op.start_time
                
                # 断言：实际持续时间 = 标准工时
                assert abs(actual_duration - expected_duration) < 0.01, (
                    f"工序时间计算错误: 订单 {op.order_id}, 工序 {op.operation_id}, "
                    f"标准工时 {expected_duration}, "
                    f"实际持续时间 {actual_duration} (开始 {op.start_time}, 结束 {op.end_time})"
                )

    
    @given(scheduling_problem_strategy())
    @settings(max_examples=100, deadline=None)
    def test_schedule_result_completeness(self, problem_data):
        """
        **Feature: production-scheduling-agent, Property 9: 排程结果完整性**
        **Validates: Requirements 2.5**
        
        属性：对于任何成功的排程结果，输入的每个订单的每道工序都应该在结果中有对应的排程记录，
        且每条记录都包含开始时间、结束时间和分配设备信息
        """
        orders, processes, equipment = problem_data
        
        # 创建排程引擎
        scheduler = Scheduler(orders, processes, equipment)
        
        # 执行排程
        result = scheduler.solve()
        
        # 如果求解失败，跳过验证
        if result.status == 'INFEASIBLE' or result.status == 'UNKNOWN':
            return
        
        # 构建期望的工序集合
        expected_operations = set()
        for order in orders:
            if order.product_id in scheduler.product_to_processes:
                for process in scheduler.product_to_processes[order.product_id]:
                    expected_operations.add((order.order_id, process.operation_id))
        
        # 构建实际的工序集合
        actual_operations = set()
        for op in result.operations:
            actual_operations.add((op.order_id, op.operation_id))
            
            # 验证每条记录包含必要信息
            assert op.start_time is not None, f"工序 {op.order_id}/{op.operation_id} 缺少开始时间"
            assert op.end_time is not None, f"工序 {op.order_id}/{op.operation_id} 缺少结束时间"
            assert op.equipment_id is not None, f"工序 {op.order_id}/{op.operation_id} 缺少设备分配"
            assert op.equipment_id != 'UNKNOWN', f"工序 {op.order_id}/{op.operation_id} 设备分配为UNKNOWN"
            
            # 验证时间的合理性
            assert op.start_time >= 0, f"工序 {op.order_id}/{op.operation_id} 开始时间为负"
            assert op.end_time >= op.start_time, f"工序 {op.order_id}/{op.operation_id} 结束时间早于开始时间"
        
        # 断言：所有期望的工序都在结果中
        assert expected_operations == actual_operations, (
            f"排程结果不完整: "
            f"期望工序 {expected_operations}, "
            f"实际工序 {actual_operations}, "
            f"缺失 {expected_operations - actual_operations}, "
            f"多余 {actual_operations - expected_operations}"
        )
