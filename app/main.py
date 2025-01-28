from fastapi import FastAPI
from decouple import config
from supabase import create_client, Client

url = config('SUPABASE_URL')
key = config('SUPABASE_KEY')
admin_key = config('SUPABASE_SERVICE_KEY')

app = FastAPI()
supabase_anon: Client = create_client(url, key)
supabase_admin: Client = create_client(url, admin_key)

@app.get("/admin/journal-entries")
def get_journal_entries():
    journal_entries = supabase_admin.table('journal_entries').select("*").execute()
    return journal_entries

@app.get("/journal-entries")
def get_journal_entries():
    journal_entries = supabase_anon.table('journal_entries').select("*").execute()
    return journal_entries