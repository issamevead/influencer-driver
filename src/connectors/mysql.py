import os
from typing import Generator, Union

import pandas
import sqlalchemy as db
from dotenv import load_dotenv

from utils.util import get_env

load_dotenv()


class MySQL:
    CONFIG = {
        "host": get_env("MYSQL_DB_HOST"),
        "port": get_env("MYSQL_DB_PORT"),
        "user": get_env("MYSQL_DB_USER"),
        "password": get_env("MYSQL_DB_PASSWORD"),
        "database": get_env("MYSQL_DB_NAME"),
    }

    def __init__(self) -> None:
        self.db_user = self.CONFIG.get("user")
        self.db_pwd = self.CONFIG.get("password")
        self.db_host = self.CONFIG.get("host")
        self.db_port = self.CONFIG.get("port")
        self.db_name = self.CONFIG.get("database")
        self.connection = self.connect()

    def connect(self):
        """Connect to MySQL database and return a connection object"""
        engine = db.create_engine(
            f"mysql+pymysql://{self.db_user}:{self.db_pwd}@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        return engine.connect()

    def healthy(self):
        """Check if the connection to the database is healthy"""
        try:
            self.connection.execute("SELECT 1")
            return True
        except:
            return False

    def _execute(self, query):
        """Execute a query and return the result"""
        result = self.connection.execute(query)
        return result

    def show_tables(self) -> Generator:
        """Show all tables in the database"""
        query = "SHOW TABLES"
        result = self._execute(query)
        return result

    def get_table(
        self, table_name: str, as_df: bool = False
    ) -> Union[Generator, pandas.DataFrame]:
        """Get a table from the database
        args:
            table_name (str): name of the table to get
            as_df (bool): return the table as a pandas dataframe
        """
        for _ in range(3):
            if self.healthy():
                query = f"SELECT * FROM {table_name.capitalize()}"
                if as_df:
                    return pandas.read_sql(query, self.connection)
                result = self._execute(query)
                return result
        raise ValueError("Connection to database failed")

    def data_checker(self, table_name: str, data: dict) -> bool:
        """Check if data exists in a table
        args:
            table_name (str): name of the table to check
            data (dict): data to check
        """
        # check if table exists
        if table_name not in [table[0] for table in self.show_tables()]:
            raise ValueError(f"Table {table_name} does not exist")
        # check if all keys are in the table
        table = self.get_table(table_name, as_df=True)
        if not all([key in table.columns for key in data.keys()]):
            raise ValueError("Data keys do not match table columns")
        return True

    def insert_to_table(self, table_name: str, data: dict) -> None:
        """Insert data into a table
        args:
            table_name (str): name of the table to insert into
            data (dict): data to insert
        """
        for _ in range(3):
            if self.healthy() and self.data_checker(table_name, data):
                query = f"INSERT INTO {table_name} ({', '.join(data.keys())}) VALUES ({', '.join([f'%({key})s' for key in data.keys()])})"
                self._execute(query, data)
                return
        raise ValueError("Data keys do not match table columns")

    def update_table(self, table_name: str, data: dict, where: str) -> None:
        """Update a table
        args:
            table_name (str): name of the table to update
            data (dict): data to update
            where (str): where clause
        """
        for _ in range(3):
            if self.healthy() and self.data_checker(table_name, data):
                query = f"UPDATE {table_name} SET {', '.join([f'{key} = %({key})s' for key in data.keys()])} WHERE {where}"
                self._execute(query, data)
                return
            raise ValueError("Data keys do not match table columns")

    def close(self):
        """Close the connection to the database"""
        self.connection.close()
