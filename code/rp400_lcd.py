import subprocess
import time
import spidev
import keyboard
import numpy as np
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

# ピン設定
DC_PIN = 25   # 物理22番
RST_PIN = 27  # 物理13番

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(DC_PIN, GPIO.OUT)
GPIO.setup(RST_PIN, GPIO.OUT)

# SPI初期化 (32MHz)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 32000000
spi.mode = 0b00

def send_cmd(cmd):
    GPIO.output(DC_PIN, GPIO.LOW)
    spi.xfer2([cmd])

def send_data(data):
    GPIO.output(DC_PIN, GPIO.HIGH)
    if isinstance(data, int):
        spi.xfer2([data])
    else:
        for i in range(0, len(data), 4096):
            spi.xfer2(list(data[i:i+4096]))

# リセット & 初期化
GPIO.output(RST_PIN, GPIO.HIGH); time.sleep(0.05)
GPIO.output(RST_PIN, GPIO.LOW);  time.sleep(0.05)
GPIO.output(RST_PIN, GPIO.HIGH); time.sleep(0.05)

send_cmd(0x01); time.sleep(0.15) # SWRESET
send_cmd(0x11); time.sleep(0.15) # SLPOUT
send_cmd(0x3A); send_data(0x05) # COLMOD
send_cmd(0x36); send_data(0x00) # MADCTL
send_cmd(0x21)                 # INVON
send_cmd(0x29); time.sleep(0.1)  # DISPON

send_cmd(0x2A); send_data([0x00, 0x00, 0x00, 0xEF])
send_cmd(0x2B); send_data([0x00, 0x00, 0x00, 0xEF])

# ターミナル管理変数
lines = ["RPi400 Linux Shell", "Type command and press Enter", "> "]
current_input = ""
font = ImageFont.load_default()

def render():
    img = Image.new("RGB", (240, 240), (0, 0, 0))
    draw = ImageDraw.Draw(img)
   
    # 緑の枠線
    draw.rectangle((1, 1, 238, 238), outline=(0, 255, 0), width=1)
   
    # 画面に入る直近の15行だけを描画
    display_lines = lines[-15:]
    y = 8
    for line in display_lines:
        draw.text((8, y), line[:35], fill=(0, 255, 100), font=font)
        y += 15

    # 高速転送
    img_np = np.array(img, dtype=np.uint16)
    r = (img_np[:, :, 0] & 0xF8) << 8
    g = (img_np[:, :, 1] & 0xFC) << 3
    b = img_np[:, :, 2] >> 3
    buf = (r | g | b).astype('>u2').tobytes()
    send_cmd(0x2C)
    send_data(buf)

def execute_cmd(cmd_str):
    global lines
    if not cmd_str.strip():
        lines.append("> ")
        return

    try:
        # コマンドを実行して標準出力を取得
        res = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=5)
        output = res.stdout if res.stdout else res.stderr
        if not output:
            output = "[OK]"
       
        # 改行で分割して描画行に追加
        for l in output.strip().split('\n'):
            lines.append(l)
    except Exception as e:
        lines.append(f"Error: {e}")
   
    lines.append("> ")

render()

def on_key(e):
    global lines, current_input
    if e.event_type != keyboard.KEY_DOWN:
        return

    if e.name == 'enter':
        cmd_to_run = current_input
        current_input = ""
        execute_cmd(cmd_to_run)
    elif e.name == 'backspace':
        if len(current_input) > 0:
            current_input = current_input[:-1]
            lines[-1] = "> " + current_input
    elif e.name == 'space':
        current_input += " "
        lines[-1] = "> " + current_input
    elif len(e.name) == 1:
        current_input += e.name
        lines[-1] = "> " + current_input

    render()

keyboard.hook(on_key)

try:
    keyboard.wait('ctrl+c')
finally:
    GPIO.cleanup()
