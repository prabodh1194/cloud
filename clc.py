import socket, signal, ast

HOST = ''
PORT = 9000
clcs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clcs.bind((HOST, PORT))
clcs.listen(1)

vm = {}

vm['0'] = []
vm['1'] = []

for i in range(0,2):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("node"+str(i*2), 9001))
    s.send("info")
    info = s.recv(1024)
    info = ast.literal_eval(info)
    s.close()

    for dom in info:
        vm[str(i)] += [[info[dom][0],dom,'a']]

while 1:
    conn, addr = clcs.accept()
    data = conn.recv(1024)
    print vm
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

        req = he[1].split("/")
        req = req[1:]
        print req

        if req[0] == "desc":
            #/desc/zone/domID
            if len(req) == 1:
                conn.send(str(vm))
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print "node"+str(int(req[1])*2)
                s.connect(("node"+str(int(req[1])*2), 9001))
                s.send("desc"+(","+req[2] if len(req)==3 else ""))
                conn.send(s.recv(1024))
                s.close()

        elif "create" in req[0]:
            #/create(s)/zone/name/cpu/memory/disk
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(int(req[1])*2), 9001))
            s.send(req[0]+","+req[2]+","+req[3]+","+req[4]+","+req[5])
            domID = s.recv(1024)
            print domID

            if req[1] not in vm:
                vm[req[1]] = []

            vm[req[1]] += [[domID, req[2],'a']]

            conn.send(str(vm))
            s.close()

        elif req[0] == "remove":
            #/remove/zone/name
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(int(req[1])*2), 9001))
            s.send("remove,"+req[2])
            domID = s.recv(1024)
            for a in vm[int(req[1])]:
                if a[0] == domID:
                    vm[int(req[1])].remove(a)
            conn.send(str(vm))
            s.close()

        elif req[0] == "shut":
            #/shut/zone/name
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(int(req[1])*2), 9001))
            s.send("shut,"+req[2])
            domID = s.recv(1024)
            for a in vm[int(req[1])]:
                if a[0] == domID:
                    a[2] = 'i'
            conn.send(str(vm))
            s.close()

        elif req[0] == "resume":
            #/start/zone/name
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(int(req[1])*2), 9001))
            s.send("resume,"+req[2])
            domID = s.recv(1024)
            for a in vm[int(req[1])]:
                if a[0] == domID:
                    a[2] = 'a'
            conn.send(str(vm))
            s.close()

        elif req[0] == "addDisk":
            #/addDisk/zone/size
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(int(req[1])*2), 9001))
            s.send("addDisk,"+req[2])
            diskName = s.recv(1024)
            conn.send(diskName+":"+req[2]+"G")
            s.close()

        elif req[0] == "attachDisk":
            #/attachDisk/zone/vmname/diskname/volname
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(int(req[1])*2), 9001))
            s.send("attachDisk,"+req[2]+","+req[3]+","+req[4])
            s.close()

        elif req[0] == "put":
            #/put/file
            file = req[1]
            hash = 0

            for f in file:
                hash ^= (ord(f)&1)

            hash <<= 2
            hash = str(hash)
            print "node"+hash
            ip = socket.gethostbyname("node"+hash)
            conn.send("curl "+ip+":9001 --upload-file "+file)

        elif req[0] == "get":
            #/get/file
            file = req[1]
            hash = 0

            for f in file:
                hash ^= (ord(f)&1)

            hash <<= 2
            hash = str(hash)
            print "node"+hash
            ip = socket.gethostbyname("node"+hash)
            conn.send("curl "+ip+":9001/"+file+" --output "+file)

        elif req[0] == "delete":
            #/delete/file
            file = req[1]
            hash = 0

            for f in file:
                hash ^= (ord(f)&1)

            hash <<= 2
            hash = str(hash)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+hash, 9001))
            s.send("deleteObject,"+req[1])
            conn.send(s.recv)
            s.close()

    conn.close()
clcs.close()

def handler(signum, frame):
    clcs.close()
signal.signal(signal.SIGINT, handler)
