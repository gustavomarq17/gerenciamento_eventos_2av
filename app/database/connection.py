import os
from supabase import create_client, Client

SUPABASE_URL = "https://fsndoqjiaxjzgeephod.supabase.co"
SUPABASE_KEY = "sua_chave_publica_aqui"

print(f"DEBUG URL SUPABASE: {SUPABASE_URL}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)