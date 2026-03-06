"""
排程引擎

核心排程算法实现，使用 OR-Tools CP-SAT 求解器。
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from data_layer.models import Order, Process, Equipment, ScheduleResult
from ortools.sat.python import cp_model


class Scheduler:
    """排程引擎类，使用约束规划进行生产排程优化"""
    
    def __init__(
        self, 
        orders: List[Order], 
        processes: List[Process], 
        equipment: List[Equipment],
        objective_weights: Dict[str, float] = None
    ):
        """
        初始化排程引擎
        
        Args:
            orders: 订单列表
            processes: 工艺路线列表
            equipment: 设备列表
            objective_weights: 目标权重字典，包含以下键：
                - 'due_date': 交期优先权重（默认1.0）
                - 'utilization': 设备利用率权重（默认0.5）
                - 'changeover': 最小换产权重（默认0.3）
                - 'makespan': 最小完工时间权重（默认0.2）
        """
        self.orders = orders
        self.processes = processes
        self.equipment = equipment
        
        # 设置目标权重（默认值）
        self.objective_weights = objective_weights or {
            'due_date': 1.0,      # 交期优先
            'utilization': 0.5,   # 设备利用率
            'changeover': 0.3,    # 最小换产
            'makespan': 0.2       # 最小完工时间
        }
        
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
        - equipment_daily_capacity: 设备每日工作时长（分钟）
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
        
        # 构建设备每日工作时长映射（分钟）
        self.equipment_daily_capacity: Dict[str, float] = {}
        for equip in self.equipment:
            # capacity 是小时/天，转换为分钟/天
            self.equipment_daily_capacity[equip.equipment_id] = equip.capacity * 60.0
        
        # 计算时间范围（horizon）：考虑设备工作时间限制
        # 估算需要的工作天数
        total_work_minutes = 0.0
        for order in self.orders:
            if order.product_id in self.product_to_processes:
                for process in self.product_to_processes[order.product_id]:
                    total_work_minutes += process.standard_time * order.quantity
        
        # 假设平均每天可用工作时长（取所有设备的平均值）
        if self.equipment_daily_capacity:
            avg_daily_capacity = sum(self.equipment_daily_capacity.values()) / len(self.equipment_daily_capacity)
        else:
            avg_daily_capacity = 8 * 60  # 默认8小时/天
        
        # 估算需要的天数，并添加缓冲
        estimated_days = (total_work_minutes / avg_daily_capacity) * 2  # 2倍缓冲
        estimated_days = max(estimated_days, 30)  # 至少30天
        
        # horizon 以分钟为单位，表示日历时间（包含非工作时间）
        # 假设每天24小时，但只有 capacity 小时是工作时间
        self.horizon = int(estimated_days * 24 * 60)  # 转换为分钟
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
        self.changeover_vars = {}  # (equipment_id, i, j) -> changeover_bool_var (是否发生换产)
        
        # 记录每台设备上的工序列表（用于换产计算）
        self.equipment_to_operations = {}  # equipment_id -> list of (order, process)
        
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
                
                # 记录设备到工序的映射（用于换产计算）
                if equip.equipment_id not in self.equipment_to_operations:
                    self.equipment_to_operations[equip.equipment_id] = []
                self.equipment_to_operations[equip.equipment_id].append((order, process, equip.equipment_id))
            
            # 约束：每个工序必须在恰好一台设备上执行
            presence_vars_list = [
                self.presence_vars[(order.order_id, process.operation_id, equip.equipment_id)]
                for equip in available_equipment
            ]
            if presence_vars_list:
                model.Add(sum(presence_vars_list) == 1)
        
        # 创建换产变量（用于最小化换产次数）
        self._create_changeover_vars(model)
        
        return model
    
    def _create_changeover_vars(self, model):
        """
        创建换产变量
        
        对于每台设备上的每对工序，创建一个布尔变量表示是否发生换产
        """
        for equipment_id, operations in self.equipment_to_operations.items():
            for i in range(len(operations)):
                for j in range(i + 1, len(operations)):
                    order_i, process_i, equip_i = operations[i]
                    order_j, process_j, equip_j = operations[j]
                    
                    # 如果两个工序属于不同订单，则可能发生换产
                    if order_i.order_id != order_j.order_id:
                        # 创建换产布尔变量
                        changeover_var = model.NewBoolVar(
                            f'changeover_{equipment_id}_{i}_{j}'
                        )
                        self.changeover_vars[(equipment_id, i, j)] = changeover_var
                        
                        # 获取presence变量
                        presence_i = self.presence_vars.get((order_i.order_id, process_i.operation_id, equipment_id))
                        presence_j = self.presence_vars.get((order_j.order_id, process_j.operation_id, equipment_id))
                        
                        if presence_i is not None and presence_j is not None:
                            # 如果两个工序都在这台设备上执行，则发生换产
                            # changeover = presence_i AND presence_j
                            model.Add(changeover_var >= presence_i + presence_j - 1)
                            model.Add(changeover_var <= presence_i)
                            model.Add(changeover_var <= presence_j)
    
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
        设置多目标优化函数
        
        目标包括：
        1. 优先交期：最小化延期惩罚
        2. 设备利用率：最大化设备使用（最小化空闲时间）
        3. 最小换产：最小化换产次数
        4. 最小总完工时间：最小化makespan
        
        Args:
            model: CP-SAT 模型对象
        """
        # 始终创建 makespan 变量
        if not hasattr(self, 'makespan_var'):
            self.makespan_var = model.NewIntVar(0, self.horizon, 'makespan')
            for key, end_var in self.end_vars.items():
                model.Add(self.makespan_var >= end_var)
        
        # 检查是否有任何非零权重
        has_objectives = any(self.objective_weights.get(key, 0) > 0 for key in 
                            ['due_date', 'utilization', 'changeover', 'makespan'])
        
        if not has_objectives:
            # 如果所有权重都是0，默认最小化makespan
            model.Minimize(self.makespan_var)
            return
        
        # 构建目标函数的各个部分
        objective_parts = []
        
        # 1. 交期目标：最小化延期惩罚
        due_date_weight = self.objective_weights.get('due_date', 0)
        if due_date_weight > 0:
            due_date_penalty = self._create_due_date_objective(model)
            weight = int(due_date_weight * 10000)
            objective_parts.append(weight * due_date_penalty)
        
        # 2. 设备利用率目标：最小化makespan（间接提高利用率）
        utilization_weight = self.objective_weights.get('utilization', 0)
        if utilization_weight > 0:
            weight = int(utilization_weight * 1)
            objective_parts.append(weight * self.makespan_var)
        
        # 3. 最小换产目标
        changeover_weight = self.objective_weights.get('changeover', 0)
        if changeover_weight > 0 and self.changeover_vars:
            # 创建总换产次数变量
            total_changeovers = model.NewIntVar(0, len(self.changeover_vars), 'total_changeovers')
            model.Add(total_changeovers == sum(self.changeover_vars.values()))
            weight = int(changeover_weight * 1000)
            objective_parts.append(weight * total_changeovers)
        
        # 4. 最小完工时间目标（makespan）
        makespan_weight = self.objective_weights.get('makespan', 0)
        if makespan_weight > 0:
            weight = int(makespan_weight * 1)
            objective_parts.append(weight * self.makespan_var)
        
        # 组合所有目标
        if objective_parts:
            model.Minimize(sum(objective_parts))
        else:
            model.Minimize(self.makespan_var)
    
    def _create_due_date_objective(self, model):
        """
        创建交期目标：最小化延期惩罚
        
        Returns:
            延期惩罚变量
        """
        # 将交期转换为相对分钟数（从基准日期开始）
        base_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        
        tardiness_vars = []
        
        for order in self.orders:
            # 计算订单的所有工序
            if order.product_id not in self.product_to_processes:
                continue
            
            # 找到订单的最后一个工序的结束时间
            processes = self.product_to_processes[order.product_id]
            if not processes:
                continue
            
            # 获取所有工序的结束时间变量
            order_end_vars = []
            for process in processes:
                key = (order.order_id, process.operation_id)
                if key in self.end_vars:
                    order_end_vars.append(self.end_vars[key])
            
            if not order_end_vars:
                continue
            
            # 订单完工时间 = 所有工序结束时间的最大值
            order_completion = model.NewIntVar(0, self.horizon, f'completion_{order.order_id}')
            for end_var in order_end_vars:
                model.Add(order_completion >= end_var)
            
            # 计算交期（转换为工作分钟）
            # 简化：假设交期是从基准日期开始的天数
            days_until_due = (order.due_date - base_date).days
            # 转换为工作分钟（假设每天8小时工作）
            due_time_minutes = days_until_due * 8 * 60
            
            # 创建延期变量：tardiness = max(0, completion - due_time)
            tardiness = model.NewIntVar(0, self.horizon, f'tardiness_{order.order_id}')
            model.Add(tardiness >= order_completion - due_time_minutes)
            model.Add(tardiness >= 0)
            
            # 根据优先级和是否急单调整权重
            weight = order.priority  # 优先级越小，权重越大
            if order.is_urgent:
                weight *= 2  # 急单加倍惩罚
            
            # 创建加权延期变量
            weighted_tardiness = model.NewIntVar(0, self.horizon * weight, f'weighted_tardiness_{order.order_id}')
            model.Add(weighted_tardiness == weight * tardiness)
            tardiness_vars.append(weighted_tardiness)
        
        # 返回总延期惩罚
        if tardiness_vars:
            total_tardiness = model.NewIntVar(0, self.horizon * len(self.orders) * 10, 'total_tardiness')
            model.Add(total_tardiness == sum(tardiness_vars))
            return total_tardiness
        else:
            return model.NewIntVar(0, 0, 'zero_tardiness')
    
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
    
    def _work_minutes_to_datetime(self, work_minutes: float, equipment_id: str, base_date: datetime) -> datetime:
        """
        将工作分钟转换为实际日期时间（考虑每日工作时长，跳过非工作时间）
        
        Args:
            work_minutes: 累计工作分钟数
            equipment_id: 设备编号
            base_date: 基准日期（排程开始日期）
            
        Returns:
            实际日期时间
        """
        # 获取设备每日工作时长（分钟）
        daily_capacity_minutes = self.equipment_daily_capacity.get(equipment_id, 8 * 60)
        
        # 计算是第几个工作日（从0开始）
        work_day = int(work_minutes / daily_capacity_minutes)
        
        # 计算当天的工作分钟数（余数）
        minutes_in_day = work_minutes % daily_capacity_minutes
        
        # 假设每天从 8:00 开始工作
        work_start_hour = 8
        
        # 计算实际日期时间
        result_date = base_date + timedelta(days=work_day)
        result_datetime = result_date.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        result_datetime += timedelta(minutes=minutes_in_day)
        
        return result_datetime
    
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
            
            # 使用基准日期（今天8点）
            base_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
            
            # 将工作分钟转换为实际日期时间
            start_datetime = self._work_minutes_to_datetime(float(start_time), assigned_equipment or 'UNKNOWN', base_date)
            end_datetime = self._work_minutes_to_datetime(float(end_time), assigned_equipment or 'UNKNOWN', base_date)
            
            # 计算工作小时数
            duration_hours = float(duration) / 60.0
            
            operations.append(ScheduledOperation(
                order_id=order.order_id,
                operation_id=process.operation_id,
                equipment_id=assigned_equipment or 'UNKNOWN',
                start_time=start_datetime,
                end_time=end_datetime,
                duration=duration_hours
            ))
        
        # 计算 makespan（日历时间跨度，小时）
        if operations:
            min_start_time = min(op.start_time for op in operations)
            max_end_time = max(op.end_time for op in operations)
            makespan = (max_end_time - min_start_time).total_seconds() / 3600.0
        else:
            makespan = 0.0
        
        # 确定求解状态
        status_str = 'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'
        
        return ScheduleResult(
            status=status_str,
            makespan=float(makespan),
            operations=operations,
            solve_time=solve_time
        )
