"""
数据模型定义

定义系统中使用的核心数据结构：
- Order: 订单数据模型
- Process: 工艺路线数据模型
- Equipment: 设备数据模型
- ScheduleResult: 排程结果数据模型
- ScheduledOperation: 已排程工序数据模型
- ValidationResult: 验证结果数据模型
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Order:
    """订单数据模型"""
    order_id: str          # 订单号
    product_id: str        # 产品编码
    quantity: int          # 数量
    due_date: datetime     # 交期
    priority: int          # 优先级 (1最高, 数字越小优先级越高)
    is_urgent: bool = False  # 是否紧急


@dataclass
class Process:
    """工艺路线数据模型"""
    product_id: str              # 产品编码
    operation_id: str            # 工序编号
    operation_name: str          # 工序名称
    sequence: int                # 工序顺序
    standard_time: float         # 单件标准工时（分钟）
    required_equipment: str      # 所需设备类型
    changeover_time: float = 0.0 # 换型时间（分钟）
    predecessor: Optional[str] = None   # 前置工序


@dataclass
class Equipment:
    """设备数据模型"""
    equipment_id: str           # 设备编号
    equipment_type: str         # 设备类型
    status: str                 # 状态（可用/不可用）
    efficiency: float           # 效率系数（0-1之间，1表示100%效率）
    available_start: datetime   # 可用开始时间
    available_end: datetime     # 可用结束时间
    capacity: float             # 产能上限（小时/天）
    changeover_time: float = 0.0  # 换产时间（分钟）


@dataclass
class ScheduledOperation:
    """已排程工序数据模型"""
    order_id: str          # 订单号
    operation_id: str      # 工序编号
    equipment_id: str      # 分配设备
    start_time: float      # 开始时间（相对时间，单位：小时）
    end_time: float        # 结束时间
    duration: float        # 持续时间


@dataclass
class ScheduleResult:
    """排程结果数据模型"""
    status: str                           # 求解状态 (OPTIMAL/FEASIBLE/INFEASIBLE)
    makespan: float                       # 总完工时间
    operations: List[ScheduledOperation]  # 已排程工序列表
    solve_time: float                     # 求解耗时（秒）


@dataclass
class ValidationResult:
    """验证结果数据模型"""
    is_valid: bool              # 是否通过验证
    errors: List[str]           # 错误信息列表
    warnings: List[str]         # 警告信息列表
