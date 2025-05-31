import tempfile
from pathlib import Path
from stow import ensure_symlink, process_directory, remove_symlink


def test_symlink_creation_when_absent():
    with (
        tempfile.TemporaryDirectory() as src,
        tempfile.TemporaryDirectory() as dest,
    ):
        src = Path(src)
        dest = Path(dest)

        src_file = src / "file"
        open(src_file, "w").close()
        dest_file = dest / "file"

        assert ensure_symlink(src_file, dest_file) is True
        assert dest_file.is_symlink()
        assert dest_file.readlink() == src_file


def test_symlink_already_exists():
    with (
        tempfile.TemporaryDirectory() as src,
        tempfile.TemporaryDirectory() as dest,
    ):
        src = Path(src)
        dest = Path(dest)

        src_file = src / "file"
        open(src_file, "w").close()
        dest_file = dest / "file"

        dest_file.symlink_to(src_file)

        assert ensure_symlink(src_file, dest_file) is False  # already correct
        assert dest_file.readlink() == src_file


def test_symlink_conflict_with_file():
    with (
        tempfile.TemporaryDirectory() as src,
        tempfile.TemporaryDirectory() as dest,
    ):
        src = Path(src)
        dest = Path(dest)

        src_file = src / "file"
        open(src_file, "w").close()
        dest_file = dest / "file"
        open(dest_file, "w").close()

        assert ensure_symlink(src_file, dest_file) is True
        assert dest_file.is_symlink()
        assert dest_file.readlink() == src_file
        backups = list(dest.glob("file.conflict.bak"))
        assert len(backups) == 1


def test_remove_symlink():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        target = tmp / "target"
        open(target, "w").close()
        link = tmp / "link"
        link.symlink_to(target)

        assert remove_symlink(link) is True
        assert not link.exists()


def test_process_directory_should_return_false_when_src_module_is_not_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        home = Path(tmp_dir)

        dotfiles = home / ".dotfiles"
        dotfiles.mkdir(parents=True)

        changed, message = process_directory(
            repository=dotfiles,
            module="test",
            destination=Path("test"),
            state="test",
        )
        assert changed is False
        assert message[0] == "Source 'test' is not a valid directory."


def test_process_directory_should_return_false_when_state_is_suppress():
    with tempfile.TemporaryDirectory() as tmp_dir:
        home = Path(tmp_dir)

        dotfiles = home / ".dotfiles"
        dotfiles.mkdir(parents=True)

        changed, message = process_directory(
            repository=dotfiles,
            module=tmp_dir,
            destination=Path("test"),
            state="suppress",
        )
        assert changed is False
        assert message[0] == "Operation was suppressed by user request."


#
def test_process_directory_shoul_remove_link_when_state_is_absent():
    with tempfile.TemporaryDirectory() as tmp_dir:
        home = Path(tmp_dir)

        dotfiles = home / ".dotfiles"
        dotfiles.mkdir(parents=True)

        module = dotfiles / "module"
        module.mkdir()

        config_file = module / ".config.txt"
        config_file.write_text("data")

        link = home / ".config.txt"
        link.symlink_to(config_file)

        changed, message = process_directory(
            repository=dotfiles,
            module="module",
            destination=home,
            state="absent",
        )

        assert changed is True
        assert message[0] == f"Removed link: {link}"


def test_process_directory_should_create_symlink_when_state_is_present():
    with tempfile.TemporaryDirectory() as tmp_dir:
        home = Path(tmp_dir)
        home.joinpath(".config").mkdir(parents=True)

        dotfiles = home / ".dotfiles"
        dotfiles.mkdir()

        module = dotfiles / "module/.config/module"
        module.mkdir(parents=True)
        module.joinpath("config.txt").touch()

        changed, message = process_directory(
            repository=dotfiles,
            module="module",
            destination=home,
            state="present",
        )
        assert changed is True
        assert message[0] == f"Created link: {home}/.config/module -> {module}"
