from typing import Optional, Dict, List

from common.db.sql_client import SqlClient, Session
from svoe_airflow.db.models import DagConfigEncoded


class DagsSqlClient(SqlClient):
    def __init__(self):
        super(DagsSqlClient, self).__init__()

    def save_db_config_encoded(
        self,
        owner_id: str,
        dag_name: str,
        dag_config_encoded: str
    ):
        item = DagConfigEncoded(
            owner_id=owner_id,
            dag_name=dag_name,
            dag_config_encoded=dag_config_encoded,
        )
        session = Session()
        session.add(item)
        session.commit()

    def select_all_configs(self) -> List[DagConfigEncoded]:
        session = Session()
        return session.query(DagConfigEncoded).all()

    def select_configs(self, owner_id: str) -> List[DagConfigEncoded]:
        session = Session()
        return session.query(DagConfigEncoded).filter(DagConfigEncoded.owner_id == owner_id).all()

    def delete_configs(self, owner_id: str):
        session = Session()
        session.query(DagConfigEncoded).filter(DagConfigEncoded.owner_id == owner_id).delete()
        session.commit()

    def report_compilation_error(self, dag_name: str, error: str):
        session = Session()
        conf = session.query(DagConfigEncoded).filter(DagConfigEncoded.dag_name == dag_name).first()
        conf.compilation_error = error
        session.commit()

    def get_compilation_error(self, dag_name) -> Optional[str]:
        session = Session()
        conf = session.query(DagConfigEncoded).filter(DagConfigEncoded.dag_name == dag_name).first()
        return conf.compilation_error
