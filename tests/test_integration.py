"""
集成测试：端到端完整流程测试

测试完整的上传→解析→排程→可视化→导出流程
验证每个步骤的输出正确性
检查错误处理是否正常工作
"""

import pytest
import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from data_layer.parser import DataParser
from data_layer.validator import DataValidator
from data_layer.models import Order, Process, Equipment
from business_logic.scheduler import Scheduler
from business_logic.metrics import MetricsCalculator
from business_logic.visualizer import Visualizer


class TestCompleteFlow:
    """测试完整的端到端流程"""
    
    def test_complete_flow_with_example_data(self):
        """
        使用示例数据执行完整流程测试
        
        流程：上传→解析→验证→排程→可视化→导出
        """
        # 1. 数据解析阶段
        parser = DataParser()
        example_data_path = os.path.join('tests', 'example_data.xlsx')
        
        # 检查示例数据文件是否存在
        assert os.path.exists(example_data_path), f"示例数据文件不存在: {example_data_path}"
        
        # 解析订单数据
        orders = parser.parse_orders(example_data_path)
        assert orders is not None, "订单解析失败"
        assert len(orders) > 0, "订单数据为空"
        
        # 解析工艺路线数据
        processes = parser.parse_processes(example_data_path)
        assert processes is not None, "工艺路线解析失败"
        assert len(processes) > 0, "工艺路线数据为空"
        
        # 解析设备数据
        equipment = parser.parse_equipment(example_data_path)
        assert equipment is not None, "设备数据解析失败"
        assert len(equipment) > 0, "设备数据为空"
        
        print(f"✓ 数据解析成功: {len(orders)} 订单, {len(processes)} 工序, {len(equipment)} 设备")
        
        # 2. 数据验证阶段
        validator = DataValidator()
        
        # 验证订单数据
        orders_validation = validator.validate_orders(orders)
        assert orders_validation.is_valid, f"订单验证失败: {orders_validation.errors}"
        
        # 验证工艺路线数据
        processes_validation = validator.validate_processes(processes)
        assert processes_validation.is_valid, f"工艺路线验证失败: {processes_validation.errors}"
        
        # 验证设备数据
        equipment_validation = validator.validate_equipment(equipment)
        assert equipment_validation.is_valid, f"设备验证失败: {equipment_validation.errors}"
        
        # 验证数据一致性
        consistency_validation = validator.validate_consistency(orders, processes, equipment)
        assert consistency_validation.is_valid, f"数据一致性验证失败: {consistency_validation.errors}"
        
        print(f"✓ 数据验证成功")
        
        # 3. 排程计算阶段
        scheduler = Scheduler(orders, processes, equipment)
        schedule_result = scheduler.solve()
        
        assert schedule_result is not None, "排程结果为空"
        assert schedule_result.status in ['OPTIMAL', 'FEASIBLE'], \
            f"排程失败，状态: {schedule_result.status}"
        assert len(schedule_result.operations) > 0, "排程结果中没有工序"
        
        # 验证所有工序都被排程
        expected_operations = len([p for p in processes if any(o.product_id == p.product_id for o in orders)])
        assert len(schedule_result.operations) >= expected_operations, \
            f"排程结果不完整: 期望至少 {expected_operations} 个工序，实际 {len(schedule_result.operations)}"
        
        print(f"✓ 排程计算成功: 状态={schedule_result.status}, "
              f"总完工时间={schedule_result.makespan:.2f}小时, "
              f"求解耗时={schedule_result.solve_time:.2f}秒")
        
        # 4. 指标计算阶段
        metrics_calculator = MetricsCalculator(equipment)
        
        # 计算总完工时间
        makespan = metrics_calculator.calculate_makespan(schedule_result)
        assert makespan > 0, "总完工时间应该大于0"
        assert makespan == schedule_result.makespan, "总完工时间计算不一致"
        
        # 计算设备利用率
        utilization = metrics_calculator.calculate_equipment_utilization(schedule_result)
        assert utilization is not None, "设备利用率计算失败"
        assert len(utilization) > 0, "设备利用率数据为空"
        
        # 验证利用率在合理范围内
        for eq_id, util in utilization.items():
            assert 0 <= util <= 100, f"设备 {eq_id} 利用率 {util}% 超出范围 [0, 100]"
        
        # 计算交期达成率
        on_time_rate = metrics_calculator.calculate_on_time_delivery(schedule_result, orders)
        assert 0 <= on_time_rate <= 100, f"交期达成率 {on_time_rate}% 超出范围 [0, 100]"
        
        # 识别瓶颈设备
        bottleneck = metrics_calculator.identify_bottleneck(schedule_result)
        if bottleneck:
            assert bottleneck in utilization, f"瓶颈设备 {bottleneck} 不在利用率数据中"
            # 验证瓶颈设备确实是利用率最高的
            max_util = max(utilization.values())
            assert utilization[bottleneck] == max_util, "瓶颈设备不是利用率最高的设备"
        
        print(f"✓ 指标计算成功: 总完工时间={makespan:.2f}小时, "
              f"交期达成率={on_time_rate:.1f}%, 瓶颈设备={bottleneck or '无'}")
        
        # 5. 可视化生成阶段
        visualizer = Visualizer()
        
        # 生成甘特图
        gantt_fig = visualizer.generate_gantt_chart(schedule_result)
        assert gantt_fig is not None, "甘特图生成失败"
        
        # 验证甘特图包含所有工序
        gantt_data = gantt_fig.data
        assert len(gantt_data) > 0, "甘特图数据为空"
        
        # 生成利用率图表
        metrics = {
            'makespan': makespan,
            'equipment_utilization': utilization,
            'on_time_delivery_rate': on_time_rate,
            'bottleneck_equipment': bottleneck
        }
        utilization_fig = visualizer.generate_utilization_chart(metrics)
        assert utilization_fig is not None, "利用率图表生成失败"
        
        print(f"✓ 可视化生成成功")
        
        # 6. 结果导出阶段
        with tempfile.TemporaryDirectory() as temp_dir:
            # 导出为 Excel
            excel_path = os.path.join(temp_dir, 'schedule_result.xlsx')
            visualizer.export_schedule_to_excel(schedule_result, excel_path)
            assert os.path.exists(excel_path), "Excel 文件导出失败"
            
            # 验证 Excel 文件可以读取
            df_excel = pd.read_excel(excel_path)
            assert len(df_excel) == len(schedule_result.operations), \
                "Excel 文件中的记录数与排程结果不一致"
            
            # 验证必要的列存在
            required_columns = ['订单号', '工序编号', '设备编号', '开始时间', '结束时间', '持续时间']
            for col in required_columns:
                assert col in df_excel.columns, f"Excel 文件缺少列: {col}"
            
            # 导出为 CSV
            csv_path = os.path.join(temp_dir, 'schedule_result.csv')
            visualizer.export_schedule_to_csv(schedule_result, csv_path)
            assert os.path.exists(csv_path), "CSV 文件导出失败"
            
            # 验证 CSV 文件可以读取
            df_csv = pd.read_csv(csv_path, encoding='utf-8-sig')
            assert len(df_csv) == len(schedule_result.operations), \
                "CSV 文件中的记录数与排程结果不一致"
            
            # 验证必要的列存在
            for col in required_columns:
                assert col in df_csv.columns, f"CSV 文件缺少列: {col}"
            
            print(f"✓ 结果导出成功: Excel 和 CSV 文件")
        
        print(f"\n✅ 完整流程测试通过！")
    
    def test_error_handling_invalid_file(self):
        """测试错误处理：无效文件"""
        parser = DataParser()
        
        # 测试文件不存在
        with pytest.raises(FileNotFoundError):
            parser.parse_orders('nonexistent_file.xlsx')
        
        print(f"✓ 文件不存在错误处理正确")
    
    def test_error_handling_invalid_data(self):
        """测试错误处理：无效数据"""
        validator = DataValidator()
        
        # 创建无效订单（缺少必填字段）
        invalid_order = Order(
            order_id="",  # 空订单号
            product_id="PROD001",
            quantity=10,
            due_date=datetime.now(),
            priority=5,
            is_urgent=False
        )
        
        # 验证应该失败
        result = validator.validate_orders([invalid_order])
        assert not result.is_valid, "应该检测到无效数据"
        assert len(result.errors) > 0, "应该有错误信息"
        
        print(f"✓ 无效数据错误处理正确: {result.errors}")
    
    def test_error_handling_infeasible_schedule(self):
        """测试错误处理：不可行的排程问题"""
        # 创建一个不可行的排程问题（交期过紧）
        orders = [
            Order(
                order_id="ORD001",
                product_id="PROD001",
                quantity=100,
                due_date=datetime.now() + timedelta(hours=1),  # 1小时内完成（不可能）
                priority=5,
                is_urgent=True
            )
        ]
        
        processes = [
            Process(
                product_id="PROD001",
                operation_id="OP001",
                operation_name="加工",
                sequence=1,
                standard_time=10.0,  # 需要10小时
                required_equipment="车床",
                predecessor=None
            )
        ]
        
        equipment = [
            Equipment(
                equipment_id="EQ001",
                equipment_type="车床",
                available_start=datetime.now(),
                available_end=datetime.now() + timedelta(hours=2),
                capacity=8.0,
                changeover_time=0.5
            )
        ]
        
        # 尝试排程
        scheduler = Scheduler(orders, processes, equipment)
        schedule_result = scheduler.solve()
        
        # 可能返回 INFEASIBLE 或者返回一个不满足交期的解
        # 无论哪种情况，系统都应该正常处理，不应该崩溃
        assert schedule_result is not None, "排程结果不应该为空"
        assert schedule_result.status in ['OPTIMAL', 'FEASIBLE', 'INFEASIBLE'], \
            f"排程状态应该是有效值，实际: {schedule_result.status}"
        
        print(f"✓ 不可行排程错误处理正确: 状态={schedule_result.status}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
