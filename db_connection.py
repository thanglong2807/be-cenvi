#!/usr/bin/env python3
"""
Database connection utility for cenvi_audit (local development)
"""
import mysql.connector
from mysql.connector import Error
import sys
import codecs

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': '123456',
    'database': 'cenvi_audit',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True
}

class DBConnection:
    """Database connection manager"""

    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor(dictionary=True)
            print("✅ Database connection successful!")
            return True
        except Error as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Connection closed")

    def execute_query(self, query, params=None):
        """Execute SELECT query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"❌ Query error: {e}")
            return None

    def execute_update(self, query, params=None):
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            print(f"✅ Affected rows: {self.cursor.rowcount}")
            return self.cursor.rowcount
        except Error as e:
            print(f"❌ Update error: {e}")
            self.connection.rollback()
            return 0

    def get_company_count(self):
        """Get total company count"""
        result = self.execute_query("SELECT COUNT(*) as total FROM COMPANY_INFO")
        if result:
            return result[0]['total']
        return 0

    def get_company_by_code(self, ma_kh):
        """Get company by code"""
        query = "SELECT * FROM COMPANY_INFO WHERE ma_kh = %s"
        result = self.execute_query(query, (ma_kh,))
        if result:
            return result[0]
        return None

    def get_all_companies(self, limit=None):
        """Get all companies"""
        if limit:
            query = f"SELECT * FROM COMPANY_INFO LIMIT {limit}"
        else:
            query = "SELECT * FROM COMPANY_INFO"
        return self.execute_query(query)


def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("Testing Database Connection to cenvi_audit")
    print("=" * 60)
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Port: {DB_CONFIG['port']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Database: {DB_CONFIG['database']}")
    print("=" * 60)
    print()

    db = DBConnection()

    if not db.connect():
        return

    # Get company count
    total = db.get_company_count()
    print(f"Total companies in database: {total}")
    print()

    # Get sample companies
    print("Sample companies (first 5):")
    print("-" * 60)
    companies = db.get_all_companies(limit=5)
    if companies:
        for company in companies:
            print(f"  {company['ma_kh']}: {company['ten_cong_ty']}")
            print(f"    Tax ID: {company['ma_so_thue']}")
            print(f"    Person in charge: {company.get('phu_trach_hien_tai', 'N/A')}")
            print(f"    Email: {company.get('pmkt_tai_khoan', 'N/A')}")
            print()

    # Test specific company
    print("Test query by code (2026KH28):")
    print("-" * 60)
    company = db.get_company_by_code('2026KH28')
    if company:
        print(f"Found: {company['ten_cong_ty']}")
        print(f"  Ma_kh: {company['ma_kh']}")
        print(f"  MST: {company['ma_so_thue']}")
        print(f"  Person in charge: {company.get('phu_trach_hien_tai', 'N/A')}")
    else:
        print("Company not found")

    print()
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

    db.disconnect()


if __name__ == '__main__':
    test_connection()
