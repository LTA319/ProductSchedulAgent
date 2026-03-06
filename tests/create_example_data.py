"""
创建示例数据文件

生成符合格式要求的示例 Excel 文件，用于测试和演示排程系统。
包含 10-15 个订单、相应的工艺路线和设备数据。
"""

import pandas as pd
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


def create_example_data():
    """创建示例数据 Excel 文件"""
    
    # 创建 Excel writer
    output_file = 'tests/example_data.xlsx'
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 1. 创建订单表
        create_orders_sheet(writer)
        
        # 2. 创建工艺路线表
        create_processes_sheet(writer)
        
        # 3. 创建设备表
        create_equipment_sheet(writer)
    
    print(f"示例数据文件已创建: {output_file}")


def create_orders_sheet(writer):
    """创建订单表"""
    
    # 基准日期
    # base_date = datetime(2026, 3, 6)
    base_date = datetime.today()

    # 订单数据
    orders_data = [
        # 订单号, 产品编码, 产品名称, 生产数量, 承诺交期, 优先级, 是否急单
        ['SO20260306-001', 'PROD-001', '轴套A型', 50, base_date + timedelta(days=5), 1, '否'],
        ['SO20260306-002', 'PROD-002', '轴套B型', 30, base_date + timedelta(days=3), 2, '是'],
        ['SO20260306-003', 'PROD-003', '法兰盘C型', 40, base_date + timedelta(days=7), 3, '否'],
        ['SO20260306-004', 'PROD-004', '连接件D型', 60, base_date + timedelta(days=10), 4, '否'],
        ['SO20260306-005', 'PROD-005', '传动轴E型', 25, base_date + timedelta(days=4), 2, '是'],
        ['SO20260306-006', 'PROD-001', '轴套A型', 35, base_date + timedelta(days=8), 3, '否'],
        ['SO20260306-007', 'PROD-006', '导向套F型', 45, base_date + timedelta(days=6), 3, '否'],
        ['SO20260306-008', 'PROD-002', '轴套B型', 20, base_date + timedelta(days=5), 4, '否'],
        ['SO20260306-009', 'PROD-007', '支撑座G型', 55, base_date + timedelta(days=9), 4, '否'],
        ['SO20260306-010', 'PROD-003', '法兰盘C型', 30, base_date + timedelta(days=6), 3, '否'],
        ['SO20260306-011', 'PROD-008', '齿轮轴H型', 40, base_date + timedelta(days=12), 5, '否'],
        ['SO20260306-012', 'PROD-004', '连接件D型', 50, base_date + timedelta(days=8), 4, '否'],
    ]
    
    # 创建 DataFrame
    df = pd.DataFrame(orders_data, columns=[
        '订单号', '产品编码', '产品名称', '生产数量（件）', '承诺交期', '优先级（1最高）', '是否急单'
    ])
    
    # 写入 Excel，第一行为标题说明
    df.to_excel(writer, sheet_name='订单表', startrow=1, index=False)
    
    # 获取工作表并添加标题行
    worksheet = writer.sheets['订单表']
    worksheet['A1'] = '订单信息表 - 包含客户订单的基本信息'
    worksheet['A1'].font = Font(bold=True, size=12)


def create_processes_sheet(writer):
    """创建工艺路线表"""
    
    # 工艺路线数据
    processes_data = [
        # 产品编码, 工序号, 工序名称, 工序顺序, 单件标准工时(分钟), 可使用设备编号, 换型时间(分钟)
        # PROD-001: 轴套A型 (3道工序)
        ['PROD-001', 'OP010', '数控车外圆', 1, 8, 'M01,M02', 20],
        ['PROD-001', 'OP020', '铣键槽', 2, 6, 'M03', 15],
        ['PROD-001', 'OP030', '钻孔', 3, 4, 'M04,M05', 10],
        
        # PROD-002: 轴套B型 (4道工序)
        ['PROD-002', 'OP010', '数控车外圆', 1, 10, 'M01,M02', 25],
        ['PROD-002', 'OP020', '磨外圆', 2, 12, 'M06', 20],
        ['PROD-002', 'OP030', '铣槽', 3, 8, 'M03', 15],
        ['PROD-002', 'OP040', '钻孔', 4, 5, 'M04,M05', 10],
        
        # PROD-003: 法兰盘C型 (3道工序)
        ['PROD-003', 'OP010', '车端面', 1, 6, 'M01,M02', 15],
        ['PROD-003', 'OP020', '钻孔', 2, 8, 'M04,M05', 12],
        ['PROD-003', 'OP030', '铣平面', 3, 10, 'M03', 18],
        
        # PROD-004: 连接件D型 (2道工序)
        ['PROD-004', 'OP010', '铣平面', 1, 12, 'M03', 20],
        ['PROD-004', 'OP020', '钻孔', 2, 6, 'M04,M05', 10],
        
        # PROD-005: 传动轴E型 (4道工序)
        ['PROD-005', 'OP010', '数控车外圆', 1, 15, 'M01,M02', 30],
        ['PROD-005', 'OP020', '磨外圆', 2, 18, 'M06', 25],
        ['PROD-005', 'OP030', '铣键槽', 3, 10, 'M03', 15],
        ['PROD-005', 'OP040', '钻孔', 4, 8, 'M04,M05', 12],
        
        # PROD-006: 导向套F型 (3道工序)
        ['PROD-006', 'OP010', '数控车内孔', 1, 12, 'M01,M02', 22],
        ['PROD-006', 'OP020', '磨内孔', 2, 15, 'M06', 20],
        ['PROD-006', 'OP030', '钻孔', 3, 6, 'M04,M05', 10],
        
        # PROD-007: 支撑座G型 (3道工序)
        ['PROD-007', 'OP010', '铣平面', 1, 14, 'M03', 22],
        ['PROD-007', 'OP020', '钻孔', 2, 10, 'M04,M05', 15],
        ['PROD-007', 'OP030', '攻丝', 3, 8, 'M07', 12],
        
        # PROD-008: 齿轮轴H型 (5道工序)
        ['PROD-008', 'OP010', '数控车外圆', 1, 20, 'M01,M02', 35],
        ['PROD-008', 'OP020', '磨外圆', 2, 22, 'M06', 30],
        ['PROD-008', 'OP030', '铣齿', 3, 25, 'M08', 40],
        ['PROD-008', 'OP040', '钻孔', 4, 10, 'M04,M05', 15],
        ['PROD-008', 'OP050', '攻丝', 5, 8, 'M07', 12],
    ]
    
    # 创建 DataFrame
    df = pd.DataFrame(processes_data, columns=[
        '产品编码', '工序号', '工序名称', '工序顺序', '单件标准工时（分钟）', '可使用设备编号', '换型时间（分钟）'
    ])
    
    # 写入 Excel
    df.to_excel(writer, sheet_name='工艺路线表', startrow=1, index=False)
    
    # 添加标题行
    worksheet = writer.sheets['工艺路线表']
    worksheet['A1'] = '工艺路线表 - 定义产品的加工工序和设备要求'
    worksheet['A1'].font = Font(bold=True, size=12)


def create_equipment_sheet(writer):
    """创建设备表"""
    
    # 设备数据
    equipment_data = [
        # 设备编号, 设备名称, 班组, 状态, 每日工作小时, 效率系数, 换型时间(分钟)
        ['M01', '数控车床CK6140', '白班', '可用', 8, 1.00, 20],
        ['M02', '数控车床CK6150', '白班', '可用', 8, 1.00, 20],
        ['M03', '立式加工中心VMC850', '白班', '可用', 8, 0.95, 25],
        ['M04', '摇臂钻床Z3050', '白班', '可用', 8, 1.00, 15],
        ['M05', '台钻Z4125', '白班', '可用', 8, 1.00, 10],
        ['M06', '外圆磨床M1432', '白班', '可用', 8, 0.90, 30],
        ['M07', '攻丝机S4016', '白班', '可用', 8, 1.00, 12],
        ['M08', '滚齿机Y3150E', '白班', '可用', 8, 0.85, 40],
    ]
    
    # 创建 DataFrame
    df = pd.DataFrame(equipment_data, columns=[
        '设备编号', '设备名称', '班组', '状态', '每日工作小时', '效率系数', '换型时间（分钟）'
    ])
    
    # 写入 Excel
    df.to_excel(writer, sheet_name='设备表', startrow=1, index=False)
    
    # 添加标题行
    worksheet = writer.sheets['设备表']
    worksheet['A1'] = '设备资源表 - 车间可用设备信息'
    worksheet['A1'].font = Font(bold=True, size=12)


if __name__ == '__main__':
    create_example_data()
