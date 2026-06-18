#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import base64
import hashlib

from cryptography.fernet import Fernet

from config import config


def _fernet() -> Fernet:
    key = hashlib.sha256(config.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_field(plaintext: str) -> str:
    """Fernet 加密，存 DB 前调用。空值原样返回。"""
    return _fernet().encrypt(plaintext.encode()).decode() if plaintext else plaintext


def decrypt_field(ciphertext: str) -> str:
    """Fernet 解密，分发前调用。空值原样返回。"""
    return _fernet().decrypt(ciphertext.encode()).decode() if ciphertext else ciphertext
