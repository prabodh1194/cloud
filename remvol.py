import libvirt

conn = libvirt.open()
pool = conn.storagePoolLookupByName('images')

vols = pool.listVolumes()

for vol in vols:
    print vol
    vo = pool.storageVolLookupByName(vol)
    vo.wipe(0)
    vo.delete(0)
