from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import database as db


db.init_db() # Initialize the database and seed it with initial data if empty
app = FastAPI(title="TimeTrack", description="A simple time tracking app with REST and MCP endpoints.", version="1.0.0")

@app.get("/api/entries")
def api_list_all_entries():
    """List all time entries in the database."""
    return db.list_all_entries()
