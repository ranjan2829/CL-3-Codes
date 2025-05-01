import java.rmi.Naming;
import java.util.Scanner;

public class HotelClient {
    public static void main(String[] args) {
        try {
            // Updated to use port 1098
            HotelApp.Hotel hotel = (HotelApp.Hotel) Naming.lookup("rmi://localhost:1098/HotelService");
            Scanner sc = new Scanner(System.in);
            while (true) {
                System.out.println("\n1. Book Room\n2. Cancel Booking\n3. Show Bookings\n4. Exit");
                System.out.print("Choice: ");
                int ch = sc.nextInt(); sc.nextLine();

                if (ch == 1) {
                    System.out.print("Enter Guest Name: ");
                    System.out.println(hotel.bookRoom(sc.nextLine()));
                } else if (ch == 2) {
                    System.out.print("Enter Guest Name: ");
                    System.out.println(hotel.cancelBooking(sc.nextLine()));
                } else if (ch == 3) {
                    String[] bookings = hotel.getBookings();
                    System.out.println("\n--- Current Bookings ---");
                    if (bookings.length == 0) {
                        System.out.println("No rooms are currently booked.");
                    } else {
                        for (String booking : bookings) {
                            System.out.println(booking);
                        }
                    }
                } else if (ch == 4) {
                    break;
                } else {
                    System.out.println("Invalid choice. Please try again.");
                }
            }
            sc.close();
        } catch (Exception e) {
            System.out.println("Client Error: " + e);
        }
    }
}