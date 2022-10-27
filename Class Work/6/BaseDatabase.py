class BaseDatabase:
    def __init__(self):
        self.dic = {}

    def set_value(self, key, val):
        try:
            self.dic[key] = val
            return True
        except Exception:
            return False

    def get_value(self, key):
        if key in self.dic.keys():
            val = self.dic[key]
        else:
            val = None
        return val

    def delete_value(self, key):
        if key in self.dic.keys():
            val = self.dic[key]
            self.dic.pop(key)
        else:
            val = None
        return val
