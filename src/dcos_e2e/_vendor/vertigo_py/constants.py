# Constants for use by the rest of the Vertigo system

import re
# The basic VBoxManage command
cmd = "VBoxManage"

# list of options for the list command
lsopts = ["vms", "runningvms", "ostypes", "hostdvds", "hostfloppies",
          "bridgedifs", "dhcpservers", "hostinfo", "hostcpuids",
          "hddbackends", "hdds", "dvds", "floppies", "usbhost", "usbfilters",
          "systemproperties", "extpacks"]


modopts = ["name", "ostype", "memory", "pagefusion", "vram", "acpi", "ioapic",
           "pae", "hpet", "hwvirtex", "hwvirtexexcl", "nestedpaging",
           "largepages", "vtxvpid", "synthcpu", "cpuidset", "cpuidremove",
           "cpuidremoveall", "hardwareuuid", "cpus", "cpuhotplug", "plugcpu",
           "unplugcpu", "cpuexecutioncap", "rtcuseutc", "monitorcount",
           "accelerate3d", "firmware", "chipset", "bioslogofadein",
           "bioslogofadeout", "bioslogodisplaytime", "bioslogoimagepath",
           "biosbootmenu", "biossystemtimeoffset", "biospxedebug", "boot",
           "nic", "nictype", "cableconnected", "nictrace", "nictracefile",
           "nicproperty", "nicspeed", "nicbootprio", "nicpromisc",
           "nicbandwidthgroup", "bridgeadapter", "intnet", "natnet|default",
           "nicgenericdrv", "natsettings,", "natpf", "nattftpprefix",
           "nattftpfile", "nattftpserver", "natbindip", "natdnspassdomain",
           "natdnsproxy", "natdnshostresolver", "nataliasmode", "macaddress",
           "mouse", "keyboard", "uart", "uartmode", "guestmemoryballoon",
           "gueststatisticsinterval", "audio", "audiocontroller", "clipboard",
           "vrde", "vrdeextpack", "vrdeproperty", "vrdeport",
           "vrdeaddress", "vrdeauthtype", "vrdeauthlibrary", "vrdemulticon",
           "vrdereusecon", "vrdevideochannel", "vrdevideochannelquality",
           "usb", "usbehci", "snapshotfolder", "teleporter", "teleporterport",
           "teleporteraddress", "teleporterpassword", "teleporterpasswordfile"]

modboolopts = ["pagefusion", "acpi", "ioapic", "pae", "hpet", "hwvirtex",
               "hwvirtexexcl", "nestedpaging", "largepages", "vtxvpid",
               "synthcpu", "cpuhotplug", "rtcuseutc", "accelerate3d",
               "bioslogofadein", "bioslogofadeout", "vrde", "vrdemulticon",
               "vrdereusecon", "vrdevideochannel", "usb", "usbehci",
               "teleporter"]

modindexopts = ["boot", "nic", "nictype", "cableconnected", "nictrace",
              "nictracefile", "nicproperty", "nicspeed", "nicbootprio",
              "nicpromisc", "nicbandwidthgroup", "bridgeadapter", "intnet",
              "natnet|default", "nicgenericdrv", "natsettings,", "natpf",
              "natpf", "nattftpprefix", "nattftpfile", "nattftpserver",
              "natbindip", "natdnspassdomain", "natdnsproxy",
              "natdnshostresolver", "nataliasmode", "macaddress", "uart"]

modenumopts = {
    "firmware" : ["bios", "efi", "efi32", "efi64"],
    "chipset" : ["ich9", "piix3"],
    "boot" : [None, "none", "floppy", "dvd", "disk", "net"],
    "nic" : [None, "none", "null", "nat", "bridged", "intnet", "generic"],
    "nictype" : ["Am79C970A", "Am79C973"],
    "nicpromisc": ["deny", "allow-vms", "allow-all"],
    "mouse": ["ps2", "usb", "usbtablet"],
    "keyboard" : ["ps2", "usb"],
    "audio" : ["none", "null", "dsound", "solaudio", "oss", "coreaudio"],
    "audiocontroller" : ["ac97", "hda", "sb16"],
    "clipboard": ["disabled", "hosttoguest", "guesttohost", "bidirectional"],
    "vrdeauthtype" : ["null", "external", "guest"]
    }

ctrlopts = ["pause", "resume", "reset", "poweroff", "savestate",
            "acpipowerbutton", "acpisleepbutton", "setlinkstate", "nic",
            "nictrace", "nictracefile", "nicproperty", "natpf",
            "guestmemoryballoon", "gueststatisticsinterval", "usbattach",
            "usbdettach", "clipboard", "draganddrop", "vrde", "vrdeport",
            "vrdevideochannelquality", "setvideomodehint", "screenshotpng",
            "setcredentials", "teleport", "plugcpu", "unplugcpu",
            "cpuexecutioncap"]

ctrlindexopts = ["setlinkstate", "nic", "nictrace", "nictracefile",
                 "nicproperty", "natpf"]

ctrlnumopts = {
    "nic" : [None, "none", "null", "nat", "bridged", "intnet", "generic"],
    "clipboard": ["disabled", "hosttoguest", "guesttohost", "bidirectional"],
    "draganddrop": ["disabled", "hosttoguest"]
    }

ctrlboolopts = ["nictrace", "vrde"]

closemediumopts = ["disk", "dvd", "floppy"]

bools = [True, False, "on", "off"]

mod_to_ls = { 'uuid' : 'UUID',
              'ostype' : 'GuestOSType',
              }
