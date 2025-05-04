import Pyro5.api

@Pyro5.api.expose
class Hotel:
    def __init__(self, total_rooms):
        self.total_rooms = total_rooms
        self.available_rooms = total_rooms
        self.guests = [None] * total_rooms

    def bookRoom(self, guest_name):
        if self.available_rooms > 0:
            for i in range(self.total_rooms):
                if self.guests[i] is None:
                    self.guests[i] = guest_name
                    self.available_rooms -= 1
                    return f"Room {i+1} booked for {guest_name}"
        return "No rooms available"

    def cancelBooking(self, guest_name):
        for i in range(self.total_rooms):
            if self.guests[i] == guest_name:
                self.guests[i] = None
                self.available_rooms += 1
                return f"Booking cancelled for {guest_name}"
        return f"No booking found for {guest_name}"

    def getBookings(self):
        return [f"Room {i+1}: {self.guests[i]}" for i in range(self.total_rooms) if self.guests[i] is not None]

def main():
    daemon = Pyro5.api.Daemon(port=1098)
    uri = daemon.register(Hotel(5), "HotelService")
    print(f"Hotel Server is ready. URI: {uri}")
    daemon.requestLoop()

if __name__ == "__main__":
    main()
