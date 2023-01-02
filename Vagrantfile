# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  with_tests = ENV["WITH_TESTS"] || "no"
  config.vm.define "f36" do |f36|
    f36.vm.box = "fedora/36-cloud-base"
  end

  config.vm.provider "libvirt" do |vb|
    vb.memory = "1024"
  end

  config.vm.provision "ansible" do |a|
    a.playbook = "contrib/pre-setup.yml"
    a.raw_arguments = [
      "-vv",
      "-e", "ansible_python_interpreter=/usr/bin/python3",
      "-e", "project_dir=/vagrant",
      "-e", "with_tests=#{with_tests}",
      "--become"
    ]
  end
  config.vm.provision "shell", :inline => "grep unified_cgroup_hierarchy /proc/cmdline || reboot"
  config.vm.provision "ansible" do |a|
    a.playbook = "contrib/post-setup.yml"
    a.raw_arguments = [
      "-vv",
      "-e", "ansible_python_interpreter=/usr/bin/python3",
      "-e", "project_dir=/vagrant",
      "-e", "with_tests=#{with_tests}",
      "--become"
    ]
  end

  if with_tests == "yes"
    config.vm.provision "shell" do |s|
      s.name = "test-script"
      s.inline = "cd /vagrant && sudo make check"
    end
  end
end
