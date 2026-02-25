import sqlite3 as sql
import json

class Database:
    def __init__(self, *, create=False) -> None:
        self.db = sql.connect("db.sqlite3", check_same_thread=False)
        self.db.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.db.cursor()
        self.schema = self._generate_schema("schema.json")
        if create:
            for table in self.schema:
                cols = self.schema[table]
                colstring = ", ".join([f"{key} {cols[key]}" for key in cols])
                self._run(f"DROP TABLE IF EXISTS {table};")
                self._run(f"CREATE TABLE {table} ({colstring});")
                
    def insert(self, table: str, args: list):
        assert table in self.schema
        placeholders = ", ".join(["?"] * len(args))
        cols = ", ".join([k for k in self.schema[table].keys() if k != "id"])
        print(cols)
        self._run_param(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", args)
        self._commit()
    
    def update(self, table: str, row_id: int, updates: dict) -> bool:
        assert table in self.schema

        # checks primary key id is not being updated
        updates = {k: v for k, v in updates.items() if k != "id"}
        if not updates:
            return False

        fields = []
        values = []

        for col, val in updates.items():
            fields.append(f"{col} = ?")
            values.append(val)

        values.append(row_id)


        # dynamic update query
        sql = f"""
            UPDATE {table}
            SET {", ".join(fields)}
            WHERE id = ?
        """

        self._run_param(sql, tuple(values))
        self._commit()

        return True
    

    def delete(self, table: str, id: int):
        assert table in self.schema
        self._run_param(f"DELETE FROM {table} WHERE id = ?", (id, ))
        self._commit()


    def select(self, table: str, where: str):
        assert table in self.schema
        cursor = None
        match where:
            case "all":
                cursor = self._run(f"SELECT * FROM {table}")
            case _:
                cursor = self._run(f"SELECT * FROM {table}")
        return cursor.fetchall()
        
    def _run(self, s:str) -> sql.Cursor:
        print(s)
        return self.cursor.execute(s)

    def _run_param(self, s:str, params:list) -> sql.Cursor:
        print(s, params)
        return self.cursor.execute(s, params)

    def _commit(self) -> None:
        self.db.commit()

    def _generate_schema(self, filename: str) -> dict:
        with open(filename, "r", encoding="UTF-8") as f:
            schema = json.load(f)
            return schema

if __name__ == "__main__":
    db = Database(create=True)
    
    db.insert("goals", ["run a 5k", "fitness", "completion", "testdate", "testdate2", "Rajt"])
    print(db.select("goals", "all"))
    db.update("goals", 1, {"name": "run a 10k", "user": "RajtRuns"}) 
    print(db.select("goals", "all"))

    # db.insert("tablename", ["", ""])