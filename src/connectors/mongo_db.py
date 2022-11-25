# pylint: disable=line-too-long
"""
Mongodb database management
"""
import ast
from contextlib import suppress
from typing import Dict, List, Optional

import pymongo
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
    WriteConcernError,
    WriteError,
)
from utils.util import get_env
from log.logger import Logs, Color

load_dotenv()
log = Logs()


class TextMongoDatabase:
    """
    Handle Database Operations
    """

    # Number of retries to access the database when it is not available
    NUMBER_OF_RETRIES = ast.literal_eval(
        get_env("NUMBER_OF_RETRIES_TO_ACCESS_DATABASE")
    )

    def __init__(self, collection: str = get_env("DATABASE_COLLECTION_NAME")) -> None:
        self.user = get_env("DATABASE_USER")
        self.password = get_env("DATABASE_PASSWORD")
        self.host = get_env("DATABASE_HOST")
        self.port = int(get_env("DATABASE_PORT"))
        self.colname = collection
        self.database = None
        self.collection = None
        self.conn = None
        self.connect(self.colname)

    def _connect(self, collection: str):
        """Create a connection to the mongodb
        set the database and collection
        """

        self.conn = MongoClient(
            f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/admin?authSource=admin&authMechanism=SCRAM-SHA-1"
        )
        self.database = self.conn[get_env("DATABASE_NAME")]
        self.collection = self.database[collection]
        Logs().info(f"Connected to {self.colname} collection")

    def ping(self) -> bool:
        """Check if the connection is alive"""
        if self.conn is not None and self.conn.server_info():
            return True
        return False

    def connect(self, collection) -> bool:
        """Create a connection to the mongodb

        Returns:
            bool: True if the connection is successful, otherwise False
        """
        for _ in range(self.NUMBER_OF_RETRIES):
            if self.conn is None:
                self._connect(collection)
            with suppress(
                ConnectionFailure, AutoReconnect, ServerSelectionTimeoutError
            ):
                if self.conn is not None and self.conn.server_info():
                    return True
                self._connect(collection)
        Logs().warn("Insertion Denied Due to: Connection Error")
        return False

    def insert_many(self, data: list) -> None:
        """Insert multiple requests (tests) to the database"""
        if self.connect(self.colname):
            try:
                self.collection.insert_many(data)
                Logs().info(f"Inserting {len(data)} records ends with success")
            except (Exception) as e:
                Logs().warn(f"Insertion Denied Due to: {e}")

    def insert_text(self, data: Dict) -> None:
        """Insert records to the mongodb

        Args:
            data (Dict): dictionary of the inserted data
        """
        if self.connect(self.colname):
            try:
                self.collection.insert_one(data)
                Logs().info("Inserting One record ends with success")
            except (WriteConcernError, WriteError) as e:
                Logs().info(f"Insertion Denied Due to: {e}")

    def select_(self, cond: dict = None) -> Optional[dict]:
        """get an inserted raw from mongo

        Args:
            value (str, optional): the value which the selection
            would be based on. Defaults to None.

        Returns:
            _type_: get the inserted raw from data based on the given value,
            otherwise, the last insertion
        """
        if self.connect(self.colname):
            if cond is not None:
                return self.collection.find_one(cond)
            return self.collection.find_one({}, sort=[("_id", pymongo.DESCENDING)])
        Logs.warn("Select Failed: Connection Error")
        return None

    def read_all(self, condition: dict, limit: int = None) -> List[dict]:
        """Read all records from the database"""
        if self.connect(self.colname):
            if limit:
                return list(self.collection.find(condition).limit(limit))
            return list(self.collection.find(condition))
        return []

    def update(self, my_query: Dict = None, new_values: Dict = None) -> None:
        """Insert new column on mongo with special query as dictionary"""
        if self.connect(self.colname):
            try:
                self.collection.update_one(my_query, {"$set": new_values})
                Logs().info("Updating one row end with success")
            except OperationFailure as err:
                Logs().info(f"UpdateFailed: {err}")
        else:
            Logs().warn("UpdateFailed: Connection Error")

    def delete_duplicate(self):
        """delete all duplicated records from mongodb and preserve the last one.
        >>> {'_id': {'media_id': '47517972'}, 'duplicates': [ObjectId('62654716754ecaad6159fcbf'),
            ObjectId('626677adfe0435a843932cc9')], 'total': 2}
        >>> deleted record: 62654716754ecaad6159fcbf
        """
        Logs().info(f"delete duplicates from {self.collection.name} | start")
        if self.connect(self.colname):
            replicas = self.collection.aggregate(
                [
                    {
                        "$group": {
                            "_id": {"media_id": "$media_id"},
                            "duplicates": {"$addToSet": "$_id"},
                            "total": {"$sum": 1},
                        }
                    },
                    {"$match": {"total": {"$gt": 1}}},
                ],
                allowDiskUse=True,
            )
            for replica in replicas:
                for object_id in replica["duplicates"][:-1]:
                    self.collection.delete_one({"_id": object_id})
            Logs().warn(f"delete duplicates from {self.collection.name} | end")
