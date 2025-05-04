import java.rmi.*;
import java.util.Scanner;

public class Client {
    public static void main(String[] args) throws Exception {
        Concat stub = (Concat) Naming.lookup("rmi://localhost/concat");
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter first string: ");
        String str1 = scanner.nextLine();
        System.out.print("Enter second string: ");
        String str2 = scanner.nextLine();
        String result = stub.concat(str1, str2);
        System.out.println("Result: " + result);
        scanner.close();
    }
}