import java.rmi.*;
import java.rmi.server.*;
import java.rmi.registry.*;

// Remote Interface
interface Concat extends Remote {
    String concat(String a, String b) throws RemoteException;
}

// Implementation
public class Server extends UnicastRemoteObject implements Concat {
    public Server() throws RemoteException {}
    public String concat(String a, String b) { return a + b; }

    public static void main(String[] args) throws Exception {
        LocateRegistry.createRegistry(1099); // Start registry in code
        Naming.rebind("concat", new Server());
        System.out.println("RMI Server ready");
    }
}
