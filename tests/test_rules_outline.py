def test_application_can_be_imported():
    from app.main import app

    assert app is not None
