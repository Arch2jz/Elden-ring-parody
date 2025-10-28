a = int(input("Enter the first number: "))
c = input("Enter the operation: ")
b = int(input("Enter the second number: "))

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b

if c == "+":
    print(add(a, b))
elif c == "-":
    print(subtract(a, b))
elif c == "*":
    print(multiply(a, b))
elif c == "/":
    print(divide(a, b))
else:
    print("Invalid operation")