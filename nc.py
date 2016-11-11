import libvirt

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
      <source file='/var/lib/libvirt/images/centos7.qcow2'/>\
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
domain=conn.createXML(xml)
