from decouple import config
from supabase import create_client, Client

def get_supabase_clients():
    url = config('SUPABASE_URL')
    anon_key = config('SUPABASE_KEY')
    admin_key = config('SUPABASE_SERVICE_KEY')

    supabase_anon: Client = create_client(url, anon_key)
    supabase_admin: Client = create_client(url, admin_key)
    return supabase_anon, supabase_admin

# Initialize clients
supabase_anon, supabase_admin = get_supabase_clients()
