
import socket

HOST = ''
PORT = 9000
ccs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ccs.bind((HOST, PORT))
ccs.listen(1)

vm = {}

while 1:
    conn, addr = ccs.accept()
    data = conn.recv(1024)

    if not data:
        continue

    request = data.split(",")

    if request[0] == "desc":
        if len(request) == 2:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(req[1]*2), 9001))
            s.send("desc")
            res1 = s.recv(1024)

            s.connect(("node"+str(req[1]*2+1), 9001))
            s.send("desc")
            res2 = s.recv(1024)

            res1 = res1.split(",")
            res2 = res2.split(",")

            res = ""

            for i in range(0,len(res1)):
                res += str(int(res1[i])+int(res2[i]))

            conn.send(res)

        if len(request) == 3:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(req[2]), 9001))
            s.send("desc")
            conn.send(s.recv(1024))

    elif request[0] == "create":

ccs.close()
