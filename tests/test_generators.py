"""
测试数据生成器的单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.data_generators import (
    generate_random_orders,
    generate_random_processes,
    generate_random_equipment,
    generate_complete_dataset,
    generate_simple_dataset,
    generate_large_dataset
)


def test_generate_random_orders():
    """测试订单生成器"""
    orders = generate_random_orders(num_orders=5, num_products=3)
    
    assert len(orders) == 5
    assert all(order.quantity > 0 for order in orders)
    assert all(1 <= order.priority <= 5 for order in orders)
    print("✓ 订单生成器测试通过")


def test_generate_random_processes():
    """测试工艺路线生成器"""
    product_ids = ['PROD-001', 'PROD-002']
    processes = generate_random_processes(product_ids, min_operations=2, max_operations=4)
    
    assert len(processes) >= 4  # 至少2个产品 * 2个工序
    assert all(p.standard_time > 0 for p in processes)
    assert all(p.sequence >= 1 for p in processes)
    
    # 验证前置工序逻辑
    for process in processes:
        if process.sequence > 1:
            assert process.predecessor is not None
        else:
            assert process.predecessor is None
    
    print("✓ 工艺路线生成器测试通过")


def test_generate_random_equipment():
    """测试设备生成器"""
    equipment = generate_random_equipment(num_equipment=5)
    
    assert len(equipment) == 5
    assert all(eq.capacity > 0 for eq in equipment)
    assert all(eq.changeover_time >= 0 for eq in equipment)
    assert all(eq.available_end > eq.available_start for eq in equipment)
    print("✓ 设备生成器测试通过")


def test_generate_complete_dataset():
    """测试完整数据集生成器"""
    orders, processes, equipment = generate_complete_dataset(
        num_orders=10,
        num_products=5,
        num_equipment=8
    )
    
    assert len(orders) == 10
    assert len(equipment) == 8
    assert len(processes) >= 10  # 至少每个产品有2个工序
    
    # 验证引用完整性
    product_ids_in_orders = set(o.product_id for o in orders)
    product_ids_in_processes = set(p.product_id for p in processes)
    equipment_ids_in_processes = set(p.required_equipment for p in processes)
    equipment_ids_in_equipment = set(e.equipment_id for e in equipment)
    
    # 订单中的产品应该在工艺路线中存在
    assert product_ids_in_orders.issubset(product_ids_in_processes)
    
    # 工艺路线中的设备应该在设备列表中存在
    assert equipment_ids_in_processes.issubset(equipment_ids_in_equipment)
    
    print("✓ 完整数据集生成器测试通过")


def test_generate_simple_dataset():
    """测试简单数据集生成器"""
    orders, processes, equipment = generate_simple_dataset()
    
    assert len(orders) == 3
    assert len(equipment) == 3
    assert len(processes) >= 4  # 至少2个产品 * 2个工序
    print("✓ 简单数据集生成器测试通过")


def test_generate_large_dataset():
    """测试大规模数据集生成器"""
    orders, processes, equipment = generate_large_dataset()
    
    assert len(orders) == 50
    assert len(equipment) == 15
    assert len(processes) >= 60  # 至少20个产品 * 3个工序
    print("✓ 大规模数据集生成器测试通过")


if __name__ == '__main__':
    test_generate_random_orders()
    test_generate_random_processes()
    test_generate_random_equipment()
    test_generate_complete_dataset()
    test_generate_simple_dataset()
    test_generate_large_dataset()
    print("\n所有数据生成器测试通过！")
