import psycopg2
from psycopg2 import sql

your_user = 'postgres'
your_password = 'postgres'


class DatabaseInitializer:
    def __init__(self, dbname='sattelites', user=your_user, password=your_password, host='localhost', port='5432'):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

    def create_database_if_not_exists(self):
        ###Создаем базу данных, если она не существует"""
        try:
            # Подключаемся к postgres для создания новой базы данных, если её ещё нет
            conn = psycopg2.connect(
                dbname='postgres',
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            conn.autocommit = True
            print("Connected to 'postgres'. Checking if database exists...")

            with conn.cursor() as cur:
                cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{self.dbname}'")
                if not cur.fetchone():
                    cur.execute(sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'").format(sql.Identifier(self.dbname)))
                    print(f"Database '{self.dbname}' created.")
                else:
                    print(f"Database '{self.dbname}' already exists.")
            conn.close()
        except Exception as e:
            print(f"Error creating database: {e}")

    def connect_to_db(self):
        """Подключаемся к базе данных 'sattelites'"""
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.connection.autocommit = True
            print(f"Connected to the database '{self.dbname}'.")
        except Exception as e:
            print(f"Error connecting to the database '{self.dbname}': {e}")

    def create_table_if_not_exists(self):
        """Создаем таблицу 'sattelites', если она не существует"""
        try:
            if self.connection:
                with self.connection.cursor() as cur:
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS sattelites (
                            NORAD_ID INT PRIMARY KEY,          -- Номер спутника, определенный вручную
                            SATNAME VARCHAR(100) NOT NULL,     -- Название спутника
                            TLE_coords VARCHAR(100) UNIQUE NOT NULL,  -- Уникальные координаты TLE
                            EXTRA INT                         -- Дополнительное поле
                        );
                    ''')
                    print("Table 'sattelites' created or already exists.")
            else:
                print("Connection to the database not established.")
        except Exception as e:
            print(f"Error creating table: {e}")

    def initialize(self):
        """Инициализация базы данных и таблицы"""
        self.create_database_if_not_exists()
        self.connect_to_db()
        self.create_table_if_not_exists()
        
        
# Пример использования
if __name__ == "__main__":
    db_initializer = DatabaseInitializer()
    db_initializer.initialize()