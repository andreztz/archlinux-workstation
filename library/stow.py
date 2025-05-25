#!/usr/bin/python
from pathlib import Path
import shutil
from ansible.module_utils.basic import AnsibleModule


def ensure_symlink(src: Path, dest: Path) -> bool:
    """
    Cria link simbólico de `src` para `dest`.

    Retorna `True` se houve alteração, `False` caso contrário.
    """
    if dest.exists():
        if dest.is_symlink():
            if dest.readlink() == src:
                return False  # symlink já está correto
            else:
                dest.unlink()  # symlink incorreto - apenas remove
                return True
        else:
            # Trata conflito com arquivo/diretório real
            backup_name = f"{dest}.conflict.bak"
            shutil.move(dest, backup_name)
            # os.remove(dest)

    dest.symlink_to(src)
    return True


def remove_symlink(path: Path) -> bool:
    """
    Remove link simbólico se existir.
    Retorna `True` se houve alteração, `False` caso contrário.
    """
    if path.is_symlink():
        path.unlink()
        return True
    return False


def process_directory(
    repository: Path, module: str, dest: Path, state: str
) -> tuple[bool, list[str]]:
    """
    Processa módulo de entrada `module`, criando links simbólicos no destino
    (`dest`) conforme necessário
    """
    changed = False
    messages = []
    module_path = repository.joinpath(module)

    if not module_path.is_dir():
        return changed, [f"src '{module}' não é um diretório válido."]

    if state == "suppress":
        return changed, ["Operação suprimida pelo usuário."]

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
                f"Link criado: {dst} -> {src}"
            )
    elif state == "absent":
        if remove_symlink(dst):
            changed = True
            messages.append(f"Link removido: {dst}")
    return changed, messages


def main():
    """
    - name: Apply dotfiles
      stow:
        repo: "/home/ztz/.dotfiles"
        module: "{{ item }}"
        dest: "/home/ztz"
        state: present
      become: true
      become_user: ztz
      loop: "{{ dotfiles }}"

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
