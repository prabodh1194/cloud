import libvirt, socket
from xml.dom import minidom

def getVolume(conn, domID):
    dom = conn.lookupByID(domID)
    raw_xml = dom.XMLDesc(0)
    xml = minidom.parseString(raw_xml)
    diskTypes = xml.getElementsByTagName('disk')
    for diskType in diskTypes:
        nam = ""
        typ = ""
        fil = ""

        if diskType.getAttribute('device') != 'disk':
            continue
        diskNodes = diskType.childNodes
        for diskNode in diskNodes:
            if fil is not "":
                print fil
                break
            attrs = diskNode.attributes
            if attrs is not None:
                for attr in attrs.keys():
                    name = str(diskNode.attributes[attr].name)
                    val = str(diskNode.attributes[attr].value)
                    if diskNode.nodeName == 'driver':
                        if name == 'name' and val == 'qemu':
                            nam = val
                        elif name == 'type' and val == 'qcow2':
                            typ = val
                    elif diskNode.nodeName == 'source':
                        if name == 'file' and typ is not "" and nam is not "":
                            fil = val
                            break

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

def createVM(conn, pool, name, cpu, memory, size):
    xml = "<?xml version='1.0'?>\
            <domain type='kvm' id='8'>\
                <name>"+name+"</name>\
                <memory unit='B'>"+memory+"</memory>\
                <vcpu>"+cpu+"</vcpu>\
                <os>\
                    <type>hvm</type>\
                    <boot dev='hd'/>\
                    <boot dev='cdrom'/>\
                </os>\
                <devices>\
                    <disk type='file' device='disk'>\
                        <driver name='qemu' type='qcow2'/>\
                        <source file='/var/lib/libvirt/images/"+name+".qcow2'/>\
                        <backingStore/>\
                        <target dev='vda' bus='virtio'/>\
                        <alias name='virtio-disk0'/>\
                        <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>\
                    </disk>\
                    <disk type='file' device='cdrom'>\
                        <driver name='qemu' type='raw'/>\
                        <source file='/var/lib/libvirt/boot/CentOS-7-x86_64-DVD-1511.iso'/>\
                        <backingStore/>\
                        <target dev='hda' bus='ide'/>\
                        <readonly/>\
                        <alias name='ide0-0-0'/>\
                        <address type='drive' controller='0' bus='0' target='0' unit='0'/>\
                    </disk>\
                    <interface type='network'>\
                        <source network='default'/>\
                    </interface>\
                    <graphics type='vnc' listen='0.0.0.0'/>\
                </devices>\
            </domain>\
            "

    createStoragePoolVolume(pool,name,size)
    domain=conn.defineXML(xml)
    domain.create()
    domain.setAutostart(1)
    vnc_port = domain.XMLDesc().index("port")
    vnc_port += 6
    vnc_port_end = domain.XMLDesc().index("'", vnc_port)
    return str(domain.ID())+","+domain.XMLDesc()[vnc_port:vnc_port_end]

def removeVM(conn, pool, domID):
    domain = conn.lookupByID(domID)
    name = domain.name()
    domain.destroy()
    domain.undefine()
    vol = pool.storageVolLookupByName(name+".qcow2")
    vol.wipe(0)
    vol.delete(0)

def shutdownVM(conn, domID):
    domain = conn.lookupByID(domID)
    print domID, domain.name()
    domain.shutdown()

def startVM(conn, domID):
    domain = conn.lookupByID(domID)
    domain.create()

def describeResources(conn,pool):
    resource = {}
    resource["vcpu"] = conn.getMaxVcpus(None)
    resource["memory"] = (conn.getInfo()[1])*1024*1024
    resource["capacity"] = pool.info()[1]

    print resource

    mem = 0
    hdd = 0
    cpu = 0

    domains = conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_RUNNING)
    for dom in domains:

        vol = 0
        try:
            vol = pool.storageVolLookupByName(dom.name()+".qcow2")
            vol = vol.info()
        except:
            continue

        print dom.name(), dom.maxMemory()

        mem += (dom.maxMemory()*1024)
        cpu += dom.maxVcpus()
        hdd += vol[1]

    resource["vcpu"] -= cpu
    resource["memory"] -= mem
    resource["capacity"] -= hdd

    res = ""

    for r in resource:
        res+=str(resource[r])+","
    return str(resource)

HOST = ''
PORT = 9002
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

memory = "1073741824"
cpu = "2"
name = "centos71"
connvm =libvirt.open("qemu:///system")
pool = connvm.storagePoolLookupByName('images')

#createVM(connvm, pool, name, cpu, memory, "10")

while 1:
    connsock, addr = s.accept()
    data = connsock.recv(1024)
    print data
    if data is None:
        continue

    instr = data.split(",")

    if instr[0] == "desc":
        connsock.send(describeResources(connvm, pool))
    elif "create" in instr[0]:
        domID = createVM(connvm, pool, instr[1], instr[2], instr[3], instr[4])
        print domID
        connsock.send(domID)
    elif instr[0] == "remove":
        domID = int(instr[1])
        removeVM(connvm, pool, domID)
        connsock.send("1")
    elif instr[0] == "shut":
        domID = int(instr[1])
        shutdownVM(connvm, domID)
        connsock.send("1")
    elif instr[0] == "start":
        domID = int(instr[1])
        startVM(connvm, domID)
        connsock.send("1")

    connsock.close()

connvm.close()

def handler(signum, frame):
    connvm.close()
signal.signal(signal.SIGINT, handler)
