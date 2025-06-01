#!/usr/bin/python
from pathlib import Path
import shutil
from ansible.module_utils.basic import AnsibleModule


def ensure_symlink(source: Path, target: Path) -> bool:
    """
    Create a symbolic link from `source` to `target`.

    Returns `True` if a new link was created or replaced otherwise `False`
    if the link was already correct.
    """
    if target.exists():
        if target.is_symlink():
            if target.readlink() == source:
                return False
            else:
                target.unlink()
                return True
        else:
            backup_name = f"{target}.conflict.bak"
            shutil.move(target, backup_name)

    if target.is_dir():
        target.symlink_to(source, target_is_directory=True)
    else:
        target.symlink_to(source, target_is_directory=False)

    return True


def remove_symlink(path: Path) -> bool:
    """
    Remove the symbolic link if it exists.

    Returns `True` if the link was removed, otherwise `False`.
    """
    if path.is_symlink():
        path.unlink()
        return True
    return False


def resolve_paths(
    package: Path, destination: Path, repository: Path
) -> tuple[Path, Path]:
    """Resolve source and target paths for a given package."""
    for item in package.rglob("*"):
        if item.is_file() and (item.parent.parent).name == repository.name:
            source = item
            target = destination / item.relative_to(package)
        elif item.is_dir() and (item.parent.parent).name != repository.name:
            source = item
            target = destination / item.relative_to(package)
    return source, target


def process_directory(
    repository: Path, package: str, destination: Path, state: str
) -> tuple[bool, list[str]]:
    """
    Create or remove symbolic links for a package.

    repository: where packages are stored.
    package: name of the package to link.
    destination: where to create the links.
    state: present, absent, latest, or suppress.

    Returns a tuple (changed, messages).
    """
    changed = False
    messages = []
    package_path = repository / package

    if not package_path.is_dir():
        return changed, [f"Source '{package}' is not a valid directory."]

    source, target = resolve_paths(package_path, destination, repository)

    match state:
        case "suppress":
            messages.append("Operation was suppressed by user request.")
        case "present" | "latest":
            result = ensure_symlink(source, target)
            changed |= result
            if result:
                messages.append(f"Created link: {target} -> {source}")
        case "absent":
            if remove_symlink(target):
                changed = True
                messages.append(f"Removed link: {target}")
        case _:
            messages.append(f"Unknown state: {state}")
    return changed, messages


def main():
    """
    Ansible module for creating symbolic links from dotfiles packages.

    Example use:
    - name: Apply dotfiles
      stow:
        repo: "/home/user/.dotfiles"
        src: "{{ item }}"
        dest: "/home/user"
        state: present
      loop:
        - zsh
        - bash
        - tmux
        - rofi
    """
    arg_spec = {
        "repo": {"type": "str", "required": True},
        "src": {"type": "str", "required": True},
        "dest": {"type": "str", "required": True},
        "state": {
            "type": "str",
            "choices": ["present", "absent", "latest", "suppress"],
            "default": "present",
        },
    }

    ansible_module = AnsibleModule(
        argument_spec=arg_spec, supports_check_mode=False
    )

    repository = Path(ansible_module.params["repo"])
    package = ansible_module.params["src"]
    dest = Path(ansible_module.params["dest"])
    state = ansible_module.params["state"]

    try:
        changed, messages = process_directory(repository, package, dest, state)
        ansible_module.exit_json(changed=changed, msg=messages)
    except Exception as exc:
        ansible_module.fail_json(msg=str(exc))


if __name__ == "__main__":
    main()
