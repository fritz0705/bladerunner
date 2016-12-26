# coding: utf-8

from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

import random
import uuid
import datetime
import string

Base = declarative_base()

def generate_password(length=12, characters=None):
    if characters is None:
        characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

class VirtualMachine(Base):
    __tablename__ = "virtual_machines"
    uuid = Column(String(length=36),
            default=uuid.uuid4,
            primary_key=True,
            nullable=False)
    created_at = Column(DateTime,
            default=datetime.datetime.now(),
            nullable=False)
    libvirt_url = Column(String,
            default="qemu:///system",
            nullable=False)
    expires_at = Column(DateTime)
    management_password = Column(String,
            default=generate_password,
            nullable=True)
    provisioned = Column(Boolean,
            default=False)
    primary_disk = Column(String)

class Token(Base):
    __tablename__ = "tokens"
    token = Column(String(length=36),
            default=uuid.uuid4,
            primary_key=True,
            nullable=False)
    expires_at = Column(DateTime)
    # 0 means forever, everything else are SI seconds
    vm_lifetime = Column(Integer, default=0)
    regenerates = Column(Boolean, default=False)
    libvirt_url = Column(String)

