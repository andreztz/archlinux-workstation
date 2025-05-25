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


# def test_process_directory_must_be_return_false_when_src_is_not_dir():
#     changed, message = process_directory(
#         module=Path("test"), dest=Path("test"), state="test"
#     )
#     assert changed is False
#     assert message[0] == "src 'test' não é um diretório válido."
#
#
# def test_process_directory_must_be_return_false_when_state_is_suppress():
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         changed, message = process_directory(
#             module=Path(tmp_dir), dest=Path("test"), state="suppress"
#         )
#         assert changed is False
#         assert message[0] == "Operação suprimida pelo usuário."

#
# def test_process_directory_must_be_return_true_when_state_is_absent():
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         home = Path(tmp_dir)
#         module = home / "module"
#         module.mkdir(parents=True)
#         module.joinpath("configfile").touch()
#
#         link = home / "link"
#         link.symlink_to(module)
#
#         changed, message = process_directory(
#             module=module, dest=home / "link", state="absent"
#         )
#         assert changed is True
#         assert message[0] == f"Link removido: {link}."


def test_process_directory_must_be_return_link_criado():
    with tempfile.TemporaryDirectory() as tmp_dir:
        destination = Path(tmp_dir)
        destination.joinpath(".config").mkdir(parents=True)

        dotfiles = Path(tmp_dir).joinpath("dotfiles")
        ruff = dotfiles / "ruff/.config/ruff"
        ruff.mkdir(parents=True)
        ruff.joinpath("configfile").touch()

        changed, message = process_directory(
            repository=dotfiles,
            module="ruff",
            dest=destination,
            state="present",
        )
        assert changed is True
        assert (
            message[0]
            == f"Link criado: {tmp_dir}/.config/ruff -> {tmp_dir}/dotfiles/ruff/.config/ruff"
        )
