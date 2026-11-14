"""Test configuration - sets up environment variables before any app imports."""

import os

# Set test environment variables BEFORE any app modules are imported
os.environ["SUPABASE_URL"] = "http://127.0.0.1:54331"
os.environ["SUPABASE_ANON_KEY"] = "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "sb_secret_N7UND0UgjKTVK-Uodkm0Hg_xSvEMPvz"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:54330/postgres"
os.environ["APP_ENV"] = "test"