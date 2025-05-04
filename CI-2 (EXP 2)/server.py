import Pyro5.api

@Pyro5.api.expose
class StringConcatenationServer:
    def concatenate_strings(self, str1, str2):
        return str1 + str2

def main():
    daemon = Pyro5.api.Daemon()
    ns = Pyro5.api.locate_ns()
    server = StringConcatenationServer()
    uri = daemon.register(server)
    ns.register("string.concatenation", uri)
    print("Server URI:", uri)
    with open("server_uri.txt", "w") as f:
        f.write(str(uri))
    daemon.requestLoop()  

if __name__ == "__main__":
    main()
