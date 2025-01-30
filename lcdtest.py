from RPLCD.i2c import CharLCD
import time
from gpiozero import LED, Button

import subprocess # Delete this line after debugging


r0 = LED(24)
r1 = LED(23)
r2 = LED(18)

c0 = Button(25)
c1 = Button(8)
c2 = Button(7)

keypad = [["SQRT", "X", 7], [4, 1, 0], ["Shift left", "^", 8],
          [5, 2, "."], ["Shift right", "Del", 9], [6, 3, "="],
          ["Solve", "AC", "+"], ["-", "*", "/"]]

last_pressed_time = [[0, 0, 0] for _ in range(8)]


lcd = CharLCD('PCF8574', 0x27)
lcd.cursor_mode = 'line'
lcd.clear()

demo_text="777888999444555666"
display_text = ""  
cursor_pos = 0  
cursor_blink_pos=0
is_shift_left_pressed=0
virtual_cursor_blink_pos=0


def update_display():
    lcd.clear()
    if (cursor_pos<16 and len(display_text)<=16):
        lcd.write_string(display_text[:len(display_text)]) 
    else:
        if(cursor_pos>16):
            lcd.write_string(display_text[cursor_pos-16:cursor_pos])
        else:
            lcd.write_string(display_text[0:16])
    lcd.cursor_pos=(0,cursor_blink_pos)
    print("update display")


def handle_button_press(row, column):
    global display_text, cursor_pos,cursor_blink_pos,is_shift_left_pressed
    current_time = time.time() 
    if (current_time - last_pressed_time[row][column] > 0.2):  # Debounce 300ms
        last_pressed_time[row][column] = current_time
        pressed_button = keypad[row][column]
        print(f"Button pressed: {pressed_button}")

        print(f"chieu dai chuoi truoc xu li {len(display_text)}")
        print(f"vi tri cur {cursor_pos}")
        print(f"vi tri nhay truoc xu li {cursor_blink_pos}")
        if (pressed_button == "Del"): #Delete character before blinking cursor
            if (cursor_blink_pos>0 and cursor_pos <=16):
                display_text = display_text[:cursor_blink_pos-1] + display_text[cursor_blink_pos:]
                if(not is_shift_left_pressed):
                    cursor_blink_pos-=1
                else:
                    is_shift_left_pressed=0
            else:
                display_text = display_text[cursor_pos-16:cursor_pos]

        elif pressed_button == "Shift left":
            if  (cursor_blink_pos!=0 and cursor_pos <=16):
                cursor_blink_pos-=1
                lcd.cursor_pos=(0,cursor_blink_pos)
                is_shift_left_pressed=1
                cursor_pos-=1
                print(f"{display_text}")
                return
            else:
                cursor_pos-=1
                
                

        elif pressed_button == "Shift right":
                if(cursor_blink_pos<15 and cursor_blink_pos<cursor_pos):
                    cursor_blink_pos+=1
                    lcd.cursor_blink_pos=(0,cursor_blink_pos)
                cursor_pos+=1

        elif pressed_button == "AC":
            display_text = ""
            cursor_pos = 0
            cursor_blink_pos=0
            subprocess.run('clear', shell=True) # Delete this line after debugging

        else:
            # Add character
            if(cursor_pos<16):
                display_text = display_text[:cursor_blink_pos] + str(pressed_button) + display_text[cursor_blink_pos:]
                # display_text = display_text[:cursor_pos] + str(pressed_button)
            else:
                display_text = display_text[:cursor_pos] + str(pressed_button)+ display_text[cursor_pos:]

            cursor_pos += 1
            if(cursor_blink_pos<15):
                cursor_blink_pos+=1

        # Đảm bảo con trỏ không vượt quá văn bản
        cursor_pos = min(cursor_pos, len(display_text))
        
        # Update LCD display
        update_display()
        print(f"{display_text}")
        print(f"chieu dai chuoi sau xu li {len(display_text)}")
        print(f"vi tri con tro sau xu li {cursor_pos}")
        print(f"vi tri nhay sau xu li {cursor_blink_pos}")


def scan_keypad():
    for row in range(8):
        
        r0.value = (row >> 0) & 1
        r1.value = (row >> 1) & 1
        r2.value = (row >> 2) & 1

        time.sleep(0.01)  

        # Check column
        if c0.is_pressed:
            handle_button_press(row, 0)
        if c1.is_pressed:
            handle_button_press(row, 1)
        if c2.is_pressed:
            handle_button_press(row, 2)

# lcd.write_string(f"{demo_text[:5]}")
while True:
    scan_keypad()

