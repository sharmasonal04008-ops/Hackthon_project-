"""Rebuild newsto.db from the SQL files (deletes old data):   python create_db.py"""
import backend

backend.build_db(reset=True)
print("newsto.db created.")
