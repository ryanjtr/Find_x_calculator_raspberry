# This version verify initial x, if initial x cause MATH ERROR while using apply_op function, then it will be plus 0.1
# Imrpove "return button" process
# Have secret shutdown 
# Have horse animation
# Process exp e -> *10^

import horse_animation 
from RPLCD.i2c import CharLCD
import time
from gpiozero import LED, Button
import subprocess


r0 = LED(24)
r1 = LED(23)
r2 = LED(18)

c0 = Button(25)
c1 = Button(8)
c2 = Button(7)
c3 = Button(1)

keypad = [["=", "x", 7,"("], ["Shift right", "Del", 9,"Return"], ["Shift left", "^", 8,")"],
          ["Solve", "AC", "+","Secure"], [4, "1", 0], [5, 2, "."],
          [6, 3, "Calculate"], ["-", "*", "/"]]

last_pressed_time = [[0, 0, 0,0] for _ in range(8)]


lcd = CharLCD('PCF8574', 0x27)
lcd.cursor_mode = 'line'
lcd.clear()

display_text = "6.3x^900.1-4.9x^-400.7+7.8x^250.3-5.6x^-125.5+3.2x^60.9-1.1"
equation = []
cursor_pos = 0  
cursor_blink_pos=0
is_shift_left_pressed=0
initial_x= '0'

is_in_solving = False
is_x_enter = False
cursor_pos_line_2 = 0
cursor_blink_pos_2=0
is_displaying_ans_x=False
last_result=0
is_return_pressed=False
is_secure_pressed=False

def slice_equation(display_text):
    global equation
    equation.clear()  # Xóa danh sách trước khi thêm mới
    current = ""

    for char in display_text:
        if char in "+-*/()=^x":
            if current:
                equation.append(current)
                current = ""
            equation.append(char)
        else:
            current += char  # Nếu là số hoặc dấu chấm, tiếp tục ghép vào
    if current:
        equation.append(current)

    print(equation)


def update_display():
    global count_repeat
    lcd.clear()
    lcd.cursor_pos=(0,0)
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
    if is_displaying_ans_x:
        lcd.cursor_pos=(1,0)
        if (cursor_pos_line_2<16 and len(last_result)<=16):
            lcd.write_string(last_result[:len(last_result)]) 
        else:
            if(cursor_pos_line_2>16):
                lcd.write_string(last_result[cursor_pos_line_2-16:cursor_pos_line_2])
            else:
                lcd.write_string(last_result[0:16])
        lcd.cursor_pos=(1,cursor_blink_pos_2)
        count_repeat=0
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
    # print(f"a: {a}")
    # print(f"b: {b}")
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
    output, stack = [], []
    i, n = 0, len(expression)

    if "j" in expression:
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string("Complex number")
        return "Error"

    while i < n:
        token = expression[i]

        # Xử lý số (kể cả số âm)
        if token.isdigit() or token == '.' or (token in "+-" and (i == 0 or expression[i - 1] in "*/(^")):
            num = token
            while i + 1 < n and (expression[i + 1].isdigit() or expression[i + 1] == '.'):
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
            lcd.write_string("Invalid Input infix")
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
                lcd.write_string("Syntax Error POSTFIX")
                return "Error"
            b, a = stack.pop(), stack.pop()
            if a == "MATH ERROR" or b == "MATH ERROR":
                return "Change initial x"
            result = apply_op(a, b, token)
            if result == "Math Error":
                return "Error"
            stack.append(result)
        else:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Invalid Input evalute")
            return "Error"

    return stack[0] if len(stack) == 1 else "Error"


def derivative_calculation(x_para):
    global equation
    cofficient_h = 1e-9
    is_ok=False
    
    while True:
        func_xh = [expr.replace("x", str(x_para + cofficient_h)) for expr in equation]
        result_xh = normal_calculation(func_xh)
        if result_xh == "Change initial x":
            x_para+=0.1
            continue
        if result_xh is not None:
            break
        cofficient_h /= 10
    while not is_ok:
        func_x = [expr.replace("x", str(x_para - cofficient_h)) for expr in equation]
        result_x = normal_calculation(func_x)
        if result_x == "Change initial x":
            x_para+=0.1
        else:
            is_ok=True
    return (result_xh - result_x) / (2 * cofficient_h) if result_xh != "Error" and result_x != "Error" else "Math Error"


def check_x_syntax(expression_text, is_finding_x):
    global initial_x

    if "x" not in expression_text:
        return expression_text  # Không có "x" thì không cần xử lý

    new_expression = []
    length = len(expression_text)

    for i, char in enumerate(expression_text):
        if char == 'x':
            if i < length - 1 and expression_text[i + 1].isdigit():
                syntax_error_display()
                return "Syntax Error"

            # Xử lý các trường hợp trước "x"
            if i > 0 and expression_text[i - 1].isdigit():
                new_expression.append("*")

            # Thay thế "x" theo mục đích
            new_expression.append("x" if is_finding_x else str(initial_x))
        else:
            new_expression.append(char)

    return ''.join(new_expression)


def normal_calculation(equation_para):
    expression = ''.join(equation_para)
    if "e" in expression:
        expression = expression.replace("e","*10^")
    postfix = infix_to_postfix(expression)
    if postfix != "Error":
        result = evaluate_postfix(postfix)
        if result != "Error" and result != "Change initial x":
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
    recalculate=False
    for lanlap in range(SO_LAN_LAP):
        count_repeat+=1
        func_x_nor = [expr.replace("x", str(x_para)) for expr in equation]
        result_func_x_nor = normal_calculation(func_x_nor)
        if result_func_x_nor == "Error":
            return "MATH Error" #Change to MATH Error
        if result_func_x_nor == "Change initial x":
            x_para+=0.1
            continue
        if result_func_x_nor == 0 and x_para == 0:
            return x_para
        result_func_x_deri = derivative_calculation(x_para)
        if result_func_x_deri == "MATH Error":
            return "MATH Error" #Change to MATH Error 
        if(result_func_x_deri==0 or abs(result_func_x_deri) < 1e-9):
            x_para+=2
            recalculate=True

        if(not recalculate):
            result = x_para - (result_func_x_nor/result_func_x_deri)
            if(abs(result-x_para)<1e-5):
                func_x_nor = [expr.replace("x", str(result)) for expr in equation]
                left_side = normal_calculation(func_x_nor)
                if left_side == "Change initial x":
                    x_para+=0.1
                    continue
                if(left_side=="Error"):
                    return "Cannot Solve" 
                
                if(abs(left_side)<1e-15 or (result-x_para==0)):
                    end = time.perf_counter()  # Lấy thời gian kết thúc
                    print(f"left side= {left_side}")
                    print(f"Thời gian thực thi: {end - start:.6f} giây")
                    return result  
                else:
                    if(lanlap==SO_LAN_LAP):
                        return "Cannot Solve"          
            x_para=result
        recalculate=False
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

def syntax_error_display():
    global equation
    equation = [] #Reset equation
    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string("Syntax ERROR")
    print("Syntax Error")

def math_error_display():
    global equation
    equation = [] #Reset equation
    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string("Math ERROR")
    print("Math Error")

def process_exp(result):
    if "e+" in result:
        result=result.replace("e+","*10^")
    elif "e-" in result:
        result=result.replace("e","*10^")
    return result


def handle_button_press(row, column):
    global display_text, cursor_pos,cursor_blink_pos,equation
    global is_return_pressed,is_secure_pressed,is_x_enter,is_displaying_ans_x,is_shift_left_pressed
    global initial_x,cursor_pos_line_2,cursor_blink_pos_2,last_result,count_repeat
    current_time = time.time() 
    if (current_time - last_pressed_time[row][column] > 0.2):  # Debounce 200ms
        last_pressed_time[row][column] = current_time
        pressed_button = keypad[row][column]
        
        if (pressed_button == "Del"): #Delete character before blinking cursor
            is_secure_pressed=False
            if (cursor_blink_pos>0 and cursor_pos <=16):
                display_text = display_text[:cursor_blink_pos-1] + display_text[cursor_blink_pos:]
                if(not is_shift_left_pressed):
                    cursor_blink_pos-=1
                else:
                    is_shift_left_pressed=0
            else:
                display_text = display_text[cursor_pos-16:cursor_pos]

        elif pressed_button == "Shift left":
            is_secure_pressed=False
            if is_displaying_ans_x:
                if  cursor_pos_line_2>15:
                    cursor_pos_line_2-=1
                else:
                    return
            else:
                if  (cursor_blink_pos!=0 and cursor_pos <=16):
                    cursor_blink_pos-=1
                    lcd.cursor_pos=(0,cursor_blink_pos)
                    is_shift_left_pressed=1
                    cursor_pos-=1
                    return
                else:
                    cursor_pos-=1
                
        elif pressed_button == "Shift right":
            is_secure_pressed=False
            if is_displaying_ans_x:
                if len(last_result)<15:
                    return
                elif cursor_pos_line_2 < len(last_result):
                    cursor_pos_line_2+=1
            else:
                if(cursor_blink_pos<15 and cursor_blink_pos<cursor_pos):
                    cursor_blink_pos+=1
                    lcd.cursor_blink_pos=(0,cursor_blink_pos)
                cursor_pos+=1
        elif pressed_button == "Secure":
            is_secure_pressed=True
        elif pressed_button == "AC":
            lcd.clear()
            if is_secure_pressed:   
                lcd.cursor_mode = 'hide'
                horse_animation.horse_animation()        
                lcd.clear()
                lcd.cursor = (0,0)
                lcd.write_string("GOODBYE.....")
                subprocess.run('sudo poweroff', shell=True) # Delete this linsube after debugging
            display_text = ""
            cursor_pos = 0
            cursor_blink_pos=0
            subprocess.run('clear', shell=True) # Delete this line after debugging
            is_x_enter=False
            is_displaying_ans_x=False
            return

        elif pressed_button == "Return":
            is_secure_pressed=False
            lcd.clear()
            if is_x_enter:
                is_return_pressed=True
            is_x_enter = False
            is_displaying_ans_x=False
            
        elif pressed_button == "Calculate":
            is_secure_pressed=False
            if is_x_enter:
                is_x_enter=False
                return
            elif error_checking():
                syntax_error_display()
                return
            else:
                print("calculation....")
                equation = []    
                temp_text = check_x_syntax(display_text,False)
                print(f"temp_text= {temp_text}")
                if(temp_text == "Syntax Error"):
                    return
                else:
                    slice_equation(temp_text) # Generate equation after slicing
                    last_result = normal_calculation(equation) # Take result
                    lcd.cursor_pos = (1, 0)
                    last_result=str(last_result)
                    print(f"last result= {last_result}")
                    if last_result == "MATH ERROR":
                        math_error_display()
                        return 
                    if len(last_result)>15:
                        cursor_pos_line_2=16
                        cursor_blink_pos_2=15
                    else:
                        cursor_pos_line_2=len(last_result)
                        cursor_blink_pos_2=cursor_pos_line_2
                    last_result = process_exp(last_result)
                    is_displaying_ans_x=True

        elif pressed_button == "Solve":
            is_secure_pressed=False
            if error_checking():          
                syntax_error_display()
                return

            if not is_displaying_ans_x:
                subprocess.run('clear', shell=True) # Delete this linsube after debugging
                equation = []    
                temp_text = check_x_syntax(display_text,True)
                print(f"temp text: {temp_text}")
                if(temp_text == "Syntax Error"):
                    return
                else:
                    if "=" in temp_text:
                        position=temp_text.index("=")
                        temp_text = temp_text[:position] + "-(" + temp_text[position+1:]+")"
                    slice_equation(temp_text) # Generate equation after slicing
                if "x" in temp_text :
                    lcd.cursor_pos = (1,0)
                    lcd.write_string("x=")
                    is_in_solving = True
                    initial_x = ''
                    is_x_enter = True
                    while(is_x_enter):
                        scan_keypad()
                
                    if not is_return_pressed:
                        last_result = find_x(float(initial_x)) # Take result
                        if last_result == "Error" or last_result == "Cannot Solve" or last_result == "MATH Error":
                            lcd.clear()
                            lcd.cursor_pos = (0, 0)
                            lcd.write_string(last_result)
                            count_repeat=0
                            return
                        else:
                            is_displaying_ans_x=True
                            last_result=str(last_result)
                            initial_x=last_result
                        if len(last_result)>15:
                            cursor_pos_line_2=16
                            cursor_blink_pos_2=15
                        else:
                            cursor_pos_line_2=len(last_result)
                            cursor_blink_pos_2=cursor_pos_line_2
                        last_result = process_exp(last_result)
                        print(f"ket qua cuoi cung= {last_result}")
                        print(f"So lan lap: {count_repeat}")
                    else:
                        is_return_pressed=False
                       
                else:
                    syntax_error_display()
        else:
            is_secure_pressed=False
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
        
        cursor_pos = min(cursor_pos, len(display_text))
        
        # Update LCD display
        update_display()

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

