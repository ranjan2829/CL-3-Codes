import java.rmi.Remote;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;

public class HotelApp {
    public interface Hotel extends Remote {
        String bookRoom(String guestName) throws RemoteException;
        String cancelBooking(String guestName) throws RemoteException;
        String[] getBookings() throws RemoteException; // Add this method
    }

    public static class HotelImpl extends UnicastRemoteObject implements Hotel {
        private int totalRooms;
        private int availableRooms;
        private String[] guests;

        public HotelImpl(int rooms) throws RemoteException {
            super();
            this.totalRooms = rooms;
            this.availableRooms = rooms;
            this.guests = new String[rooms];
        }

        public synchronized String bookRoom(String guestName) throws RemoteException {
            if (availableRooms > 0) {
                for (int i = 0; i < totalRooms; i++) {
                    if (guests[i] == null) {
                        guests[i] = guestName;
                        availableRooms--;
                        return "Room " + (i + 1) + " booked for " + guestName;
                    }
                }
            }
            return "No rooms available";
        }

        public synchronized String cancelBooking(String guestName) throws RemoteException {
            for (int i = 0; i < totalRooms; i++) {
                if (guests[i] != null && guests[i].equals(guestName)) {
                    guests[i] = null;
                    availableRooms++;
                    return "Booking cancelled for " + guestName;
                }
            }
            return "No booking found for " + guestName;
        }

        public String[] getBookings() throws RemoteException {
            // Create a list of bookings in format "Room X: Guest Name"
            java.util.List<String> bookingsList = new java.util.ArrayList<>();
            
            for (int i = 0; i < totalRooms; i++) {
                if (guests[i] != null) {
                    bookingsList.add("Room " + (i + 1) + ": " + guests[i]);
                }
            }
            
            return bookingsList.toArray(new String[0]);
        }
    }

    public static void main(String[] args) {
        try {
            // Use a different port (1098 instead of default 1099)
            int port = 1098;
            HotelImpl hotel = new HotelImpl(5);
            
            // Create registry on custom port
            Registry registry = LocateRegistry.createRegistry(port);
            registry.rebind("HotelService", hotel);
            
            System.out.println("Hotel Server is ready on port " + port);
        } catch (Exception e) {
            System.out.println("Server Error: " + e);
        }
    }
}