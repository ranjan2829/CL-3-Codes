import Pyro5.api

def main():
    uri = f"PYRO:HotelService@localhost:1098"
    hotel = Pyro5.api.Proxy(uri)
    while True:
        print("\n1. Book Room\n2. Cancel Booking\n3. Show Bookings\n4. Exit")
        ch = input("Choice: ")
        if ch == "1":
            name = input("Enter Guest Name: ")
            print(hotel.bookRoom(name))
        elif ch == "2":
            name = input("Enter Guest Name: ")
            print(hotel.cancelBooking(name))
        elif ch == "3":
            bookings = hotel.getBookings()
            print("\n--- Current Bookings ---")
            if not bookings:
                print("No rooms are currently booked.")
            else:
                for b in bookings:
                    print(b)
        elif ch == "4":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
