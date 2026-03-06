"""
验证示例数据文件的完整性和可用性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_layer.parser import DataParser
from data_layer.validator import DataValidator


def verify_example_data():
    """验证示例数据文件"""
    
    print("=" * 60)
    print("验证示例数据文件")
    print("=" * 60)
    
    # 初始化解析器和验证器
    parser = DataParser()
    validator = DataValidator()
    
    # Determine the correct file path
    if os.path.exists('tests/example_data.xlsx'):
        file_path = 'tests/example_data.xlsx'
    else:
        file_path = 'example_data.xlsx'
    
    # 1. 解析订单数据
    print("\n1. 解析订单数据...")
    try:
        orders = parser.parse_orders(file_path)
        print(f"   ✓ 成功解析 {len(orders)} 个订单")
        print(f"   - 第一个订单: {orders[0].order_id}, 产品: {orders[0].product_id}, 数量: {orders[0].quantity}")
    except Exception as e:
        print(f"   ✗ 解析失败: {e}")
        return False
    
    # 2. 验证订单数据
    print("\n2. 验证订单数据...")
    validation_result = validator.validate_orders(orders)
    if validation_result.is_valid:
        print(f"   ✓ 订单数据验证通过")
    else:
        print(f"   ✗ 订单数据验证失败:")
        for error in validation_result.errors:
            print(f"     - {error}")
        return False
    
    # 3. 解析工艺路线数据
    print("\n3. 解析工艺路线数据...")
    try:
        processes = parser.parse_processes(file_path)
        print(f"   ✓ 成功解析 {len(processes)} 个工序")
        print(f"   - 第一个工序: {processes[0].operation_id}, 产品: {processes[0].product_id}, 工时: {processes[0].standard_time}h")
    except Exception as e:
        print(f"   ✗ 解析失败: {e}")
        return False
    
    # 4. 验证工艺路线数据
    print("\n4. 验证工艺路线数据...")
    validation_result = validator.validate_processes(processes)
    if validation_result.is_valid:
        print(f"   ✓ 工艺路线数据验证通过")
    else:
        print(f"   ✗ 工艺路线数据验证失败:")
        for error in validation_result.errors:
            print(f"     - {error}")
        return False
    
    # 5. 解析设备数据
    print("\n5. 解析设备数据...")
    try:
        equipment = parser.parse_equipment(file_path)
        print(f"   ✓ 成功解析 {len(equipment)} 台设备")
        print(f"   - 第一台设备: {equipment[0].equipment_id}, 产能: {equipment[0].capacity}h/天")
    except Exception as e:
        print(f"   ✗ 解析失败: {e}")
        return False
    
    # 6. 验证设备数据
    print("\n6. 验证设备数据...")
    validation_result = validator.validate_equipment(equipment)
    if validation_result.is_valid:
        print(f"   ✓ 设备数据验证通过")
    else:
        print(f"   ✗ 设备数据验证失败:")
        for error in validation_result.errors:
            print(f"     - {error}")
        return False
    
    # 7. 验证数据一致性
    print("\n7. 验证数据一致性...")
    validation_result = validator.validate_consistency(orders, processes, equipment)
    if validation_result.is_valid:
        print(f"   ✓ 数据一致性验证通过")
    else:
        print(f"   ✗ 数据一致性验证失败:")
        for error in validation_result.errors:
            print(f"     - {error}")
        return False
    
    # 8. 统计信息
    print("\n" + "=" * 60)
    print("数据统计")
    print("=" * 60)
    print(f"订单数量: {len(orders)}")
    print(f"产品种类: {len(set(o.product_id for o in orders))}")
    print(f"工序总数: {len(processes)}")
    print(f"设备数量: {len(equipment)}")
    
    product_ids = set(o.product_id for o in orders)
    print(f"\n产品列表:")
    for pid in sorted(product_ids):
        product_orders = [o for o in orders if o.product_id == pid]
        product_processes = [p for p in processes if p.product_id == pid]
        total_qty = sum(o.quantity for o in product_orders)
        print(f"  - {pid}: {len(product_orders)} 个订单, {len(product_processes)} 道工序, 总数量 {total_qty} 件")
    
    print("\n" + "=" * 60)
    print("✓ 示例数据文件验证完成，所有检查通过！")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    success = verify_example_data()
    sys.exit(0 if success else 1)
