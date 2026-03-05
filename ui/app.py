"""
Streamlit Web 应用主程序

提供用户交互界面，用于上传数据、执行排程、展示结果。
"""

import streamlit as st


def main():
    """主应用程序入口"""
    st.set_page_config(
        page_title="生产排程智能体",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🏭 生产排程智能体")
    st.markdown("基于约束规划的自动化生产排程系统")
    
    # 侧边栏
    with st.sidebar:
        st.header("📁 数据上传")
        st.info("请上传以下三个数据文件：")
        
        # 文件上传组件（待实现）
        st.file_uploader("订单数据 (orders.xlsx)", type=['xlsx', 'xls'])
        st.file_uploader("工艺路线 (processes.xlsx)", type=['xlsx', 'xls'])
        st.file_uploader("设备数据 (equipment.xlsx)", type=['xlsx', 'xls'])
    
    # 主内容区
    st.header("📋 数据预览")
    st.info("上传数据文件后，这里将显示数据预览")
    
    # 排程按钮
    st.header("🚀 开始排程")
    if st.button("执行排程计算", type="primary", disabled=True):
        st.info("排程功能将在后续任务中实现")
    
    # 结果展示区
    st.header("📊 排程结果")
    tab1, tab2, tab3 = st.tabs(["甘特图", "关键指标", "详细数据"])
    
    with tab1:
        st.info("甘特图将在这里显示")
    
    with tab2:
        st.info("关键指标将在这里显示")
    
    with tab3:
        st.info("详细排程数据将在这里显示")


if __name__ == "__main__":
    main()
