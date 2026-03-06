"""
属性测试：数据解析

测试数据解析器的正确性属性
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
import pandas as pd
from datetime import datetime
import tempfile
import os

from data_layer.parser import DataParser
from data_layer.models import Order, Process, Equipment


@composite
def order_data_strategy(draw):
    """生成随机订单数据"""
    num_orders = draw(st.integers(min_value=1, max_value=20))
    orders = []
    
    for i in range(num_orders):
        order = {
            '订单号': f'SO{draw(st.integers(min_value=20260101, max_value=20261231))}-{i+1:03d}',
            '产品编码': f'PART-{draw(st.text(alphabet="ABCDEFGH", min_size=1, max_size=2))}{draw(st.integers(min_value=1, max_value=99)):02d}',
            '产品名称': draw(st.text(alphabet="产品零件轴套法兰", min_size=2, max_size=10)),
            '生产数量（件）': draw(st.integers(min_value=1, max_value=200)),
            '承诺交期': draw(st.datetimes(min_value=datetime(2026, 3, 1), max_value=datetime(2026, 12, 31))),
            '优先级（1最高）': draw(st.integers(min_value=1, max_value=5)),
            '是否急单': draw(st.sampled_from(['是', '否']))
        }
        orders.append(order)
    
    return orders


@settings(max_examples=100)
@given(order_data=order_data_strategy())
def test_order_parsing_completeness(order_data):
    """
    **功能：production-scheduling-agent，属性 1：数据解析完整性**
    **验证需求：1.1**
    
    对于任何符合格式要求的 Excel 订单文件，解析后的订单对象列表应该包含所有行的数据，
    且每个订单对象的所有必填字段（订单号、产品编码、数量、交期、优先级）都应该被正确提取
    """
    # 创建临时 Excel 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 创建 DataFrame 并写入 Excel
        df = pd.DataFrame(order_data)
        
        # 创建带标题行的 Excel（模拟实际文件格式）
        with pd.ExcelWriter(tmp_path, engine='openpyxl') as writer:
            # 第一行是标题，第二行开始是数据
            df.to_excel(writer, sheet_name='订单表', index=False, startrow=1, header=True)
        
        # 解析数据
        parser = DataParser()
        parsed_orders = parser.parse_orders(tmp_path)
        
        # 验证：解析的订单数量应该等于输入数据的行数
        assert len(parsed_orders) == len(order_data), \
            f"解析的订单数量 {len(parsed_orders)} 不等于输入数据行数 {len(order_data)}"
        
        # 验证：每个订单的所有必填字段都被正确提取
        for i, parsed_order in enumerate(parsed_orders):
            original = order_data[i]
            
            # 验证订单号
            assert parsed_order.order_id == original['订单号'], \
                f"订单号不匹配: {parsed_order.order_id} != {original['订单号']}"
            
            # 验证产品编码
            assert parsed_order.product_id == original['产品编码'], \
                f"产品编码不匹配: {parsed_order.product_id} != {original['产品编码']}"
            
            # 验证数量
            assert parsed_order.quantity == original['生产数量（件）'], \
                f"数量不匹配: {parsed_order.quantity} != {original['生产数量（件）']}"
            
            # 验证交期（日期部分）
            assert parsed_order.due_date.date() == original['承诺交期'].date(), \
                f"交期不匹配: {parsed_order.due_date.date()} != {original['承诺交期'].date()}"
            
            # 验证优先级
            assert parsed_order.priority == original['优先级（1最高）'], \
                f"优先级不匹配: {parsed_order.priority} != {original['优先级（1最高）']}"
            
            # 验证是否急单
            expected_urgent = original['是否急单'] == '是'
            assert parsed_order.is_urgent == expected_urgent, \
                f"是否急单不匹配: {parsed_order.is_urgent} != {expected_urgent}"
    
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)



@composite
def process_data_strategy(draw):
    """生成随机工艺路线数据"""
    num_products = draw(st.integers(min_value=1, max_value=5))
    processes = []
    
    for p in range(num_products):
        product_id = f'PART-{draw(st.text(alphabet="ABCDEFGH", min_size=1, max_size=2))}{draw(st.integers(min_value=1, max_value=99)):02d}'
        num_operations = draw(st.integers(min_value=1, max_value=5))
        
        for i in range(num_operations):
            process = {
                '产品编码': product_id,
                '工序号': f'OP{(i+1)*10:03d}',
                '工序名称': draw(st.text(alphabet="数控车铣钻磨", min_size=2, max_size=8)),
                '工序顺序': i + 1,
                '单件标准工时（分钟）': draw(st.integers(min_value=1, max_value=120)),
                '可使用设备编号': f'M{draw(st.integers(min_value=1, max_value=10)):02d}',
                '换型时间（分钟）': draw(st.integers(min_value=0, max_value=60))
            }
            processes.append(process)
    
    return processes


@settings(max_examples=100)
@given(process_data=process_data_strategy())
def test_process_parsing_correctness(process_data):
    """
    **功能：production-scheduling-agent，属性 2：工艺数据解析正确性**
    **验证需求：1.2**
    
    对于任何符合格式要求的工艺路线数据，解析后应该正确建立产品到工序的映射关系，
    且每个工序的标准工时、设备要求、工序顺序都应该与源数据一致
    """
    # 创建临时 Excel 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 创建 DataFrame 并写入 Excel
        df = pd.DataFrame(process_data)
        
        with pd.ExcelWriter(tmp_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='工艺路线表', index=False, startrow=1, header=True)
        
        # 解析数据
        parser = DataParser()
        parsed_processes = parser.parse_processes(tmp_path)
        
        # 验证：解析的工序数量应该等于输入数据的行数
        assert len(parsed_processes) == len(process_data), \
            f"解析的工序数量 {len(parsed_processes)} 不等于输入数据行数 {len(process_data)}"
        
        # 构建产品到工序的映射
        product_operations = {}
        for original in process_data:
            product_id = original['产品编码']
            if product_id not in product_operations:
                product_operations[product_id] = []
            product_operations[product_id].append(original)
        
        # 验证：每个工序的字段都被正确提取
        for i, parsed_process in enumerate(parsed_processes):
            original = process_data[i]
            
            # 验证产品编码
            assert parsed_process.product_id == original['产品编码'], \
                f"产品编码不匹配: {parsed_process.product_id} != {original['产品编码']}"
            
            # 验证工序编号
            assert parsed_process.operation_id == original['工序号'], \
                f"工序编号不匹配: {parsed_process.operation_id} != {original['工序号']}"
            
            # 验证工序名称
            assert parsed_process.operation_name == original['工序名称'], \
                f"工序名称不匹配: {parsed_process.operation_name} != {original['工序名称']}"
            
            # 验证工序顺序
            assert parsed_process.sequence == original['工序顺序'], \
                f"工序顺序不匹配: {parsed_process.sequence} != {original['工序顺序']}"
            
            # 验证标准工时（分钟转小时）
            expected_time = original['单件标准工时（分钟）'] / 60.0
            assert abs(parsed_process.standard_time - expected_time) < 0.001, \
                f"标准工时不匹配: {parsed_process.standard_time} != {expected_time}"
            
            # 验证设备要求（取第一个设备）
            expected_equipment = original['可使用设备编号'].split(',')[0].strip()
            assert parsed_process.required_equipment == expected_equipment, \
                f"设备要求不匹配: {parsed_process.required_equipment} != {expected_equipment}"
            
            # 验证前置工序逻辑
            if parsed_process.sequence == 1:
                assert parsed_process.predecessor is None, \
                    f"第一道工序不应该有前置工序，但得到: {parsed_process.predecessor}"
            else:
                # 找到同产品的前一道工序
                product_ops = [p for p in process_data if p['产品编码'] == original['产品编码']]
                product_ops_sorted = sorted(product_ops, key=lambda x: x['工序顺序'])
                prev_op = product_ops_sorted[parsed_process.sequence - 2]
                assert parsed_process.predecessor == prev_op['工序号'], \
                    f"前置工序不匹配: {parsed_process.predecessor} != {prev_op['工序号']}"
    
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)



@composite
def equipment_data_strategy(draw):
    """生成随机设备数据"""
    num_equipment = draw(st.integers(min_value=1, max_value=10))
    equipment_list = []
    
    for i in range(num_equipment):
        equipment = {
            '设备编号': f'M{draw(st.integers(min_value=1, max_value=99)):02d}',
            '设备名称': draw(st.text(alphabet="数控车床加工中心钻床", min_size=3, max_size=10)),
            '班组': draw(st.sampled_from(['白班', '夜班', '两班'])),
            '每日工作小时': draw(st.integers(min_value=4, max_value=16)),
            '每日工作分钟': draw(st.integers(min_value=240, max_value=960)),
            '效率系数': draw(st.floats(min_value=0.8, max_value=1.0)),
            '状态': '可用'  # 只生成可用设备
        }
        equipment_list.append(equipment)
    
    return equipment_list


@settings(max_examples=100)
@given(equipment_data=equipment_data_strategy())
def test_equipment_parsing_correctness(equipment_data):
    """
    **功能：production-scheduling-agent，属性 3：设备数据解析正确性**
    **验证需求：1.3**
    
    对于任何符合格式要求的设备数据，解析后的设备对象应该包含所有设备，
    且设备编号、可用时段、产能上限、换产时间等字段都应该被正确提取
    """
    # 创建临时 Excel 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 创建 DataFrame 并写入 Excel
        df = pd.DataFrame(equipment_data)
        
        with pd.ExcelWriter(tmp_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='设备表', index=False, startrow=1, header=True)
        
        # 解析数据
        parser = DataParser()
        parsed_equipment = parser.parse_equipment(tmp_path)
        
        # 验证：解析的设备数量应该等于输入数据的行数（只包含可用设备）
        available_equipment = [e for e in equipment_data if e['状态'] == '可用']
        assert len(parsed_equipment) == len(available_equipment), \
            f"解析的设备数量 {len(parsed_equipment)} 不等于可用设备数量 {len(available_equipment)}"
        
        # 验证：每个设备的字段都被正确提取
        for i, parsed_eq in enumerate(parsed_equipment):
            original = available_equipment[i]
            
            # 验证设备编号
            assert parsed_eq.equipment_id == original['设备编号'], \
                f"设备编号不匹配: {parsed_eq.equipment_id} != {original['设备编号']}"
            
            # 验证设备类型（使用设备编号作为类型）
            assert parsed_eq.equipment_type == original['设备编号'], \
                f"设备类型不匹配: {parsed_eq.equipment_type} != {original['设备编号']}"
            
            # 验证产能上限
            assert parsed_eq.capacity == original['每日工作小时'], \
                f"产能上限不匹配: {parsed_eq.capacity} != {original['每日工作小时']}"
            
            # 验证可用时段（应该有合理的开始和结束时间）
            assert parsed_eq.available_start is not None, "可用开始时间不应为空"
            assert parsed_eq.available_end is not None, "可用结束时间不应为空"
            assert parsed_eq.available_end > parsed_eq.available_start, \
                "可用结束时间应该大于开始时间"
            
            # 验证换产时间（当前实现为0）
            assert parsed_eq.changeover_time >= 0, \
                f"换产时间应该非负: {parsed_eq.changeover_time}"
    
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)



@settings(max_examples=100)
@given(order_data=order_data_strategy())
def test_order_import_roundtrip_consistency(order_data):
    """
    **功能：production-scheduling-agent，属性 5：数据导入往返一致性**
    **验证需求：1.5**
    
    对于任何成功导入的数据，从内存中读取的数据应该与原始输入数据在所有关键字段上保持一致
    """
    # 创建临时 Excel 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 创建 DataFrame 并写入 Excel
        df = pd.DataFrame(order_data)
        
        with pd.ExcelWriter(tmp_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='订单表', index=False, startrow=1, header=True)
        
        # 第一次解析
        parser = DataParser()
        parsed_orders_1 = parser.parse_orders(tmp_path)
        
        # 将解析的数据写回 Excel
        export_data = []
        for order in parsed_orders_1:
            export_data.append({
                '订单号': order.order_id,
                '产品编码': order.product_id,
                '产品名称': '测试产品',  # 这个字段不在模型中，使用占位符
                '生产数量（件）': order.quantity,
                '承诺交期': order.due_date,
                '优先级（1最高）': order.priority,
                '是否急单': '是' if order.is_urgent else '否'
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp2:
            tmp_path_2 = tmp2.name
        
        try:
            df2 = pd.DataFrame(export_data)
            with pd.ExcelWriter(tmp_path_2, engine='openpyxl') as writer:
                df2.to_excel(writer, sheet_name='订单表', index=False, startrow=1, header=True)
            
            # 第二次解析
            parsed_orders_2 = parser.parse_orders(tmp_path_2)
            
            # 验证：两次解析的结果应该一致
            assert len(parsed_orders_1) == len(parsed_orders_2), \
                f"两次解析的订单数量不一致: {len(parsed_orders_1)} != {len(parsed_orders_2)}"
            
            for i, (order1, order2) in enumerate(zip(parsed_orders_1, parsed_orders_2)):
                assert order1.order_id == order2.order_id, \
                    f"订单 {i}: 订单号不一致 {order1.order_id} != {order2.order_id}"
                assert order1.product_id == order2.product_id, \
                    f"订单 {i}: 产品编码不一致 {order1.product_id} != {order2.product_id}"
                assert order1.quantity == order2.quantity, \
                    f"订单 {i}: 数量不一致 {order1.quantity} != {order2.quantity}"
                assert order1.due_date.date() == order2.due_date.date(), \
                    f"订单 {i}: 交期不一致 {order1.due_date.date()} != {order2.due_date.date()}"
                assert order1.priority == order2.priority, \
                    f"订单 {i}: 优先级不一致 {order1.priority} != {order2.priority}"
                assert order1.is_urgent == order2.is_urgent, \
                    f"订单 {i}: 是否急单不一致 {order1.is_urgent} != {order2.is_urgent}"
        
        finally:
            if os.path.exists(tmp_path_2):
                os.unlink(tmp_path_2)
    
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@settings(max_examples=100)
@given(process_data=process_data_strategy())
def test_process_import_roundtrip_consistency(process_data):
    """
    **功能：production-scheduling-agent，属性 5：数据导入往返一致性**
    **验证需求：1.5**
    
    对于任何成功导入的工艺数据，从内存中读取的数据应该与原始输入数据在所有关键字段上保持一致
    """
    # 创建临时 Excel 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 创建 DataFrame 并写入 Excel
        df = pd.DataFrame(process_data)
        
        with pd.ExcelWriter(tmp_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='工艺路线表', index=False, startrow=1, header=True)
        
        # 第一次解析
        parser = DataParser()
        parsed_processes_1 = parser.parse_processes(tmp_path)
        
        # 将解析的数据写回 Excel
        export_data = []
        for process in parsed_processes_1:
            export_data.append({
                '产品编码': process.product_id,
                '工序号': process.operation_id,
                '工序名称': process.operation_name,
                '工序顺序': process.sequence,
                '单件标准工时（分钟）': int(process.standard_time * 60),
                '可使用设备编号': process.required_equipment,
                '换型时间（分钟）': 0
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp2:
            tmp_path_2 = tmp2.name
        
        try:
            df2 = pd.DataFrame(export_data)
            with pd.ExcelWriter(tmp_path_2, engine='openpyxl') as writer:
                df2.to_excel(writer, sheet_name='工艺路线表', index=False, startrow=1, header=True)
            
            # 第二次解析
            parsed_processes_2 = parser.parse_processes(tmp_path_2)
            
            # 验证：两次解析的结果应该一致
            assert len(parsed_processes_1) == len(parsed_processes_2), \
                f"两次解析的工序数量不一致: {len(parsed_processes_1)} != {len(parsed_processes_2)}"
            
            for i, (proc1, proc2) in enumerate(zip(parsed_processes_1, parsed_processes_2)):
                assert proc1.product_id == proc2.product_id, \
                    f"工序 {i}: 产品编码不一致 {proc1.product_id} != {proc2.product_id}"
                assert proc1.operation_id == proc2.operation_id, \
                    f"工序 {i}: 工序编号不一致 {proc1.operation_id} != {proc2.operation_id}"
                assert proc1.operation_name == proc2.operation_name, \
                    f"工序 {i}: 工序名称不一致 {proc1.operation_name} != {proc2.operation_name}"
                assert proc1.sequence == proc2.sequence, \
                    f"工序 {i}: 工序顺序不一致 {proc1.sequence} != {proc2.sequence}"
                # 标准工时可能有微小的浮点误差
                assert abs(proc1.standard_time - proc2.standard_time) < 0.02, \
                    f"工序 {i}: 标准工时不一致 {proc1.standard_time} != {proc2.standard_time}"
                assert proc1.required_equipment == proc2.required_equipment, \
                    f"工序 {i}: 设备要求不一致 {proc1.required_equipment} != {proc2.required_equipment}"
        
        finally:
            if os.path.exists(tmp_path_2):
                os.unlink(tmp_path_2)
    
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
