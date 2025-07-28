import time
import socket
import psutil
import os
import subprocess
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

# 屏幕尺寸
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64  # 如果是32像素高的屏幕，请改为32

# 修复 I2C 设备权限
def fix_i2c_permissions():
    try:
        os.system('sudo chmod 666 /dev/i2c-0')
    except:
        pass

# 初始化 OLED 屏幕
def init_oled():
    try:
        fix_i2c_permissions()
        serial = i2c(port=0, address=0x3C)
        device = ssd1306(serial, width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        print("OLED screen initialized")
        return device
    except Exception as e:
        print(f"OLED init failed: {e}")
        return None

# 创建字体对象
def create_fonts():
    try:
        # 使用更小的字体以容纳更多内容
        font_tiny = ImageFont.truetype("DejaVuSans.ttf", 10)  # 新增超小字体
        font_small = ImageFont.truetype("DejaVuSans.ttf", 12)
        font_medium = ImageFont.truetype("DejaVuSans.ttf", 14)
        font_large = ImageFont.truetype("DejaVuSans.ttf", 22)
        return font_tiny, font_small, font_medium, font_large  # 返回四个字体对象
    except:
        # 使用默认字体
        print("Using default font")
        font = ImageFont.load_default()
        return font, font, font, font  # 返回四个相同的默认字体

# 获取文本宽度
def get_text_width(font, text):
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
    except AttributeError:
        return font.getsize(text)[0]

# 创建 WiFi 信号格图标
def create_wifi_icon(strength=3):
    icon = Image.new('1', (20, 12), 0)
    draw = ImageDraw.Draw(icon)
    if strength >= 1:
        draw.rectangle((15, 9, 18, 11), fill=1)
    if strength >= 2:
        draw.rectangle((10, 6, 13, 11), fill=1)
    if strength >= 3:
        draw.rectangle((5, 3, 8, 11), fill=1)
    if strength >= 4:
        draw.rectangle((0, 0, 3, 11), fill=1)
    return icon

# 粒子动画函数
def particle_animation(device, font_large, duration=4):
    print("Playing particle animation...")
    start_time = time.time()
    
    # 目标文字设置
    target_text = "OrangePi"
    text_bbox = font_large.getbbox(target_text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (device.width - text_width) // 2
    text_y = (device.height - text_height) // 2

    # 预生成文字掩模
    text_mask = Image.new("1", (text_width, text_height))
    ImageDraw.Draw(text_mask).text((0, 0), target_text, font=font_large, fill=1)
    
    # 粒子类
    class Particle:
        def __init__(self):
            edge = random.choice(["top", "bottom", "left", "right"])
            if edge in ["top", "bottom"]:
                self.x = random.randint(0, device.width)
                self.y = 0 if edge == "top" else device.height
            else:
                self.x = 0 if edge == "left" else device.width
                self.y = random.randint(0, device.height)
            
            self.target_x = text_x + random.randint(0, text_width)
            self.target_y = text_y + random.randint(0, text_height)
            self.speed = random.uniform(2.0, 4.0)
            self.size = 1

    particles = [Particle() for _ in range(100)]
    
    while time.time() - start_time < duration:
        progress = min(1.0, (time.time() - start_time) / duration)
        
        # 创建帧图像
        frame = Image.new("1", (device.width, device.height))
        draw = ImageDraw.Draw(frame)

        # 绘制粒子
        for p in particles:
            t = min(1.0, progress * 2)
            current_x = p.x + (p.target_x - p.x) * t
            current_y = p.y + (p.target_y - p.y) * t
            draw.point((int(current_x), int(current_y)), fill=1)

        # 显示文字
        if progress > 0.7:
            draw.bitmap((text_x, text_y), text_mask, fill=1)
        
        device.display(frame)
        time.sleep(0.02)
    
    # 最终显示
    frame = Image.new("1", (device.width, device.height))
    ImageDraw.Draw(frame).bitmap((text_x, text_y), text_mask, fill=1)
    device.display(frame)
    time.sleep(0.5)

# 计算每行位置（缓存结果）
def calculate_line_positions():
    if not hasattr(calculate_line_positions, 'positions'):
        line_count = 4
        total_height = SCREEN_HEIGHT
        line_height = total_height // line_count
        calculate_line_positions.positions = [i * line_height + (line_height // 4) for i in range(line_count)]
    return calculate_line_positions.positions

# 获取系统信息函数（优化缓存）
def get_cpu_temp():
    if not hasattr(get_cpu_temp, 'last_value') or time.time() - get_cpu_temp.last_time > 2:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
            get_cpu_temp.last_value = f"{temp:.1f}°C"
        except:
            get_cpu_temp.last_value = "N/A"
        get_cpu_temp.last_time = time.time()
    return get_cpu_temp.last_value

def get_cpu_usage():
    if not hasattr(get_cpu_usage, 'last_value') or time.time() - get_cpu_usage.last_time > 1:
        try:
            get_cpu_usage.last_value = f"{psutil.cpu_percent(interval=0.1)}%"
        except:
            get_cpu_usage.last_value = "N/A"
        get_cpu_usage.last_time = time.time()
    return get_cpu_usage.last_value

def get_ip_address():
    if not hasattr(get_ip_address, 'last_value') or time.time() - get_ip_address.last_time > 30:
        try:
            result = subprocess.run(['ip', '-4', 'addr', 'show', 'wlan0'], 
                                   capture_output=True, text=True)
            if "inet" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "inet" in line:
                        get_ip_address.last_value = line.split()[1].split('/')[0]
                        break
            else:
                result = subprocess.run(['ip', '-4', 'addr', 'show', 'eth0'], 
                                       capture_output=True, text=True)
                if "inet" in result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "inet" in line:
                            get_ip_address.last_value = line.split()[1].split('/')[0]
                            break
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    get_ip_address.last_value = s.getsockname()[0]
                    s.close()
        except:
            get_ip_address.last_value = "No IP"
        get_ip_address.last_time = time.time()
    return get_ip_address.last_value

def get_memory_info():
    if not hasattr(get_memory_info, 'last_value') or time.time() - get_memory_info.last_time > 2:
        try:
            mem = psutil.virtual_memory()
            used = mem.used // 1024 // 1024
            total = mem.total // 1024 // 1024
            get_memory_info.last_value = f"{used}M/{total}M"
        except:
            get_memory_info.last_value = "N/A"
        get_memory_info.last_time = time.time()
    return get_memory_info.last_value

def get_network_speed(last_net_io, last_time):
    try:
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        time_diff = max(current_time - last_time, 0.1)  # 确保时间间隔不小于0.1秒
        
        # 直接计算Kbps值
        up_kbps = (current_net_io.bytes_sent - last_net_io.bytes_sent) / time_diff * 8 / 1024
        down_kbps = (current_net_io.bytes_recv - last_net_io.bytes_recv) / time_diff * 8 / 1024

        # 格式化为字符串
        if up_kbps >= 1000:
            up_display = f"{up_kbps/1000:.1f}M"  # 简化单位显示
        else:
            up_display = f"{up_kbps:.1f}K"

        if down_kbps >= 1000:
            down_display = f"{down_kbps/1000:.1f}M"  # 简化单位显示
        else:
            down_display = f"{down_kbps:.1f}K"

        return up_display, down_display, current_net_io, current_time

    except Exception as e:
        print(f"Error in get_network_speed: {e}")
        return "N/A", "N/A", psutil.net_io_counters(), time.time()

# 获取磁盘使用率
def get_disk_info():
    if not hasattr(get_disk_info, 'last_value') or time.time() - get_disk_info.last_time > 10:
        try:
            disk = psutil.disk_usage('/')
            used_gb = round(disk.used / (1024**3), 1) 
            total_gb = round(disk.total / (1024**3), 1)  
            percent = disk.percent
            get_disk_info.last_value = (f"{used_gb}G/{total_gb}G", f"{percent}%")
        except:
            get_disk_info.last_value = ("N/A", "N/A")
        get_disk_info.last_time = time.time()
    return get_disk_info.last_value

def is_active_time():
    if not hasattr(is_active_time, 'last_check') or time.time() - is_active_time.last_check > 60:
        now = datetime.now()
        hour = now.hour
        is_active_time.last_value = 7 <= hour < 23
        is_active_time.last_check = time.time()
    return is_active_time.last_value

# 优化显示函数，减少重复创建对象
def display_info(device, font_tiny, font_small, font_medium, wifi_icon, 
                last_net_io, last_time, display_on):
    # 获取信息
    cpu_usage = get_cpu_usage()
    cpu_temp = get_cpu_temp()
    ip_addr = get_ip_address()
    mem_info = get_memory_info()
    up_speed_str, down_speed_str, new_net_io, new_time = get_network_speed(last_net_io, last_time)
    
    if display_on:
        # 创建图像
        image = Image.new("1", (device.width, device.height))
        draw = ImageDraw.Draw(image)
        line_pos = calculate_line_positions()
        
        # 第一行: IP + WiFi (使用小字体)
        draw.bitmap((0, line_pos[0]), wifi_icon, fill=1)
        ip_text = f"{ip_addr}"[:15] + "..." if len(ip_addr) > 15 else ip_addr
        draw.text((22, line_pos[0]), ip_text, font=font_small, fill=1)
        
        # 第二行: CPU使用率 + 温度 (使用小字体)
        cpu_text = f"CPU:{cpu_usage}"
        temp_text = f"{cpu_temp}"
        draw.text((0, line_pos[1]), cpu_text, font=font_small, fill=1)
        draw.text((device.width - get_text_width(font_small, temp_text), line_pos[1]), 
                  temp_text, font=font_small, fill=1)
        
        # 第三行: 上传 + 下载 (使用超小字体)
        up_text = f"UP:{up_speed_str}"
        down_text = f"DL:{down_speed_str}"
        
        # 计算位置，确保不重叠
        up_width = get_text_width(font_tiny, up_text)
        down_width = get_text_width(font_tiny, down_text)
        gap = 5  # 中间留空5像素
        
        # 如果总宽度超过屏幕宽度，调整位置
        if up_width + down_width + gap > device.width:
            # 缩小字体大小或调整位置
            up_x = 0
            down_x = device.width - down_width
        else:
            # 居中显示
            total_width = up_width + gap + down_width
            start_x = (device.width - total_width) // 2
            up_x = start_x
            down_x = start_x + up_width + gap
        
        draw.text((up_x, line_pos[2]), up_text, font=font_tiny, fill=1)
        draw.text((down_x, line_pos[2]), down_text, font=font_tiny, fill=1)
        
        # 第四行: 内存 (使用小字体)
        draw.text((0, line_pos[3]), f"Mem:{mem_info}", font=font_small, fill=1)
        
        # 显示图像
        device.display(image)
    else:
        device.clear()
    
    return new_net_io, new_time

# 获取系统运行时间
def get_uptime():
    """获取系统运行时间"""
    if not hasattr(get_uptime, 'last_value') or time.time() - get_uptime.last_time > 10:
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                get_uptime.last_value = "{}d {}h {}m".format(days, hours, minutes)
        except:
            get_uptime.last_value = "N/A"
        get_uptime.last_time = time.time()
    return get_uptime.last_value

# 获取5分钟平均负载
def get_load_avg():
    """获取5分钟平均负载"""
    if not hasattr(get_load_avg, 'last_value') or time.time() - get_load_avg.last_time > 10:
        try:
            get_load_avg.last_value = "{:.2f}".format(os.getloadavg()[1])
        except:
            get_load_avg.last_value = "N/A"
        get_load_avg.last_time = time.time()
    return get_load_avg.last_value

# 获取运行的Docker容器数量
def get_docker_count():
    """获取运行的Docker容器数量"""
    if not hasattr(get_docker_count, 'last_value') or time.time() - get_docker_count.last_time > 10:
        try:
            result = subprocess.run(['docker', 'ps', '-q'], capture_output=True, text=True)
            count = len(result.stdout.splitlines())
            get_docker_count.last_value = str(count)
        except:
            get_docker_count.last_value = "N/A"
        get_docker_count.last_time = time.time()
    return get_docker_count.last_value

# 显示磁盘信息
def display_disk_info(device, font_small, font_medium, wifi_icon, display_on):
    """显示系统信息屏幕"""
    if display_on:
        # 获取信息
        disk_usage, disk_percent = get_disk_info()
        uptime = get_uptime()
        load_avg = get_load_avg()
        docker_count = get_docker_count()
        
        # 创建图像
        image = Image.new("1", (device.width, device.height))
        draw = ImageDraw.Draw(image)
        line_pos = calculate_line_positions()
        
        # 第一行: 运行时间
        draw.text((0, line_pos[0]), f"Run:{uptime}", font=font_small, fill=1)
        
        # 第二行: 5分钟系统平均负载
        draw.text((0, line_pos[1]), f"Load:{load_avg}", font=font_small, fill=1)
        
        # 第三行: 磁盘使用量
        draw.text((0, line_pos[2]), f"Disk:{disk_usage}", font=font_small, fill=1)
        
        # 第四行: Docker容器计数
        draw.text((0, line_pos[3]), f"Docker:{docker_count}", font=font_small, fill=1)
        
        # 显示图像
        device.display(image)
    else:
        device.clear()

def main():
    print("OLED system monitor starting...")
    device = init_oled()
    if device is None:
        print("Failed to initialize OLED, exiting")
        return
    
    # 获取四个字体对象
    font_tiny, font_small, font_medium, font_large = create_fonts()
    wifi_icon = create_wifi_icon(strength=3)
    
    # 播放动画（仅限64像素高屏幕）
    if SCREEN_HEIGHT >= 64:
        particle_animation(device, font_large, duration=4)
    
    last_net_io = psutil.net_io_counters()
    last_time = time.time()
    display_on = True
    
    # 屏幕切换相关变量
    screen_mode = "info"  # 初始显示系统信息
    last_switch_time = time.time()
    switch_interval = 30  # 30秒切换一次
    
    # 预计算行位置
    line_positions = calculate_line_positions()
    
    try:
        while True:
            current_display_on = is_active_time()
            if current_display_on != display_on:
                display_on = current_display_on
                print(f"Screen {'ON' if display_on else 'OFF'}")
            
            # 检查是否需要切换屏幕
            current_time = time.time()
            if current_time - last_switch_time >= switch_interval:
                # 切换屏幕模式
                screen_mode = "disk" if screen_mode == "info" else "info"
                last_switch_time = current_time
                print(f"Switching to {screen_mode} screen")
            
            # 根据当前模式显示相应内容
            if screen_mode == "info":
                last_net_io, last_time = display_info(
                    device, font_tiny, font_small, font_medium, wifi_icon,
                    last_net_io, last_time, display_on
                )
            else:  # disk 模式
                display_disk_info(
                    device, font_small, font_medium, wifi_icon, display_on
                )
            
            time.sleep(0.5)  # 减少睡眠时间，提高响应速度
    except KeyboardInterrupt:
        print("\nProgram stopped")
    finally:
        device.clear()
        print("OLED screen cleared")

if __name__ == "__main__":
    main()