from pathlib import Path

import pymysql

OUTPUT = Path("docker/db/init.sql")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

conn = pymysql.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="Thanglong2001",
    database="cenvi_audit",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.Cursor,
    read_timeout=300,
    write_timeout=300,
    connect_timeout=30,
)

with conn:
    with conn.cursor() as cur, OUTPUT.open("w", encoding="utf-8") as f:
        f.write("SET NAMES utf8mb4;\n")
        f.write("SET FOREIGN_KEY_CHECKS=0;\n")
        f.write("CREATE DATABASE IF NOT EXISTS `cenvi_audit`;\n")
        f.write("USE `cenvi_audit`;\n\n")

        cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            cur.execute(f"SHOW CREATE TABLE `{table}`")
            create_stmt = cur.fetchone()[1]
            f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
            f.write(create_stmt + ";\n\n")

            conn.ping(reconnect=True)
            with conn.cursor(pymysql.cursors.SSCursor) as stream_cur:
                stream_cur.execute(f"SELECT * FROM `{table}`")
                if not stream_cur.description:
                    continue

                columns = [desc[0] for desc in stream_cur.description]
                col_sql = ", ".join(f"`{c}`" for c in columns)

                while True:
                    batch = stream_cur.fetchmany(1000)
                    if not batch:
                        break
                    for row in batch:
                        values = ", ".join(conn.escape(value) for value in row)
                        f.write(f"INSERT INTO `{table}` ({col_sql}) VALUES ({values});\n")
            f.write("\n")

        f.write("SET FOREIGN_KEY_CHECKS=1;\n")

print(f"Exported MySQL dump to {OUTPUT}")
