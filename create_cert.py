#!/usr/bin/env python
"""
Скрипт для создания самоподписанного сертификата
"""
from OpenSSL import crypto
import os

def create_self_signed_cert():
    # Генерируем ключ
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # Создаем сертификат
    cert = crypto.X509()
    cert.get_subject().C = "RU"
    cert.get_subject().ST = "Moscow"
    cert.get_subject().L = "Moscow"
    cert.get_subject().O = "Algoritmika"
    cert.get_subject().OU = "Development"
    cert.get_subject().CN = "127.0.0.1"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # 1 год
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')
    
    # Сохраняем сертификат и ключ
    with open("cert.pem", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open("key.pem", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    print("Сертификат создан: cert.pem и key.pem")

if __name__ == "__main__":
    create_self_signed_cert() 