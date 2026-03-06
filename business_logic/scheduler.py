"""
排程引擎

核心排程算法实现，使用 OR-Tools CP-SAT 求解器。
"""

from typing import List, Dict, Tuple
from data_layer.models import Order, Process, Equipment, ScheduleResult
from ortools.sat.python import cp_model


class Scheduler:
    """排程引擎类，使用约束规划进行生产排程优化"""
    
    def __init__(
        self, 
        orders: List[Order], 
        processes: List[Process], 
        equipment: List[Equipment]
    ):
        """
        初始化排程引擎
        
        Args:
            orders: 订单列表
            processes: 工艺路线列表
            equipment: 设备列表
        """
        self.orders = orders
        self.processes = processes
        self.equipment = equipment
        
        # 数据预处理
        self._preprocess_data()
    
    def _preprocess_data(self):
        """
        数据预处理：时间离散化、索引构建
        
        构建以下索引结构：
        - product_to_processes: 产品到工艺路线的映射
        - operation_to_process: 工序ID到工艺对象的映射
        - equipment_type_to_equipment: 设备类型到设备列表的映射
        - horizon: 时间范围（所有工序的总工时之和的上界）
        """
        # 构建产品到工艺路线的映射
        self.product_to_processes: Dict[str, List[Process]] = {}
        for process in self.processes:
            if process.product_id not in self.product_to_processes:
                self.product_to_processes[process.product_id] = []
            self.product_to_processes[process.product_id].append(process)
        
        # 对每个产品的工艺路线按序号排序
        for product_id in self.product_to_processes:
            self.product_to_processes[product_id].sort(key=lambda p: p.sequence)
        
        # 构建工序ID到工艺对象的映射
        self.operation_to_process: Dict[str, Process] = {
            p.operation_id: p for p in self.processes
        }
        
        # 构建设备类型到设备列表的映射
        self.equipment_type_to_equipment: Dict[str, List[Equipment]] = {}
        for equip in self.equipment:
            if equip.equipment_type not in self.equipment_type_to_equipment:
                self.equipment_type_to_equipment[equip.equipment_type] = []
            self.equipment_type_to_equipment[equip.equipment_type].append(equip)
        
        # 构建设备组映射：将 "M01,M02" 这样的字符串映射到对应的设备列表
        self.equipment_group_to_equipment: Dict[str, List[Equipment]] = {}
        for process in self.processes:
            equipment_str = process.required_equipment
            if equipment_str not in self.equipment_group_to_equipment:
                # 解析设备列表
                equipment_ids = [eid.strip() for eid in equipment_str.split(',')]
                # 查找对应的设备对象
                equipment_objs = [eq for eq in self.equipment if eq.equipment_id in equipment_ids]
                self.equipment_group_to_equipment[equipment_str] = equipment_objs
        
        # 计算时间范围（horizon）：所有订单的所有工序的总工时之和
        # 这是一个保守的上界估计
        total_time = 0.0
        for order in self.orders:
            if order.product_id in self.product_to_processes:
                for process in self.product_to_processes[order.product_id]:
                    # standard_time 现在是分钟
                    total_time += process.standard_time * order.quantity
        
        # 时间单位已经是分钟，直接使用
        self.horizon = int(total_time) + 10000  # 添加缓冲时间
        self.time_scale = 1  # 时间缩放因子：1分钟 = 1单位
        
        # 构建订单-工序对列表（用于后续建模）
        self.job_operations: List[Tuple[Order, Process]] = []
        for order in self.orders:
            if order.product_id in self.product_to_processes:
                for process in self.product_to_processes[order.product_id]:
                    self.job_operations.append((order, process))
    
    def build_model(self):
        """
        构建 CP-SAT 优化模型
        
        创建决策变量：
        - 每个工序的开始时间
        - 每个工序的结束时间
        - 每个工序分配的设备
        
        Returns:
            CP-SAT 模型对象
        """
        model = cp_model.CpModel()
        
        # 存储决策变量
        self.start_vars = {}  # (order_id, operation_id) -> start_time_var
        self.end_vars = {}    # (order_id, operation_id) -> end_time_var
        self.interval_vars = {}  # (order_id, operation_id, equipment_id) -> interval_var
        self.presence_vars = {}  # (order_id, operation_id, equipment_id) -> presence_var
        self.equipment_to_intervals = {}  # equipment_id -> list of interval_vars
        
        # 为每个订单的每个工序创建决策变量
        for order, process in self.job_operations:
            key = (order.order_id, process.operation_id)
            
            # 创建开始时间变量
            start_var = model.NewIntVar(0, self.horizon, f'start_{order.order_id}_{process.operation_id}')
            self.start_vars[key] = start_var
            
            # 创建结束时间变量
            end_var = model.NewIntVar(0, self.horizon, f'end_{order.order_id}_{process.operation_id}')
            self.end_vars[key] = end_var
            
            # 工序持续时间（标准工时，单位：分钟）
            # 实际时间 = 单件标准工时 × 订单数量
            duration = int(process.standard_time * order.quantity)
            
            # 为每个可用设备创建区间变量
            # 获取可以执行此工序的设备列表（使用设备组映射）
            available_equipment = self.equipment_group_to_equipment.get(process.required_equipment, [])
            
            for equip in available_equipment:
                # 创建一个布尔变量表示是否在此设备上执行
                presence_var = model.NewBoolVar(f'presence_{order.order_id}_{process.operation_id}_{equip.equipment_id}')
                self.presence_vars[(order.order_id, process.operation_id, equip.equipment_id)] = presence_var
                
                # 创建可选区间变量
                interval_var = model.NewOptionalIntervalVar(
                    start_var,
                    duration,
                    end_var,
                    presence_var,
                    f'interval_{order.order_id}_{process.operation_id}_{equip.equipment_id}'
                )
                
                self.interval_vars[(order.order_id, process.operation_id, equip.equipment_id)] = interval_var
                
                # 记录设备到区间的映射
                if equip.equipment_id not in self.equipment_to_intervals:
                    self.equipment_to_intervals[equip.equipment_id] = []
                self.equipment_to_intervals[equip.equipment_id].append(interval_var)
            
            # 约束：每个工序必须在恰好一台设备上执行
            presence_vars_list = [
                self.presence_vars[(order.order_id, process.operation_id, equip.equipment_id)]
                for equip in available_equipment
            ]
            if presence_vars_list:
                model.Add(sum(presence_vars_list) == 1)
        
        return model
    
    def add_constraints(self, model):
        """
        添加排程约束
        
        包括：
        1. 工艺顺序约束：前置工序必须先完成
        2. 设备互斥约束：同一设备不能同时执行多个工序
        3. 工序时间约束：结束时间 = 开始时间 + 标准工时
        4. 设备可用时间窗口约束
        
        Args:
            model: CP-SAT 模型对象
        """
        # 1. 工艺顺序约束
        for order in self.orders:
            if order.product_id not in self.product_to_processes:
                continue
            
            processes = self.product_to_processes[order.product_id]
            
            # 按序号排序的工艺路线
            for i in range(len(processes) - 1):
                current_process = processes[i]
                next_process = processes[i + 1]
                
                current_key = (order.order_id, current_process.operation_id)
                next_key = (order.order_id, next_process.operation_id)
                
                # 当前工序的结束时间 <= 下一工序的开始时间
                if current_key in self.end_vars and next_key in self.start_vars:
                    model.Add(self.end_vars[current_key] <= self.start_vars[next_key])
            
            # 处理显式的前置工序约束
            for process in processes:
                if process.predecessor:
                    pred_key = (order.order_id, process.predecessor)
                    curr_key = (order.order_id, process.operation_id)
                    
                    if pred_key in self.end_vars and curr_key in self.start_vars:
                        model.Add(self.end_vars[pred_key] <= self.start_vars[curr_key])
        
        # 2. 设备互斥约束：使用 AddNoOverlap
        for equipment_id, intervals in self.equipment_to_intervals.items():
            if intervals:
                model.AddNoOverlap(intervals)
        
        # 3. 工序时间约束：结束时间 = 开始时间 + 标准工时 × 订单数量
        for order, process in self.job_operations:
            key = (order.order_id, process.operation_id)
            duration = int(process.standard_time * order.quantity * self.time_scale)
            
            if key in self.start_vars and key in self.end_vars:
                model.Add(self.end_vars[key] == self.start_vars[key] + duration)
        
        # 4. 设备可用时间窗口约束
        # 简化处理：假设所有设备从时间0开始可用
        # 在实际应用中，可以根据 equipment.available_start 和 available_end 添加约束
        for order, process in self.job_operations:
            key = (order.order_id, process.operation_id)
            if key in self.start_vars:
                # 确保开始时间非负
                model.Add(self.start_vars[key] >= 0)
    
    def set_objective(self, model):
        """
        设置优化目标：最小化总完工时间（makespan）
        
        Args:
            model: CP-SAT 模型对象
        """
        # 创建 makespan 变量：所有工序结束时间的最大值
        self.makespan_var = model.NewIntVar(0, self.horizon, 'makespan')
        
        # makespan >= 所有工序的结束时间
        for key, end_var in self.end_vars.items():
            model.Add(self.makespan_var >= end_var)
        
        # 最小化 makespan
        model.Minimize(self.makespan_var)
    
    def solve(self) -> ScheduleResult:
        """
        执行排程求解
        
        Returns:
            排程结果
        """
        import time
        
        start_time = time.time()
        
        # 构建模型
        model = self.build_model()
        
        # 添加约束
        self.add_constraints(model)
        
        # 设置优化目标
        self.set_objective(model)
        
        # 创建求解器
        solver = cp_model.CpSolver()
        
        # 设置求解器参数
        solver.parameters.max_time_in_seconds = 60.0  # 最大求解时间60秒
        
        # 求解
        status = solver.Solve(model)
        
        solve_time = time.time() - start_time
        
        # 根据求解状态返回结果
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return self.extract_solution(solver, solve_time, status)
        elif status == cp_model.INFEASIBLE:
            return ScheduleResult(
                status='INFEASIBLE',
                makespan=0.0,
                operations=[],
                solve_time=solve_time
            )
        else:
            return ScheduleResult(
                status='UNKNOWN',
                makespan=0.0,
                operations=[],
                solve_time=solve_time
            )
    
    def extract_solution(self, solver, solve_time: float, status) -> ScheduleResult:
        """
        从求解器提取排程结果
        
        Args:
            solver: CP-SAT 求解器对象
            solve_time: 求解耗时
            
        Returns:
            排程结果
        """
        from data_layer.models import ScheduledOperation
        
        operations = []
        
        # 提取每个工序的排程信息
        for order, process in self.job_operations:
            key = (order.order_id, process.operation_id)
            
            if key not in self.start_vars or key not in self.end_vars:
                continue
            
            start_time = solver.Value(self.start_vars[key])
            end_time = solver.Value(self.end_vars[key])
            duration = end_time - start_time
            
            # 找到分配的设备
            assigned_equipment = None
            available_equipment = self.equipment_group_to_equipment.get(process.required_equipment, [])
            
            for equip in available_equipment:
                presence_key = (order.order_id, process.operation_id, equip.equipment_id)
                if presence_key in self.presence_vars:
                    if solver.Value(self.presence_vars[presence_key]) == 1:
                        assigned_equipment = equip.equipment_id
                        break
            
            if assigned_equipment is None and available_equipment:
                # 如果没有找到，使用第一个可用设备（fallback）
                assigned_equipment = available_equipment[0].equipment_id
            
            operations.append(ScheduledOperation(
                order_id=order.order_id,
                operation_id=process.operation_id,
                equipment_id=assigned_equipment or 'UNKNOWN',
                start_time=float(start_time) / 60.0,  # 转换为小时用于显示
                end_time=float(end_time) / 60.0,      # 转换为小时用于显示
                duration=float(duration) / 60.0       # 转换为小时用于显示
            ))
        
        # 获取 makespan（转换为小时用于显示）
        makespan = solver.Value(self.makespan_var) / 60.0 if hasattr(self, 'makespan_var') else 0.0
        
        # 确定求解状态
        status_str = 'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'
        
        return ScheduleResult(
            status=status_str,
            makespan=float(makespan),
            operations=operations,
            solve_time=solve_time
        )
