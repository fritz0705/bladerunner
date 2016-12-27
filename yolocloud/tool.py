#!/usr/bin/env python
# coding: utf-8

import argparse

import yolocloud.database as database
import yolocloud.virt as virt

def create_token():
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

    argparser_create_token.add_argument("--vm-lifetime", type=int, default=0,
            dest="vm_lifetime", help="Lifetime for virtual machines in SI seconds")
    argparser_create_token.add_argument("--regenerate", type=bool, default=False,
            dest="regenerate", help="If set, then the tokens won't expire on use")
    argparser_create_token.add_argument("--libvirt-url", type=str,
            dest="libvirt_url", help="Enforce libvirt URL for generated virtual machines")
    argparser_create_token.add_argument("token", nargs="?", type=str,
            default="", help="Token string")

    args = argparser.parse_args(argv)

    if args.command == "create-token":
        pass
    elif args.command == "create-domain"):
        pass

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

