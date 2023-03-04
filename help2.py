import json
from collections import defaultdict

import requests


SKILLZ = "https://coding.skillz-edu.org"
BLOB_NAME_URL = SKILLZ + "/backend/api/run?bot_id=0&category=ttw&guid="
SKILLZ_RESULT_URL = "https://codez.blob.core.windows.net/replays/"


guids = [1059936, 1060061, 1060105, 1061132, 1061172, 1061293, 1061465, 1061488, 1061644, 1061672, 1063241, 1063289, 1063349, 1063398, 1063451, 1063514, 1063577, 1063653, 1063731, 1063790, 1063849, 1063928, 1063986, 1064012, 1064041, 1064089, 1064834, 1064837, 1064844, 1064854, 1064872, 1064882, 1064884, 1064896, 1064918, 1064926, 1064971, 1065015]
groups_guids = defaultdict(list)


for guid in guids:
    res = requests.get(BLOB_NAME_URL + str(guid))
    res = json.loads(res.content)
    blob = res["blob_name"]
    res = requests.get(SKILLZ_RESULT_URL + blob)
    res = json.loads(res.content)
    other_group = res["winnerNames"][0]
    groups_guids[other_group].append(guid)


for group_name, guids in groups_guids.items():
    print(f"{group_name}: {guids}")
