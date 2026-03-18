from pathlib import Path
from typing import Optional
import datetime

from sqlmodel import Field, Session, SQLModel, create_engine, select

# Table 1 - Experiments 

class Experiment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str = ""
    
    created_at: str = Field(default_factory = lambda:datetime.datetime.utcnow().isoformat())
    
class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True, unique=True)
    name: str
    experiment: str = Field(default="default")
    status: str = Field(default="running")
    tags: str = Field(default="")
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat()
    )
    finished_at: Optional[str] = Field(default=None)
    duration_sec: Optional[float] = Field(default=None)
    
class Metric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    key: str
    value: float
    step: int = Field(default=0)
    logged_at: str = Field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat()
    )
    
class Param(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Which run this param belongs to
    run_id: str = Field(index=True)

    # Param name: "learning_rate", "depth", "optimizer" etc
    key: str

    # Always stored as string — handles int, float, bool, str uniformly
    # "0.05", "6", "True", "adam" — all stored the same way
    value: str
    
# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────

def find_db() -> Path:
    """
    Walk up from the current directory to find .mlx/mlx.db
    
    This lets you run mlx commands from anywhere inside your project,
    not just from the root folder. Same idea as how git works —
    you can run `git status` from any subfolder.
    """
    cwd = Path.cwd()

    # Check current folder, then parent, then grandparent, etc.
    for directory in [cwd, *cwd.parents]:
        db_path = directory / ".mlx" / "mlx.db"
        if db_path.exists():
            return db_path

    # If we walked all the way to / and found nothing
    raise FileNotFoundError(
        "No mlx project found.\n"
        "Run 'mlx init' first to initialize a project."
    )


def get_engine(db_path: Optional[Path] = None):
    """
    Create a SQLAlchemy engine connected to the SQLite database.
    
    The engine is the core connection to the database.
    You use it to create sessions (individual transactions).
    """
    path = db_path or find_db()
    return create_engine(
        f"sqlite:///{path}",
        echo=False,       # Set True to see raw SQL in terminal (useful for debugging)
    )


def init_db(db_path: Path):
    """
    Create all tables in a fresh database.
    
    Called once by `mlx init`.
    Safe to call multiple times — won't delete existing data.
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    # This reads all classes with `table=True` and creates their tables
    SQLModel.metadata.create_all(engine)

    return engine


def get_session(db_path: Optional[Path] = None) -> Session:
    """
    Open a database session — your connection for reading/writing.

    Always use this as a context manager:
        with get_session() as session:
            session.add(something)
            session.commit()
    
    The 'with' block automatically closes the connection when done,
    even if an error occurs.
    """
    engine = get_engine(db_path)
    return Session(engine)