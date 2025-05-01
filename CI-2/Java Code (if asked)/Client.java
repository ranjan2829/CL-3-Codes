import java.rmi.*;

public class Client {
    public static void main(String[] args) throws Exception {
        Concat stub = (Concat) Naming.lookup("rmi://localhost/concat");
        System.out.println("Result: " + stub.concat("Hi", "there!"));
    }
}
