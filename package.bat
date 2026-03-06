@echo off
echo ========================================
echo 生产排程系统打包脚本
echo ========================================
echo.

echo [1/4] 清理旧文件...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.zip del /q *.zip

echo [2/4] 创建发布目录...
mkdir dist
mkdir dist\production-scheduler

echo [3/4] 复制项目文件...
xcopy /E /I /Y data_layer dist\production-scheduler\data_layer
xcopy /E /I /Y business_logic dist\production-scheduler\business_logic
xcopy /E /I /Y ui dist\production-scheduler\ui
xcopy /E /I /Y docs dist\production-scheduler\docs
copy requirements.txt dist\production-scheduler\
copy README.md dist\production-scheduler\
copy DEPLOYMENT.md dist\production-scheduler\
copy run.bat dist\production-scheduler\
copy Dockerfile dist\production-scheduler\
copy docker-compose.yml dist\production-scheduler\

echo [4/4] 创建压缩包...
powershell Compress-Archive -Path dist\production-scheduler -DestinationPath production-scheduler-v1.0.0.zip -Force

echo.
echo ========================================
echo 打包完成！
echo 输出文件: production-scheduler-v1.0.0.zip
echo ========================================
pause
