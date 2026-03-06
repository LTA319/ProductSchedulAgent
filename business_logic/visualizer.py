"""
可视化生成器

生成甘特图和其他可视化图表。
"""

from typing import Dict
from datetime import datetime, timedelta
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from data_layer.models import ScheduleResult


class Visualizer:
    """可视化生成器类，用于生成排程结果的可视化图表"""
    
    def __init__(self, equipment_list=None):
        """
        初始化可视化生成器
        
        Args:
            equipment_list: 设备列表，用于获取每日工作时长信息
        """
        self.equipment_list = equipment_list or []
        # 构建设备每日工作时长映射（小时）
        self.equipment_daily_capacity = {}
        for equip in self.equipment_list:
            self.equipment_daily_capacity[equip.equipment_id] = equip.capacity
    
    def _split_operation_by_days(self, op, equipment_id: str):
        """
        将跨天的工序拆分为多个每日片段
        
        Args:
            op: ScheduledOperation 对象（start_time 和 end_time 已经是 datetime）
            equipment_id: 设备编号
            
        Returns:
            拆分后的片段列表 [(start_datetime, end_datetime), ...]
        """
        daily_capacity_hours = self.equipment_daily_capacity.get(equipment_id, 8.0)
        work_start_hour = 8
        
        segments = []
        current_datetime = op.start_time
        end_datetime = op.end_time
        
        while current_datetime < end_datetime:
            # 当天工作结束时间
            day_end = current_datetime.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
            day_end += timedelta(hours=daily_capacity_hours)
            
            # 本片段的结束时间：取当天结束时间和任务结束时间的较小值
            segment_end = min(day_end, end_datetime)
            
            segments.append((current_datetime, segment_end))
            
            # 如果还有剩余，移动到下一天的开始时间
            if segment_end < end_datetime:
                next_day = current_datetime + timedelta(days=1)
                current_datetime = next_day.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
            else:
                break
        
        return segments
    
    def generate_gantt_chart(self, schedule: ScheduleResult):
        """
        生成甘特图
        
        Args:
            schedule: 排程结果
            
        Returns:
            Plotly Figure 对象
        """
        if not schedule.operations:
            # 返回空图表
            fig = go.Figure()
            fig.update_layout(
                title="排程甘特图（无数据）",
                xaxis_title="时间（小时）",
                yaxis_title="设备"
            )
            return fig
        
        # 准备甘特图数据
        df_data = []
        
        # 为不同订单分配颜色
        order_ids = list(set(op.order_id for op in schedule.operations))
        color_palette = [
            'rgb(220, 0, 0)', 'rgb(0, 0, 220)', 'rgb(0, 220, 0)',
            'rgb(220, 220, 0)', 'rgb(220, 0, 220)', 'rgb(0, 220, 220)',
            'rgb(128, 0, 0)', 'rgb(0, 128, 0)', 'rgb(0, 0, 128)',
            'rgb(128, 128, 0)', 'rgb(128, 0, 128)', 'rgb(0, 128, 128)'
        ]
        
        # 构建订单到颜色的映射
        order_to_color = {}
        for idx, order_id in enumerate(order_ids):
            order_to_color[order_id] = color_palette[idx % len(color_palette)]
        
        # 构建甘特图数据，并为每个Resource分配颜色
        colors = {}
        
        for op in schedule.operations:
            # 将跨天工序拆分为多个每日片段
            segments = self._split_operation_by_days(op, op.equipment_id)
            
            # 为每个片段创建甘特图条目
            for idx, (start_datetime, end_datetime) in enumerate(segments):
                # 为每个片段生成唯一的 resource_key
                if len(segments) > 1:
                    resource_key = f"{op.order_id}-{op.operation_id}-day{idx+1}"
                else:
                    resource_key = f"{op.order_id}-{op.operation_id}"
                
                df_data.append(dict(
                    Task=op.equipment_id,
                    Start=start_datetime,
                    Finish=end_datetime,
                    Resource=resource_key
                ))
                # 为每个片段分配对应订单的颜色
                colors[resource_key] = order_to_color[op.order_id]
        
        # 创建甘特图
        fig = ff.create_gantt(
            df_data,
            colors=colors,
            index_col='Resource',
            show_colorbar=True,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True,
            title='生产排程甘特图'
        )
        
        # 更新布局
        fig.update_layout(
            xaxis_title="时间",
            yaxis_title="设备",
            height=max(600, len(set(op.equipment_id for op in schedule.operations)) * 80),
            hovermode='closest',
            # 启用拖动和缩放
            dragmode='pan'
        )
        
        # 更新 x 轴格式，显示日期和时间，不倾斜
        fig.update_xaxes(
            tickformat='%m-%d %H:%M',
            tickangle=0,  # 不倾斜
            # 启用范围滑块，方便查看长时间轴
            rangeslider_visible=False
        )
        
        return fig
    
    def generate_utilization_chart(self, metrics: Dict):
        """
        生成设备利用率图表
        
        Args:
            metrics: 指标数据字典，应包含 'equipment_utilization' 键
            
        Returns:
            Plotly Figure 对象
        """
        if 'equipment_utilization' not in metrics or not metrics['equipment_utilization']:
            # 返回空图表
            fig = go.Figure()
            fig.update_layout(
                title="设备利用率（无数据）",
                xaxis_title="设备",
                yaxis_title="利用率 (%)"
            )
            return fig
        
        utilization = metrics['equipment_utilization']
        
        # 准备数据
        equipment_ids = list(utilization.keys())
        utilization_values = [utilization[eq_id] for eq_id in equipment_ids]
        
        # 创建柱状图
        fig = go.Figure(data=[
            go.Bar(
                x=equipment_ids,
                y=utilization_values,
                text=[f'{val:.1f}%' for val in utilization_values],
                textposition='auto',
                marker_color='rgb(55, 83, 109)'
            )
        ])
        
        # 更新布局
        fig.update_layout(
            title='设备利用率分析',
            xaxis_title='设备编号',
            yaxis_title='利用率 (%)',
            yaxis_range=[0, 100],
            showlegend=False,
            height=400
        )
        
        return fig
    
    def save_gantt_to_file(self, figure, file_path: str):
        """
        保存甘特图到文件
        
        Args:
            figure: Plotly Figure 对象
            file_path: 保存路径
        """
        # 根据文件扩展名选择保存格式
        if file_path.endswith('.html'):
            figure.write_html(file_path)
        elif file_path.endswith('.png'):
            figure.write_image(file_path)
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            figure.write_image(file_path)
        elif file_path.endswith('.pdf'):
            figure.write_image(file_path)
        else:
            # 默认保存为 HTML
            figure.write_html(file_path + '.html')
    
    def export_schedule_to_excel(self, schedule: ScheduleResult, file_path: str):
        """
        导出排程结果为 Excel 格式
        
        Args:
            schedule: 排程结果
            file_path: 保存路径
        """
        if not schedule.operations:
            # 创建空的DataFrame
            df = pd.DataFrame(columns=[
                '订单号', '工序编号', '设备编号', '开始时间', '结束时间', '持续时间(小时)'
            ])
        else:
            # 构建数据
            data = []
            for op in schedule.operations:
                data.append({
                    '订单号': op.order_id,
                    '工序编号': op.operation_id,
                    '设备编号': op.equipment_id,
                    '开始时间': op.start_time.strftime('%Y-%m-%d %H:%M'),
                    '结束时间': op.end_time.strftime('%Y-%m-%d %H:%M'),
                    '持续时间(小时)': round(op.duration, 2)
                })
            
            df = pd.DataFrame(data)
        
        # 导出到Excel
        df.to_excel(file_path, index=False, engine='openpyxl')
    
    def export_schedule_to_csv(self, schedule: ScheduleResult, file_path: str):
        """
        导出排程结果为 CSV 格式
        
        Args:
            schedule: 排程结果
            file_path: 保存路径
        """
        if not schedule.operations:
            # 创建空的DataFrame
            df = pd.DataFrame(columns=[
                '订单号', '工序编号', '设备编号', '开始时间', '结束时间', '持续时间(小时)'
            ])
        else:
            # 构建数据
            data = []
            for op in schedule.operations:
                data.append({
                    '订单号': op.order_id,
                    '工序编号': op.operation_id,
                    '设备编号': op.equipment_id,
                    '开始时间': op.start_time.strftime('%Y-%m-%d %H:%M'),
                    '结束时间': op.end_time.strftime('%Y-%m-%d %H:%M'),
                    '持续时间(小时)': round(op.duration, 2)
                })
            
            df = pd.DataFrame(data)
        
        # 导出到CSV
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
