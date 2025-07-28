
OLED System Monitor 安装指南

## 硬件要求
- 支持I2C的OLED屏幕（128x64分辨率推荐）
- Orange Pi/Raspberry Pi等Linux单板计算机
- microSD卡（建议8GB以上）

## 软件依赖
1. Python 3.6+
2. 必要库：
   ```bash
   pip install luma.core luma.oled psutil Pillow
   ```
3. 字体文件（需手动下载）：
   - DejaVuSans.ttf（可从https://www.fontsquirrel.com/fonts/dejavu-sans下载）

## 设备配置
### 1. I2C接口启用
```bash
# Raspberry Pi配置示例
sudo raspi-config
# 选择 Interfacing Options -> I2C -> Enable

# Orange Pi配置示例
sudo nano /etc/modules-load.d/i2c.conf
# 添加内容：i2c-dev
sudo reboot
```

### 2. 权限设置
```bash
# 添加用户到i2c组（永久生效）
sudo usermod -aG i2c $USER
# 临时权限修复（每次开机需执行）
echo 'sudo chmod 666 /dev/i2c-0' >> ~/.bashrc
source ~/.bashrc
```

## 项目部署
### 1. 代码获取
```bash
git clone https://github.com/Hex994/oled-monitor.git
cd oled-monitor
```

### 2. 配置文件（可选）
创建config.py添加自定义配置：
```python
# 自定义参数示例
SCREEN_HEIGHT = 32  # 修改为实际屏幕高度
FONT_PATH = "/path/to/DejaVuSans.ttf"  # 修改为实际字体路径
UPDATE_INTERVAL = 5  # 数据更新间隔（秒）
```

## 运行程序
```bash
# 后台运行（推荐）
nohup python3 main.py >/dev/null 2>&1 &

# 前台调试
python3 main.py
```

## 故障排查
1. **屏幕无显示**
   - 检查I2C连接（使用i2cdetect命令）
   - 确认屏幕方向正确
   - 尝试调整屏幕初始化参数

2. **数据异常**
   - 检查网络连接状态
   - 确认Docker服务已启动（如使用get_docker_count功能）
   - 查看系统日志：`journalctl -f`

3. **权限问题**
   ```bash
   # 检查i2c设备权限
   ls -l /dev/i2c-*
   # 应显示类似：crw-rw---- 1 root i2c 89, 0 7月 29 00:48 /dev/i2c-0
   ```

## 扩展功能
1. 添加自定义监控指标：
   ```python
   # 在display_info函数中添加新字段
   gpu_temp = get_gpu_temperature()  # 自定义函数
   draw.text((0, line_pos[4]), f"GPU:{gpu_temp}", font=font_small, fill=1)
   ```

2. 实现自动亮度调节：
   ```python
   from gpiozero import LightSensor
   sensor = LightSensor(18)
   
   def adjust_brightness():
       brightness = 0.5 + sensor.value * 0.5
       device.contrast(int(255 * brightness))
   ```
