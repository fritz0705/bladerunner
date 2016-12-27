# coding: utf-8

import functools

import celery
import libvirt
import sqlalchemy
import sqlalchemy.orm
import jinja2

import yolocloud.database as database
import yolocloud.virt as virt

app = celery.Celery("yolocloud", broker="pyamqp://")
engine = sqlalchemy.create_engine("sqlite:///yolocloud.db")
Session = sqlalchemy.orm.sessionmaker(bind=engine)
templates = { "base": virt.BaseVMTemplate() }

jinja2_env = jinja2.Environment(loader=jinja2.PackageLoader("yolocloud", "templates"))

def render_template(name, **kwargs):
    return jinja2_env.get_template(name).render(**kwargs)

def with_database_session(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        pass
    return wrapper

@app.task
def provision_vm(uuid, template, config={}):
    db = Session()
    vm = db.query(database.VirtualMachine).filter(
            database.VirtualMachine.uuid == uuid).first()
    if not vm:
        db.close()
        return
    vir_conn = libvirt.open(vm.libvirt_url)
    tpl = vm_templates[template]
    try:
        tpl.provision(self, vm, vir_conn)
    finally:
        vir_conn.close()
    try:
        vm.provisioned = True
        db.add(vm)
        db.commit()
    finally:
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

@app.task
def change_media(uuid, media_volume, media_pool="iso"):
    db = Session()
    vm = db.query(database.VirtualMachine).filter(
            database.VirtualMachine.uuid == uuid).first()
    if not vm:
        db.close()
        return
    vir_conn = libvirt.open(vm.libvirt_url)
    try:
        vir_dom = vir_conn.lookupByUUIDString(vm.uuid)
    finally:
        vir_con.close()
        db.close()

