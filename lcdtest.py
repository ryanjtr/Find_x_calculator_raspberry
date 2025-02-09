from RPLCD.i2c import CharLCD
import time
from gpiozero import LED, Button
import numpy as np
import subprocess # Delete this line after debugging


r0 = LED(24)
r1 = LED(23)
r2 = LED(18)

c0 = Button(25)
c1 = Button(8)
c2 = Button(7)

keypad = [["=", "x", "7"], ["4", "1", "0"], ["Shift left", "^", "8"],
          ["5", "2", "."], ["Shift right", "Del", "9"], ["6", "3", "Calculate"],
          ["Solve", "AC", "+"], ["-", "*", "/"]]

last_pressed_time = [[0, 0, 0] for _ in range(8)]


lcd = CharLCD('PCF8574', 0x27)
lcd.cursor_mode = 'line'
lcd.clear()

demo_text="777888999444555666"
display_text = ""
text_after_verifying = ""
equation = []
result_text= ""
cursor_pos = 0  
cursor_blink_pos=0
is_shift_left_pressed=0
default_x=0
is_x_exist=0


def slice_equation(display_text):
    global equation
    current = ""
    for char in display_text:
        if char in "+-*/()=^x":  
            if current:  # Thêm số đang xử lý vào danh sách
                equation.append(current)
                current = ""
            equation.append(char)  # Thêm toán tử hoặc dấu ngoặc
        elif char.isdigit() or char == '.':  # Nếu là số hoặc dấu chấm
            current += char
        elif char.isspace():  # Bỏ qua khoảng trắng
            if current:
                equation.append(current)
                current = ""
    if current:  # Thêm số cuối cùng
        equation.append(current)
    print(equation)


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

def syntax_error_display():
    global equation
    equation = [] #Reset equation
    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string("Syntax Error")
    print("Syntax Error")




#--------------------------- Shunting Yard Algorithm --------------------------#

def precedence(op):
    if op in ('+', '-'): 
        return 1
    if op in ('*', '/'): 
        return 2
    if op == '^':  # Change to '^' for exponentiation
        return 3  # Highest precedence for power
    return 0

def apply_op(a, b, op):
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    if op == '/':
        if b == 0:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            return "Math Error"
        return a / b
    if op == '^':  # Change to '^' for exponentiation
        return pow(a, b)  # Or use a ** b for exponentiation

def is_operator(token):
    return token in ['+', '-', '*', '/', '^']

def infix_to_postfix(expression):
    output = []
    stack = []
    i = 0

    while i < len(expression):
        token = expression[i]
        print(token)
        # Xử lý số âm hoặc dương khi có dấu trước số
        if token in ('+', '-') and (i == 0 or expression[i-1] in '*/(+ -'):
            num = token
            i += 1
            while i < len(expression) and (expression[i].isdigit() or expression[i] == '.'):
                num += expression[i]
                i += 1
            output.append(num)
            continue

        if token.isdigit() or token == '.':
            num = token
            while i + 1 < len(expression) and (expression[i + 1].isdigit() or expression[i + 1] == '.'):
                i += 1
                num += expression[i]
            output.append(num)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        elif is_operator(token):
            while stack and precedence(stack[-1]) >= precedence(token):
                output.append(stack.pop())
            stack.append(token)
        else:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Invalid Input")
            return []

        i += 1

    while stack:
        output.append(stack.pop())

    return output

def evaluate_postfix(postfix):
    stack = []

    for token in postfix:
        print(token)
        if token.lstrip('+-').replace('.', '', 1).isdigit():
            stack.append(float(token))
        elif is_operator(token):
            print("In is operator ")
            if len(stack) < 2:
                lcd.clear()
                lcd.cursor_pos = (0, 0)
                lcd.write_string("Syntax Error POSTFIX") #Rename to Syntax Error after code complete
                return "Error"
            b = stack.pop()
            a = stack.pop()
            
            result = apply_op(a, b, token)
            stack.append(result)
        else:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Invalid Input")
            return "Error"

    if len(stack) != 1:
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string("Syntax Error len stack") #Rename to Syntax Error after code complete
        return "Error"

    return stack[0]


#-----------------------------------------------------------------------------------#

#----------Coefficient and Function for calculating the derivative---------------#

COEFFICIENT_H = 1e-5 #10^-5

DEMO_X = 5

def derivative_calculation(x_para):
    global equation
    func_xh = equation.copy()
    func_x = equation.copy()

    func_xh = [expr.replace("x", str(x_para+COEFFICIENT_H)) for expr in func_xh]
    func_x = [expr.replace("x", str(x_para)) for expr in func_x]
    
    result = (normal_calculation(func_xh) - normal_calculation(func_x))/COEFFICIENT_H
    return result
    
#---------------------------------------------------------------------------------#

def normal_calculation(equation_para):
    print(f"equation_para= {equation_para}")
    expression = ''.join(equation_para)
    postfix = infix_to_postfix(expression)
    if postfix:
        result = evaluate_postfix(postfix)
        if result != "Error":
            return result
    

def find_x():
    result = 0
    return result


def error_checking():
    global display_text
    is_error = False
    if "*/" in display_text or "/*" in display_text or "+*" in display_text or "-*" in display_text or "+/" in display_text or "-/" in display_text or "**" in display_text or "//" in display_text:
        is_error = True
        print("loi dau")
    elif display_text.count(")") != display_text.count("("):
        is_error = True
        print("Loi thieu ngoac")
    elif "()" in display_text:
        is_error = True
        print("Loi trong ngoac khong co gi")
    elif "-)" in display_text or "+)" in display_text or "*)" in display_text or "/)" in display_text or "(*" in display_text or "(/)" in display_text:
        is_error = True
        print("Loi chi co dau trong ngoac")
    return is_error
 




def handle_button_press(row, column):
    global display_text, cursor_pos,cursor_blink_pos,is_shift_left_pressed,equation
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
        
        elif pressed_button == "Calculate":
            if "=" in display_text:
                syntax_error_display()
            elif error_checking():
                syntax_error_display()
            else:
                equation = []
                # slice_equation(display_text) # Generate equation after slicing
                if "x" in display_text:
                    temp_text = str([expr.replace("x","*0") for expr in display_text])
                    slice_equation(temp_text) # Generate equation after slicing
                    print(f"display text: {display_text}")
                    print(f"temp_text: {temp_text}")
                    print(f"equation with temp_text: {equation}")
                else: 
                    slice_equation(display_text) # Generate equation after slicing
                result = normal_calculation(equation) # Take result
                lcd.cursor_pos = (1, 0)
                lcd.write_string(f"{result}")
                print(f"{result}")
                # Thiếu xử lí nếu số ra vượt 16 kí tự: 1.152921504606847e+18, thay e+18 thành *10^18.
                # Sử dụng nút qua trái/phải để xem kết quả
            return

        elif pressed_button == "Solve":
            equation = []
            slice_equation(display_text) # Generate equation after slicing
            if "x" in display_text : #thiếu trường hợp nếu không gõ = thì mặc định tìm x với vế phải bằng 0
                # find_x()
                result = derivative_calculation(DEMO_X) # Take result
                lcd.cursor_pos = (1, 0)
                lcd.write_string(f"{result}")
                print(f"{result}")  
            else:
                print("Debugging line 315")
                syntax_error_display()
            return
 
        else:
            # Add character
            if(cursor_pos<16):
                display_text = display_text[:cursor_blink_pos] + str(pressed_button) + display_text[cursor_blink_pos:]
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

