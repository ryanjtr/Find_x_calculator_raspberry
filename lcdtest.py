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
c3 = Button(1)

keypad = [["=", "x", 7,"("], ["Shift right", "Del", 9,"Return"], ["Shift left", "^", 8,")"],
          ["Solve", "AC", "+","null"], [4, "1", 0], [5, 2, "."],
          [6, 3, "Calculate"], ["-", "*", "/"]]

last_pressed_time = [[0, 0, 0,0] for _ in range(8)]


lcd = CharLCD('PCF8574', 0x27)
lcd.cursor_mode = 'line'
lcd.clear()

display_text = "2.5x^6.3-4.1x^3.2+8.7"
equation = []
cursor_pos = 0  
cursor_blink_pos=0
is_shift_left_pressed=0
initial_x= '0.5'
is_in_solving = False
is_x_enter = False
cursor_pos_line_2 = 0
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
    if is_x_enter:
        lcd.cursor_pos = (1,0)
        lcd.write_string("x="+initial_x[:cursor_pos_line_2])
    print(f"update display: {display_text}")

def syntax_error_display():
    global equation
    equation = [] #Reset equation
    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string("Syntax ERROR")
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
        try:
            return pow(a, b)  # Or use a ** b for exponentiation
        except:
            return "MATH ERROR"

def is_operator(token):
    return token in ['+', '-', '*', '/', '^']

def infix_to_postfix(expression):
    output = []
    stack = []
    i = 0

    while i < len(expression):
        token = expression[i]
        # Xử lý số âm hoặc dương khi có dấu trước số
        print(token)
        if token in ('+', '-') and (i == 0 or expression[i-1] in '*/(+ -^'):
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
        elif token == 'j':
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Complex number")
            return "Error"
        else:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Invalid Input")
            return "Error"

        i += 1

    while stack:
        output.append(stack.pop())

    return output

def evaluate_postfix(postfix):
    stack = []

    for token in postfix:
        if token.lstrip('+-').replace('.', '', 1).isdigit():
            stack.append(float(token))
        elif is_operator(token):
            if len(stack) < 2:
                lcd.clear()
                lcd.cursor_pos = (0, 0)
                lcd.write_string("Syntax Error POSTFIX") #Rename to Syntax Error after code complete
                print("len stack < 2")
                return "Error"
            b = stack.pop()
            a = stack.pop()
            
            result = apply_op(a, b, token)
            # print(f"result line 172: {result}")
            if result == "MATH ERROR":
                print("MATh error in evaluate postfix")
                return "Error"
            else:
                stack.append(result)
        else:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Invalid Input")
            print("invalid input")
            return "Error"

    if len(stack) != 1:
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string("Syntax Error len stack") #Rename to Syntax Error after code complete
        print("Syntax Error len stack")
        return "Error"
    return stack[0]


#-----------------------------------------------------------------------------------#

#----------Function for calculating the derivative---------------#

DEMO_X = 0

def derivative_calculation(x_para):
    global equation
    func_xh = equation.copy()
    func_x = equation.copy()
    cofficient_h=1e-2
    func_xh = [expr.replace("x", str(x_para+cofficient_h)) for expr in func_xh]
    func_x = [expr.replace("x", str(x_para-cofficient_h)) for expr in func_x]
    # print(f"func_x: {func_x}")
    # print(f"ket qua phep tinh func_xh: {normal_calculation(func_xh)} ")
    # print(f"ket qua phep tinh func_x: {normal_calculation(func_x)} ")

    # result_xh = normal_calculation(func_xh)
    # print("tinh toan func_xh---------")
    cofficient_not_ok=True
    while(cofficient_not_ok):
        result_xh = normal_calculation(func_xh)
        if(result_xh == None):
            cofficient_h = cofficient_h / 10
        else:
            cofficient_not_ok=False
    # print("tinh toan func_x ---------")
    result_x = normal_calculation(func_x)
    if result_xh == "Error" or result_x == "Error":
        result = "MATH ERROR"
    else:
        result = ( result_xh - result_x)/(2*cofficient_h)
    return result
    
#---------------------------------------------------------------------------------#

def check_x_syntax(expression_text,is_finding_x):
    if "x" in expression_text:
        expression_text = list(expression_text) #convert string to list
        for i in range(0,len(expression_text)):                      
            if expression_text[i]== 'x':
                if i >= 0 and i != len(expression_text)-1 and expression_text[i+1].isdigit():
                        syntax_error_display()
                        return "Syntax Error"
                elif i > 0:
                    if expression_text[i-1].isdigit(): # Ex: 2x+3
                            if is_finding_x:
                                expression_text[i] = "*x"
                            else:
                                expression_text[i] = '*' + str(initial_x)
                    elif expression_text[i-1] == '+':
                        expression_text[i] = str(initial_x) 
                    elif expression_text[i-1] == '-':
                        expression_text[i] = str(initial_x) 
                else:
                    if not is_finding_x:
                        expression_text[i] = str(initial_x)
    expression_text = ''.join(expression_text) #convert list to string
    return expression_text

def normal_calculation(equation_para):
    # print(f"equation_para= {equation_para}")
    expression = ''.join(equation_para)
    postfix = infix_to_postfix(expression)
    if postfix != "Error":
        result = evaluate_postfix(postfix)
        if result != "Error":
            if result == 0.0: # eliminate negative -0.0
                result = 0.0
        return result
    else:
        return postfix

        
    
count_repeat=0
def find_x(x_para):
    start = time.perf_counter()  # Lấy thời gian bắt đầu
    global count_repeat
    SO_LAN_LAP=10000
    for lanlap in range(SO_LAN_LAP):
        count_repeat+=1
        func_x_nor = [expr.replace("x", str(x_para)) for expr in equation]
        # print(f"func nor= {func_x_nor}")
        result_func_x_nor = normal_calculation(func_x_nor)
        if result_func_x_nor == "Error":
            # print("func nor error")
            return "MATH Error"
        # print(f"ket qua tinh nor= {result_func_x_nor} -------------------------")

        result_func_x_deri = derivative_calculation(x_para)
        if result_func_x_deri == "MATH Error" or abs(result_func_x_deri) < 1e-9:
            # print("func deri error")
            return "MATH Error"

        result = x_para - (result_func_x_nor/result_func_x_deri)
        # print(f"sai so nghiem trc va sau: {abs(result-x_para)}")
        if(abs(result-x_para)<1e-5):
            func_x_nor = [expr.replace("x", str(result)) for expr in equation]
            left_side = normal_calculation(func_x_nor)
            if(left_side=="Error"):
                return "Cannot Solve" 
            
            if(abs(left_side)<1e-15 or (result-x_para==0)):
                end = time.perf_counter()  # Lấy thời gian kết thúc
                print(f"left side= {left_side}")
                print(f"ket qua co the dung:{result}")
                print(f"Thời gian thực thi: {end - start:.6f} giây")
                return result  
            else:
                if(lanlap==SO_LAN_LAP):
                    return "Cannot Solve"          
        x_para=result
    return "Cannot Solve"

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
    global initial_x,is_x_enter,cursor_pos_line_2
    current_time = time.time() 
    if (current_time - last_pressed_time[row][column] > 0.2):  # Debounce 300ms
        last_pressed_time[row][column] = current_time
        pressed_button = keypad[row][column]
        # print(f"Button pressed: {pressed_button}")
        # print(f"chieu dai chuoi truoc xu li {len(display_text)}")
        # print(f"vi tri cur {cursor_pos}")
        # print(f"vi tri nhay truoc xu li {cursor_blink_pos}")
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
                # print(f"{display_text}")
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
            is_x_enter=False
            lcd.clear()
            return
        elif pressed_button == "Return":
            lcd.clear()
            is_x_enter = False
        elif pressed_button == "Calculate":
            if is_x_enter:
                is_x_enter=False
                return
            else:
                if "=" in display_text:
                    syntax_error_display()
                elif error_checking():
                    syntax_error_display()
                else:
                    equation = []    
                    temp_text = check_x_syntax(display_text,False)
                    if(temp_text == "Syntax Error"):
                        return
                    else:
                        slice_equation(temp_text) # Generate equation after slicing
                        result = normal_calculation(equation) # Take result
                        lcd.cursor_pos = (1, 0)
                        lcd.write_string(f"{result}")
                        print(f"{result}")
                    # Thiếu xử lí nếu số ra vượt 16 kí tự: 1.152921504606847e+18, thay e+18 thành *10^18.
                    # Sử dụng nút qua trái/phải để xem kết quả
                return

        elif pressed_button == "Solve":
            subprocess.run('clear', shell=True) # Delete this line after debugging
            equation = []    
            temp_text = check_x_syntax(display_text,True)
            if(temp_text == "Syntax Error"):
                return
            else:
                slice_equation(temp_text) # Generate equation after slicing
            if "x" in temp_text : #thiếu trường hợp nếu không gõ = thì mặc định tìm x với vế phải bằng 0
                lcd.cursor_pos = (1,0)
                lcd.write_string("x=")
                is_in_solving = True
                initial_x = ''
                is_x_enter = True
                while(is_x_enter):
                    scan_keypad()
                result = find_x(float(initial_x)) # Take result
                if result == "Error" or result == "Cannot Solve" or result == "MATH Error":
                    lcd.clear()
                    lcd.cursor_pos = (0, 0)
                else:
                    print(f"type result: {type(result)}")
                    initial_x=str(result)
                    lcd.cursor_pos = (1, 0) 
                lcd.write_string(f"{result}")
                print(f"ket qua cuoi cung= {result}")
                print(f"phep tinh: {display_text}")
                print(f"So lan lap: {count_repeat}")
            else:
                syntax_error_display()
            return
 
        else:
            # Add character
            if  not is_x_enter:
                if(cursor_pos<16):
                    display_text = display_text[:cursor_blink_pos] + str(pressed_button) + display_text[cursor_blink_pos:]
                else:
                    display_text = display_text[:cursor_pos] + str(pressed_button)+ display_text[cursor_pos:]
                cursor_pos += 1
                if(cursor_blink_pos<15):
                    cursor_blink_pos+=1
            else: 
                initial_x = initial_x[:cursor_pos_line_2]+str(pressed_button)
                cursor_pos_line_2+=1 
        # Đảm bảo con trỏ không vượt quá văn bản
        cursor_pos = min(cursor_pos, len(display_text))
        
        # Update LCD display
        update_display()
        # print(f"{display_text}")
        # print(f"chieu dai chuoi sau xu li {len(display_text)}")
        # print(f"vi tri con tro sau xu li {cursor_pos}")
        # print(f"vi tri nhay sau xu li {cursor_blink_pos}")

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
        if c3.is_pressed:
            handle_button_press(row, 3)
# lcd.write_string(f"{demo_text[:5]}")
while True:
    scan_keypad()

