from threading import Event, Thread
import libvirt, socket, sys, ast, signal

t = None

def handler(signum, frame):
    ccs.close()
    cancel()

def packer():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("node"+str(ccID*2), 9002))
    s.send("desc")
    res1 = s.recv(1024)
    res1 = ast.literal_eval(res1)
    s.close()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("node"+str(ccID*2+1), 9002))
    s.send("desc")
    res2 = s.recv(1024)
    res2 = ast.literal_eval(res2)
    s.close()

    flag = 1

    for i in res1:
        flag &= int(res1[i]) < int(res2[i])

    conn1 = libvirt.open("qemu+tcp://node"+str(src)+"/system")
    conn2 = libvirt.open("qemu+tcp://node"+str(tar)+"/system")

    for k, v in vm:

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("node"+str(src), 9002))
        s.send("desc,"+str(v[0]))
        res = s.recv(1024)
        res = ast.literal_eval(res)
        s.close()

        flag = 1
        if v[1]&1 == 0: #migrate from 1 to 2
            for i in res1:
                flag &= (int(res2[i])+int(res[i])) < (int(res1[i])-int(res[i]))
            if flag:
                dom = conn1.lookupByID(v[0])
                dom.migrate(conn2, libvirt.VIR_MIGRATE_LIVE, None, "tcp://node"+str(v[1]+1), 0)

                for i in res:
                    res1[i] -= res[i]
                    res2[i] += res[i]

        else:
            for i in res1: #migrate from 2 to 1
                flag &= (int(res1[i])+int(res[i])) < (int(res2[i])-int(res[i]))
            if flag:
                dom = conn2.lookupByID(domain[0])
                dom.migrate(conn1, libvirt.VIR_MIGRATE_LIVE, None, "tcp://node"+str(v[1]-1), 0)

                for i in res:
                    res1[i] += res[i]
                    res2[i] -= res[i]

    conn1.close()
    conn2.close()

def call_repeatedly(interval, func, *args):
    stopped = Event()
    def loop():
        while not stopped.wait(interval): # the first call is in `interval` secs
            func(*args)
    Thread(target=loop).start()
    return stopped.set

def createStoragePoolVolume(pool, name, size):
    stpVolXml = """
    <volume>
        <name>"""+name+""".qcow2</name>
        <allocation>0</allocation>
        <capacity unit="G">"""+size+"""</capacity>
        <target>
            <format type='qcow2'/>
            <path>/var/lib/libvirt/images/"""+name+""".qcow2</path>
            <permissions>
                <owner>107</owner>
                <group>107</group>
                <mode>0744</mode>
                <label>virt_image_t</label>
            </permissions>
        </target>
    </volume>
    """
    stpVol = pool.createXML(stpVolXml, 0)
    return stpVol

signal.signal(signal.SIGINT, handler)
connvm = libvirt.open("qemu:///system")
pool = connvm.storagePoolLookupByName('images')

cancel = call_repeatedly(5, packer)

ccID = int(sys.argv[1])
HOST = ''
PORT = 9001
objectStorePath = "/home/group1/osd/"

vm = {}
state = 0
disk = 0

ccs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ccs.bind((HOST, PORT))
ccs.listen(1)

while 1:
    conn, addr = ccs.accept()
    data = conn.recv(1024)
    print vm

    if not data:
        continue

    if "PUT" in data:
        head = data.split("\n")[0]
        length = data.split("\n")[4]
        length = int(length.split(" ")[1])
        file = head.split(" ")[1][1:]
        file = open(objectStorePath+file, "w")
        while length > 0:
            dat = conn.recv(1024)
            length -= len(dat)
            file.write(dat)
            if dat == None:
                print "donw"
                conn.send("200")
                conn.close()
                file.close()
                break

    if "GET" in data:
        head = data.split("\n")[0]
        file = head.split(" ")[1][1:]

        try:
            file = open(objectStorePath+file, "r")
        except:
            conn.close()
            continue

        for line in file:
            conn.send(line)
        conn.close()
        file.close()

    request = data.split(",")
    print request

    if request[0] == "desc":
        if len(request) == 1:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("node"+str(ccID*2), 9002))
            s.send("desc")
            res1 = s.recv(1024)
            s.close()

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("node"+str(ccID*2), 9002))
        s.send("desc")
        res1 = s.recv(1024)
        res1 = ast.literal_eval(res1)
        s.close()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("node"+str(ccID*2+1), 9002))
        s.send("desc")
        res2 = s.recv(1024)
        res2 = ast.literal_eval(res2)
        s.close()

        flag = 1

        for i in res1:
            flag &= int(res1[i]) < int(res2[i])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("node"+str(ccID*2+flag), 9002))
        s.send(data)
        dd = s.recv(1024)
        print dd
        domID,port = dd.split(",")
        domID = int(domID)
        port = int(port)

        if(domID != -1):
            vm[request[1]] = [domID, ccID*2+state]

        conn.send("node"+str(ccID*2+flag)+","+str(domID)+","+str(port))
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

    elif request[0] == "addDisk":
        createStoragePoolVolume(pool, "disk"+str(disk), request[1])
        disk += 1
        conn.send("disk"+str(disk-1))

    elif request[0] == "attachDisk":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("node"+str(vm[request[1]][1]), 9002))
        s.send("attach,"+str(vm[request[1]][0])+","+request[2]+","+request[3])
        s.close()

    elif request[0] == "deleteObject":
        try:
            os.remove(request[1])
            conn.send("Success")
        except:
            conn.send("File not exists")

    conn.close()
ccs.close()
