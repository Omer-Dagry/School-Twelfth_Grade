from SyncDB import FileDatabase, SyncDatabase

chat_id_name_file_db = FileDatabase("chat_id_name", ignore_existing=True)
chat_id_name_db = SyncDatabase(chat_id_name_file_db, False, max_reads_together=100)
print("100" in chat_id_name_db)
chat_id_name_db["100"] = 5
print("100" in chat_id_name_db)
print(chat_id_name_db["100"])
print(chat_id_name_db.get("100"))
try:
    print(chat_id_name_db[100])
except:
    raise
print(chat_id_name_db.get(100))
