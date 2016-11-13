import socket

HOST = ''
PORT = 9000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

while 1:
    conn, addr = s.accept()
    data = conn.recv(1024)
    if not data:
        continue
    if "favicon" in data:
        continue
    he = data.split("\r\n")
    he = he[0].split(" ")
    print he
    
    if he[0] == "GET":
        if he[1] == "/":
            continue

        request = he[1].split("/")
        request = request[1:]
        print request

        if request[0] == "desc":
            conn.send("description")

conn.close()
