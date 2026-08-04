@pytest.fixture
def test_db_sync() -> Generator[Session, None, None]:
    """
    Create a fresh synchronous database session for each test function
    """
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=sync_test_engine)
    # Create all tables
    Base.metadata.create_all(bind=sync_test_engine)
    # Create session
    session = SyncTestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up database
        Base.metadata.drop_all(bind=sync_test_engine)
