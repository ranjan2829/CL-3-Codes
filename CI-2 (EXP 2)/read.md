

````markdown
# Pyro5 String Concatenation Example

## How to Run

1. **Install Pyro5**  
   ```bash
   pip install Pyro5
````

2. **Start Pyro5 Name Server**

   ```bash
   pyro5-ns
   ```

   *If Pyro5 isn't working, use Pyro4:*

   ```bash
   python3 -m Pyro4.naming
   ```

3. **Start the Server**

   ```bash
   python3 server.py
   ```

4. **Run the Client**

   ```bash
   python3 client.py
   ```

## How it Works

* Server exposes a method to concatenate two strings.
* Client reads `server_uri.txt`, inputs two strings, and prints the result.

**Note:** Ensure `server_uri.txt` is in the same directory as `server.py` and `client.py`.
