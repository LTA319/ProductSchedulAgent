"""
数据验证器

验证输入数据的完整性和一致性。
"""

from typing import List
from datetime import datetime
from data_layer.models import Order, Process, Equipment, ValidationResult


class DataValidator:
    """数据验证器类，用于验证生产数据的有效性"""
    
    def validate_orders(self, orders: List[Order]) -> ValidationResult:
        """
        验证订单数据
        
        Args:
            orders: 订单对象列表
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        if not orders:
            errors.append("订单列表为空")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        for i, order in enumerate(orders):
            # 检查必填字段
            if not order.order_id or not order.order_id.strip():
                errors.append(f"订单 {i+1}: 订单号不能为空")
            
            if not order.product_id or not order.product_id.strip():
                errors.append(f"订单 {i+1} ({order.order_id}): 产品编码不能为空")
            
            # 检查数量
            if order.quantity <= 0:
                errors.append(f"订单 {order.order_id}: 生产数量必须大于0，当前值: {order.quantity}")
            
            # 检查交期
            if not isinstance(order.due_date, datetime):
                errors.append(f"订单 {order.order_id}: 交期格式无效")
            elif order.due_date < datetime.now():
                warnings.append(f"订单 {order.order_id}: 交期已过期")
            
            # 检查优先级（1最高，数字越小优先级越高）
            if order.priority < 1:
                errors.append(f"订单 {order.order_id}: 优先级必须大于等于1，当前值: {order.priority}")
        
        # 检查订单号唯一性
        order_ids = [o.order_id for o in orders]
        duplicates = [oid for oid in order_ids if order_ids.count(oid) > 1]
        if duplicates:
            errors.append(f"存在重复的订单号: {set(duplicates)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
    
    def validate_processes(self, processes: List[Process]) -> ValidationResult:
        """
        验证工艺路线数据
        
        Args:
            processes: 工艺路线对象列表
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        if not processes:
            errors.append("工艺路线列表为空")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        for i, process in enumerate(processes):
            # 检查必填字段
            if not process.product_id or not process.product_id.strip():
                errors.append(f"工序 {i+1}: 产品编码不能为空")
            
            if not process.operation_id or not process.operation_id.strip():
                errors.append(f"工序 {i+1}: 工序编号不能为空")
            
            if not process.operation_name or not process.operation_name.strip():
                errors.append(f"工序 {i+1} ({process.operation_id}): 工序名称不能为空")
            
            # 检查工序顺序
            if process.sequence <= 0:
                errors.append(f"工序 {process.operation_id}: 工序顺序必须大于0，当前值: {process.sequence}")
            
            # 检查标准工时
            if process.standard_time <= 0:
                errors.append(f"工序 {process.operation_id}: 标准工时必须大于0，当前值: {process.standard_time}")
            
            # 检查设备要求
            if not process.required_equipment or not process.required_equipment.strip():
                errors.append(f"工序 {process.operation_id}: 所需设备不能为空")
        
        # 检查工序编号唯一性（同一产品内）
        product_operations = {}
        for process in processes:
            if process.product_id not in product_operations:
                product_operations[process.product_id] = []
            product_operations[process.product_id].append(process)
        
        for product_id, ops in product_operations.items():
            # 检查工序顺序连续性
            sequences = sorted([op.sequence for op in ops])
            if sequences != list(range(1, len(sequences) + 1)):
                warnings.append(f"产品 {product_id}: 工序顺序不连续 {sequences}")
            
            # 检查前置工序引用有效性
            op_ids = {op.operation_id for op in ops}
            for op in ops:
                if op.predecessor and op.predecessor not in op_ids:
                    errors.append(f"工序 {op.operation_id}: 前置工序 {op.predecessor} 不存在")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
    
    def validate_equipment(self, equipment: List[Equipment]) -> ValidationResult:
        """
        验证设备数据
        
        Args:
            equipment: 设备对象列表
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        if not equipment:
            errors.append("设备列表为空")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        for i, eq in enumerate(equipment):
            # 检查必填字段
            if not eq.equipment_id or not eq.equipment_id.strip():
                errors.append(f"设备 {i+1}: 设备编号不能为空")
            
            if not eq.equipment_type or not eq.equipment_type.strip():
                errors.append(f"设备 {i+1} ({eq.equipment_id}): 设备类型不能为空")
            
            # 检查产能
            if eq.capacity <= 0:
                errors.append(f"设备 {eq.equipment_id}: 产能上限必须大于0，当前值: {eq.capacity}")
            
            # 检查换产时间
            if eq.changeover_time < 0:
                errors.append(f"设备 {eq.equipment_id}: 换产时间不能为负数，当前值: {eq.changeover_time}")
            
            # 检查可用时段
            if not isinstance(eq.available_start, datetime):
                errors.append(f"设备 {eq.equipment_id}: 可用开始时间格式无效")
            
            if not isinstance(eq.available_end, datetime):
                errors.append(f"设备 {eq.equipment_id}: 可用结束时间格式无效")
            
            if isinstance(eq.available_start, datetime) and isinstance(eq.available_end, datetime):
                if eq.available_end <= eq.available_start:
                    errors.append(f"设备 {eq.equipment_id}: 可用结束时间必须大于开始时间")
        
        # 检查设备编号唯一性
        equipment_ids = [e.equipment_id for e in equipment]
        duplicates = [eid for eid in equipment_ids if equipment_ids.count(eid) > 1]
        if duplicates:
            errors.append(f"存在重复的设备编号: {set(duplicates)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
    
    def validate_consistency(
        self, 
        orders: List[Order], 
        processes: List[Process], 
        equipment: List[Equipment]
    ) -> ValidationResult:
        """
        验证数据一致性（引用完整性）
        
        Args:
            orders: 订单对象列表
            processes: 工艺路线对象列表
            equipment: 设备对象列表
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 构建产品和设备集合
        product_ids_in_orders = {order.product_id for order in orders}
        product_ids_in_processes = {process.product_id for process in processes}
        equipment_ids = {eq.equipment_id for eq in equipment}
        
        # 检查订单中的产品是否都有工艺路线
        missing_processes = product_ids_in_orders - product_ids_in_processes
        if missing_processes:
            errors.append(f"以下产品在订单中存在但缺少工艺路线: {missing_processes}")
        
        # 检查工艺路线中的产品是否都有订单（这是警告，不是错误）
        unused_processes = product_ids_in_processes - product_ids_in_orders
        if unused_processes:
            warnings.append(f"以下产品有工艺路线但没有订单: {unused_processes}")
        
        # 检查工艺路线中要求的设备是否都存在
        # required_equipment 现在可能是逗号分隔的设备列表（如 "M01,M02"）
        required_equipment_groups = {process.required_equipment for process in processes}
        missing_equipment = []
        
        for equipment_group in required_equipment_groups:
            # 解析设备列表
            equipment_ids_in_group = [eid.strip() for eid in equipment_group.split(',')]
            # 检查每个设备是否存在
            for eq_id in equipment_ids_in_group:
                if eq_id not in equipment_ids:
                    missing_equipment.append(eq_id)
        
        if missing_equipment:
            errors.append(f"以下设备在工艺路线中被要求但不存在: {set(missing_equipment)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
