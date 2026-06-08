# Breakbeam Counter + Countdown Timer + Servo
# --------------------------------------------
# Hardware:
#   LCD SDA         → GP0  (pin 1)
#   LCD SCL         → GP1  (pin 2)
#   LCD VCC         → 5V (VBUS pin 40 or battery)
#   LCD GND         → shared GND
#   IR Transmitter  → GP14 (pin 19)  |  VCC → VBUS 5V (pin 40)
#   IR Receiver     → GP15 (pin 20)  |  VCC → 3V3 (pin 36)
#   Servo signal    → GP16 (pin 21)  |  VCC → 5V (VBUS or battery)
#   All GND         → shared GND rail

from machine import Pin, I2C, PWM, Timer
from pico_i2c_lcd import I2cLcd
import utime

# ── CONFIGURATION ──────────────────────────────────────────
I2C_SDA_PIN     = 0
I2C_SCL_PIN     = 1
I2C_FREQ        = 100_000
LCD_I2C_ADDR    = 0x27
LCD_COLS        = 16
LCD_ROWS        = 2
TRANSMITTER_PIN = 14
RECEIVER_PIN    = 15
SERVO_PIN       = 16
COUNTDOWN_SECS  = 120
MEDIUM_SPEED    = 6800

# ── SERVO ───────────────────────────────────────────────────
servo_pwm = PWM(Pin(SERVO_PIN))
servo_pwm.freq(50)

def servo_start():
    servo_pwm.duty_u16(MEDIUM_SPEED)

def servo_stop():
    servo_pwm.duty_u16(0)

# ── IR SENSORS ──────────────────────────────────────────────
transmitter = Pin(TRANSMITTER_PIN, Pin.OUT)
transmitter.value(1)  # always on
receiver = Pin(RECEIVER_PIN, Pin.IN, Pin.PULL_UP)

# ── LCD ─────────────────────────────────────────────────────
utime.sleep(2)  # give LCD time to power up
i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
lcd = I2cLcd(i2c, LCD_I2C_ADDR, LCD_ROWS, LCD_COLS)

# ── STATE ───────────────────────────────────────────────────
count        = 0
time_left    = COUNTDOWN_SECS
game_running = True

# ── HELPERS ─────────────────────────────────────────────────
def fmt_time(secs):
    return "{:02d}:{:02d}".format(secs // 60, secs % 60)

def update_display():
    lcd.move_to(0, 0)
    lcd.putstr("Count:  {:<8}".format(count))
    lcd.move_to(0, 1)
    lcd.putstr("Time:   {}   ".format(fmt_time(time_left)))

def game_over():
    servo_stop()
    transmitter.value(0)
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("  Game Over!    ")
    lcd.move_to(0, 1)
    lcd.putstr("Score: {:<9}".format(count))

# ── TIMER CALLBACK (runs every 1 second) ────────────────────
def tick(t):
    global time_left, game_running
    if not game_running:
        return
    time_left -= 1
    update_display()
    if time_left <= 0:
        time_left = 0
        game_running = False
        countdown_timer.deinit()
        game_over()

# ── STARTUP SEQUENCE ────────────────────────────────────────
lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("  Get Ready...  ")
utime.sleep(2)
lcd.clear()
update_display()
servo_start()

countdown_timer = Timer()
countdown_timer.init(period=1000, mode=Timer.PERIODIC, callback=tick)

# ── MAIN LOOP ───────────────────────────────────────────────
beam_was_clear = True
while True:
    if not game_running:
        break
    beam_blocked = (receiver.value() == 0)  # LOW = beam broken
    if beam_blocked and beam_was_clear:
        count += 1
        update_display()
        beam_was_clear = False
    elif not beam_blocked:
        beam_was_clear = True
    utime.sleep_ms(50)
