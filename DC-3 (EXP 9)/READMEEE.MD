

````markdown
# Java RMI Hotel Booking System (EXP 9)



2. **Compile the Java files** using the following command:

    ```bash
    javac HotelApp.java HotelClient.java
    ```

---

## 🛰️ Step 1: Start the RMI Registry

In the **same directory** as your compiled `.class` files, run the following command to start the RMI registry:

```bash
rmiregistry
````

- This starts the RMI registry on **port 1099** by default. Leave this terminal open.
- **If port 1099 is already in use**, use the following commands to kill the process using the port:
  ```bash
  lsof -i :1099  # Find the PID using the port
  kill -9 <PID>  # Kill the process using that port
  ```

---

## 🖥️ Step 2: Run the RMI Server

In a **new terminal window**, navigate to the same directory and run the server application:

```bash
java HotelApp
```

You should see the following output indicating the server is ready:

```
Hotel Server is ready...
```

---

## 🧑‍💻 Step 3: Run the Client

In another **new terminal window**, navigate to the same directory and run the client application:

```bash
java HotelClient
```

---

## 💡 Sample Client Output

The client will prompt you to book or cancel a room:

```
1. Book Room
2. Cancel Booking
3. Exit
Choice: 1
Enter Guest Name: Ranjan
Room booked for Ranjan

Choice: 2
Enter Guest Name to Cancel: Ranjan
Booking cancelled for Ranjan
```

---
