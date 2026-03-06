"""
指标计算器

计算排程方案的关键性能指标。
"""

from typing import Dict, List
from datetime import datetime, timedelta
from data_layer.models import ScheduleResult, Order, Equipment


class MetricsCalculator:
    """指标计算器类，用于计算排程方案的性能指标"""
    
    def __init__(self, equipment: List[Equipment]):
        """
        初始化指标计算器
        
        Args:
            equipment: 设备列表，用于计算利用率时获取设备可用时间
        """
        self.equipment = equipment
        # 构建设备ID到设备对象的映射
        self.equipment_map = {eq.equipment_id: eq for eq in equipment}
    
    def calculate_makespan(self, schedule: ScheduleResult) -> float:
        """
        计算总完工时间
        
        Args:
            schedule: 排程结果
            
        Returns:
            总完工时间（小时，从排程开始到最后完工的时间跨度）
        """
        if not schedule.operations:
            return 0.0
        
        # 找到最早的开始时间和最晚的结束时间
        min_start_time = min(op.start_time for op in schedule.operations)
        max_end_time = max(op.end_time for op in schedule.operations)
        
        # 计算时间跨度（小时）
        time_span = (max_end_time - min_start_time).total_seconds() / 3600.0
        
        return time_span
    
    def calculate_equipment_utilization(
        self, 
        schedule: ScheduleResult
    ) -> Dict[str, float]:
        """
        计算设备利用率
        
        Args:
            schedule: 排程结果
            
        Returns:
            设备利用率字典 {设备ID: 利用率%}
        """
        if not schedule.operations:
            return {}
        
        # 计算每台设备的总工作时间（小时）
        equipment_work_time: Dict[str, float] = {}
        
        for operation in schedule.operations:
            equipment_id = operation.equipment_id
            if equipment_id not in equipment_work_time:
                equipment_work_time[equipment_id] = 0.0
            equipment_work_time[equipment_id] += operation.duration
        
        # 计算排程的时间跨度（天数）
        if schedule.operations:
            min_start_time = min(op.start_time for op in schedule.operations)
            max_end_time = max(op.end_time for op in schedule.operations)
            
            # 计算跨越的天数（向上取整）
            time_span_days = (max_end_time - min_start_time).days + 1
        else:
            time_span_days = 1
        
        # 计算利用率
        utilization: Dict[str, float] = {}
        
        for equipment_id, work_time in equipment_work_time.items():
            # 获取设备的每日工作时长
            equipment = self.equipment_map.get(equipment_id)
            if equipment:
                daily_capacity = equipment.capacity  # 小时/天
                # 可用工作时间 = 天数 × 每日工作时长
                available_time = time_span_days * daily_capacity
                
                if available_time > 0:
                    # 利用率 = (实际工作时间 / 可用工作时间) × 100%
                    utilization[equipment_id] = (work_time / available_time) * 100.0
                else:
                    utilization[equipment_id] = 0.0
            else:
                # 如果找不到设备信息，使用默认的8小时/天
                available_time = time_span_days * 8.0
                utilization[equipment_id] = (work_time / available_time) * 100.0 if available_time > 0 else 0.0
        
        # 对于没有分配任何工序的设备，利用率为0
        for equipment in self.equipment:
            if equipment.equipment_id not in utilization:
                utilization[equipment.equipment_id] = 0.0
        
        return utilization
    
    def calculate_on_time_delivery(
        self, 
        schedule: ScheduleResult, 
        orders: List[Order]
    ) -> float:
        """
        计算交期达成率
        
        Args:
            schedule: 排程结果
            orders: 订单列表
            
        Returns:
            交期达成率 (0-100%)
        """
        if not orders:
            return 100.0
        
        # 计算每个订单的完工时间
        order_completion_time: Dict[str, datetime] = {}
        
        for operation in schedule.operations:
            order_id = operation.order_id
            if order_id not in order_completion_time:
                order_completion_time[order_id] = operation.end_time
            else:
                # 订单完工时间是其所有工序结束时间的最大值
                if operation.end_time > order_completion_time[order_id]:
                    order_completion_time[order_id] = operation.end_time
        
        # 统计按时完成的订单数量
        on_time_count = 0
        
        for order in orders:
            if order.order_id in order_completion_time:
                completion_time = order_completion_time[order.order_id]
                # 比较完工时间和交期
                # 将交期时间设置为当天的工作结束时间（假设16:00）
                due_datetime = order.due_date.replace(hour=16, minute=0, second=0, microsecond=0)
                
                if completion_time <= due_datetime:
                    on_time_count += 1
        
        # 计算交期达成率
        if len(orders) > 0:
            return (on_time_count / len(orders)) * 100.0
        else:
            return 100.0
    
    def identify_bottleneck(self, schedule: ScheduleResult) -> str:
        """
        识别瓶颈设备
        
        Args:
            schedule: 排程结果
            
        Returns:
            瓶颈设备ID
        """
        if not schedule.operations:
            return ""
        
        # 计算设备利用率
        utilization = self.calculate_equipment_utilization(schedule)
        
        if not utilization:
            return ""
        
        # 找到利用率最高的设备
        bottleneck_equipment = max(utilization.items(), key=lambda x: x[1])
        
        return bottleneck_equipment[0]
