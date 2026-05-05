"""
SQLite dan Azure SQL ga ma'lumotlarni ko'chirish skripti.
Bu skript:
1. Azure SQL da jadvallar yaratadi (Customers, History)
2. Mavjud SQLite bazasidan barcha ma'lumotlarni Azure SQL ga yuklaydi
"""

import sqlite3
import pyodbc
from config import get_connection_string

SQLITE_PATH = "database.db"


def create_azure_tables(cursor):
    """Azure SQL da jadvallar yaratish"""
    
    # Agar jadvallar mavjud bo'lsa, o'chirish
    cursor.execute("""
        IF OBJECT_ID('History', 'U') IS NOT NULL DROP TABLE History;
        IF OBJECT_ID('Customers', 'U') IS NOT NULL DROP TABLE Customers;
    """)
    
    # Customers jadvali
    cursor.execute('''
        CREATE TABLE Customers (
            Id INT IDENTITY(1,1) PRIMARY KEY,
            FullName NVARCHAR(255) NOT NULL,
            Gender NVARCHAR(50),
            Balance INT DEFAULT 0
        )
    ''')
    
    # History jadvali
    cursor.execute('''
        CREATE TABLE History (
            Id INT IDENTITY(1,1) PRIMARY KEY,
            SenderId INT,
            ReceiverId INT,
            Amount INT,
            Date DATETIME DEFAULT GETDATE(),
            FOREIGN KEY (SenderId) REFERENCES Customers(Id),
            FOREIGN KEY (ReceiverId) REFERENCES Customers(Id)
        )
    ''')
    
    print("Azure SQL da jadvallar yaratildi!")


def migrate_data():
    """SQLite dan Azure SQL ga ma'lumotlarni ko'chirish"""
    
    # SQLite ga ulanish
    print("SQLite bazasidan ma'lumotlar o'qilmoqda...")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    customers = sqlite_conn.execute("SELECT * FROM Customers").fetchall()
    history = sqlite_conn.execute("SELECT * FROM History").fetchall()
    sqlite_conn.close()
    
    print(f"   Mijozlar soni: {len(customers)}")
    print(f"   Tarix yozuvlari: {len(history)}")
    
    # Azure SQL ga ulanish
    print("\nAzure SQL ga ulanilmoqda...")
    azure_conn = pyodbc.connect(get_connection_string())
    azure_cursor = azure_conn.cursor()
    
    # Jadvallar yaratish
    create_azure_tables(azure_cursor)
    azure_conn.commit()
    
    # IDENTITY_INSERT yoqish (Id larni saqlab qolish uchun)
    print("\nMijozlar yuklanmoqda...")
    azure_cursor.execute("SET IDENTITY_INSERT Customers ON")
    
    for c in customers:
        azure_cursor.execute(
            "INSERT INTO Customers (Id, FullName, Gender, Balance) VALUES (?, ?, ?, ?)",
            (c["Id"], c["FullName"], c["Gender"], c["Balance"])
        )
    
    azure_cursor.execute("SET IDENTITY_INSERT Customers OFF")
    azure_conn.commit()
    print(f"   OK: {len(customers)} ta mijoz yuklandi!")
    
    # History ma'lumotlarini yuklash
    print("\nTarix yozuvlari yuklanmoqda...")
    azure_cursor.execute("SET IDENTITY_INSERT History ON")
    
    for h in history:
        azure_cursor.execute(
            "INSERT INTO History (Id, SenderId, ReceiverId, Amount, Date) VALUES (?, ?, ?, ?, ?)",
            (h["Id"], h["SenderId"], h["ReceiverId"], h["Amount"], h["Date"])
        )
    
    azure_cursor.execute("SET IDENTITY_INSERT History OFF")
    azure_conn.commit()
    print(f"   OK: {len(history)} ta tarix yozuvi yuklandi!")
    
    azure_conn.close()
    print("\nBarcha ma'lumotlar Azure SQL ga muvaffaqiyatli ko'chirildi!")
    print("=" * 50)
    print("Endi app.py ni ishga tushirishingiz mumkin.")
    print("Ma'lumotlaringiz bulutda xavfsiz saqlangan!")


if __name__ == "__main__":
    migrate_data()
