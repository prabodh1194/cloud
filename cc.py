import socket, sys, ast, pdb

ccID = int(sys.argv[1])
HOST = ''
PORT = 9001
ccs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ccs.bind((HOST, PORT))
ccs.listen(1)

vm = {}
state = 0

while 1:
    conn, addr = ccs.accept()
    data = conn.recv(1024)
    print vm

    if not data:
        continue

    request = data.split(",")
    print request

    if request[0] == "desc":
        if len(request) == 1:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(ccID*2), 9002))
            s.send("desc")
            res1 = s.recv(1024)
            s.close()

            s.connect(("node"+str(ccID*2+1), 9002))
            s.send("desc")
            res2 = s.recv(1024)
            s.close()

            res1 = ast.literal_eval(res1)
            res2 = ast.literal_eval(res2)

            res = {}

            for i in res1:
                res[i] = int(res1[i])+int(res2[i])

            conn.send(str(res))

        if len(request) == 2:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+request[1], 9002))
            s.send("desc")
            conn.send(s.recv(1024))

    #round-robin
    elif request[0] == "create":
        for k in range(0,2):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(ccID*2+state), 9002))

            s.send("desc")
            res = s.recv(1024)
            res = ast.literal_eval(res)

            req_param = {'vcpu':request[2], 'memory':request[3], 'capacity': 1024*1024*1024*int(request[4])}
            print res, req_param

            flag = 1

            for i in res:
                flag &= int(res[i]) >= int(req_param[i])

            s.close()
            if not flag:
                state ^= 1
            else:
                break

        if not flag:
            conn.send("fail")
            break

        print "node"+str(ccID*2+state), data
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("node"+str(ccID*2+state), 9002))
        s.send(data)
        domID,port = s.recv(1024).split(",")
        domID = int(domID)
        port = int(port)

        if(domID != -1):
            vm[request[1]] = [domID, ccID*2+state]

        conn.send("node"+str(ccID*2+state)+","+str(domID)+","+str(port))
        s.close()
        state ^= 1

    #greedy
    elif request[0] == "creates":
        s.connect(("node"+str(ccID*2), 9002))
        s.send("desc")
        res1 = s.recv(1024)
        res1 = ast.literal_eval(res1)
        s.close()

        s.connect(("node"+str(ccID*2+1), 9002))
        s.send("desc")
        res2 = s.recv(1024)
        res2 = ast.literal_eval(res2)
        s.close()

        flag = 1

        for i in res1:
            flag &= int(res1[i]) < int(res2[i])

        s.connect(("node"+str(ccID*2+flag), 9002))
        s.send(data)
        domID = int(s.recv(10))

        if(domID != -1):
            vm[request[1]] = [domID, ccID*2+state]

        conn.send("node"+str(ccID*2+state)+","+str(domID))
        s.close()

    elif request[0] == "remove":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("node"+str(vm[request[1]][1]), 9002))
        s.send("remove,"+str(vm[request[1]][0]))
        success = int(s.recv(10))
        conn.send(str(vm[request[1]][0]))

        if success:
            vm.pop(request[1])

        s.close()

    elif request[0] == "shut":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(vm[request[1]][1]), 9002))
            s.send("shut,"+str(vm[request[1]][0]))
            success = int(s.recv(10))
            print success
            conn.send(str(vm[request[1]][0]))
            s.close()

    elif request[0] == "resume":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(vm[request[1]][1]), 9002))
            s.send("shut,"+str(vm[request[1]][0]))
            success = int(s.recv(10))
            conn.send(str(vm[request[1]][0]))
            s.close()

    conn.close()
ccs.close()

def handler(signum, frame):
    ccs.close()
signal.signal(signal.SIGINT, handler)
