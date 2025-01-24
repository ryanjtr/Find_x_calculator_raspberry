from RPLCD.i2c import CharLCD
import time
from gpiozero import LED, Button

# Khởi tạo các chân điều khiển LED và nút bấm
r0 = LED(22)
r1 = LED(27)
r2 = LED(17)

c0 = Button(10)
c1 = Button(9)
c2 = Button(11)

# Các nút trên bàn phím ma trận
keypad = [["SQRT", "X", 7], [4, 1, 0], ["Shift left", "^", 8],
          [5, 2, "."], ["Shift right", "Del", 9], [6, 3, "="],
          ["Solve", "AC", "+"], ["-", "*", "/"]]

last_pressed = [0, 0, 0]  # Thời gian lần cuối các nút được nhấn (theo cột)

# Khởi tạo LCD với địa chỉ I2C và kích thước màn hình (16x2)
lcd = CharLCD('PCF8574', 0x27)
lcd.clear()

# Dùng một biến toàn cục để theo dõi văn bản hiển thị trên LCD
display_text = ""  # Chuỗi lưu trữ nội dung đang hiển thị
cursor_pos = 0  # Vị trí con trỏ hiển thị trên màn hình


# Hàm cập nhật màn hình LCD
def update_display():
    lcd.clear()
    # Hiển thị tối đa 16 ký tự từ vị trí con trỏ
    lcd.write_string(display_text[:16])

# Hàm xử lý nhấn nút
def handle_button_press(column_index):
    global display_text
    global cursor_pos
    global current_row
    current_time = time.time()

    if current_time - last_pressed[column_index] > 0.3:  # Debounce 300ms
        last_pressed[column_index] = current_time
        pressed_button = keypad[current_row][column_index]
        print(f"Button pressed: {pressed_button}")

        if pressed_button == "Del":
            # Xóa ký tự tại vị trí con trỏ
            if cursor_pos < len(display_text):
                display_text = display_text[:cursor_pos] + display_text[cursor_pos + 1:]
        elif pressed_button == "Shift left":
            # Di chuyển con trỏ sang trái
            cursor_pos = max(cursor_pos - 1, 0)
        elif pressed_button == "Shift right":
            # Di chuyển con trỏ sang phải
            cursor_pos = min(cursor_pos + 1, len(display_text))
        elif pressed_button == "AC":
            # Xóa toàn bộ văn bản và đặt con trỏ về đầu
            display_text = ""
            cursor_pos = 0
        else:
            # Thêm ký tự vào chuỗi hiển thị tại vị trí con trỏ
            if len(display_text) < 16:  # Giới hạn số ký tự hiển thị
                display_text = display_text[:cursor_pos] + str(pressed_button) + display_text[cursor_pos:]
                cursor_pos += 1

        # Cập nhật nội dung hiển thị
        update_display()

# Hàm quét hàng
def scan_row(row_count):
    r0.value = (row_count >> 0) & 1
    r1.value = (row_count >> 1) & 1
    r2.value = (row_count >> 2) & 1

# Gán sự kiện nhấn nút
c0.when_pressed = lambda: handle_button_press(0)
c1.when_pressed = lambda: handle_button_press(1)
c2.when_pressed = lambda: handle_button_press(2)

# Chương trình chính
while True:
    for current_row in range(0, 8):
        scan_row(current_row)
        time.sleep(0.02)
