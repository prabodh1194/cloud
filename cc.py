import socket, sys

ccID = sys.argv[1]
HOST = ''
PORT = 9000
ccs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ccs.bind((HOST, PORT))
ccs.listen(1)

vm = {}
state = 0

while 1:
    conn, addr = ccs.accept()
    data = conn.recv(1024)

    if not data:
        continue

    request = data.split(",")

    if request[0] == "desc":
        if len(request) == 1:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(ccID*2), 9001))
            s.send("desc")
            res1 = s.recv(1024)

            s.connect(("node"+str(ccID*2+1), 9001))
            s.send("desc")
            res2 = s.recv(1024)

            res1 = res1.split(",")
            res2 = res2.split(",")

            res = ""

            for i in range(0,len(res1)):
                res += str(int(res1[i])+int(res2[i]))

            conn.send(res)
            s.close()

        if len(request) == 2:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+req[1], 9001))
            s.send("desc")
            conn.send(s.recv(1024))

    elif request[0] == "create":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(ccID*2+state), 9001))
            s.send(data)
            domID = int(s.recv(10))

            if(domID != -1):
                vm.request[1] = [domID, ccID*2+state]

            state ^= 1
            s.close()

    elif request[0] == "remove":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(vm[request[1]]), 9001))
            s.send("remove,"+str(vm[request[0]]))
            success = int(s.recv(10))
            conn.send(str(vm[request[1]][0]))

            if success:
                vm.pop(request[1])

            s.close()

    elif request[0] == "shut":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(vm[request[1]]), 9001))
            s.send("shut,"+str(vm[request[0]]))
            success = int(s.recv(10))
            conn.send(str(vm[request[1]][0]))
            s.close()

    elif request[0] == "resume":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(vm[request[1]]), 9001))
            s.send("resume,"+str(vm[request[0]]))
            success = int(s.recv(10))
            conn.send(str(vm[request[1]][0]))
            s.close()

    conn.close()
ccs.close()
