"""Tests for logslice.checkpoint."""

import json
import os
import pytest

from logslice.checkpoint import (
    load_checkpoint,
    save_checkpoint,
    update_checkpoint,
    get_offset,
)


@pytest.fixture()
def tmp_path_file(tmp_path):
    return str(tmp_path / "checkpoint.json")


class TestLoadCheckpoint:
    def test_returns_empty_dict_when_file_missing(self, tmp_path_file):
        result = load_checkpoint(tmp_path_file)
        assert result == {}

    def test_loads_offsets_from_valid_file(self, tmp_path_file):
        data = {"version": 1, "offsets": {"service_a.log": 1024, "service_b.log": 512}}
        with open(tmp_path_file, "w") as fh:
            json.dump(data, fh)
        result = load_checkpoint(tmp_path_file)
        assert result == {"service_a.log": 1024, "service_b.log": 512}

    def test_returns_empty_dict_on_invalid_json(self, tmp_path_file):
        with open(tmp_path_file, "w") as fh:
            fh.write("not valid json{{{")
        assert load_checkpoint(tmp_path_file) == {}

    def test_returns_empty_dict_when_offsets_missing(self, tmp_path_file):
        with open(tmp_path_file, "w") as fh:
            json.dump({"version": 1}, fh)
        assert load_checkpoint(tmp_path_file) == {}

    def test_returns_empty_dict_when_top_level_not_dict(self, tmp_path_file):
        with open(tmp_path_file, "w") as fh:
            json.dump([1, 2, 3], fh)
        assert load_checkpoint(tmp_path_file) == {}


class TestSaveCheckpoint:
    def test_writes_file_with_offsets(self, tmp_path_file):
        save_checkpoint(tmp_path_file, {"svc.log": 256})
        with open(tmp_path_file, "r") as fh:
            data = json.load(fh)
        assert data["offsets"] == {"svc.log": 256}

    def test_roundtrip_save_and_load(self, tmp_path_file):
        offsets = {"a.log": 100, "b.log": 200}
        save_checkpoint(tmp_path_file, offsets)
        assert load_checkpoint(tmp_path_file) == offsets

    def test_overwrites_existing_file(self, tmp_path_file):
        save_checkpoint(tmp_path_file, {"a.log": 10})
        save_checkpoint(tmp_path_file, {"b.log": 20})
        assert load_checkpoint(tmp_path_file) == {"b.log": 20}


class TestUpdateCheckpoint:
    def test_adds_new_source(self):
        result = update_checkpoint({}, "new.log", 42)
        assert result == {"new.log": 42}

    def test_updates_existing_source(self):
        result = update_checkpoint({"svc.log": 10}, "svc.log", 99)
        assert result["svc.log"] == 99

    def test_does_not_mutate_original(self):
        original = {"svc.log": 10}
        update_checkpoint(original, "svc.log", 99)
        assert original["svc.log"] == 10


class TestGetOffset:
    def test_returns_stored_offset(self):
        assert get_offset({"svc.log": 512}, "svc.log") == 512

    def test_returns_none_for_unknown_source(self):
        assert get_offset({}, "missing.log") is None
