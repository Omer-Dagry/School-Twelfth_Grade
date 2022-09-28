import datetime
import hashlib
import itertools

ABC = "abcdefghigklmnopqrstuvwxyz"
NUMBERS = "1234567890"
SIGNS = "!?:|\\/.,<>;'@#$%^&*(){}[]~`" + '"'
# 3735928559

md5_hash = "EC9C0F7EDCC18A98B1F31853B1813301".lower()
message = ""
exit()
print(datetime.datetime.now())
for option in itertools.product(NUMBERS, repeat=10):
    if hashlib.md5("".join(option).encode('utf-8')).hexdigest() == md5_hash:
        message = "".join(option)
        break
print(datetime.datetime.now())
print(message)
