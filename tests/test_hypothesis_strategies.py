"""
测试 Hypothesis 策略
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, settings
from tests.data_generators import order_strategy, process_strategy, equipment_strategy


@given(order_strategy())
@settings(max_examples=10)
def test_order_strategy(order):
    """测试订单策略生成有效的订单对象"""
    assert order.order_id is not None
    assert len(order.order_id) >= 5
    assert order.product_id is not None
    assert order.quantity > 0
    assert order.quantity <= 200
    assert 1 <= order.priority <= 5
    assert isinstance(order.is_urgent, bool)


@given(process_strategy())
@settings(max_examples=10)
def test_process_strategy(process):
    """测试工艺路线策略生成有效的工艺对象"""
    assert process.product_id is not None
    assert process.operation_id is not None
    assert process.operation_name is not None
    assert process.sequence >= 1
    assert process.standard_time > 0
    assert process.required_equipment is not None
    
    # 验证前置工序逻辑
    if process.sequence > 1:
        assert process.predecessor is not None
    else:
        assert process.predecessor is None


@given(equipment_strategy())
@settings(max_examples=10)
def test_equipment_strategy(equipment):
    """测试设备策略生成有效的设备对象"""
    assert equipment.equipment_id is not None
    assert equipment.equipment_type is not None
    assert equipment.capacity >= 4.0
    assert equipment.capacity <= 12.0
    assert equipment.changeover_time >= 0.0
    assert equipment.available_end > equipment.available_start


if __name__ == '__main__':
    print("测试订单策略...")
    test_order_strategy()
    print("✓ 订单策略测试通过")
    
    print("测试工艺路线策略...")
    test_process_strategy()
    print("✓ 工艺路线策略测试通过")
    
    print("测试设备策略...")
    test_equipment_strategy()
    print("✓ 设备策略测试通过")
    
    print("\n所有 Hypothesis 策略测试通过！")
