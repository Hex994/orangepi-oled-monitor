# orangepi-oled-monitor
Orange Pi OLED 系统监控程序安装教程
一、硬件准备
​OLED 屏幕​：128x64 或 128x32 的 SSD1306 OLED 屏幕
​连接方式​：
SDA → Orange Pi SDA 引脚（GPIO2）
SCL → Orange Pi SCL 引脚（GPIO3）
VCC → 3.3V 电源
GND → GND
二、系统要求
​操作系统​：Armbian / Ubuntu 20.04+ / Debian 11+
​支持的设备​：Orange Pi 全系列 (Zero/Rock/Prime 等)
三、安装步骤

# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 启用I2C接口
sudo armbian-config
# 选择 System → Hardware → 启用 i2c0
# 或手动添加: 
# echo "dtparam=i2c_arm=on" | sudo tee -a /boot/armbianEnv.txt
sudo reboot

# 3. 安装系统依赖
sudo apt install -y python3-pip python3-dev i2c-tools libopenjp2-7 libtiff5

# 4. 安装Python库
sudo pip3 install psutil pillow luma.oled

# 5. 安装字体
sudo apt install -y fonts-dejavu

# 6. 克隆代码库
git clone https://github.com/Hex994/orangepi-oled-monitor.git
cd orangepi-oled-monitor

四、首次运行配置

# 1. 检查I2C设备是否识别
sudo i2cdetect -y 0  # 应显示3C地址

# 2. 修复I2C权限（每次重启后需执行）
sudo chmod 666 /dev/i2c-0

# 3. 启动程序
python3 oled_monitor.py

五、设置开机自启（可选）

# 1. 创建服务文件
sudo nano /etc/systemd/system/oled-monitor.service

# 2. 添加以下内容
[Unit]
Description=OLED System Monitor
After=network.target

[Service]
User=orangepi
WorkingDirectory=/home/orangepi/orangepi-oled-monitor
ExecStart=/usr/bin/python3 /home/orangepi/orangepi-oled-monitor/oled_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target

# 3. 启用服务
sudo systemctl daemon-reload
sudo systemctl enable oled-monitor.service
sudo systemctl start oled-monitor.service

六、功能说明
程序启动后：

​显示模式​：每30秒自动切换
​系统信息屏​：IP地址/CPU温度/内存/网络速度
​磁盘信息屏​：磁盘用量/运行时间/Docker容器数
​自动节电​：23:00-7:00 自动关闭屏幕
​开机动画​：启动时显示"OrangePi"粒子动画

七、常见问题解决

# 1. I2C权限问题
sudo usermod -aG i2c orangepi

# 2. 缺少luma.oled库
sudo pip3 install --upgrade luma.oled

# 3. 屏幕不显示
# 检查接线是否正确，尝试更换I2C地址(0x3C或0x3D)
nano oled_monitor.py
# 修改 init_oled() 中的 address=0x3C

# 4. 低分辨率屏幕支持
# 修改 SCREEN_HEIGHT = 32
nano oled_monitor.py

八、自定义选项

# 在代码中修改以下变量：
SCREEN_HEIGHT = 64  # 屏幕高度(32/64)
SWITCH_INTERVAL = 30  # 屏幕切换间隔(秒)
