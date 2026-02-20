import sqlite3 as sql

class Database:
    def __init__(self, name: str) -> None:
        self.name = name
        # self.db = sql.connect(name, check_same_thread=False)
        # self.cursor = self.db.cursor()
        self.run("CREATE TABLE IF NOT EXISTS <table> ( \
                    title TEXT, \
                    tags TEXT, \
                    i_date_created INTEGER, \
                    date_created TEXT, \
                    date_modified TEXT, \
                    body TEXT \
                    );"
                )
        

    def insert(self, table, args):
        placeholders = ", ".join(["?"] * len(args))
        self.run_param(f"INSERT INTO {table} VALUES ({placeholders})", args)


    def run(self, s:str) -> sql.Cursor:
        # return self.cursor.execute(s)
        print(s)

    def run_param(self, s:str, params:list) -> sql.Cursor:
        # return self.cursor.execute(s, params)
        print(s, params)

if __name__ == "__main__":
    db = Database("test.db")
    db.insert("tablename", ["title", "tags", 1234567890, "2024-01-01", "2024-01-01", "body"])