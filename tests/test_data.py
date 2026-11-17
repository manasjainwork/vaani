import json

import pytest

from vaani.data import load_manifest


def make_row(**changes):
    row = {
        "id": "clip_001",
        "audio": "audio/clip_001.wav",
        "text": "mera order kab aayega",
        "turns": [{"start": 0.4, "end": 2.1}],
        "speaker": "s1",
        "consent": True,
        "notes": "quiet room",
    }
    row.update(changes)
    return row


def write_manifest(tmp_path, rows):
    path = tmp_path / "manifest.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return path


def test_loads_a_good_manifest(tmp_path):
    path = write_manifest(tmp_path, [make_row(), make_row(id="clip_002", text="मेरा ऑर्डर कब आएगा")])
    clips = load_manifest(path, check_audio=False)
    assert [c.id for c in clips] == ["clip_001", "clip_002"]
    assert clips[1].text == "मेरा ऑर्डर कब आएगा"
    assert clips[0].turns[0].end == pytest.approx(2.1)
    assert clips[0].audio_path == tmp_path / "audio/clip_001.wav"


def test_clip_without_consent_is_rejected(tmp_path):
    path = write_manifest(tmp_path, [make_row(consent=False)])
    with pytest.raises(ValueError, match="no consent"):
        load_manifest(path, check_audio=False)


def test_missing_field_names_the_line(tmp_path):
    bad = make_row()
    del bad["speaker"]
    path = write_manifest(tmp_path, [make_row(), bad])
    with pytest.raises(ValueError, match=r":2: missing fields"):
        load_manifest(path, check_audio=False)


def test_bad_turn_times_are_rejected(tmp_path):
    path = write_manifest(tmp_path, [make_row(turns=[{"start": 2.0, "end": 1.0}])])
    with pytest.raises(ValueError, match="bad turn times"):
        load_manifest(path, check_audio=False)


def test_overlapping_turns_are_rejected(tmp_path):
    turns = [{"start": 0.0, "end": 2.0}, {"start": 1.5, "end": 3.0}]
    path = write_manifest(tmp_path, [make_row(turns=turns)])
    with pytest.raises(ValueError, match="bad turn times"):
        load_manifest(path, check_audio=False)


def test_duplicate_ids_are_rejected(tmp_path):
    path = write_manifest(tmp_path, [make_row(), make_row()])
    with pytest.raises(ValueError, match="duplicate"):
        load_manifest(path, check_audio=False)


def test_missing_audio_file_is_reported(tmp_path):
    path = write_manifest(tmp_path, [make_row()])
    with pytest.raises(FileNotFoundError):
        load_manifest(path)


def test_audio_file_present_passes(tmp_path):
    (tmp_path / "audio").mkdir()
    (tmp_path / "audio/clip_001.wav").write_bytes(b"")
    path = write_manifest(tmp_path, [make_row()])
    assert len(load_manifest(path)) == 1
