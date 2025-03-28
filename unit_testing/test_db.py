import pytest
from model.dbc_model import Tournament_DB, Player


@pytest.fixture()
def db_instance():
    db = Tournament_DB(db_name=":memory:")
    yield db
    db.close_db()


def test_create_player_table(db_instance):
    # Instantiate Player and share the same connection and cursor from the fixture.
    player = Player(db_name=":memory:")
    player.connection = db_instance.connection
    player.cursor = db_instance.cursor

    # Create the player table.
    player.createTable()

    # Query the database metadata to check if the table exists.
    db_instance.cursor.execute("PRAGMA table_info(player)")
    columns = db_instance.cursor.fetchall()

    # Assert that columns were returned (meaning the table exists).
    assert len(columns) > 0


class DummyInteraction:
    class DummyUser:
        id = 12345

    user = DummyUser


def test_register_and_fetch_player(db_instance):
    player = Player(db_name=":memory:")
    player.connection = db_instance.connection
    player.cursor = db_instance.cursor
    player.createTable()

    dummy = DummyInteraction()

    player.register(dummy, "TestGame", "TestTag")

    result = player.fetch(dummy)

    assert result is not None, "Player record should exist after registration"

    assert result[0] == dummy.user.id
    assert result[1] == "TestGame"
    assert result[3] == "TestTag"


