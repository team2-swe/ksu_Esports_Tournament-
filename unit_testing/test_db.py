import json

import pytest
from model.dbc_model import Tournament_DB, Player, Game


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


def test_is_account_exist(db_instance):
    player = Player(db_name=":memory:")
    player.connection = db_instance.connection
    player.cursor = db_instance.cursor
    player.createTable()

    dummy = DummyInteraction()
    assert not player.isAcountExist(dummy)

    player.register(dummy, "GameX", "TagX")
    assert player.isAcountExist(dummy)


def test_get_all_players(db_instance):
    player = Player(db_name=":memory:")
    player.connection = db_instance.connection
    player.cursor = db_instance.cursor
    player.createTable()

    dummy = DummyInteraction()
    player.register(dummy, "GameY", "TagY")

    all_players = player.get_all_player()
    assert len(all_players) == 1
    assert all_players[0][1] == "GameY"


def test_remove_player(db_instance):
    player = Player(db_name=":memory:")
    player.connection = db_instance.connection
    player.cursor = db_instance.cursor
    player.createTable()

    dummy = DummyInteraction()
    player.register(dummy, "GameZ", "TagZ")
    assert player.fetch(dummy) is not None

    player.remove_player(dummy.user.id)
    assert player.fetch(dummy) is None


def test_increment_and_get_mvp_count(db_instance):
    player = Player(db_name=":memory:")
    player.connection = db_instance.connection
    player.cursor = db_instance.cursor
    player.createTable()

    dummy = DummyInteraction()
    player.register(dummy, "GameA", "TagA")

    initial_count = player.get_mvp_count(dummy.user.id)
    assert initial_count == 0

    new_count = player.increment_mvp_count(dummy.user.id)
    assert new_count == 1

    final_count = player.get_mvp_count(dummy.user.id)
    assert final_count == 1


def test_create_game_table(db_instance):
    game = Game(db_name=":memory:")
    game.connection = db_instance.connection
    game.cursor = db_instance.cursor
    game.createTable()

    db_instance.cursor.execute("PRAGMA table_info(game)")
    columns = db_instance.cursor.fetchall()
    assert len(columns) > 0


def test_update_pref(db_instance):
    from model.dbc_model import Player, Game

    player = Player(db_name=":memory:")
    player.connection = db_instance.connection
    player.cursor = db_instance.cursor
    player.createTable()

    game = Game(db_name=":memory:")
    game.connection = db_instance.connection
    game.cursor = db_instance.cursor
    game.createTable()

    dummy = DummyInteraction()
    player.register(dummy, "LoL", "1234")

    pref = {"top": True, "mid": False}
    game.update_pref(dummy, pref)

    result = game.fetchGameDetails()
    assert len(result) == 1
    assert json.loads(result[0][4])["top"] is True
