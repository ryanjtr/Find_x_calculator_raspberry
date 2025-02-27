import time
import random
import smbus2  # Thư viện giao tiếp I2C
from RPLCD.i2c import CharLCD

# Khởi tạo LCD I2C (địa chỉ LCD có thể khác)
lcd = CharLCD('PCF8574', 0x27)  # Thay bằng địa chỉ thực tế của bạn

# Danh sách ký tự ngẫu nhiên mô phỏng hiệu ứng Matrix
matrix_chars = ['0', '1', '!', '@', '#', '$', '%', '&', '*', ' ']

def matrix_animation():
    lcd.clear()
    cols = 16  # Đổi thành 20 nếu dùng LCD 20x4
    rows = 2   # Đổi thành 4 nếu dùng LCD 20x4

    while True:
        for r in range(rows):
            random_chars = ''.join(random.choice(matrix_chars) for _ in range(cols))
            lcd.cursor_pos = (r, 0)
            lcd.write_string(random_chars)

        time.sleep(0.2)  # Điều chỉnh tốc độ hiệu ứng

try:
    matrix_animation()
except KeyboardInterrupt:
    lcd.clear()
    lcd.write_string("Goodbye!")
