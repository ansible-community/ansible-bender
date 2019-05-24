# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  with_tests = ENV["WITH_TESTS"] || "no"
  if with_tests == "yes"
    config.vm.define "f29" do |f29|
      f29.vm.box = "fedora/29-cloud-base"
    end
  end

  config.vm.define "f30" do |f30|
    f30.vm.box = "fedora/30-cloud-base"
  end

  config.vm.provider "libvirt" do |vb|
    vb.memory = "1024"
  end

  config.vm.provision "ansible" do |a|
    a.playbook = "recipe.yml"
    a.raw_arguments = [
      "-vv",
      "-e", "ansible_python_interpreter=/usr/bin/python3",
      "-e", "project_dir=/vagrant",
      "-e", "with_tests=#{with_tests}",
      "--become"
    ]
  end

  if with_tests == "yes"
    config.vm.provision "shell", inline: <<-EOF
      cd /vagrant && \
      sudo make check
    EOF
  end
end
