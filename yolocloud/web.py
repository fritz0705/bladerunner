# coding: utf-8

import datetime
import random
import functools

import bottle
import libvirt
import jinja2

import yolocloud.database as database
import yolocloud.virt as virt

class Jinja2Mixin(object):
    def __init__(self, *args, loader=None, **kwargs):
        if loader is None:
            loader = jinja2.PackageLoader("yolocloud", "views")
        self._jinja2_env = jinja2.Environment(loader=loader)
        # implement the _render_view protocol
        self._render_view = self._render_jinja2

    def _render_jinja2(self, name, *args, **kwargs):
        return self._jinja2_env.get_template(name).render(*args, **kwargs)

    @staticmethod
    def with_jinja2_renderer(f, template=None):
        if isinstance(f, str):
            return lambda g: Jinja2Mixin.with_jinja2_renderer(g, template=f)
        if template is None:
            template = f.__name__
        @functools.wraps(f)
        def wrapper(self, *args, **kwds):
            res = f(self, *args, **kwds)
            if isinstance(res, dict):
                return self._render_jinja2(template, **res)
            elif res is None:
                return self._render_jinja2(template)
            return res
        return wrapper

class DatabaseMixin(object):
    def __init__(self, *args, engine="sqlite:///yolocloud.db", **kwargs):
        import sqlalchemy
        import sqlalchemy.orm
        if isinstance(engine, str):
            engine = sqlalchemy.create_engine(engine)
        self._Session = sqlalchemy.orm.sessionmaker(bind=engine)

    @staticmethod
    def with_database_session(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwds):
            session = self._Session()
            try:
                return f(self, *args, **kwds, db=session)
            finally:
                session.close()
        return wrapper

class CeleryMixin(object):
    def __init__(self, *args, celery_app=None, **kwargs):
        if celery_app is None:
            import celery
            celery_app = celery.Celery("yolocloud", broker="pyamqp://")
        self.celery_app = celery_app

    @staticmethod
    def task(f):
        if isinstance(f, str):
            def wrapper(self, *args, **kwargs):
                self.queue_task(f, *args, **kwargs)
            return wrapper
        return f
    
    def queue_task(self, task, *args, **kwargs):
        if self.celery_app is False:
            return
        self.celery_app.send_task(task, args=args, kwargs=kwargs)

    def send_task(self, task, *args, **kwargs):
        if self.celery_app is False:
            return
        self.celery_app.send_task(task *args, **kwargs)

class BaseApplication(bottle.Bottle):
    def __init__(self, *args, **kwargs):
        bottle.Bottle.__init__(self)

    def mount(self, prefix, app, **options):
        if isinstance(app, bottle.Bottle):
            # It seems that we got a Bottle application (e.g. an application
            # controller), so we create an instance of it with supplied
            # environment and configuration dictionaries
            app = app(config=self.config)
        return bottle.Bottle.mount(prefix, app, **options)

    @property
    def request(self):
        return bottle.request

    @property
    def response(self):
        return bottle.response

class VMController(BaseApplication, Jinja2Mixin, DatabaseMixin, CeleryMixin):
    provision_vm = CeleryMixin.task("yolocloud.tasks.provision_vm")
    shutdown_vm = CeleryMixin.task("yolocloud.tasks.shutdown_vm")
    reboot_vm = CeleryMixin.task("yolocloud.tasks.reboot_vm")
    start_vm = CeleryMixin.task("yolocloud.tasks.start_vm")
    reset_vm = CeleryMixin.task("yolocloud.tasks.reset_vm")
    destroy_vm = CeleryMixin.task("yolocloud.tasks.destroy_vm")

    require_token = False

    def __init__(self, *args, vm_hosts=None, require_token=False, **kwargs):
        BaseApplication.__init__(self, *args, **kwargs)
        Jinja2Mixin.__init__(self, loader=jinja2.PackageLoader("yolocloud", "views/vm"))
        DatabaseMixin.__init__(self, *args, **kwargs)
        CeleryMixin.__init__(self, *args, **kwargs)
        self.vm_hosts = vm_hosts or ["qemu:///system"]
        self.require_token = require_token
        self.route("/<uuid>", "GET", self.show_vm)
        self.route("/<uuid>", "POST", self.update_vm)
        self.route("/<uuid>/delete", "POST", self.delete_vm)
        self.route("/<uuid>", "DELETE", self.delete_vm)
        self.route("/", "GET", self.index_page)
        self.route("/", "POST", self.create_vm)

    @Jinja2Mixin.with_jinja2_renderer("index.html")
    def index_page(self):
        if "manage" in self.request.query and self.request.query.get("uuid"):
            bottle.redirect("/{}".format(self.request.query["uuid"]))

    @DatabaseMixin.with_database_session
    def create_vm(self, db):
        vm = database.VirtualMachine()
        token = db.query(database.Token).filter(
                database.Token.token == self.request.forms["token"]).first()
        if token:
            if token.vm_lifetime:
                vm.expires_at = datetime.datetime.now() + datetime.timedelta(seconds=token.vm_lifetime)
            if token.libvirt_url:
                vm.libvirt_url = token.libvirt_url
            if not token.regenerates:
                db.delete(token)
        elif self.require_token:
            self.report_403("Engine creation not possible without token")
        if not vm.libvirt_url:
            vm.libvirt_url = self._pick_libvirt_host()
        try:
            if token and not token.regenerates:
                db.delete(token)
            db.add(vm)
            db.commit()
        except:
            db.rollback()
        self.provision_vm(uuid=vm.uuid, preset=self.request.forms.get("preset"))
        bottle.redirect("/{}".format(vm.uuid))

    @DatabaseMixin.with_database_session
    @Jinja2Mixin.with_jinja2_renderer("show.html")
    def show_vm(self, uuid, db=None):
        vm = db.query(database.VirtualMachine).filter(
                database.VirtualMachine.uuid == uuid).first()
        if vm is None:
            return self.report_404("Engine not found")
        elif not vm.provisioned:
            return self.report_202("Engine not ready")
        vir_conn = libvirt.open(vm.libvirt_url)
        vm_desc = None
        vm_info = None
        try:
            vir_dom = vir_conn.lookupByUUIDString(vm.uuid)
            vm_info = vir_dom.info()
            vm_desc = virt.DomainDescription(vir_dom)
        finally:
            vir_conn.close()
        return dict(vm=vm,
            vm_desc=vm_desc,
            vm_state=virt.state_to_text_mapping.get(vm_info[0]),
            vm_info=vm_info)

    @DatabaseMixin.with_database_session
    def update_vm(self, uuid, db=None):
        vm = db.query(database.VirtualMachine).filter(
                database.VirtualMachine.uuid == uuid).first()
        action = self.request.forms.get("action")
        if action == "shutdown":
            self.shutdown_vm(uuid=vm.uuid)
        elif action == "reboot":
            self.reboot_vm(uuid=vm.uuid)
        elif action == "start":
            self.start_vm(uuid=vm.uuid)
        elif action == "reset":
            self.reset_vm(uuid=vm.uuid)
        elif action == "force-shutdown":
            self.destroy_vm(uuid=vm.uuid)
        bottle.redirect("/{}".format(vm.uuid))

    @DatabaseMixin.with_database_session
    def delete_vm(self, uuid, db=None):
        vm = db.query(database.VirtualMachine).filter(
                database.VirtualMachine.uuid == uuid).first()
        if vm:
            self.enqueue("delete_vm", uuid=vm.uuid)
        bottle.redirect("/")

    def _pick_libvirt_host(self):
        return random.choice(self.vm_hosts)

    @Jinja2Mixin.with_jinja2_renderer("404.html")
    def report_404(self, reason):
        self.response.status = 404
        return dict(reason=reason)

    @Jinja2Mixin.with_jinja2_renderer("403.html")
    def report_403(self, reason):
        self.response.status = 403
        return dict(reason=reason)

    @Jinja2Mixin.with_jinja2_renderer("202.html")
    def report_202(self, reason):
        self.response.status = 202
        return dict(reason=reason)

wsgi_app = VMController()

