import asyncio
import importlib
import pkgutil

from sqlalchemy import MetaData

from app.core.database import Base as Base1
from app.core.database import async_engine as engine
from app.db import models
from app.db.base_class import Base as Base2


async def init_all_tables():
    print("Importing all models to register with Base objects...")
    # Dynamically import all modules in app.db.models
    for loader, module_name, is_pkg in pkgutil.walk_packages(
        models.__path__, models.__name__ + "."
    ):
        importlib.import_module(module_name)

    print("Creating all missing tables...")

    # Combine metadata
    combined_metadata = MetaData()
    for table in Base1.metadata.tables.values():
        table.tometadata(combined_metadata)
    for table in Base2.metadata.tables.values():
        table.tometadata(combined_metadata)

    async with engine.begin() as conn:
        await conn.run_sync(combined_metadata.create_all)
    print("Tables created successfully.")


if __name__ == "__main__":
    asyncio.run(init_all_tables())
