#! /usr/bin/env python3.4
# Fibonacci numbers module

def fib(n):    # write Fibonacci series up to n
    a=0
    b=1
    while b < n:
        print(b)
        a,b=b,a+b

def fib2(n): # return Fibonacci series up to n
    result = []
    a, b = 0, 1
    while b < n:
        result.append(b)
        a, b = b, a+b
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) <=1 or '-h' in sys.argv:
       help_info = 'Fibbonacci numbers'
       print("Help message: "+help_info)
    else:
       fib(int(sys.argv[1]))
