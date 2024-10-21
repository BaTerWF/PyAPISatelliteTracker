import psycopg2 as psdb
from psycopg2 import sql
import os
from loguru import logger
import datetime


#Тут пока все норм
class Database:
    def __init__(self, host, database, user, password, port=5432, schema_file='SQL/create_database.sql'):
        try:
            self.db = psdb.connect(
                host=host,
                dbname=database,
                user=user,
                password=password,
                port=port
            )
            self.cursor = self.db.cursor()
            self.ensure_tables_exist(schema_file)
            self.run_migrations('SQL')
        except Exception as e:
            print('Connection failed')
            print(f'host: {host}, database: {database}, user: {user}, port: {port}')
            raise e

    def run_migrations(self, migrations_folder):
        try:
            for file in sorted(list(os.listdir(migrations_folder))):
                if file.endswith('.sql'):
                    with open(os.path.join(migrations_folder, file), 'r') as f:
                        logger.info(f"Running migration: {file}")
                        self.cursor.execute(f.read())
                        self.db.commit()
        except Exception as e:
            print("An error occurred while running migrations.")
            self.db.rollback()
            raise e

    def ensure_tables_exist(self, schema_file):
        try:
            with open(schema_file, 'r') as file:
                schema = file.read()
            self.cursor.execute(schema)
            self.db.commit()
        except Exception as e:
            print("An error occurred while creating tables.")
            self.db.rollback()
            raise e
    def execute(self, query, args=()):
        try:
            self.cursor.execute(query, args)
            self.db.commit()
            try:
                return self.cursor.fetchall()
            except psdb.ProgrammingError:
                return None
        except Exception as e:
            self.db.rollback()
            print(f"An error occurred: {e}")
            raise e
    def insert_tle(self, satellite_name, line1, line2):
        try:
            norad_id = line1[2:7].strip()

            query = sql.SQL("""
                INSERT INTO "Satelite".tle_data (satellite_name, line1, line2, norad_id, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (norad_id) 
                DO UPDATE SET
                    satellite_name = EXCLUDED.satellite_name,
                    line1 = EXCLUDED.line1,
                    line2 = EXCLUDED.line2,
                    timestamp = EXCLUDED.timestamp
            """)
            self.execute(query, (satellite_name, line1, line2, norad_id, datetime.datetime.utcnow()))
            logger.info(f"Successfully inserted/updated TLE data for {satellite_name} (NORAD ID: {norad_id})")

        except Exception as e:
            logger.error(f"Failed to insert/update TLE data for {satellite_name}: {str(e)}")
            raise e

    def get_tle_by_name_or_norad(self, satelliteName=None, noradID=None):
        try:
            if satelliteName:
                query = sql.SQL("""
                    SELECT satellite_name, line1, line2
                    FROM "Satelite".tle_data
                    WHERE satellite_name = %s
                """)
                self.cursor.execute(query, (satelliteName,))
            elif noradID:
                query = sql.SQL("""
                    SELECT satellite_name, line1, line2
                    FROM "Satelite".tle_data
                    WHERE norad_id = %s
                """)
                self.cursor.execute(query, (noradID,))
            else:
                return None

            result = self.cursor.fetchone()
            if result:
                return {
                    "satellite_name": result[0],
                    "line1": result[1],
                    "line2": result[2]
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching TLE data: {str(e)}")
            raise e