# Java RMI String Concatenation Example

This project demonstrates a simple Java RMI client-server application for string concatenation.

## How to Run

1. **Compile the Java files**  
   Open a terminal in the project directory and run:
   ```
   javac Server.java Client.java
   ```

2. **Start the RMI Registry**  
   In the same directory, run:
   ```
   rmiregistry
   ```
   Leave this terminal open.

3. **Start the Server**  
   Open a new terminal in the same directory and run:
   ```
   java Server
   ```

4. **Run the Client**  
   Open another terminal in the same directory and run:
   ```
   java Client
   ```

## How it Works

- The server implements a remote method to concatenate two strings.
- The client looks up the remote object and calls the method.

**Note:**  
Make sure all terminals are in the same directory as your `.class` files.