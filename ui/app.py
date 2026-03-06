"""
Streamlit Web 应用主程序

提供用户交互界面，用于上传数据、执行排程、展示结果。
"""

import streamlit as st
import tempfile
import os
import pandas as pd
import io
from typing import Optional
from data_layer.parser import DataParser
from data_layer.validator import DataValidator
from data_layer.models import Order, Process, Equipment, ScheduleResult
from business_logic.scheduler import Scheduler
from business_logic.metrics import MetricsCalculator
from business_logic.visualizer import Visualizer


def init_session_state():
    """初始化 session_state 状态管理"""
    if 'orders' not in st.session_state:
        st.session_state.orders = None
    if 'processes' not in st.session_state:
        st.session_state.processes = None
    if 'equipment' not in st.session_state:
        st.session_state.equipment = None
    if 'schedule_result' not in st.session_state:
        st.session_state.schedule_result = None
    if 'metrics' not in st.session_state:
        st.session_state.metrics = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False


def load_and_validate_data(data_file):
    """
    加载并验证上传的数据文件
    
    Args:
        data_file: 包含订单、工艺路线、设备数据的 Excel 文件
        
    Returns:
        tuple: (success, message, orders, processes, equipment)
    """
    parser = DataParser()
    validator = DataValidator()
    
    try:
        # 保存上传的文件到临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存数据文件
            data_path = os.path.join(temp_dir, "data.xlsx")
            with open(data_path, "wb") as f:
                f.write(data_file.getbuffer())
            
            # 从同一个文件的不同工作表解析数据
            orders = parser.parse_orders(data_path)
            processes = parser.parse_processes(data_path)
            equipment = parser.parse_equipment(data_path)
            
            # 验证数据
            orders_validation = validator.validate_orders(orders)
            if not orders_validation.is_valid:
                error_msg = "订单数据验证失败：\n" + "\n".join(orders_validation.errors)
                return False, error_msg, None, None, None
            
            processes_validation = validator.validate_processes(processes)
            if not processes_validation.is_valid:
                error_msg = "工艺路线数据验证失败：\n" + "\n".join(processes_validation.errors)
                return False, error_msg, None, None, None
            
            equipment_validation = validator.validate_equipment(equipment)
            if not equipment_validation.is_valid:
                error_msg = "设备数据验证失败：\n" + "\n".join(equipment_validation.errors)
                return False, error_msg, None, None, None
            
            # 验证数据一致性
            consistency_validation = validator.validate_consistency(orders, processes, equipment)
            if not consistency_validation.is_valid:
                error_msg = "数据一致性验证失败：\n" + "\n".join(consistency_validation.errors)
                return False, error_msg, None, None, None
            
            # 收集警告信息
            warnings = []
            if orders_validation.warnings:
                warnings.extend(orders_validation.warnings)
            if processes_validation.warnings:
                warnings.extend(processes_validation.warnings)
            if equipment_validation.warnings:
                warnings.extend(equipment_validation.warnings)
            if consistency_validation.warnings:
                warnings.extend(consistency_validation.warnings)
            
            success_msg = "✅ 数据加载成功！"
            if warnings:
                success_msg += "\n\n⚠️ 警告：\n" + "\n".join(warnings)
            
            return True, success_msg, orders, processes, equipment
            
    except FileNotFoundError as e:
        return False, f"文件未找到: {str(e)}", None, None, None
    except ValueError as e:
        return False, f"数据格式错误: {str(e)}", None, None, None
    except Exception as e:
        return False, f"加载数据时发生错误: {str(e)}", None, None, None


def main():
    """主应用程序入口"""
    # 页面配置
    st.set_page_config(
        page_title="生产排程智能体",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化状态
    init_session_state()
    
    # 页面标题
    st.title("🏭 生产排程智能体")
    st.markdown("基于约束规划的自动化生产排程系统")
    st.markdown("---")
    
    # 侧边栏 - 数据上传区
    with st.sidebar:
        st.header("📁 数据上传")
        st.markdown("请上传包含订单、工艺路线、设备数据的 Excel 文件")
        st.caption("文件应包含三个工作表：订单表、工艺路线表、设备表")
        
        # 文件上传组件
        data_file = st.file_uploader(
            "生产数据 (data.xlsx)", 
            type=['xlsx', 'xls'],
            key='data_file',
            help="Excel 文件应包含三个工作表：订单表、工艺路线表、设备表"
        )
        
        # 加载数据按钮
        if data_file:
            if st.button("📥 加载数据", type="primary", width='stretch'):
                with st.spinner("正在加载和验证数据..."):
                    success, message, orders, processes, equipment = load_and_validate_data(
                        data_file
                    )
                    
                    if success:
                        st.session_state.orders = orders
                        st.session_state.processes = processes
                        st.session_state.equipment = equipment
                        st.session_state.data_loaded = True
                        st.session_state.schedule_result = None  # 清除旧的排程结果
                        st.session_state.metrics = None
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                        st.session_state.data_loaded = False
        
        st.markdown("---")
        
        # 显示数据加载状态
        if st.session_state.data_loaded:
            st.success("✅ 数据已加载")
            if st.session_state.orders:
                st.info(f"📦 订单数: {len(st.session_state.orders)}")
            if st.session_state.processes:
                st.info(f"⚙️ 工序数: {len(st.session_state.processes)}")
            if st.session_state.equipment:
                st.info(f"🔧 设备数: {len(st.session_state.equipment)}")
            
            # 清除数据按钮
            if st.button("🗑️ 清除数据", width='stretch'):
                st.session_state.orders = None
                st.session_state.processes = None
                st.session_state.equipment = None
                st.session_state.data_loaded = False
                st.session_state.schedule_result = None
                st.session_state.metrics = None
                st.rerun()
        else:
            st.warning("⚠️ 请上传数据文件")
    
    # 主内容区
    # 数据预览区
    st.header("📋 数据预览")
    if not st.session_state.data_loaded:
        st.info("上传数据文件后，这里将显示数据预览")
    else:
        # 使用 tabs 展示不同数据
        preview_tab1, preview_tab2, preview_tab3 = st.tabs(["订单数据", "工艺路线", "设备数据"])
        
        with preview_tab1:
            if st.session_state.orders:
                st.subheader(f"订单数据 ({len(st.session_state.orders)} 条)")
                # 转换为 DataFrame 显示
                orders_data = []
                for order in st.session_state.orders:
                    orders_data.append({
                        '订单号': order.order_id,
                        '产品编码': order.product_id,
                        '数量': order.quantity,
                        '交期': order.due_date.strftime('%Y-%m-%d'),
                        '优先级': order.priority,
                        '是否急单': '是' if order.is_urgent else '否'
                    })
                df_orders = pd.DataFrame(orders_data)
                st.dataframe(df_orders, width='stretch', hide_index=True)
        
        with preview_tab2:
            if st.session_state.processes:
                st.subheader(f"工艺路线数据 ({len(st.session_state.processes)} 条)")
                # 转换为 DataFrame 显示
                processes_data = []
                for process in st.session_state.processes:
                    processes_data.append({
                        '产品编码': process.product_id,
                        '工序编号': process.operation_id,
                        '工序名称': process.operation_name,
                        '工序顺序': process.sequence,
                        '标准工时(分钟)': f"{process.standard_time:.1f}",
                        '换型时间(分钟)': f"{process.changeover_time:.1f}",
                        '所需设备': process.required_equipment,
                        '前置工序': process.predecessor or '-'
                    })
                df_processes = pd.DataFrame(processes_data)
                st.dataframe(df_processes, width='stretch', hide_index=True)
        
        with preview_tab3:
            if st.session_state.equipment:
                st.subheader(f"设备数据 ({len(st.session_state.equipment)} 条)")
                # 转换为 DataFrame 显示
                equipment_data = []
                for equip in st.session_state.equipment:
                    equipment_data.append({
                        '设备编号': equip.equipment_id,
                        '状态': equip.status,
                        '效率系数': f"{equip.efficiency:.2f}",
                        '产能(小时/天)': equip.capacity,
                        '换型时间(分钟)': f"{equip.changeover_time:.1f}",
                        '可用开始': equip.available_start.strftime('%Y-%m-%d'),
                        '可用结束': equip.available_end.strftime('%Y-%m-%d')
                    })
                df_equipment = pd.DataFrame(equipment_data)
                st.dataframe(df_equipment, width='stretch', hide_index=True)
    
    st.markdown("---")
    
    # 排程计算区
    st.header("🚀 排程计算")
    
    if not st.session_state.data_loaded:
        st.info("请先上传并加载数据")
    else:
        # 排程目标权重设置
        st.subheader("排程目标设置")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            due_date_weight = st.slider(
                "交期优先",
                min_value=0.0,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="优先满足订单交期，减少延期"
            )
        
        with col2:
            utilization_weight = st.slider(
                "设备利用率",
                min_value=0.0,
                max_value=2.0,
                value=0.5,
                step=0.1,
                help="提高设备使用效率"
            )
        
        with col3:
            changeover_weight = st.slider(
                "最小换产",
                min_value=0.0,
                max_value=2.0,
                value=0.3,
                step=0.1,
                help="减少设备换产次数"
            )
        
        with col4:
            makespan_weight = st.slider(
                "最小完工时间",
                min_value=0.0,
                max_value=2.0,
                value=0.2,
                step=0.1,
                help="缩短总完工时间"
            )
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("点击下方按钮开始执行排程计算")
        
        with col2:
            if st.button(
                "开始排程", 
                type="primary", 
                disabled=not st.session_state.data_loaded,
                width='stretch'
            ):
                # 执行排程计算
                with st.spinner("🔄 正在执行排程计算，请稍候..."):
                    try:
                        # 构建目标权重字典
                        objective_weights = {
                            'due_date': due_date_weight,
                            'utilization': utilization_weight,
                            'changeover': changeover_weight,
                            'makespan': makespan_weight
                        }
                        
                        # 创建排程引擎
                        scheduler = Scheduler(
                            st.session_state.orders,
                            st.session_state.processes,
                            st.session_state.equipment,
                            objective_weights=objective_weights
                        )
                        
                        # 执行排程
                        schedule_result = scheduler.solve()
                        
                        # 检查排程结果状态
                        if schedule_result.status == 'INFEASIBLE':
                            st.error("❌ 排程失败：无法找到可行解")
                            st.error("可能的原因：")
                            st.error("- 约束过于严格（交期太紧、设备不足）")
                            st.error("- 工艺路线存在冲突")
                            st.error("- 设备产能不足")
                            st.session_state.schedule_result = None
                            st.session_state.metrics = None
                        elif schedule_result.status == 'UNKNOWN':
                            st.error("❌ 排程失败：求解器状态未知")
                            st.error("可能的原因：")
                            st.error("- 求解超时")
                            st.error("- 问题规模过大")
                            st.session_state.schedule_result = None
                            st.session_state.metrics = None
                        else:
                            # 排程成功
                            st.session_state.schedule_result = schedule_result
                            
                            # 计算指标
                            metrics_calculator = MetricsCalculator(st.session_state.equipment)
                            
                            makespan = metrics_calculator.calculate_makespan(schedule_result)
                            utilization = metrics_calculator.calculate_equipment_utilization(schedule_result)
                            on_time_rate = metrics_calculator.calculate_on_time_delivery(
                                schedule_result, 
                                st.session_state.orders
                            )
                            bottleneck = metrics_calculator.identify_bottleneck(schedule_result)
                            
                            st.session_state.metrics = {
                                'makespan': makespan,
                                'equipment_utilization': utilization,
                                'on_time_delivery_rate': on_time_rate,
                                'bottleneck_equipment': bottleneck
                            }
                            
                            st.success(f"✅ 排程计算完成！（耗时: {schedule_result.solve_time:.2f} 秒）")
                            st.success(f"状态: {schedule_result.status}")
                            st.success(f"总完工时间: {makespan:.2f} 小时")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ 排程计算过程中发生错误: {str(e)}")
                        st.session_state.schedule_result = None
                        st.session_state.metrics = None
        
        with col3:
            if st.button(
                "清除结果",
                disabled=st.session_state.schedule_result is None,
                width='stretch'
            ):
                st.session_state.schedule_result = None
                st.session_state.metrics = None
                st.success("✅ 排程结果已清除")
                st.rerun()
        
        # 显示当前排程状态
        if st.session_state.schedule_result:
            st.info(f"✅ 已完成排程计算 - 状态: {st.session_state.schedule_result.status}")
            st.info(f"📊 总完工时间: {st.session_state.schedule_result.makespan:.2f} 小时")
            st.info(f"⏱️ 求解耗时: {st.session_state.schedule_result.solve_time:.2f} 秒")
    
    st.markdown("---")
    
    # 结果展示区
    st.header("📊 排程结果")
    
    if st.session_state.schedule_result is None:
        st.info("执行排程后，结果将在这里显示")
    else:
        # 使用 tabs 组织不同视图
        tab1, tab2, tab3 = st.tabs(["📈 甘特图", "📊 关键指标", "📋 详细数据"])
        
        with tab1:
            st.subheader("生产排程甘特图")
            
            try:
                # 生成甘特图
                visualizer = Visualizer(st.session_state.equipment)
                gantt_fig = visualizer.generate_gantt_chart(st.session_state.schedule_result)
                
                # 显示甘特图（启用交互功能）
                st.plotly_chart(gantt_fig, width='stretch', config={
                    'scrollZoom': True,  # 启用滚轮缩放
                    'displayModeBar': True,  # 显示工具栏
                    'modeBarButtonsToAdd': ['pan2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
                })
                
                st.markdown("---")
                st.caption("💡 提示：甘特图展示了每台设备上的工序安排，不同颜色代表不同订单。可以拖动、缩放查看详细信息")
                
            except Exception as e:
                st.error(f"生成甘特图时发生错误: {str(e)}")
        
        with tab2:
            st.subheader("关键性能指标")
            
            if st.session_state.metrics:
                # 使用列布局展示关键指标
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric(
                        label="📅 总完工时间",
                        value=f"{st.session_state.metrics['makespan']:.2f} 小时",
                        help="所有订单完成所需的总时间"
                    )
                
                with metric_col2:
                    st.metric(
                        label="✅ 交期达成率",
                        value=f"{st.session_state.metrics['on_time_delivery_rate']:.1f}%",
                        help="按时完成的订单比例"
                    )
                
                with metric_col3:
                    bottleneck = st.session_state.metrics['bottleneck_equipment']
                    st.metric(
                        label="🔧 瓶颈设备",
                        value=bottleneck if bottleneck else "无",
                        help="利用率最高的设备"
                    )
                
                st.markdown("---")
                
                # 设备利用率图表
                st.subheader("设备利用率分析")
                
                try:
                    utilization_fig = visualizer.generate_utilization_chart(st.session_state.metrics)
                    st.plotly_chart(utilization_fig, width='stretch')
                except Exception as e:
                    st.error(f"生成利用率图表时发生错误: {str(e)}")
                
                st.markdown("---")
                
                # 设备利用率详细表格
                st.subheader("设备利用率详情")
                utilization_data = []
                for eq_id, util in st.session_state.metrics['equipment_utilization'].items():
                    utilization_data.append({
                        '设备编号': eq_id,
                        '利用率': f"{util:.2f}%",
                        '状态': '瓶颈' if eq_id == bottleneck else '正常'
                    })
                
                df_utilization = pd.DataFrame(utilization_data)
                df_utilization = df_utilization.sort_values('利用率', ascending=False)
                st.dataframe(df_utilization, width='stretch', hide_index=True)
            else:
                st.warning("指标数据不可用")
        
        with tab3:
            st.subheader("详细排程数据")
            
            if st.session_state.schedule_result.operations:
                # 转换为 DataFrame 显示
                operations_data = []
                for op in st.session_state.schedule_result.operations:
                    operations_data.append({
                        '订单号': op.order_id,
                        '工序编号': op.operation_id,
                        '设备编号': op.equipment_id,
                        '开始时间': op.start_time.strftime('%Y-%m-%d %H:%M'),
                        '结束时间': op.end_time.strftime('%Y-%m-%d %H:%M'),
                        '持续时间(小时)': f"{op.duration:.2f}"
                    })
                
                df_operations = pd.DataFrame(operations_data)
                
                # 添加筛选功能
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    # 按订单筛选
                    order_ids = ['全部'] + sorted(list(set(op.order_id for op in st.session_state.schedule_result.operations)))
                    selected_order = st.selectbox("筛选订单", order_ids)
                
                with filter_col2:
                    # 按设备筛选
                    equipment_ids = ['全部'] + sorted(list(set(op.equipment_id for op in st.session_state.schedule_result.operations)))
                    selected_equipment = st.selectbox("筛选设备", equipment_ids)
                
                # 应用筛选
                filtered_df = df_operations.copy()
                if selected_order != '全部':
                    filtered_df = filtered_df[filtered_df['订单号'] == selected_order]
                if selected_equipment != '全部':
                    filtered_df = filtered_df[filtered_df['设备编号'] == selected_equipment]
                
                st.dataframe(filtered_df, width='stretch', hide_index=True)
                
                st.caption(f"共 {len(filtered_df)} 条记录（总计 {len(df_operations)} 条）")
            else:
                st.warning("没有排程数据")
    
    # 结果导出区
    if st.session_state.schedule_result is not None:
        st.markdown("---")
        st.header("💾 导出结果")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            st.subheader("导出为 Excel")
            
            try:
                # 生成 Excel 文件
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                tmp_file.close()  # 关闭文件句柄，Windows 需要这样做
                
                visualizer = Visualizer(st.session_state.equipment)
                visualizer.export_schedule_to_excel(st.session_state.schedule_result, tmp_file.name)
                
                # 读取文件内容
                with open(tmp_file.name, 'rb') as f:
                    excel_data = f.read()
                
                # 删除临时文件
                os.unlink(tmp_file.name)
                
                # 提供下载按钮
                st.download_button(
                    label="📥 下载 Excel 文件",
                    data=excel_data,
                    file_name="排程结果.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )
                
                st.caption("包含订单号、工序、设备、时间等详细信息")
                
            except Exception as e:
                st.error(f"生成 Excel 文件时发生错误: {str(e)}")
        
        with export_col2:
            st.subheader("导出为 CSV")
            
            try:
                # 生成 CSV 文件
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8-sig')
                tmp_file.close()  # 关闭文件句柄，Windows 需要这样做
                
                visualizer = Visualizer(st.session_state.equipment)
                visualizer.export_schedule_to_csv(st.session_state.schedule_result, tmp_file.name)
                
                # 读取文件内容
                with open(tmp_file.name, 'r', encoding='utf-8-sig') as f:
                    csv_data = f.read()
                
                # 删除临时文件
                os.unlink(tmp_file.name)
                
                # 提供下载按钮
                st.download_button(
                    label="📥 下载 CSV 文件",
                    data=csv_data,
                    file_name="排程结果.csv",
                    mime="text/csv",
                    width='stretch'
                )
                
                st.caption("适用于进一步数据分析和处理")
                
            except Exception as e:
                st.error(f"生成 CSV 文件时发生错误: {str(e)}")


if __name__ == "__main__":
    main()
