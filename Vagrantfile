# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "fedora/29-cloud-base"

  config.vm.provider "libvirt" do |vb|
    # Customize the amount of memory on the VM:
    vb.memory = "2048"
  end

  config.vm.provision "ansible" do |a|
    # FIXME: it will fail since the playbook expects a container environment
    #        we should fix it
    a.playbook = "recipe.yml"
    a.raw_arguments = ["-e", "ansible_python_interpreter=/usr/bin/python3", "--become"]
  end
end
