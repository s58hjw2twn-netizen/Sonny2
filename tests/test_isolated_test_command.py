import pytest

from sonny.isolated_test_command import build_test_command

IMAGE = "python:3.11-slim@sha256:" + "a" * 64


def test_command_has_isolation_guards(tmp_path):
    command = build_test_command(str(tmp_path), IMAGE)
    assert command[:2] == ["docker", "run"]
    assert "--network" in command and command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert "--cap-drop" in command
    assert "--memory" in command
    assert "--pids-limit" in command
    assert "--user" in command
    assert "--mount" in command
    assert "readonly" in command[command.index("--mount") + 1]
    assert command[-5:] == ["python", "-m", "unittest", "discover", "-s", "tests"]


@pytest.mark.parametrize("image", [
    "python:3.11-slim", "python:latest", "python:3.11-slim@sha256:abc",
])
def test_unpinned_images_rejected(tmp_path, image):
    with pytest.raises(ValueError):
        build_test_command(str(tmp_path), image)


def test_missing_workspace_rejected(tmp_path):
    with pytest.raises(ValueError):
        build_test_command(str(tmp_path / "missing"), IMAGE)


def test_mount_delimiter_rejected(tmp_path):
    bad = tmp_path / "unsafe,readonly=false"
    bad.mkdir()
    with pytest.raises(ValueError):
        build_test_command(str(bad), IMAGE)
