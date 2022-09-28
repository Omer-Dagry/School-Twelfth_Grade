import hashlib
import itertools


ABC = "abcdefghigklmnopqrstuvwxyz"
NUMBERS = "1234567890"
SIGNS = "!?:|\\/.,<>;'@#$%^&*(){}[]~`" + '"'


md5_hash = "EC9C0F7EDCC18A98B1F31853B1813301".lower()
message = ""
for option in itertools.product(ABC + NUMBERS, repeat=10):
    if hashlib.md5("".join(option).encode('utf-8')).hexdigest() == md5_hash:
        message = "".join(option)
        break
print(message)
