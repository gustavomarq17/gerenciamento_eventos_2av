import os
from supabase import create_client, Client
# [2AV] URL e chave agora vêm do .env (via app/core/config.py), em vez de ficarem
# fixas no código. Também foi removido o print de debug.
from app.core.config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
