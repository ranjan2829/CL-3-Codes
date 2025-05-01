import xmlrpc.client

with xmlrpc.client.ServerProxy("http://localhost:8000/RPC2") as proxy:
    try:
        
        input_value = 5
        result = proxy.calculate_factorial(input_value)
        print(f"Factorial of {input_value} is: {result}")
    except Exception as e:
        print(f"Error: {e}")