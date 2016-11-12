import libvirt
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
                    <graphics type='vnc'/>\
                </devices>\
            </domain>\
            "
    
    createStoragePoolVolume(pool,name,size)
    domain=conn.defineXML(xml)
    domain.create()
    domain.setAutostart(1)

def describeResources(conn,pool):
    resource = {}
    resource["capacity"] = pool.info()[1]
    resource["vcpu"] = conn.getMaxVcpus(None)
    resource["memory"] = (conn.getInfo()[1])*1024*1024

    print resource

    mem = 0
    hdd = 0
    cpu = 0

    domains = conn.listAllDomains(0)
    for dom in domains:

        vol = pool.storageVolLookupByName(dom.name()+".qcow2")
        vol = vol.info()

        print dom.name(), dom.maxMemory()

        mem += (dom.maxMemory()*1024)
        cpu += dom.maxVcpus()
        hdd += vol[1]

    resource["capacity"] -= hdd
    resource["vcpu"] -= cpu
    resource["memory"] -= mem
    return resource

memory = "1073741824"
cpu = "2"
name = "centos71"
conn=libvirt.open("qemu:///system")
pool = conn.storagePoolLookupByName('images')
createVM(conn, pool, name, cpu, memory, "10")
print describeResources(conn, pool)
