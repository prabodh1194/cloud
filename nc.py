import libvirt

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

def createVM(conn, name, cpu, memory, size):
    xml = "<?xml version='1.0'?>\
            <domain type='kvm' id='8'>\
                <name>"+name+"</name>\
                <memory unit='KiB'>"+memory+"</memory>\
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
    
    pool = conn.storagePoolLookupByName('images')
    #createStoragePoolVolume(pool,name,size)
    domain=conn.createXML(xml)

def describeResources(conn,pool):
    resource = {}
    resource.capacity = pool.info()[1]
    resource.vcpu = conn.getMaxVcpus(None)
    resource.memory = conn.getInfo()[1]



memory = "2097152"
cpu = "2"
name = "centos71"
conn=libvirt.open("qemu:///system")
createVM(conn, name, cpu, memory, "10")
