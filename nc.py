import libvirt

def createStoragePool(conn):
    xmlDesc = """
    <pool type='dir'>
    <name>guest images</name>
    <capacity unit='bytes'>4306780815</capacity>
    <allocation unit='bytes'>237457858</allocation>
    <available unit='bytes'>4069322956</available>
    <source>
    </source>
    <target>
    <path>/home/hduser</path>
    <permissions>
    <mode>0755</mode>
    <owner>-1</owner>
    <group>-1</group>
    </permissions>
    </target>
    </pool>
    """
    pool = conn.storagePoolDefineXML(xmlDesc, 0)
    pool.setAutostart(1)
    return pool

def createStoragePoolVolume(pool, name):
    stpVolXml = """
    <volume>
        <name>"""+name+""".qcow2</name>
        <allocation>0</allocation>
        <capacity unit="G">10</capacity>
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

xml = "<?xml version='1.0'?>\
        <domain type='kvm' id='8'>\
        <name>centos7</name>\
        <uuid>4ca049a8-2521-48a8-bf91-fa7df6769ff3</uuid>\
        <memory unit='KiB'>2097152</memory>\
        <currentMemory unit='KiB'>2097152</currentMemory>\
        <vcpu>2</vcpu>\
        <os>\
        <type>hvm</type>\
        <boot dev='cdrom'/>\
        <boot dev='hd'/>\
        </os>\
        <devices>\
        <disk type='file' device='disk'>\
        <driver name='qemu' type='qcow2'/>\
        <source file='/var/lib/libvirt/images/centos71.qcow2'/>\
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
        <graphics type='vnc' port='5900'/>\
        </devices>\
        </domain>\
        "

conn=libvirt.open("qemu:///system")
pool = conn.storagePoolLookupByName('images')
createStoragePoolVolume(pool,"centos71")
domain=conn.createXML(xml)
