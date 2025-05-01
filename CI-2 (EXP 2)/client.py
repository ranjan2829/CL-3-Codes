import Pyro4

def main():
    try:
        
        with open("server_uri.txt", "r") as f:
            uri = f.read().strip()

        
        server = Pyro4.Proxy(uri)

        
        str1 = input("Enter the first string: ")
        str2 = input("Enter the second string: ")

        
        result = server.concatenate_strings(str1, str2)

        print("Concatenated Result:", result)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
