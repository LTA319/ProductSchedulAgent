"""
属性测试：数据验证

测试数据验证器的正确性属性
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from datetime import datetime, timedelta

from data_layer.validator import DataValidator
from data_layer.models import Order, Process, Equipment


@composite
def invalid_order_strategy(draw):
    """生成包含无效数据的订单"""
    invalid_type = draw(st.sampled_from([
        'empty_order_id',
        'empty_product_id',
        'negative_quantity',
        'zero_quantity',
        'invalid_priority_low',
        'invalid_priority_high'
    ]))
    
    base_order = Order(
        order_id='SO20260301-001',
        product_id='PART-A01',
        quantity=10,
        due_date=datetime(2026, 3, 15),
        priority=3,
        is_urgent=False
    )
    
    if invalid_type == 'empty_order_id':
        base_order.order_id = ''
    elif invalid_type == 'empty_product_id':
        base_order.product_id = ''
    elif invalid_type == 'negative_quantity':
        base_order.quantity = draw(st.integers(max_value=-1))
    elif invalid_type == 'zero_quantity':
        base_order.quantity = 0
    elif invalid_type == 'invalid_priority_low':
        base_order.priority = draw(st.integers(max_value=0))
    elif invalid_type == 'invalid_priority_high':
        base_order.priority = draw(st.integers(min_value=6))
    
    return base_order, invalid_type


@settings(max_examples=100)
@given(invalid_data=invalid_order_strategy())
def test_invalid_order_detection(invalid_data):
    """
    **功能：production-scheduling-agent，属性 4：无效数据错误检测**
    **验证需求：1.4**
    
    对于任何包含无效数据的输入（如缺失必填字段、数据类型错误、负数数量等），
    验证器应该返回失败状态，并在错误信息中明确指出具体的问题字段和错误原因
    """
    invalid_order, invalid_type = invalid_data
    
    validator = DataValidator()
    result = validator.validate_orders([invalid_order])
    
    # 验证：应该返回失败状态
    assert not result.is_valid, \
        f"验证器应该检测到无效数据 ({invalid_type})，但返回了有效状态"
    
    # 验证：应该有错误信息
    assert len(result.errors) > 0, \
        f"验证器应该返回错误信息 ({invalid_type})，但错误列表为空"
    
    # 验证：错误信息应该包含相关关键字
    error_text = ' '.join(result.errors).lower()
    
    if invalid_type in ['empty_order_id']:
        assert '订单号' in error_text or 'order_id' in error_text, \
            f"错误信息应该提到订单号问题，但得到: {result.errors}"
    elif invalid_type in ['empty_product_id']:
        assert '产品编码' in error_text or 'product_id' in error_text, \
            f"错误信息应该提到产品编码问题，但得到: {result.errors}"
    elif invalid_type in ['negative_quantity', 'zero_quantity']:
        assert '数量' in error_text or 'quantity' in error_text, \
            f"错误信息应该提到数量问题，但得到: {result.errors}"
    elif invalid_type in ['invalid_priority_low', 'invalid_priority_high']:
        assert '优先级' in error_text or 'priority' in error_text, \
            f"错误信息应该提到优先级问题，但得到: {result.errors}"


@composite
def invalid_process_strategy(draw):
    """生成包含无效数据的工序"""
    invalid_type = draw(st.sampled_from([
        'empty_product_id',
        'empty_operation_id',
        'empty_operation_name',
        'negative_sequence',
        'zero_sequence',
        'negative_standard_time',
        'zero_standard_time',
        'empty_equipment'
    ]))
    
    base_process = Process(
        product_id='PART-A01',
        operation_id='OP010',
        operation_name='数控车',
        sequence=1,
        standard_time=0.5,
        required_equipment='M01',
        predecessor=None
    )
    
    if invalid_type == 'empty_product_id':
        base_process.product_id = ''
    elif invalid_type == 'empty_operation_id':
        base_process.operation_id = ''
    elif invalid_type == 'empty_operation_name':
        base_process.operation_name = ''
    elif invalid_type == 'negative_sequence':
        base_process.sequence = draw(st.integers(max_value=-1))
    elif invalid_type == 'zero_sequence':
        base_process.sequence = 0
    elif invalid_type == 'negative_standard_time':
        base_process.standard_time = draw(st.floats(max_value=-0.1, allow_nan=False, allow_infinity=False))
    elif invalid_type == 'zero_standard_time':
        base_process.standard_time = 0.0
    elif invalid_type == 'empty_equipment':
        base_process.required_equipment = ''
    
    return base_process, invalid_type


@settings(max_examples=100)
@given(invalid_data=invalid_process_strategy())
def test_invalid_process_detection(invalid_data):
    """
    **功能：production-scheduling-agent，属性 4：无效数据错误检测**
    **验证需求：1.4**
    
    对于任何包含无效工序数据的输入，验证器应该返回失败状态，
    并在错误信息中明确指出具体的问题字段和错误原因
    """
    invalid_process, invalid_type = invalid_data
    
    validator = DataValidator()
    result = validator.validate_processes([invalid_process])
    
    # 验证：应该返回失败状态
    assert not result.is_valid, \
        f"验证器应该检测到无效数据 ({invalid_type})，但返回了有效状态"
    
    # 验证：应该有错误信息
    assert len(result.errors) > 0, \
        f"验证器应该返回错误信息 ({invalid_type})，但错误列表为空"


@composite
def invalid_equipment_strategy(draw):
    """生成包含无效数据的设备"""
    invalid_type = draw(st.sampled_from([
        'empty_equipment_id',
        'empty_equipment_type',
        'negative_capacity',
        'zero_capacity',
        'negative_changeover',
        'invalid_time_range'
    ]))
    
    base_date = datetime(2026, 3, 1)
    base_equipment = Equipment(
        equipment_id='M01',
        equipment_type='数控车床',
        available_start=base_date,
        available_end=base_date + timedelta(days=365),
        capacity=8.0,
        changeover_time=0.5
    )
    
    if invalid_type == 'empty_equipment_id':
        base_equipment.equipment_id = ''
    elif invalid_type == 'empty_equipment_type':
        base_equipment.equipment_type = ''
    elif invalid_type == 'negative_capacity':
        base_equipment.capacity = draw(st.floats(max_value=-0.1, allow_nan=False, allow_infinity=False))
    elif invalid_type == 'zero_capacity':
        base_equipment.capacity = 0.0
    elif invalid_type == 'negative_changeover':
        base_equipment.changeover_time = draw(st.floats(max_value=-0.1, allow_nan=False, allow_infinity=False))
    elif invalid_type == 'invalid_time_range':
        # 结束时间早于开始时间
        base_equipment.available_end = base_date - timedelta(days=1)
    
    return base_equipment, invalid_type


@settings(max_examples=100)
@given(invalid_data=invalid_equipment_strategy())
def test_invalid_equipment_detection(invalid_data):
    """
    **功能：production-scheduling-agent，属性 4：无效数据错误检测**
    **验证需求：1.4**
    
    对于任何包含无效设备数据的输入，验证器应该返回失败状态，
    并在错误信息中明确指出具体的问题字段和错误原因
    """
    invalid_equipment, invalid_type = invalid_data
    
    validator = DataValidator()
    result = validator.validate_equipment([invalid_equipment])
    
    # 验证：应该返回失败状态
    assert not result.is_valid, \
        f"验证器应该检测到无效数据 ({invalid_type})，但返回了有效状态"
    
    # 验证：应该有错误信息
    assert len(result.errors) > 0, \
        f"验证器应该返回错误信息 ({invalid_type})，但错误列表为空"
