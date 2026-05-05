# Azure SQL Database Configuration
# Fotima's Bank Application - Azure SQL

AZURE_SQL = {
    "server": "fotima-bank-server.database.windows.net",
    "database": "BankDB",
    "username": "sqladmin",
    "password": "BankLoyiha2026!",
    "driver": "{ODBC Driver 17 for SQL Server}"
}

def get_connection_string():
    """Azure SQL uchun connection string qaytaradi"""
    return (
        f"DRIVER={AZURE_SQL['driver']};"
        f"SERVER={AZURE_SQL['server']};"
        f"DATABASE={AZURE_SQL['database']};"
        f"UID={AZURE_SQL['username']};"
        f"PWD={AZURE_SQL['password']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
