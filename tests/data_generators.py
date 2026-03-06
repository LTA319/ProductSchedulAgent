"""
测试数据生成器

提供随机数据生成函数，用于属性测试和压力测试。
生成符合业务规则的随机订单、工艺路线和设备数据。
"""

import random
import string
from datetime import datetime, timedelta
from typing import List, Tuple
from data_layer.models import Order, Process, Equipment


def generate_random_orders(
    num_orders: int = 10,
    num_products: int = 5,
    base_date: datetime = None,
    min_quantity: int = 10,
    max_quantity: int = 100
) -> List[Order]:
    """
    生成随机订单数据
    
    Args:
        num_orders: 订单数量
        num_products: 产品种类数量
        base_date: 基准日期（默认为当前日期）
        min_quantity: 最小生产数量
        max_quantity: 最大生产数量
        
    Returns:
        订单对象列表
    """
    if base_date is None:
        base_date = datetime.now()
    
    # 生成产品编码列表
    product_ids = [f'PROD-{i:03d}' for i in range(1, num_products + 1)]
    
    orders = []
    for i in range(1, num_orders + 1):
        order = Order(
            order_id=f'SO{base_date.strftime("%Y%m%d")}-{i:03d}',
            product_id=random.choice(product_ids),
            quantity=random.randint(min_quantity, max_quantity),
            due_date=base_date + timedelta(days=random.randint(3, 15)),
            priority=random.randint(1, 5),
            is_urgent=random.choice([True, False])
        )
        orders.append(order)
    
    return orders


def generate_random_processes(
    product_ids: List[str],
    min_operations: int = 2,
    max_operations: int = 5,
    equipment_ids: List[str] = None,
    min_time: float = 0.1,
    max_time: float = 0.5
) -> List[Process]:
    """
    生成随机工艺路线数据
    
    Args:
        product_ids: 产品编码列表
        min_operations: 每个产品的最小工序数
        max_operations: 每个产品的最大工序数
        equipment_ids: 可用设备编号列表（如果为None，自动生成）
        min_time: 最小标准工时（小时）
        max_time: 最大标准工时（小时）
        
    Returns:
        工艺路线对象列表
    """
    if equipment_ids is None:
        equipment_ids = [f'M{i:02d}' for i in range(1, 9)]
    
    # 工序名称池
    operation_names = [
        '数控车外圆', '数控车内孔', '铣平面', '铣槽', '铣键槽',
        '钻孔', '攻丝', '磨外圆', '磨内孔', '车端面'
    ]
    
    processes = []
    for product_id in product_ids:
        # 为每个产品生成随机数量的工序
        num_operations = random.randint(min_operations, max_operations)
        
        for seq in range(1, num_operations + 1):
            # 确定前置工序
            predecessor = None
            if seq > 1:
                predecessor = f'OP{(seq-1)*10:03d}'
            
            # 随机选择1-2个可用设备
            num_equipment = random.randint(1, min(2, len(equipment_ids)))
            required_equipment = random.choice(equipment_ids)
            
            process = Process(
                product_id=product_id,
                operation_id=f'OP{seq*10:03d}',
                operation_name=random.choice(operation_names),
                sequence=seq,
                standard_time=round(random.uniform(min_time, max_time), 2),
                required_equipment=required_equipment,
                predecessor=predecessor
            )
            processes.append(process)
    
    return processes


def generate_random_equipment(
    num_equipment: int = 8,
    base_date: datetime = None,
    min_capacity: float = 6.0,
    max_capacity: float = 10.0,
    min_changeover: float = 0.0,
    max_changeover: float = 0.5
) -> List[Equipment]:
    """
    生成随机设备数据
    
    Args:
        num_equipment: 设备数量
        base_date: 基准日期（默认为当前日期）
        min_capacity: 最小每日产能（小时）
        max_capacity: 最大每日产能（小时）
        min_changeover: 最小换产时间（小时）
        max_changeover: 最大换产时间（小时）
        
    Returns:
        设备对象列表
    """
    if base_date is None:
        base_date = datetime.now()
    
    # 设备类型池
    equipment_types = [
        '数控车床', '立式加工中心', '摇臂钻床', '台钻',
        '外圆磨床', '攻丝机', '滚齿机', '铣床'
    ]
    
    equipment_list = []
    for i in range(1, num_equipment + 1):
        equipment = Equipment(
            equipment_id=f'M{i:02d}',
            equipment_type=f'M{i:02d}',  # 使用设备编号作为类型
            available_start=base_date,
            available_end=base_date + timedelta(days=365),  # 一年可用期
            capacity=round(random.uniform(min_capacity, max_capacity), 1),
            changeover_time=round(random.uniform(min_changeover, max_changeover), 2)
        )
        equipment_list.append(equipment)
    
    return equipment_list


def generate_complete_dataset(
    num_orders: int = 10,
    num_products: int = 5,
    num_equipment: int = 8,
    min_operations_per_product: int = 2,
    max_operations_per_product: int = 5
) -> Tuple[List[Order], List[Process], List[Equipment]]:
    """
    生成完整的测试数据集（订单、工艺路线、设备）
    
    确保数据之间的引用关系正确：
    - 订单引用的产品在工艺路线中存在
    - 工艺路线引用的设备在设备列表中存在
    
    Args:
        num_orders: 订单数量
        num_products: 产品种类数量
        num_equipment: 设备数量
        min_operations_per_product: 每个产品的最小工序数
        max_operations_per_product: 每个产品的最大工序数
        
    Returns:
        (订单列表, 工艺路线列表, 设备列表)
    """
    # 生成设备
    equipment_list = generate_random_equipment(num_equipment)
    equipment_ids = [eq.equipment_id for eq in equipment_list]
    
    # 生成产品编码
    product_ids = [f'PROD-{i:03d}' for i in range(1, num_products + 1)]
    
    # 生成工艺路线
    processes = generate_random_processes(
        product_ids=product_ids,
        min_operations=min_operations_per_product,
        max_operations=max_operations_per_product,
        equipment_ids=equipment_ids
    )
    
    # 生成订单
    orders = generate_random_orders(
        num_orders=num_orders,
        num_products=num_products
    )
    
    return orders, processes, equipment_list


def generate_simple_dataset() -> Tuple[List[Order], List[Process], List[Equipment]]:
    """
    生成简单的测试数据集（用于快速测试）
    
    Returns:
        (订单列表, 工艺路线列表, 设备列表)
    """
    return generate_complete_dataset(
        num_orders=3,
        num_products=2,
        num_equipment=3,
        min_operations_per_product=2,
        max_operations_per_product=3
    )


def generate_large_dataset() -> Tuple[List[Order], List[Process], List[Equipment]]:
    """
    生成大规模测试数据集（用于压力测试）
    
    Returns:
        (订单列表, 工艺路线列表, 设备列表)
    """
    return generate_complete_dataset(
        num_orders=50,
        num_products=20,
        num_equipment=15,
        min_operations_per_product=3,
        max_operations_per_product=8
    )


# Hypothesis strategies for property-based testing
try:
    from hypothesis import strategies as st
    from hypothesis.strategies import composite
    
    @composite
    def order_strategy(draw, base_date=None):
        """Hypothesis strategy for generating Order objects"""
        if base_date is None:
            base_date = datetime(2026, 3, 6)
        
        return Order(
            order_id=draw(st.text(min_size=5, max_size=20, alphabet=string.ascii_uppercase + string.digits)),
            product_id=draw(st.text(min_size=5, max_size=15, alphabet=string.ascii_uppercase + string.digits + '-')),
            quantity=draw(st.integers(min_value=1, max_value=200)),
            due_date=base_date + timedelta(days=draw(st.integers(min_value=1, max_value=30))),
            priority=draw(st.integers(min_value=1, max_value=5)),
            is_urgent=draw(st.booleans())
        )
    
    @composite
    def process_strategy(draw, product_id=None, sequence=None):
        """Hypothesis strategy for generating Process objects"""
        if product_id is None:
            product_id = draw(st.text(min_size=5, max_size=15, alphabet=string.ascii_uppercase + string.digits + '-'))
        
        if sequence is None:
            sequence = draw(st.integers(min_value=1, max_value=10))
        
        predecessor = None
        if sequence > 1:
            predecessor = f'OP{(sequence-1)*10:03d}'
        
        return Process(
            product_id=product_id,
            operation_id=f'OP{sequence*10:03d}',
            operation_name=draw(st.sampled_from(['车削', '铣削', '钻孔', '磨削', '攻丝'])),
            sequence=sequence,
            standard_time=draw(st.floats(min_value=0.05, max_value=2.0)),
            required_equipment=draw(st.sampled_from([f'M{i:02d}' for i in range(1, 11)])),
            predecessor=predecessor
        )
    
    @composite
    def equipment_strategy(draw, base_date=None):
        """Hypothesis strategy for generating Equipment objects"""
        if base_date is None:
            base_date = datetime(2026, 3, 6)
        
        equipment_id = draw(st.text(min_size=2, max_size=10, alphabet=string.ascii_uppercase + string.digits))
        
        return Equipment(
            equipment_id=equipment_id,
            equipment_type=equipment_id,
            available_start=base_date,
            available_end=base_date + timedelta(days=draw(st.integers(min_value=30, max_value=365))),
            capacity=draw(st.floats(min_value=4.0, max_value=12.0)),
            changeover_time=draw(st.floats(min_value=0.0, max_value=1.0))
        )
    
except ImportError:
    # Hypothesis not installed, skip strategy definitions
    pass
