# coding: utf-8

import celery
import libvirt
import sqlalchemy
import sqlalchemy.orm

import yolocloud.database as database

app = celery.Celery("yolocloud", broker="pyamqp://")
engine = sqlalchemy.create_engine("sqlite:///yolocloud.db")
Session = sqlalchemy.orm.sessionmaker(bind=engine)

@app.task
def provision_vm(uuid):
    db = Session()
    vm = db.query(database.VirtualMachine).filter(
            database.VirtualMachine.uuid == uuid).first()
    if not vm:
        db.close()
        return
    # Generate volume.xml
    # Generate domain.xml
    db.close()

@app.task
def shutdown_vm(uuid):
    db = Session()
    vm = db.query(database.VirtualMachine).filter(
            database.VirtualMachine.uuid == uuid).first()
    if not vm:
        db.close()
        return
    vir_conn = libvirt.open(vm.libvirt_url)
    try:
        vir_dom = vir_conn.lookupByUUIDString(vm.uuid)
        vir_dom.shutdown()
    finally:
        vir_conn.close()
        db.close()

@app.task
def reboot_vm(uuid):
    db = Session()
    vm = db.query(database.VirtualMachine).filter(
            database.VirtualMachine.uuid == uuid).first()
    if not vm:
        db.close()
        return
    vir_conn = libvirt.open(vm.libvirt_url)
    try:
        vir_dom = vir_conn.lookupByUUIDString(vm.uuid)
        vir_dom.reboot()
    finally:
        vir_conn.close()
        db.close()

@app.task
def start_vm(uuid):
    db = Session()
    vm = db.query(database.VirtualMachine).filter(
            database.VirtualMachine.uuid == uuid).first()
    if not vm:
        db.close()
        return
    vir_conn = libvirt.open(vm.libvirt_url)
    try:
        vir_dom = vir_conn.lookupByUUIDString(vm.uuid)
        vir_dom.create()
    finally:
        vir_conn.close()
        db.close()

@app.task
def reset_vm(uuid):
    db = Session()
    vm = db.query(database.VirtualMachine).filter(
            database.VirtualMachine.uuid == uuid).first()
    if not vm:
        db.close()
        return
    vir_conn = libvirt.open(vm.libvirt_url)
    try:
        vir_dom = vir_conn.lookupByUUIDString(vm.uuid)
        vir_dom.reset()
    finally:
        vir_conn.close()
        db.close()

@app.task
def destroy_vm(uuid):
    db = Session()
    vm = db.query(database.VirtualMachine).filter(
            database.VirtualMachine.uuid == uuid).first()
    if not vm:
        db.close()
        return
    vir_conn = libvirt.open(vm.libvirt_url)
    try:
        vir_dom = vir_conn.lookupByUUIDString(vm.uuid)
        vir_dom.destroy()
    finally:
        vir_conn.close()
        db.close()

