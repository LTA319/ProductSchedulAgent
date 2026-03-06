"""
数据解析器

负责从 Excel 文件中读取和解析生产数据。
"""

import pandas as pd
from typing import List
from datetime import datetime
from data_layer.models import Order, Process, Equipment


class DataParser:
    """数据解析器类，用于解析 Excel 格式的生产数据"""
    
    def parse_orders(self, file_path: str) -> List[Order]:
        """
        解析订单数据
        
        Args:
            file_path: Excel 文件路径
            
        Returns:
            订单对象列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或数据无效
        """
        try:
            # 读取 Excel 文件，跳过第一行标题
            df = pd.read_excel(file_path, sheet_name='订单表', header=1)
            
            # 删除空列
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            orders = []
            for _, row in df.iterrows():
                # 跳过空行
                if pd.isna(row['订单号']):
                    continue
                    
                # 解析交期
                due_date = row['承诺交期']
                if isinstance(due_date, str):
                    due_date = pd.to_datetime(due_date)
                elif not isinstance(due_date, datetime):
                    due_date = pd.to_datetime(due_date)
                
                # 解析是否急单
                is_urgent = str(row['是否急单']).strip() in ['是', 'True', 'true', '1', 'Y', 'y']
                
                order = Order(
                    order_id=str(row['订单号']).strip(),
                    product_id=str(row['产品编码']).strip(),
                    quantity=int(row['生产数量（件）']),
                    due_date=due_date,
                    priority=int(row['优先级（1最高）']),
                    is_urgent=is_urgent
                )
                orders.append(order)
            
            return orders
            
        except FileNotFoundError:
            raise FileNotFoundError(f"文件未找到: {file_path}")
        except Exception as e:
            raise ValueError(f"文件无法读取，可能已损坏或格式错误: {str(e)}")
    
    def parse_processes(self, file_path: str) -> List[Process]:
        """
        解析工艺路线数据
        
        Args:
            file_path: Excel 文件路径
            
        Returns:
            工艺路线对象列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或数据无效
        """
        try:
            # 读取 Excel 文件，跳过第一行标题
            df = pd.read_excel(file_path, sheet_name='工艺路线表', header=1)
            
            # 删除空列
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            processes = []
            # 构建前置工序映射
            process_map = {}
            
            for _, row in df.iterrows():
                # 跳过空行
                if pd.isna(row['产品编码']):
                    continue
                
                product_id = str(row['产品编码']).strip()
                operation_id = str(row['工序号']).strip()
                sequence = int(row['工序顺序'])
                
                # 单件标准工时（分钟）
                standard_time = float(row['单件标准工时（分钟）'])
                
                # 换型时间（分钟），如果列不存在则默认为0
                changeover_time = 0.0
                if '换型时间（分钟）' in row and pd.notna(row['换型时间（分钟）']):
                    changeover_time = float(row['换型时间（分钟）'])
                
                # 解析可使用设备（保留完整的设备列表作为设备类型标识）
                equipment_str = str(row['可使用设备编号']).strip()
                # 使用完整的设备列表字符串作为 required_equipment
                # 这样相同设备组的工序可以共享设备池
                required_equipment = equipment_str
                
                # 记录产品的工序顺序
                if product_id not in process_map:
                    process_map[product_id] = {}
                process_map[product_id][sequence] = operation_id
                
                # 确定前置工序
                predecessor = None
                if sequence > 1:
                    predecessor = process_map[product_id].get(sequence - 1)
                
                process = Process(
                    product_id=product_id,
                    operation_id=operation_id,
                    operation_name=str(row['工序名称']).strip(),
                    sequence=sequence,
                    standard_time=standard_time,
                    required_equipment=required_equipment,
                    changeover_time=changeover_time,
                    predecessor=predecessor
                )
                processes.append(process)
            
            return processes
            
        except FileNotFoundError:
            raise FileNotFoundError(f"文件未找到: {file_path}")
        except Exception as e:
            raise ValueError(f"文件无法读取，可能已损坏或格式错误: {str(e)}")
    
    def parse_equipment(self, file_path: str) -> List[Equipment]:
        """
        解析设备数据
        
        Args:
            file_path: Excel 文件路径
            
        Returns:
            设备对象列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或数据无效
        """
        try:
            # 读取 Excel 文件，跳过第一行标题
            df = pd.read_excel(file_path, sheet_name='设备表', header=1)
            
            # 删除空列
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            equipment_list = []
            # 假设当前日期为基准
            base_date = datetime(2026, 2, 26)
            
            for _, row in df.iterrows():
                # 跳过空行
                if pd.isna(row['设备编号']):
                    continue
                
                # 读取状态
                status = str(row['状态']).strip()
                
                # 跳过不可用设备
                if status != '可用':
                    continue
                
                # 每日工作小时
                capacity = float(row['每日工作小时'])
                
                # 效率系数，如果列不存在则默认为1.0（100%效率）
                efficiency = 1.0
                if '效率系数' in row and pd.notna(row['效率系数']):
                    efficiency = float(row['效率系数'])
                
                # 换型时间（分钟），如果列不存在则默认为0
                changeover_time = 0.0
                if '换型时间（分钟）' in row and pd.notna(row['换型时间（分钟）']):
                    changeover_time = float(row['换型时间（分钟）'])
                
                equipment_id = str(row['设备编号']).strip()
                
                equipment = Equipment(
                    equipment_id=equipment_id,
                    equipment_type=equipment_id,  # 设备类型就是设备编号本身
                    status=status,
                    efficiency=efficiency,
                    available_start=base_date,
                    available_end=base_date.replace(year=2027),  # 假设一年可用期
                    capacity=capacity,
                    changeover_time=changeover_time
                )
                equipment_list.append(equipment)
            
            return equipment_list
            
        except FileNotFoundError:
            raise FileNotFoundError(f"文件未找到: {file_path}")
        except Exception as e:
            raise ValueError(f"文件无法读取，可能已损坏或格式错误: {str(e)}")
