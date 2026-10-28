"""COM612 SQLite console: inspect the schema and execute SQL interactively.

Usage:
    python com612_sqlite_console.py
    python com612_sqlite_console.py path/to/another.db

Enter one SQL statement at a time, ending with a semicolon.
Commands: .schema, .tables, .help, .quit
"""

import sqlite3
import sys


def show_schema(connection):
    objects = connection.execute("""
        SELECT type, name, sql
        FROM sqlite_master
        WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    if not objects:
        print("(No tables, views, indexes, or triggers found.)")
        return

    print("\nDATABASE SCHEMA")
    print("=" * 60)
    for object_type, name, sql in objects:
        print(f"-- {object_type}: {name}")
        print(sql.strip().rstrip(";") + ";\n")


def show_tables(connection):
    rows = connection.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()
    print("Tables:", ", ".join(row[0] for row in rows) if rows else "(none)")


def display_results(cursor):
    headings = [description[0] for description in cursor.description]
    rows = cursor.fetchmany(100)
    more_rows = cursor.fetchone() is not None

    values = [["NULL" if value is None else str(value) for value in row] for row in rows]
    widths = [
        max([len(headings[index])] + [len(row[index]) for row in values])
        for index in range(len(headings))
    ]

    print(" | ".join(heading.ljust(widths[index]) for index, heading in enumerate(headings)))
    print("-+-".join("-" * width for width in widths))
    for row in values:
        print(" | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))
    print(f"({len(rows)} row(s) displayed" + (", more rows available" if more_rows else "") + ")")


def execute_sql(connection, sql):
    try:
        cursor = connection.execute(sql)
        if cursor.description is not None:
            display_results(cursor)
        else:
            connection.commit()
            print("Statement executed successfully.")
            if cursor.rowcount >= 0:
                print(f"Rows affected: {cursor.rowcount}")
    except sqlite3.Error as error:
        connection.rollback()
        print(f"SQL error: {error}")


def main():
    database_file = sys.argv[1] if len(sys.argv) > 1 else "sensors.db"
    connection = sqlite3.connect(database_file)
    try:
        # Set up the COM612 example table if it does not already exist.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT,
                topic TEXT,
                payload TEXT
            )
        """)
        connection.commit()

        print(f"Connected to SQLite database: {database_file}")
        print("Enter one SQL statement ending with ';'. Type .help for commands.")
        show_schema(connection)

        statement = ""
        while True:
            try:
                line = input("...> " if statement else "sql> ")
            except EOFError:
                print("\nGoodbye.")
                break
            except KeyboardInterrupt:
                statement = ""
                print("\nStatement cancelled. Type .quit to exit.")
                continue

            command = line.strip().lower()
            if not statement and command.startswith("."):
                if command in (".quit", ".exit"):
                    print("Goodbye.")
                    break
                if command == ".schema":
                    show_schema(connection)
                elif command == ".tables":
                    show_tables(connection)
                elif command == ".help":
                    print("Commands: .schema  .tables  .help  .quit")
                    print("SQL: enter one statement, ending with a semicolon (;).")
                else:
                    print("Unknown command. Type .help for available commands.")
                continue

            statement += line + "\n"
            if sqlite3.complete_statement(statement):
                if statement.strip():
                    execute_sql(connection, statement)
                statement = ""
    finally:
        connection.close()


if __name__ == "__main__":
    main()
