
# Generic class for catching and communicating errors from VBoxManage commands
class CommandError(Exception):
    def __init__(self, cmd, error):
        self.cmd = ' '.join(cmd)
        self.code = str(error.returncode)
        self.msg = error.output

    def __str__(self):
        return "Command " + self.cmd + " failed with code " + self.code + \
            " and message:\n" + self.msg

# Error for when using a user-specified option with a VBoxManage command fails
class UnknownOptionError(Exception):
    def __init__(self, cmd, option):
        self.cmd = cmd
        self.option = option

    def __str__(self):
        return "Unknown Option " + self.option + " for command " + self.cmd


# Error for when the VM specified by name and UUID is unrecognized
class UnknownVMError(Exception):
    def __init__(self, name, uuid):
        self.name = str(name)
        self.uuid = str(uuid)

    def __str__(self):
        return "No VM found for name " + self.name + " and UUID " + self.uuid

# Error when trying to register a VM from its XML file
class RegistrationError(Exception):
    def __init__(self, filename, error):
        self.filename = filename
        self.code = str(error.returncode)
        self.msg = error.output

    def __str__(self):
        filerr = "Unable to register VM from file " + filename + "\n"
        errmsg = "Returned message was:\n" + self.msg
        return filerr + errmsg

# Error for closemedium
class CloseMediumError(Exception):
    def __init__(self, device, target, error=None):
        self.device = device
        self.target = target
        if error:
            self.msg = error.output
        else:
            self.msg = ""

    def __str__(self):
         e = "Cannot close device " + self.device + " with target " + self.target
         return e + "\n" + self.msg

class NoMediumError(CloseMediumError):
    def __str__(self):
        return self.device + " is not a valid device"
