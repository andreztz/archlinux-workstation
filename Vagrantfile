# -*- mode: ruby -*-
# vi: set ft=ruby :
Vagrant.configure("2") do |config|
  config.vm.box = "archlinux/archlinux"
  config.vm.box_check_update = true
  config.vm.synced_folder ".", "/vagrant", disabled: false
  config.vm.provider "virtualbox" do |vb|
    vb.gui = true
    vb.memory = "2048"
  end

  config.vm.provision "shell", inline: <<-SHELL
    sudo pacman -Syu --noconfirm
    sudo pacman -S --needed --noconfirm sudo
    # virtualbox-guest-utils-nox é somente para ambiente texto
    sudo pacman -R virtualbox-guest-utils-nox --noconfirm
    sudo pacman -S virtualbox-guest-utils --noconfirm
    (id ztz || sudo useradd -m -G wheel -s /usr/bin/bash ztz) > /dev/null 2>&1
    echo -e "lab\nlab" | sudo passwd ztz
    echo -e 'Defaults:ztz !requiretty\nztz ALL=(ALL) NOPASSWD: ALL' | sudo EDITOR='tee -a' visudo -f /etc/sudoers.d/ztz
  SHELL

  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "bootstrap.yml"
    ansible.become = true
    ansible.limit = "all"
    ansible.inventory_path = "hosts.ini"
  end

  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "playbook.yml"
    ansible.become = true
    ansible.limit = "all"
    ansible.inventory_path = "hosts.ini"
    ansible.verbose = true
  end
end
