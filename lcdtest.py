from RPLCD.i2c import CharLCD
import time

from gpiozero import LED,Button

# initialize row and column
r0 = LED(22)
r1=LED(27)
r2=LED(17)

c0=Button(10)
c1=Button(9)
c2=Button(11)

current_row = 0

keypad = [["SQRT","X",7],[4,1,0],["Shift left","^",8],
[5,2,"."],["Shift right","Del",9],[6,3,"="],["Solve","AC","+"],["-","*","/"]]

last_pressed = [0, 0, 0]  # Thời gian lần cuối các nút được nhấn (theo cột)
#--------------------------------

def handle_button_press(column_index):
    global last_pressed
    global is_press
    current_time = time.time()  # Lấy thời gian hiện tại
    if current_time - last_pressed[column_index] > 0.3:  # Debounce 300ms
        last_pressed[column_index] = current_time
        print(f"button is: {keypad[current_row][column_index]}")



def scan_row(row_count):
	r0.value = (row_count>>0)&1
	r1.value = (row_count>>1)&1
	r2.value = (row_count>>2)&1

c0.when_pressed = lambda: handle_button_press(0)
c1.when_pressed = lambda: handle_button_press(1)
c2.when_pressed = lambda: handle_button_press(2)


# Khởi tạo LCD với địa chỉ I2C và kích thước màn hình (16x2)
lcd = CharLCD('PCF8574', 0x27)

# Xóa màn hình
lcd.clear()

# Hiển thị thông điệp khác
lcd.clear()
lcd.write_string("Starting check keypad")

while(1):
	
	for current_row in range (0,8):
		scan_row(current_row)
		time.sleep(0.01)