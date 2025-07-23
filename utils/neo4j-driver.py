from neo4j import GraphDatabase
import os
import atexit

class Neo4jDriver:
    _instance = None

    def __init__(self):
        if Neo4jDriver._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.driver = GraphDatabase.driver(
                uri=os.environ["NEO4J_URI"],
                auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
            )
            Neo4jDriver._instance = self

    @staticmethod
    def get_instance():
        if Neo4jDriver._instance is None:
            Neo4jDriver()
        return Neo4jDriver._instance

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    def get_driver(self):
        return self.driver

def get_neo4j_driver():
    return Neo4jDriver.get_instance().get_driver()

def close_neo4j_driver():
    Neo4jDriver.get_instance().close()

# Register the close function to be called when the program exits
atexit.register(close_neo4j_driver)
