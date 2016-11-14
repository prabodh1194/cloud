import socket

HOST = ''
PORT = 9000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

vm = {}

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
            #/desc/zone/domID
            if len(req) == 1:
                conn.send(str(vm))
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("node"+str(req[1]*2), 9001))
                s.send("description,"+req[1]+(","+req[2] if len(req)==3 else ""))
                conn.send(s.recv(1024))
                s.close()

        elif request[0] == "create":
            #/create/zone/name/cpu/memory/disk
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(req[1]*2), 9001))
            s.send("create,"+req[2]+","+req[3]+","+req[4]+","+req[5])
            domID = s.recv(1024)

            if req[1] not in vm:
                vm[req[1]] = []

            vm[req[1]] += [[domID, req[2]]]

            s.close()

        elif request[0] == "remove":
            #/remove/zone/name
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(req[1]*2), 9001))
            s.send("remove,"+req[2])
            domID = s.recv(1024)
            for a in vm[int(req[1])]:
                
         
    conn.close()
