from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
from app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

# Strip channel_binding if present
if "channel_binding=" in db_url:
    import urllib.parse as urlparse
    parsed = urlparse.urlparse(db_url)
    query = urlparse.parse_qs(parsed.query)
    query.pop('channel_binding', None)
    new_query = urlparse.urlencode(query, doseq=True)
    db_url = urlparse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))


# Configure connect_args based on database type
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Use ssl_context = True to require SSL when connecting via pg8000
    connect_args = {"ssl_context": True}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """Dependency for API endpoints to get a DB session.
    Closes the session after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
