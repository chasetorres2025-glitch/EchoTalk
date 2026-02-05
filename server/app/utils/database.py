import pymysql
from pymongo import MongoClient
from flask import current_app

class MySQLDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MySQLDB, cls).__new__(cls)
        return cls._instance

    def get_connection(self):
        return pymysql.connect(
            host=current_app.config['MYSQL_HOST'],
            port=current_app.config['MYSQL_PORT'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute(self, sql, params=None, fetchone=False):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                conn.commit()
                if fetchone:
                    return cursor.fetchone()
                return cursor.fetchall()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_many(self, sql, params_list):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.executemany(sql, params_list)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class MongoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def init_app(self, app):
        self.client = MongoClient(app.config['MONGO_URI'])
        self.db = self.client.get_default_database()

    def get_collection(self, name):
        return self.db[name]

mysql_db = MySQLDB()
mongo_db = MongoDB()
