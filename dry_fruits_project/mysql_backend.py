from django.db.backends.mysql import base, features

class DatabaseFeatures(features.DatabaseFeatures):
    # Override the version check
    supports_transactions = True
    # Add any other features you need to override

class DatabaseWrapper(base.DatabaseWrapper):
    features_class = DatabaseFeatures

    def get_new_connection(self, conn_params):
        # Call the original method to get a connection
        connection = super().get_new_connection(conn_params)
        return connection

    def init_connection_state(self):
        # Skip the version check in the parent method
        with self.cursor() as cursor:
            # Set the transaction isolation level
            cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
        
        # Initialize the connection properly
        self.connection.set_charset('utf8mb4')
        self.connection.autocommit(False)
