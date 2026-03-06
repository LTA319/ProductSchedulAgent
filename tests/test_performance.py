"""
性能验证测试

测试小规模问题（10 订单，5 设备）的求解时间
确保在 10 秒内完成
"""

import pytest
from datetime import datetime, timedelta
from data_layer.models import Order, Process, Equipment
from business_logic.scheduler import Scheduler


class TestPerformance:
    """性能验证测试类"""
    
    def test_small_scale_problem_performance(self):
        """
        测试小规模问题的求解性能
        
        规模：10 订单，5 设备，每个订单 3-5 道工序
        要求：在 10 秒内完成求解
        """
        # 创建 10 个订单
        orders = []
        for i in range(10):
            order = Order(
                order_id=f"ORD{i+1:03d}",
                product_id=f"PROD{(i % 3) + 1:03d}",  # 3 种产品
                quantity=10,
                due_date=datetime.now() + timedelta(days=7),
                priority=3,
                is_urgent=False
            )
            orders.append(order)
        
        # 创建 3 种产品的工艺路线（每种产品 3-5 道工序）
        processes = []
        
        # 产品 1：3 道工序
        processes.extend([
            Process(
                product_id="PROD001",
                operation_id="OP001_P1",
                operation_name="粗加工",
                sequence=1,
                standard_time=2.0,
                required_equipment="车床",
                predecessor=None
            ),
            Process(
                product_id="PROD001",
                operation_id="OP002_P1",
                operation_name="精加工",
                sequence=2,
                standard_time=1.5,
                required_equipment="铣床",
                predecessor="OP001_P1"
            ),
            Process(
                product_id="PROD001",
                operation_id="OP003_P1",
                operation_name="检验",
                sequence=3,
                standard_time=0.5,
                required_equipment="检测设备",
                predecessor="OP002_P1"
            )
        ])
        
        # 产品 2：4 道工序
        processes.extend([
            Process(
                product_id="PROD002",
                operation_id="OP001_P2",
                operation_name="下料",
                sequence=1,
                standard_time=1.0,
                required_equipment="车床",
                predecessor=None
            ),
            Process(
                product_id="PROD002",
                operation_id="OP002_P2",
                operation_name="粗加工",
                sequence=2,
                standard_time=2.5,
                required_equipment="铣床",
                predecessor="OP001_P2"
            ),
            Process(
                product_id="PROD002",
                operation_id="OP003_P2",
                operation_name="精加工",
                sequence=3,
                standard_time=1.5,
                required_equipment="磨床",
                predecessor="OP002_P2"
            ),
            Process(
                product_id="PROD002",
                operation_id="OP004_P2",
                operation_name="检验",
                sequence=4,
                standard_time=0.5,
                required_equipment="检测设备",
                predecessor="OP003_P2"
            )
        ])
        
        # 产品 3：5 道工序
        processes.extend([
            Process(
                product_id="PROD003",
                operation_id="OP001_P3",
                operation_name="下料",
                sequence=1,
                standard_time=1.0,
                required_equipment="车床",
                predecessor=None
            ),
            Process(
                product_id="PROD003",
                operation_id="OP002_P3",
                operation_name="粗加工",
                sequence=2,
                standard_time=2.0,
                required_equipment="铣床",
                predecessor="OP001_P3"
            ),
            Process(
                product_id="PROD003",
                operation_id="OP003_P3",
                operation_name="热处理",
                sequence=3,
                standard_time=3.0,
                required_equipment="热处理炉",
                predecessor="OP002_P3"
            ),
            Process(
                product_id="PROD003",
                operation_id="OP004_P3",
                operation_name="精加工",
                sequence=4,
                standard_time=1.5,
                required_equipment="磨床",
                predecessor="OP003_P3"
            ),
            Process(
                product_id="PROD003",
                operation_id="OP005_P3",
                operation_name="检验",
                sequence=5,
                standard_time=0.5,
                required_equipment="检测设备",
                predecessor="OP004_P3"
            )
        ])
        
        # 创建 5 台设备
        equipment = [
            Equipment(
                equipment_id="EQ001",
                equipment_type="车床",
                available_start=datetime.now(),
                available_end=datetime.now() + timedelta(days=30),
                capacity=8.0,
                changeover_time=0.5
            ),
            Equipment(
                equipment_id="EQ002",
                equipment_type="铣床",
                available_start=datetime.now(),
                available_end=datetime.now() + timedelta(days=30),
                capacity=8.0,
                changeover_time=0.5
            ),
            Equipment(
                equipment_id="EQ003",
                equipment_type="磨床",
                available_start=datetime.now(),
                available_end=datetime.now() + timedelta(days=30),
                capacity=8.0,
                changeover_time=0.5
            ),
            Equipment(
                equipment_id="EQ004",
                equipment_type="热处理炉",
                available_start=datetime.now(),
                available_end=datetime.now() + timedelta(days=30),
                capacity=24.0,  # 热处理炉可以连续运行
                changeover_time=0.0
            ),
            Equipment(
                equipment_id="EQ005",
                equipment_type="检测设备",
                available_start=datetime.now(),
                available_end=datetime.now() + timedelta(days=30),
                capacity=8.0,
                changeover_time=0.2
            )
        ]
        
        # 执行排程
        scheduler = Scheduler(orders, processes, equipment)
        schedule_result = scheduler.solve()
        
        # 验证求解成功
        assert schedule_result is not None, "排程结果为空"
        assert schedule_result.status in ['OPTIMAL', 'FEASIBLE'], \
            f"排程失败，状态: {schedule_result.status}"
        
        # 验证求解时间在 10 秒内
        assert schedule_result.solve_time < 10.0, \
            f"求解时间 {schedule_result.solve_time:.2f} 秒超过 10 秒限制"
        
        # 验证排程结果完整性
        assert len(schedule_result.operations) > 0, "排程结果中没有工序"
        
        # 验证总完工时间合理
        assert schedule_result.makespan > 0, "总完工时间应该大于 0"
        
        print(f"\n✅ 性能测试通过！")
        print(f"   问题规模: {len(orders)} 订单, {len(processes)} 工序, {len(equipment)} 设备")
        print(f"   求解时间: {schedule_result.solve_time:.2f} 秒")
        print(f"   求解状态: {schedule_result.status}")
        print(f"   总完工时间: {schedule_result.makespan:.2f} 小时")
        print(f"   排程工序数: {len(schedule_result.operations)}")
    
    def test_medium_scale_problem_performance(self):
        """
        测试中等规模问题的求解性能
        
        规模：20 订单，8 设备
        要求：在合理时间内完成（不超过 30 秒）
        """
        # 创建 20 个订单
        orders = []
        for i in range(20):
            order = Order(
                order_id=f"ORD{i+1:03d}",
                product_id=f"PROD{(i % 5) + 1:03d}",  # 5 种产品
                quantity=5,
                due_date=datetime.now() + timedelta(days=10),
                priority=3,
                is_urgent=False
            )
            orders.append(order)
        
        # 创建 5 种产品的工艺路线（每种产品 3 道工序）
        processes = []
        for prod_idx in range(1, 6):
            for op_idx in range(1, 4):
                equipment_types = ["车床", "铣床", "磨床", "钻床", "检测设备"]
                processes.append(
                    Process(
                        product_id=f"PROD{prod_idx:03d}",
                        operation_id=f"OP{op_idx:03d}_P{prod_idx}",
                        operation_name=f"工序{op_idx}",
                        sequence=op_idx,
                        standard_time=1.0 + op_idx * 0.5,
                        required_equipment=equipment_types[op_idx - 1],
                        predecessor=f"OP{op_idx-1:03d}_P{prod_idx}" if op_idx > 1 else None
                    )
                )
        
        # 创建 8 台设备
        equipment_types = ["车床", "铣床", "磨床", "钻床", "检测设备"]
        equipment = []
        for i in range(8):
            equipment.append(
                Equipment(
                    equipment_id=f"EQ{i+1:03d}",
                    equipment_type=equipment_types[i % len(equipment_types)],
                    available_start=datetime.now(),
                    available_end=datetime.now() + timedelta(days=30),
                    capacity=8.0,
                    changeover_time=0.3
                )
            )
        
        # 执行排程
        scheduler = Scheduler(orders, processes, equipment)
        schedule_result = scheduler.solve()
        
        # 验证求解成功
        assert schedule_result is not None, "排程结果为空"
        assert schedule_result.status in ['OPTIMAL', 'FEASIBLE'], \
            f"排程失败，状态: {schedule_result.status}"
        
        # 验证求解时间在 30 秒内
        assert schedule_result.solve_time < 30.0, \
            f"求解时间 {schedule_result.solve_time:.2f} 秒超过 30 秒限制"
        
        # 验证排程结果完整性
        assert len(schedule_result.operations) > 0, "排程结果中没有工序"
        
        print(f"\n✅ 中等规模性能测试通过！")
        print(f"   问题规模: {len(orders)} 订单, {len(processes)} 工序, {len(equipment)} 设备")
        print(f"   求解时间: {schedule_result.solve_time:.2f} 秒")
        print(f"   求解状态: {schedule_result.status}")
        print(f"   总完工时间: {schedule_result.makespan:.2f} 小时")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
