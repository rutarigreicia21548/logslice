"""Tests for logslice.cli_checkpoint."""

import argparse
import json
import pytest

from logslice.cli_checkpoint import (
    add_checkpoint_args,
    load_offsets,
    persist_offsets,
    record_position,
)


def _make_namespace(checkpoint=None):
    ns = argparse.Namespace()
    ns.checkpoint = checkpoint
    return ns


class TestAddCheckpointArgs:
    def setup_method(self):
        self.parser = argparse.ArgumentParser()
        add_checkpoint_args(self.parser)

    def test_default_is_none(self):
        args = self.parser.parse_args([])
        assert args.checkpoint is None

    def test_accepts_checkpoint_flag(self, tmp_path):
        path = str(tmp_path / "cp.json")
        args = self.parser.parse_args(["--checkpoint", path])
        assert args.checkpoint == path


class TestLoadOffsets:
    def test_returns_empty_when_no_checkpoint(self):
        ns = _make_namespace(checkpoint=None)
        assert load_offsets(ns) == {}

    def test_returns_empty_when_file_missing(self, tmp_path):
        ns = _make_namespace(checkpoint=str(tmp_path / "missing.json"))
        assert load_offsets(ns) == {}

    def test_loads_offsets_from_file(self, tmp_path):
        cp = tmp_path / "cp.json"
        cp.write_text(json.dumps({"version": 1, "offsets": {"svc.log": 77}}))
        ns = _make_namespace(checkpoint=str(cp))
        assert load_offsets(ns) == {"svc.log": 77}


class TestPersistOffsets:
    def test_writes_file_when_checkpoint_set(self, tmp_path):
        cp = str(tmp_path / "cp.json")
        ns = _make_namespace(checkpoint=cp)
        persist_offsets(ns, {"svc.log": 55})
        with open(cp) as fh:
            data = json.load(fh)
        assert data["offsets"] == {"svc.log": 55}

    def test_does_nothing_when_no_checkpoint(self, tmp_path):
        ns = _make_namespace(checkpoint=None)
        persist_offsets(ns, {"svc.log": 55})  # should not raise


class TestRecordPosition:
    def test_updates_offsets_in_memory(self, tmp_path):
        ns = _make_namespace(checkpoint=None)
        updated = record_position(ns, {}, "svc.log", 128)
        assert updated == {"svc.log": 128}

    def test_persists_when_checkpoint_configured(self, tmp_path):
        cp = str(tmp_path / "cp.json")
        ns = _make_namespace(checkpoint=cp)
        record_position(ns, {}, "svc.log", 200)
        with open(cp) as fh:
            data = json.load(fh)
        assert data["offsets"]["svc.log"] == 200

    def test_returns_updated_dict(self, tmp_path):
        ns = _make_namespace(checkpoint=None)
        offsets = {"a.log": 10}
        result = record_position(ns, offsets, "b.log", 20)
        assert result == {"a.log": 10, "b.log": 20}
