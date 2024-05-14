from django.db import connection
from django.db.migrations.executor import MigrationExecutor


class Migrator:
    def __init__(self, connection=connection):
        self.executor = MigrationExecutor(connection)

    def migrate(self, app_label: str, migration: str):
        target = [(app_label, migration)]
        self.executor.loader.build_graph()
        self.executor.migrate(target)
        self.apps = self.executor.loader.project_state(target).apps
