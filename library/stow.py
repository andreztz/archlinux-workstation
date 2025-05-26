#!/usr/bin/python
from pathlib import Path
import shutil
from ansible.module_utils.basic import AnsibleModule


def ensure_symlink(src: Path, dest: Path) -> bool:
    """
    Create a symbolic link from `src` to `dest`.

    Returns `True` if a new link was created or replaced otherwise `False` 
    if the link was already correct.
    """
    if dest.exists():
        if dest.is_symlink():
            if dest.readlink() == src:
                return False
            else:
                dest.unlink()
                return True
        else:
            backup_name = f"{dest}.conflict.bak"
            shutil.move(dest, backup_name)

    dest.symlink_to(src)
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


def process_directory(
    repository: Path, module: str, dest: Path, state: str
) -> tuple[bool, list[str]]:
    """
    Create or remove symbolic links for a module.

    repository: where modules are stored.
    module: name of the module to link.
    destination: where to create the links.
    state: present, absent, latest, or suppress.

    Returns a tuple (changed, messages).
    """
    changed = False
    messages = []
    module_path = repository.joinpath(module)

    if not module_path.is_dir():
        return changed, [f"Source '{module}' is not a valid directory."]

    if state == "suppress":
        return changed, ["Operation was suppressed by user request."]

    layout = None

    for item in module_path.rglob("*"):
        if item.name != module and item.is_dir():
            layout = item.name

    if layout is None:
       for item in module_path.iterdir():
           src = item
           dst = dest / item.name
    else:
        src = repository / module / layout / module
        dst = dest / layout / module

    if state in {"present", "latest"}:
        result = ensure_symlink(src, dst)
        changed |= result
        if result:
            messages.append(
                f"Created link: {dst} -> {src}"
            )
    elif state == "absent":
        if remove_symlink(dst):
            changed = True
            messages.append(f"Removed link: {dst}")
    return changed, messages


def main():
    """
    Ansible module for creating symbolic links from dotfiles modules.

    Example use:
    - name: Apply dotfiles
      stow:
        repo: "/home/user/.dotfiles"
        module: "{{ item }}"
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
        "module": {"type": "str", "required": True},
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
    module = ansible_module.params["module"]
    dest = Path(ansible_module.params["dest"])
    state = ansible_module.params["state"]

    try:
        changed, messages = process_directory(repository, module, dest, state)
        ansible_module.exit_json(changed=changed, msg=messages)
    except Exception as exc:
        ansible_module.fail_json(msg=str(exc))


if __name__ == "__main__":
    main()
