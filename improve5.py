from RPLCD.i2c import CharLCD
import time
from gpiozero import LED, Button
import subprocess
import math
import subprocess

r0 = LED(24)
r1 = LED(23)
r2 = LED(18)

c0 = Button(25)
c1 = Button(8)
c2 = Button(7)
c3 = Button(1)

keypad = [["=", "x", 7,"("], ["Shift right", "Del", 9,"Return"], ["Shift left", "^", 8,")"],
          ["Solve", "AC", "+","Menu"], [4, 1, 0], [5, 2, "."],
          [6, 3, "Calculate"], ["-", "*", "/"]]  

last_pressed_time = [[0, 0, 0, 0] for _ in range(8)]

lcd = CharLCD('PCF8574', 0x27)
lcd.cursor_mode = 'line'
lcd.clear()

# display_text = "(x^14-3*x^12+7*x^9)-(5*x^8+2*x^6)+(4*x^5-11*x^3+6*x^2)-(20*x-50)"
# display_text = "3*sin(3x)-3^0.5*cos(9x)=1+4*sin(3x)^3"
display_text="cos(3x)-sin(5x)=3^0.5*(cos(5x)-sin(3x))"
#display_text = "sin(x)-1"


equation = []
cursor_pos = 0  
cursor_blink_pos = 0
is_shift_left_pressed = 0
initial_x = 1

cursor_pos_line_2 = 0
cursor_blink_pos_2 = 0
is_displaying_ans_x = False
last_result = 0
is_return_pressed = False
lanlap = 0
is_in_menu=False
is_trigonometry_selected=False
# Danh sách các hàm toán học được hỗ trợ
supported_functions = ["sin", "cos", "tan", "cot"]

def slice_equation(display_text):
    global equation
    equation.clear()  
    current = ""
    i = 0
    n = len(display_text)
    
    while i < n:
        # Kiểm tra hàm toán học
        found_function = False
        for func in supported_functions:
            if i + len(func) <= n and display_text[i:i+len(func)] == func:
                if current:
                    equation.append(current)
                    current = ""
                equation.append(func)
                i += len(func)
                found_function = True
                break
                
        if found_function:
            continue
            
        char = display_text[i]
        if char in "+-*/()=^x":
            if current:
                equation.append(current)
                current = ""
            equation.append(char)
        else:
            current += char  # Nếu là số hoặc dấu chấm, tiếp tục ghép vào
        i += 1
        
    if current:
        equation.append(current)


def update_display():
    global count_repeat
    lcd.clear()
    lcd.cursor_pos=(0,0)
    if (cursor_pos<15 and len(display_text)<=15):
        lcd.write_string(display_text[:len(display_text)]) 
    else:
        if(cursor_pos>15):
            lcd.write_string(display_text[cursor_pos-15:cursor_pos])
        else:
            lcd.write_string(display_text[0:15])
    lcd.cursor_pos=(0,cursor_blink_pos)
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
    equation = []  # Reset equation
    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string("Syntax ERROR")
    print("Syntax Error")


def precedence(op):
    if op in ('+', '-'): 
        return 1
    if op in ('*', '/'): 
        return 2
    if op == '^':  
        return 3  
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
    if op == '^':
        try:
            return pow(a, b)
        except:
            return "Math Error"


def apply_function(func, value):
    try:
        if func == "sin":
            return math.sin(value)
        elif func == "cos":
            return math.cos(value)
        elif func == "tan":
            # Kiểm tra tan(π/2 + k*π)
            adjusted_value = value % math.pi
            if abs(adjusted_value - math.pi/2) < 1e-10:
                return "Math Error"
            return math.tan(value)
        elif func == "cot":
            # Check if tan(x) == 0 
            tan_value = math.tan(value)
            if abs(tan_value) < 1e-10:
                return "Math Error"
            return 1 / tan_value
        else:
            return "Math Error"
    except:
        return "Math Error"


def is_operator(token):
    return token in ['+', '-', '*', '/', '^']


def is_function(token):
    return token in supported_functions


def infix_to_postfix(expression):
    output, stack = [], []
    i, n = 0, len(expression)

    if "j" in expression:  # Kiểm tra số phức
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string("Complex number")
        print("Complex number")
        return "Error"

    while i < n:
        # Tìm token tiếp theo
        # Kiểm tra hàm
        is_func = False
        for func in supported_functions:
            if i + len(func) <= n and expression[i:i+len(func)] == func:
                stack.append(func)
                i += len(func)
                is_func = True
                break
                
        if is_func:
            continue
            
        token = expression[i]

        # Xử lý số (bao gồm số âm)
        if token.isdigit() or token == '.' or (token == '-' and (i == 0 or expression[i - 1] in "*/^+-(")): 
            num = token
            while i + 1 < n and (expression[i + 1].isdigit() or expression[i + 1] == '.'):
                i += 1
                num += expression[i]

            output.append(num)  # Lưu số hoàn chỉnh vào danh sách

        elif token in "*/^+-":  # Xử lý toán tử
            while stack and stack[-1] not in "(" and precedence(stack[-1]) >= precedence(token) and not is_function(stack[-1]):
                output.append(stack.pop())
            stack.append(token)

        elif token == '(':  # Dấu mở ngoặc
            stack.append(token)

        elif token == ')':  # Dấu đóng ngoặc
            while stack and stack[-1] != '(':
                output.append(stack.pop())
                
            if stack and stack[-1] == '(':
                stack.pop()  # Bỏ dấu '(' khỏi stack
                
                # Nếu trước dấu '(' là một hàm, thêm hàm vào output
                if stack and is_function(stack[-1]):
                    output.append(stack.pop())
            else:
                return "Error"  # Ngoặc không cân đối

        else:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Invalid Input infix")
            print("Invalid Input infix")
            return "Error"

        i += 1

    while stack:
        if stack[-1] == '(':
            return "Error"  # Ngoặc không cân đối
        output.append(stack.pop())

    return output


def evaluate_postfix(postfix):
    stack = []
    
    for token in postfix:
        if token.lstrip('+-').replace('.', '', 1).isdigit():
            stack.append(float(token))
        elif is_operator(token):
            if len(stack) < 2:
                print("Syntax Error POSTFIX")
                # print(f"len stack: {len(stack)}")
                lcd.clear()
                lcd.cursor_pos = (0, 0)
                lcd.write_string("Syntax Error POSTFIX")
                return "Error"
            b, a = stack.pop(), stack.pop()
            # print(f"a= {a}")
            # print(f"b= {b}")
            # print(f"token= {token}")
            if a == "Math Error" or b == "Math Error":
                print("Error in stack pop")
                return "Change initial x"
            result = apply_op(a, b, token)
            if result == "Math Error":
                print("Error in apply_op")
                return "Error"
            stack.append(result)
            # print(f"stack: {stack}")
            # print("-------")
        elif is_function(token):
            if len(stack) < 1:
                print("Syntax Error FUNCTION")
                return "Error"
            a = stack.pop()
            
            if a == "Math Error":
                print("Error in stack pop")
                return "Change initial x"
            result = apply_function(token, a)
            if result == "Math Error":
                print("Error in apply_function")
                return "Error"
            stack.append(result)
        else:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Invalid Input evalute")
            print("Invalid Input evalute")
            return "Error"
            
    return stack[0] if len(stack) == 1 else "Error"


def derivative_calculation(x_para):
    global equation
    cofficient_h = 1e-9
    
    while True:
        func_xh = [expr.replace("x", str(x_para + cofficient_h)) for expr in equation]
        result_xh = normal_calculation(func_xh)
        if result_xh == "Change initial x":
            x_para += 0.1
            continue
        if result_xh is not None:
            break
        cofficient_h /= 10
        
    while True:
        func_x = [expr.replace("x", str(x_para - cofficient_h)) for expr in equation]
        result_x = normal_calculation(func_x)
        if result_x == "Change initial x":
            x_para += 0.1
        else:
            break
            
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

def check_trigonometry_syntax(expression_text):

    if "sin(" not in expression_text or "cos(" not in expression_text or "tan(" not in expression_text or "cot(" not in expression_text:
        return expression_text

def normal_calculation(equation_para):
    expression = ''.join(equation_para)
    if "e" in expression:
        expression = expression.replace("e", "*10^")
        
    # Chuyển đổi biểu thức thành mảng
    postfix = infix_to_postfix(expression)
    
    if postfix != "Error":
        result = evaluate_postfix(postfix)
        if result != "Error" and result != "Change initial x":
            if result == 0.0:  # eliminate negative -0.0
                result = 0.0
        return result
    else:
        return postfix


def find_x(x_para):
    start = time.monotonic()  # Bắt đầu đếm thời gian
    global lanlap
    SO_LAN_LAP = 10000
    recalculate = False
    
    for lanlap in range(SO_LAN_LAP):
        func_x_nor = [expr.replace("x", str(x_para)) for expr in equation]
        result_func_x_nor = normal_calculation(func_x_nor)

        if result_func_x_nor == "Error":
            print("Error of result_func_x_nor")
            return "Math Error"
        if result_func_x_nor == "Change initial x":
            x_para += 0.1
            continue
        if result_func_x_nor == 0 and x_para == 0:
            return x_para

        result_func_x_deri = derivative_calculation(x_para)
        if result_func_x_deri == "Math Error":
            print("Error of result_func_x_deri")
            return "Math Error"
        if result_func_x_deri == 0 or abs(result_func_x_deri) < 1e-9:
            x_para += 2
            recalculate = True

        if not recalculate:
            result = x_para - (result_func_x_nor / result_func_x_deri)
            if abs(result - x_para) < 1e-5:
                func_x_nor = [expr.replace("x", str(result)) for expr in equation]
                left_side = normal_calculation(func_x_nor)
                if left_side == "Change initial x":
                    x_para += 0.1
                    continue
                if left_side == "Error":
                    return "Cannot Solve"

                if abs(left_side) < 1e-13 or (result - x_para == 0):
                    end = time.monotonic()  # Lấy thời gian kết thúc
                    print(f"Thời gian thực thi: {end - start:.6f} giây")
                    print(f"left side= {left_side}")
                    return result
                elif abs(left_side) < 1e-11:
                    end = time.monotonic()  # Lấy thời gian kết thúc
                    print(f"Thời gian thực thi: {end - start:.6f} giây")
                    print(f"left side= {left_side}")
                    return result
                else:
                    if lanlap == SO_LAN_LAP - 1:
                        print("Cannot Solve")
                        return "Cannot Solve"          
            x_para = result
        recalculate = False

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
    lcd.write_string("Math Error")
    print("Math Error")

def process_exp(result):
    if "e+" in result:
        result=result.replace("e+","*10^")
    elif "e-" in result:
        result=result.replace("e","*10^")
    return result


def handle_button_press(row, column):
    global display_text, cursor_pos,cursor_blink_pos,equation
    global is_return_pressed,is_secure_pressed,is_displaying_ans_x,is_shift_left_pressed
    global initial_x,cursor_pos_line_2,cursor_blink_pos_2,last_result,count_repeat,is_in_menu,is_trigonometry_selected
    current_time = time.time() 
    if (current_time - last_pressed_time[row][column] > 0.2):  # Debounce 200ms
        last_pressed_time[row][column] = current_time
        pressed_button = keypad[row][column]
        print(pressed_button)
        
        if (pressed_button == "Menu"):
            is_in_menu=True
            lcd.clear()
            lcd.cursor_mode = 'hide'
            lcd.cursor_pos=(0,0)
            lcd.write_string("1.Sin   2.Cos")
            lcd.cursor_pos=(1,0)
            lcd.write_string("3.Tan   4.Cot")
            return
        if (pressed_button == "Del"): #Delete character before blinking cursor
            if(not is_in_menu):
                if (cursor_blink_pos>0 and cursor_pos <=16):
                    display_text = display_text[:cursor_blink_pos-1] + display_text[cursor_blink_pos:]
                    if(not is_shift_left_pressed):
                        cursor_blink_pos-=1
                    else:
                        is_shift_left_pressed=0
                else:
                    display_text = display_text[cursor_pos-16:cursor_pos]

        elif pressed_button == "Shift left":
            print(f"cursor blink pos: {cursor_blink_pos}")
            print(f"cursor pos: {cursor_pos}")
            if(not is_in_menu):
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
                        print(f"cursor blink pos after shift left: {cursor_blink_pos}")
                        return
                    else:
                        if(cursor_pos!= 0):
                            cursor_pos-=1
                        # print(f"cursor pos after -1: {cursor_pos}")
        elif pressed_button == "Shift right":
            if(not is_in_menu):
                if is_displaying_ans_x:
                    if len(last_result)<15:
                        return
                    elif cursor_pos_line_2 < len(last_result):
                        cursor_pos_line_2+=1
                else:
                    if(cursor_blink_pos<15 and cursor_blink_pos<=cursor_pos):
                        cursor_blink_pos+=1
                        lcd.cursor_blink_pos=(0,cursor_blink_pos)
                    cursor_pos+=1
        elif pressed_button == "AC":
            lcd.clear()
            display_text = ""
            cursor_pos = 0
            cursor_blink_pos=0
            subprocess.run('clear', shell=True) # Delete this line after debugging
            is_in_menu=False
            is_displaying_ans_x=False
            lcd.cursor_mode = 'line'
            return

        elif pressed_button == "Return":
            lcd.clear()
            is_displaying_ans_x=False
            is_in_menu=False
            lcd.cursor_mode = 'line'

        elif pressed_button == "Calculate":
            if(not is_in_menu):
                if error_checking():
                    syntax_error_display()
                    return
                else:
                    # print("calculation....")
                    equation = []    
                    temp_text = check_x_syntax(display_text,False)
                    # print(f"temp_text= {temp_text}")
                    if(temp_text == "Syntax Error"):
                        return
                    else:
                        slice_equation(temp_text) # Generate equation after slicing
                        last_result = normal_calculation(equation) # Take result
                        lcd.cursor_pos = (1, 0)
                        last_result=str(last_result)
                        print(f"last result= {last_result}")
                        if last_result == "Math Error":
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
            if(not is_in_menu):
                # print("In solve")
                if error_checking():          
                    syntax_error_display()
                    return

                if not is_displaying_ans_x:
                    subprocess.run('clear', shell=True) # Delete this linsube after debugging
                    # print(f"initial x: {initial_x} ")
                    equation = []    
                    temp_text = check_x_syntax(display_text,True)
                    # print(f"temp text: {temp_text}")
                    if(temp_text == "Syntax Error"):
                        return
                    else:
                        if "=" in temp_text:
                            position=temp_text.index("=")
                            temp_text = temp_text[:position] + "-(" + temp_text[position+1:]+")"
                        slice_equation(temp_text) # Generate equation after slicing
                    if "x" in temp_text :                  
                        last_result = find_x(float(initial_x)) # Take result
                        if last_result == "Error" or last_result == "Cannot Solve" or last_result == "Math Error":
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
                        print(f"So lan lap: {lanlap}")
                    
                    else:
                        syntax_error_display()
        else:
            if(is_in_menu):
                if(pressed_button==1):
                    pressed_button="sin("
                    is_trigonometry_selected=True
                elif pressed_button==2:
                    pressed_button="cos("
                    is_trigonometry_selected=True
                elif pressed_button==3:
                    pressed_button="tan("
                    is_trigonometry_selected=True
                elif pressed_button==4:
                    pressed_button="cot("
                    is_trigonometry_selected=True
                else:
                    lcd.cursor_mode = 'line'
                    return
                
        
            # Add character
            if(cursor_pos<16):
                display_text = display_text[:cursor_blink_pos] + str(pressed_button) + display_text[cursor_blink_pos:]
            else:
                display_text = display_text[:cursor_pos] + str(pressed_button)+ display_text[cursor_pos:]
            cursor_pos += 1
            if(cursor_blink_pos<15):
                cursor_blink_pos+=1

            if (is_trigonometry_selected):
                lcd.cursor_mode = 'line'
                is_in_menu=False
                is_trigonometry_selected=False
                cursor_pos+=3
                cursor_blink_pos+=3
                if(cursor_blink_pos>=15):
                    cursor_blink_pos=15
                

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

while True:
    scan_keypad()

