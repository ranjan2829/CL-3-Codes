# Pyro4 String Concatenation Example

This project demonstrates a simple client-server application using Pyro4 for remote string concatenation.

## How to Run

1. **Start the Pyro4 Name Server**  
   Open a terminal and run:
   ```
   python3 -m Pyro4.naming
   ```

2. **Start the Server**  
   In a new terminal, run:
   ```
   python3 server.py
   ```

3. **Run the Client**  
   In another terminal, run:
   ```
   python3 client.py
   ```

## How it Works

- The server exposes a method to concatenate two strings.
- The client reads the server URI from `server_uri.txt`, takes two strings as input, and prints the concatenated result.

**Note:**  
Make sure `server_uri.txt` is in the same directory as the client and server scripts.