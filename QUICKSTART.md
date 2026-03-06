# 快速开始指南

本指南将帮助您在5分钟内启动并运行生产排程智能体。

## 前置要求

- Python 3.8 或更高版本
- 网络连接（用于安装依赖包）

## 快速启动步骤

### Windows 用户

1. **双击运行启动脚本**
   ```
   双击 run.bat 文件
   ```

2. **等待自动配置**
   - 脚本会自动检查 Python 环境
   - 自动创建虚拟环境（如果不存在）
   - 自动安装依赖包（如果未安装）
   - 自动启动 Web 应用

3. **访问应用**
   - 浏览器会自动打开 `http://localhost:8501`
   - 如果没有自动打开，请手动访问该地址

### Linux/Mac 用户

1. **在终端中运行启动脚本**
   ```bash
   chmod +x run.sh  # 首次运行需要添加执行权限
   ./run.sh
   ```

2. **等待自动配置**
   - 脚本会自动检查 Python 环境
   - 自动创建虚拟环境（如果不存在）
   - 自动安装依赖包（如果未安装）
   - 自动启动 Web 应用

3. **访问应用**
   - 浏览器会自动打开 `http://localhost:8501`
   - 如果没有自动打开，请手动访问该地址

## 使用示例数据

系统提供了示例数据文件，您可以直接使用：

1. 在 Web 界面的侧边栏找到"数据上传"区域
2. 上传以下文件（位于 `tests/` 目录）：
   - 订单数据：`tests/example_data.xlsx` (选择"订单表"工作表)
   - 工艺路线数据：`tests/example_data.xlsx` (选择"工艺路线表"工作表)
   - 设备数据：`tests/example_data.xlsx` (选择"设备表"工作表)
3. 点击"开始排程"按钮
4. 查看排程结果

## 使用自己的数据

### 准备数据文件

创建一个 Excel 文件，包含三个工作表：

1. **订单表**（必填字段）
   - 订单号
   - 产品编码
   - 生产数量（件）
   - 承诺交期
   - 优先级（1最高）
   - 是否急单

2. **工艺路线表**（必填字段）
   - 产品编码
   - 工序号
   - 工序名称
   - 工序顺序
   - 单件标准工时（分钟）
   - 可使用设备编号

3. **设备表**（必填字段）
   - 设备编号
   - 状态
   - 每日工作小时

详细的数据格式说明请参考 `docs/DATA_FORMAT.md`

### 上传并运行

1. 在 Web 界面上传您的数据文件
2. 系统会自动验证数据格式
3. 如果验证通过，点击"开始排程"
4. 等待计算完成（通常10-60秒）
5. 查看甘特图、指标和详细数据
6. 下载排程结果

## 常见问题

### Q: 启动脚本报错"未检测到 Python"

**A**: 请先安装 Python 3.8 或更高版本
- Windows: 从 https://www.python.org/downloads/ 下载安装
- Mac: `brew install python3`
- Ubuntu/Debian: `sudo apt-get install python3 python3-venv python3-pip`

### Q: 依赖包安装失败

**A**: 尝试以下方法：
1. 确保网络连接正常
2. 手动安装：
   ```bash
   # Windows
   venv\Scripts\activate
   pip install -r requirements.txt
   
   # Linux/Mac
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. 如果仍然失败，尝试使用国内镜像：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### Q: 浏览器没有自动打开

**A**: 手动在浏览器中访问 `http://localhost:8501`

### Q: 端口 8501 被占用

**A**: 修改端口号：
```bash
streamlit run ui/app.py --server.port 8502
```

### Q: 数据上传后显示验证错误

**A**: 请检查：
1. 工作表名称是否正确（订单表、工艺路线表、设备表）
2. 表头是否在第2行
3. 必填字段是否完整
4. 数据格式是否符合要求
详细说明请参考 `docs/DATA_FORMAT.md`

### Q: 排程计算时间过长

**A**: 
- 小规模问题（10-20订单）通常在10秒内完成
- 中等规模（20-50订单）可能需要30-60秒
- 大规模问题建议分批处理或简化约束

### Q: 如何停止应用

**A**: 在终端窗口按 `Ctrl+C`

## 下一步

- 阅读完整的 [README.md](README.md) 了解更多功能
- 查看 [数据格式说明](docs/DATA_FORMAT.md) 了解详细的数据要求
- 查看 [设计文档](.kiro/specs/production-scheduling-agent/design.md) 了解系统架构
- 运行测试：`pytest tests/`

## 技术支持

如遇到问题，请：
1. 查看本文档的常见问题部分
2. 查看 `docs/DATA_FORMAT.md` 中的常见问题
3. 查看项目 README.md
4. 查看系统日志输出

---

**祝您使用愉快！**
