from pyDes import triple_des



charset = "utf-8"
password = b'Tsc\xcf\\\x8c5\x99\xfd\x879\xd0\x1b\x04\n`'
decrypted_password = triple_des('ABCDEFRTGHJSKLDS').decrypt(bytes(password), padmode=2)
print(str(decrypted_password, "utf-8"))