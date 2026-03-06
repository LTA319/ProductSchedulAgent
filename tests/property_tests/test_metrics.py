"""
指标计算器属性测试

使用 Hypothesis 进行基于属性的测试，验证指标计算器的正确性属性。
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from data_layer.models import Order, Process, Equipment, ScheduleResult, ScheduledOperation
from business_logic.metrics import MetricsCalculator


# 生成器：生成随机已排程工序
@st.composite
def scheduled_operation_strategy(draw, order_ids=None, operation_ids=None, equipment_ids=None):
    """生成随机已排程工序"""
    if order_ids is None:
        order_ids = ['O1', 'O2', 'O3']
    if operation_ids is None:
        operation_ids = ['OP1', 'OP2', 'OP3']
    if equipment_ids is None:
        equipment_ids = ['M1', 'M2', 'M3']
    
    order_id = draw(st.sampled_from(order_ids))
    operation_id = draw(st.sampled_from(operation_ids))
    equipment_id = draw(st.sampled_from(equipment_ids))
    
    # 生成合理的时间范围
    start_time = draw(st.floats(min_value=0.0, max_value=100.0))
    duration = draw(st.floats(min_value=1.0, max_value=10.0))
    end_time = start_time + duration
    
    return ScheduledOperation(
        order_id=order_id,
        operation_id=operation_id,
        equipment_id=equipment_id,
        start_time=start_time,
        end_time=end_time,
        duration=duration
    )


# 生成器：生成随机排程结果
@st.composite
def schedule_result_strategy(draw):
    """生成随机排程结果，确保同一设备上的工序不重叠"""
    status = draw(st.sampled_from(['OPTIMAL', 'FEASIBLE']))
    
    # 生成1-10个工序
    num_operations = draw(st.integers(min_value=1, max_value=10))
    operations = []
    
    order_ids = ['O1', 'O2', 'O3']
    operation_ids = [f'OP{i}' for i in range(1, 6)]
    equipment_ids = ['M1', 'M2', 'M3']
    
    # 使用集合跟踪已生成的工序，避免重复
    used_operations = set()
    
    # 跟踪每台设备的已占用时间段
    equipment_schedules: Dict[str, List[Tuple[float, float]]] = {
        eq_id: [] for eq_id in equipment_ids
    }
    
    for i in range(num_operations):
        # 生成唯一的工序
        max_attempts = 50
        for attempt in range(max_attempts):
            order_id = draw(st.sampled_from(order_ids))
            operation_id = draw(st.sampled_from(operation_ids))
            equipment_id = draw(st.sampled_from(equipment_ids))
            
            op_key = (order_id, operation_id)
            
            if op_key not in used_operations:
                # 为这个工序找一个不重叠的时间段
                duration = draw(st.floats(min_value=1.0, max_value=10.0))
                
                # 找到该设备上的最后结束时间
                if equipment_schedules[equipment_id]:
                    last_end_time = max(end for _, end in equipment_schedules[equipment_id])
                    # 在最后结束时间之后开始
                    start_time = last_end_time
                else:
                    # 设备空闲，从0开始
                    start_time = 0.0
                
                end_time = start_time + duration
                
                # 创建工序
                op = ScheduledOperation(
                    order_id=order_id,
                    operation_id=operation_id,
                    equipment_id=equipment_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration
                )
                
                used_operations.add(op_key)
                equipment_schedules[equipment_id].append((start_time, end_time))
                operations.append(op)
                break
        else:
            # 如果无法生成唯一工序，停止添加
            break
    
    # makespan 应该是所有工序结束时间的最大值
    if operations:
        makespan = max(op.end_time for op in operations)
    else:
        makespan = 0.0
    
    solve_time = draw(st.floats(min_value=0.1, max_value=10.0))
    
    return ScheduleResult(
        status=status,
        makespan=makespan,
        operations=operations,
        solve_time=solve_time
    )


# 生成器：生成设备列表
@st.composite
def equipment_list_strategy(draw):
    """生成设备列表"""
    equipment_ids = ['M1', 'M2', 'M3']
    equipment_types = ['Type1', 'Type2']
    
    equipment_list = []
    for eq_id in equipment_ids:
        eq_type = draw(st.sampled_from(equipment_types))
        available_start = datetime.now()
        available_end = available_start + timedelta(days=30)
        capacity = draw(st.floats(min_value=8.0, max_value=24.0))
        changeover_time = draw(st.floats(min_value=0.0, max_value=2.0))
        
        equipment_list.append(Equipment(
            equipment_id=eq_id,
            equipment_type=eq_type,
            available_start=available_start,
            available_end=available_end,
            capacity=capacity,
            changeover_time=changeover_time
        ))
    
    return equipment_list


class TestMetricsCalculatorProperties:
    """指标计算器属性测试类"""
    
    @given(schedule_result_strategy(), equipment_list_strategy())
    @settings(max_examples=100, deadline=None)
    def test_key_metrics_calculability(self, schedule, equipment):
        """
        **Feature: production-scheduling-agent, Property 10: 关键指标可计算性**
        **Validates: Requirements 3.3**
        
        属性：对于任何排程结果，系统应该能够成功计算总完工时间（makespan）、
        每台设备的利用率、交期达成率等关键指标，且这些指标的值应该在合理范围内
        （如利用率在 0-100% 之间）
        """
        # 创建指标计算器
        calculator = MetricsCalculator(equipment)
        
        # 测试 1: 计算总完工时间
        makespan = calculator.calculate_makespan(schedule)
        assert makespan >= 0, f"总完工时间不能为负: {makespan}"
        
        # 如果有工序，makespan 应该等于最大结束时间
        if schedule.operations:
            expected_makespan = max(op.end_time for op in schedule.operations)
            assert abs(makespan - expected_makespan) < 0.01, (
                f"总完工时间计算错误: 期望 {expected_makespan}, 实际 {makespan}"
            )
        else:
            assert makespan == 0.0, "空排程的总完工时间应该为0"
        
        # 测试 2: 计算设备利用率
        utilization = calculator.calculate_equipment_utilization(schedule)
        assert isinstance(utilization, dict), "设备利用率应该返回字典"
        
        # 验证利用率在合理范围内
        for equipment_id, util_value in utilization.items():
            assert 0.0 <= util_value <= 100.0, (
                f"设备 {equipment_id} 利用率超出范围 [0, 100]: {util_value}"
            )
        
        # 测试 3: 识别瓶颈设备
        if schedule.operations:
            bottleneck = calculator.identify_bottleneck(schedule)
            assert isinstance(bottleneck, str), "瓶颈设备应该返回字符串"
            
            # 瓶颈设备应该在利用率字典中
            if bottleneck:
                assert bottleneck in utilization, (
                    f"瓶颈设备 {bottleneck} 不在利用率字典中"
                )
                
                # 瓶颈设备应该是利用率最高的设备
                max_util = max(utilization.values())
                assert utilization[bottleneck] == max_util, (
                    f"瓶颈设备 {bottleneck} 利用率 {utilization[bottleneck]} "
                    f"不是最高的 {max_util}"
                )
    
    @given(schedule_result_strategy(), equipment_list_strategy())
    @settings(max_examples=100, deadline=None)
    def test_equipment_work_time_calculation(self, schedule, equipment):
        """
        **Feature: production-scheduling-agent, Property 13: 设备工作时间计算正确性**
        **Validates: Requirements 6.1**
        
        属性：对于任何排程结果和任意设备，该设备的总工作时间应该等于
        分配到该设备的所有工序的持续时间之和
        """
        # 创建指标计算器
        calculator = MetricsCalculator(equipment)
        
        # 手动计算每台设备的总工作时间
        expected_work_time: Dict[str, float] = {}
        for op in schedule.operations:
            if op.equipment_id not in expected_work_time:
                expected_work_time[op.equipment_id] = 0.0
            expected_work_time[op.equipment_id] += op.duration
        
        # 计算设备利用率（内部会计算工作时间）
        utilization = calculator.calculate_equipment_utilization(schedule)
        
        # 验证工作时间计算
        makespan = calculator.calculate_makespan(schedule)
        
        for equipment_id, expected_time in expected_work_time.items():
            # 从利用率反推工作时间
            if makespan > 0:
                actual_time = (utilization[equipment_id] / 100.0) * makespan
                
                # 验证工作时间相等（允许小的浮点误差）
                assert abs(actual_time - expected_time) < 0.01, (
                    f"设备 {equipment_id} 工作时间计算错误: "
                    f"期望 {expected_time}, 实际 {actual_time}"
                )
    
    @given(schedule_result_strategy(), equipment_list_strategy())
    @settings(max_examples=100, deadline=None)
    def test_equipment_utilization_calculation(self, schedule, equipment):
        """
        **Feature: production-scheduling-agent, Property 14: 设备利用率计算正确性**
        **Validates: Requirements 6.2**
        
        属性：对于任何设备，其利用率应该等于（总工作时间 / 可用时间）× 100%，
        且结果应该在 0-100% 范围内
        """
        # 创建指标计算器
        calculator = MetricsCalculator(equipment)
        
        # 计算设备利用率
        utilization = calculator.calculate_equipment_utilization(schedule)
        
        # 计算makespan（可用时间）
        makespan = calculator.calculate_makespan(schedule)
        
        # 手动计算每台设备的工作时间
        equipment_work_time: Dict[str, float] = {}
        for op in schedule.operations:
            if op.equipment_id not in equipment_work_time:
                equipment_work_time[op.equipment_id] = 0.0
            equipment_work_time[op.equipment_id] += op.duration
        
        # 验证利用率计算公式
        for equipment_id, work_time in equipment_work_time.items():
            if makespan > 0:
                expected_utilization = (work_time / makespan) * 100.0
                actual_utilization = utilization[equipment_id]
                
                # 验证利用率计算正确
                assert abs(actual_utilization - expected_utilization) < 0.01, (
                    f"设备 {equipment_id} 利用率计算错误: "
                    f"期望 {expected_utilization}%, 实际 {actual_utilization}%"
                )
                
                # 验证利用率在合理范围内
                assert 0.0 <= actual_utilization <= 100.0, (
                    f"设备 {equipment_id} 利用率超出范围 [0, 100]: {actual_utilization}%"
                )
        
        # 验证没有分配工序的设备利用率为0
        for eq in equipment:
            if eq.equipment_id not in equipment_work_time:
                assert utilization[eq.equipment_id] == 0.0, (
                    f"未分配工序的设备 {eq.equipment_id} 利用率应该为0"
                )
    
    @given(schedule_result_strategy(), equipment_list_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bottleneck_identification(self, schedule, equipment):
        """
        **Feature: production-scheduling-agent, Property 15: 瓶颈设备识别正确性**
        **Validates: Requirements 6.3**
        
        属性：对于任何排程结果，识别出的瓶颈设备应该是所有设备中利用率最高的设备
        """
        # 创建指标计算器
        calculator = MetricsCalculator(equipment)
        
        # 如果没有工序，跳过测试
        if not schedule.operations:
            return
        
        # 计算设备利用率
        utilization = calculator.calculate_equipment_utilization(schedule)
        
        # 识别瓶颈设备
        bottleneck = calculator.identify_bottleneck(schedule)
        
        # 验证瓶颈设备不为空
        assert bottleneck, "瓶颈设备不应该为空字符串"
        
        # 验证瓶颈设备在利用率字典中
        assert bottleneck in utilization, (
            f"瓶颈设备 {bottleneck} 不在利用率字典中"
        )
        
        # 验证瓶颈设备是利用率最高的设备
        max_utilization = max(utilization.values())
        bottleneck_utilization = utilization[bottleneck]
        
        assert bottleneck_utilization == max_utilization, (
            f"瓶颈设备 {bottleneck} 利用率 {bottleneck_utilization}% "
            f"不是最高的 {max_utilization}%"
        )
        
        # 验证没有其他设备的利用率更高
        for equipment_id, util_value in utilization.items():
            assert util_value <= bottleneck_utilization, (
                f"设备 {equipment_id} 利用率 {util_value}% "
                f"高于瓶颈设备 {bottleneck} 的利用率 {bottleneck_utilization}%"
            )
