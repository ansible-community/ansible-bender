# -*- mode: ruby -*-
# vi: set ft=ruby :

with_tests = ENV["WITH_TESTS"] || "no"

Vagrant.configure("2") do |config|
  config.vm.provider "libvirt" do |vb|
    vb.memory = "1024"
  end

  config.vm.define "f37" do |f37|
    f37.vm.box = "fedora/37-cloud-base"

    f37.vm.provision "ansible" do |a|
      a.playbook = "contrib/setup.yml"
      a.raw_arguments = [
        "-vv",
        "-e", "ansible_python_interpreter=/usr/bin/python3",
        "-e", "project_dir=/src",
        "-e", "with_tests=#{with_tests}",
        "--become"
      ]
    end

    f37.vm.synced_folder ".", "/src"

    if with_tests == "yes"
      f37.vm.provision "shell", :inline => "cd /src && sudo make check"
    end
  end
end
