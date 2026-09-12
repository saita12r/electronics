from machine import Pin, PWM
import time

# ピンの設定（GP15:スピーカー, GP16:ボタン1, GP17:ボタン2）
speaker = PWM(Pin(15))
btn1 = Pin(16, Pin.IN, Pin.PULL_DOWN)
btn2 = Pin(17, Pin.IN, Pin.PULL_DOWN)

HIGH_RE = 587  # 高いレの音

# 指定した秒数だけ音を鳴らす命令（関数）
def play_sound(duration):
    speaker.freq(HIGH_RE)
    speaker.duty_u16(32768)  # 音を出す
    time.sleep(duration)     # 指定した時間待つ
    speaker.duty_u16(0)      # 音を止める

while True:
    if btn1.value() == 1:
        play_sound(0.3)  # ボタン1で0.3秒鳴らす
    elif btn2.value() == 1:
        play_sound(0.7)  # ボタン2で0.7秒鳴らす
   
    time.sleep(0.05)
