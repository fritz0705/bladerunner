#!/usr/bin/env python
# coding: utf-8

import argparse

import libvirt
import sqlalchemy
import sqlalchemy.orm

import yolocloud.database as database
import yolocloud.virt as virt

Session = sqlalchemy.orm.sessionmaker()

def main_create_token(args):
    session = Session()
    token = database.Token(token=args.token, libvirt_url=args.libvirt_url,
            regenerates=args.regenerate, vm_lifetime=args.vm_lifetime)
    session.add(token)
    session.commit()

def main_create_domain(args):
    session = Session()
    vm = database.VirtualMachine()

def main_delete_domain(args):
    pass

def main(argv):
    argparser = argparse.ArgumentParser(description="YoloCloud CLI tool")
    argparser.add_argument("--engine", default="sqlite://", dest="engine",
            help="Database engine URI")
    argparser.add_argument("--broker", default="pyamqp://", dest="broker",
            help="Celery broker URI")

    subparsers = argparser.add_subparsers(dest="command")

    argparser_create_token = subparsers.add_parser("create-token")
    argparser_create_domain = subparsers.add_parser("create-domain")
    argparser_delete_domain = subparsers.add_parser("delete-domain")

    argparser_create_token.add_argument("--vm-lifetime", type=int, default=0,
            dest="vm_lifetime", help="Lifetime for virtual machines in SI seconds")
    argparser_create_token.add_argument("--regenerate", type=bool, default=False,
            dest="regenerate", help="If set, then the tokens won't expire on use")
    argparser_create_token.add_argument("--libvirt-url", type=str,
            dest="libvirt_url", help="Enforce libvirt URL for generated virtual machines")
    argparser_create_token.add_argument("token", nargs="?", type=str,
            default=None, help="Token string")

    argparser_create_domain.add_argument("template", type=str,
            help="Domain template name")
    argparser_create_domain.add_argument("--provision", type=bool, default=True,
            dest="provision", help="If set, enqueue provisioning")
    
    argparser_delete_domain.add_argument("--keep-hdd", type=bool, default=False,
            dest="keep_hdd", help="If set, then the HDDs won't get deleted.")

    args = argparser.parse_args(argv)

    engine = sqlalchemy.create_engine(args.engine)
    Session.configure(bind=engine)

    if args.command == "create-token":
        main_create_token(args)
    elif args.command == "create-domain":
        main_create_domain(args)
    elif args.command == "delete-domain":
        main_delete_domain(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

