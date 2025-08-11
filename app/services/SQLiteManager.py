import sqlite3
import threading

class SQLiteManager:
    def __init__(self, db_path, use_wal=True):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.use_wal = use_wal

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        if self.use_wal:
            conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def execute(self, sql, params=None, fetch=False, many=False, fetch_one=False):
        """通用 SQL 执行接口，支持查询或写入"""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if many and params:
                    cursor.executemany(sql, params)
                else:
                    cursor.execute(sql, params or [])
                if fetch_one:
                    return cursor.fetchone()
                elif fetch:
                    result = cursor.fetchall()
                else:
                    conn.commit()
                    result = None
                cursor.close()
                return result
            finally:
                conn.close()

    def create_table(self, table_sql):
        """执行建表语句"""
        self.execute(table_sql)

    def insert(self, table, data: dict):
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        return self.execute(sql, list(data.values()))

    def update(self, table, data: dict, where: str, where_args: list):
        set_clause = ', '.join([f"{k}=?" for k in data])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        return self.execute(sql, list(data.values()) + where_args)

    def delete(self, table, where: str, where_args: list):
        sql = f"DELETE FROM {table} WHERE {where}"
        return self.execute(sql, where_args)

    def select(self, table, where: str = "", where_args: list = None):
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return self.execute(sql, where_args or [], fetch=True)

    def select_one(self, table, where: str = "", where_args: list = None):
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return self.execute(sql, where_args or [], fetch=True, fetch_one=True)