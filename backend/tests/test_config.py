"""Test configuration - sets up environment variables before any app imports."""

from dotenv import load_dotenv
import os

load_dotenv()

# Set test environment variables BEFORE any app modules are imported
os.environ["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "http://127.0.0.1:54331")
os.environ["SUPABASE_ANON_KEY"] = os.getenv("SUPABASE_ANON_KEY")
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@127.0.0.1:54330/postgres")
os.environ["APP_ENV"] = "test"