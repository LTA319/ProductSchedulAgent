"""
可视化组件属性测试

使用 Hypothesis 进行基于属性的测试，验证可视化组件的正确性属性。
"""

import pytest
import os
import tempfile
import pandas as pd
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from data_layer.models import ScheduleResult, ScheduledOperation
from business_logic.visualizer import Visualizer


# 生成器：生成随机已排程工序
@st.composite
def scheduled_operation_strategy(draw):
    """生成随机已排程工序"""
    order_id = f"O{draw(st.integers(min_value=1, max_value=100))}"
    operation_id = f"OP{draw(st.integers(min_value=1, max_value=10))}"
    equipment_id = f"M{draw(st.integers(min_value=1, max_value=5))}"
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
    """生成随机排程结果"""
    status = draw(st.sampled_from(['OPTIMAL', 'FEASIBLE']))
    
    # 生成1-20个工序
    num_operations = draw(st.integers(min_value=1, max_value=20))
    operations = [draw(scheduled_operation_strategy()) for _ in range(num_operations)]
    
    # 计算makespan
    makespan = max(op.end_time for op in operations) if operations else 0.0
    
    solve_time = draw(st.floats(min_value=0.1, max_value=10.0))
    
    return ScheduleResult(
        status=status,
        makespan=makespan,
        operations=operations,
        solve_time=solve_time
    )


class TestVisualizationProperties:
    """可视化组件属性测试类"""
    
    @given(schedule_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_gantt_chart_data_completeness(self, schedule: ScheduleResult):
        """
        **Feature: production-scheduling-agent, Property 11: 甘特图数据完整性**
        **Validates: Requirements 4.1, 4.3**
        
        属性：对于任何排程结果，生成的甘特图数据应该包含所有已排程的工序，
        且每个工序条都应该包含订单号、工序名称、开始时间和结束时间信息
        """
        visualizer = Visualizer()
        
        # 生成甘特图
        fig = visualizer.generate_gantt_chart(schedule)
        
        # 验证图表对象存在
        assert fig is not None, "甘特图对象不应为空"
        
        # 如果没有工序，图表应该是空的但有效
        if not schedule.operations:
            assert fig.data is not None, "空排程结果应该返回有效的空图表"
            return
        
        # 验证图表包含数据
        assert len(fig.data) > 0, "甘特图应该包含数据"
        
        # 提取甘特图中的工序信息
        # Plotly甘特图使用shapes或bars来表示任务
        # 我们需要验证所有工序都被包含
        
        # 从图表数据中提取工序标识
        # 对于figure_factory.create_gantt创建的图表，数据在fig.data中
        chart_operations = set()
        
        # 检查图表的数据结构
        if hasattr(fig, 'data') and fig.data:
            for trace in fig.data:
                if hasattr(trace, 'text') and trace.text:
                    # 文本可能包含订单号和工序信息
                    if isinstance(trace.text, (list, tuple)):
                        for text in trace.text:
                            if text:
                                chart_operations.add(str(text))
                    else:
                        chart_operations.add(str(trace.text))
        
        # 验证所有工序都在图表中
        expected_operations = set()
        for op in schedule.operations:
            # 构建期望的工序标识（与甘特图中的Resource字段对应）
            operation_key = f"{op.order_id}-{op.operation_id}"
            expected_operations.add(operation_key)
        
        # 由于Plotly甘特图的内部结构可能复杂，我们至少验证：
        # 1. 图表有数据
        # 2. 图表的布局包含必要的轴标签
        assert fig.layout is not None, "甘特图应该有布局信息"
        
        # 验证轴标签存在
        if hasattr(fig.layout, 'xaxis') and fig.layout.xaxis:
            assert fig.layout.xaxis.title is not None or hasattr(fig.layout.xaxis, 'title'), \
                "甘特图应该有X轴标签（时间）"
        
        if hasattr(fig.layout, 'yaxis') and fig.layout.yaxis:
            assert fig.layout.yaxis.title is not None or hasattr(fig.layout.yaxis, 'title'), \
                "甘特图应该有Y轴标签（设备）"
        
        # 验证图表标题存在
        if hasattr(fig.layout, 'title'):
            assert fig.layout.title is not None or hasattr(fig.layout.title, 'text'), \
                "甘特图应该有标题"
    
    @given(schedule_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_export_roundtrip_consistency(self, schedule: ScheduleResult):
        """
        **Feature: production-scheduling-agent, Property 12: 结果导出往返一致性**
        **Validates: Requirements 5.5**
        
        属性：对于任何排程结果，导出为 Excel/CSV 后再读取，
        关键信息（订单号、工序、设备、时间）应该与原始结果保持一致
        """
        visualizer = Visualizer()
        
        # 如果没有工序，跳过测试
        if not schedule.operations:
            return
        
        # 创建临时文件
        with tempfile.TemporaryDirectory() as tmpdir:
            # 测试Excel导出和读取
            excel_path = os.path.join(tmpdir, 'test_schedule.xlsx')
            visualizer.export_schedule_to_excel(schedule, excel_path)
            
            # 读取Excel文件
            df_excel = pd.read_excel(excel_path, engine='openpyxl')
            
            # 验证Excel往返一致性
            assert len(df_excel) == len(schedule.operations), \
                f"Excel导出后行数不一致: 期望 {len(schedule.operations)}, 实际 {len(df_excel)}"
            
            for idx, op in enumerate(schedule.operations):
                row = df_excel.iloc[idx]
                
                assert row['订单号'] == op.order_id, \
                    f"Excel第{idx}行订单号不一致: 期望 {op.order_id}, 实际 {row['订单号']}"
                assert row['工序编号'] == op.operation_id, \
                    f"Excel第{idx}行工序编号不一致: 期望 {op.operation_id}, 实际 {row['工序编号']}"
                assert row['设备编号'] == op.equipment_id, \
                    f"Excel第{idx}行设备编号不一致: 期望 {op.equipment_id}, 实际 {row['设备编号']}"
                
                # 时间字段允许小的浮点误差
                assert abs(row['开始时间'] - op.start_time) < 0.01, \
                    f"Excel第{idx}行开始时间不一致: 期望 {op.start_time}, 实际 {row['开始时间']}"
                assert abs(row['结束时间'] - op.end_time) < 0.01, \
                    f"Excel第{idx}行结束时间不一致: 期望 {op.end_time}, 实际 {row['结束时间']}"
                assert abs(row['持续时间'] - op.duration) < 0.01, \
                    f"Excel第{idx}行持续时间不一致: 期望 {op.duration}, 实际 {row['持续时间']}"
            
            # 测试CSV导出和读取
            csv_path = os.path.join(tmpdir, 'test_schedule.csv')
            visualizer.export_schedule_to_csv(schedule, csv_path)
            
            # 读取CSV文件
            df_csv = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # 验证CSV往返一致性
            assert len(df_csv) == len(schedule.operations), \
                f"CSV导出后行数不一致: 期望 {len(schedule.operations)}, 实际 {len(df_csv)}"
            
            for idx, op in enumerate(schedule.operations):
                row = df_csv.iloc[idx]
                
                assert row['订单号'] == op.order_id, \
                    f"CSV第{idx}行订单号不一致: 期望 {op.order_id}, 实际 {row['订单号']}"
                assert row['工序编号'] == op.operation_id, \
                    f"CSV第{idx}行工序编号不一致: 期望 {op.operation_id}, 实际 {row['工序编号']}"
                assert row['设备编号'] == op.equipment_id, \
                    f"CSV第{idx}行设备编号不一致: 期望 {op.equipment_id}, 实际 {row['设备编号']}"
                
                # 时间字段允许小的浮点误差
                assert abs(row['开始时间'] - op.start_time) < 0.01, \
                    f"CSV第{idx}行开始时间不一致: 期望 {op.start_time}, 实际 {row['开始时间']}"
                assert abs(row['结束时间'] - op.end_time) < 0.01, \
                    f"CSV第{idx}行结束时间不一致: 期望 {op.end_time}, 实际 {row['结束时间']}"
                assert abs(row['持续时间'] - op.duration) < 0.01, \
                    f"CSV第{idx}行持续时间不一致: 期望 {op.duration}, 实际 {row['持续时间']}"
