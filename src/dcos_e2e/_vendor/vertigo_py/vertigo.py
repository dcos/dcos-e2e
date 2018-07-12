import re
import subprocess
from . import constants

from .error import *

# functions that don't fall into the VM class

# basic utility function to execute some arguments and return the result
def execute (args):
    try:
        result = subprocess.check_output(args)
    except subprocess.CalledProcessError as e:
        raise CommandError(args, e)
    return result

# Return the current Virtualbox version as a string
def version():
    return subprocess.check_output([constants.cmd, "-v"])

# Public: List available virtual machines, virtual devices and their relevant
# properties. Currently only returns a string representation. Will eventually
# return a more structured format, probably a dictionary
#
# option - the resource to list. Possible options listed in constants.py and the
#          VBoxManage manual
# longform - supply the --long switch to VBoxManage. Only relevant for a few
# options
#
# Returns a string representation of the requested option, or a dictionary of
# all of them
def ls(option="all", longform=False):

    cmd = [constants.cmd, "list"]

    if longform:
        cmd.append("--long")

    if not option in constants.lsopts and not option == "all":
        raise UnknownOptionError("list", option)

    if option == "all":
        result = {}
        for opt in constants.lsopts:
            result[opt] = subprocess.check_output(cmd + [opt])
        return result
    else:
        return subprocess.check_output(cmd + [option])

# Public: Create a new virtual with the given options.
#
# name - String that is the name of the new VM
# ostype - String that should be the OS type
# register - Boolean whether or not to register this VM in Virtualbox
# basefolder - String giving the path where to store the VM files
# uuid - Hexadecimal String to be the UUID of the VM
#
# Returns a VM object (eventually) wrapping the VM 
def createvm(name,ostype=None,register=False,basefolder=None,uuid=None):
    cmd = [constants.cmd, "createvm", "--name", name]

    if ostype:
        cmd += ["--ostype", ostype]
    if register:
        cmd += ["--register"]
    if basefolder:
        cmd += ["--basefolder", basefolder]
    if uuid:
        cmd += ["--uuid", uuid]

    # TODO: change to return VM object
    return subprocess.check_output(cmd)

# Public: Register a VM from its XML file
#
# filename - String giving the filepath to the XML file to use
#
# Returns True if the registration succeeded.
# Raises RegistrationError otherwise
def registervm(self, filename):
    args = [constants.cmd, "registervm", filename]

    try:
        result = subprocess.check_output(args)
    except subprocess.CalledProcessError as e:
        raise RegistrationError(filename, e)

    return True

# Public: Close a device based on a UUID or a filename
#
# device - one of "dvd", "floppy" or "disk"
# target - UUID or filename
# delete - whether or not to delete the device after closing
#
# Returns True if the registration succeeded.
# Raises NoMediumError if the device type is invalid, CommandError if there's
#        some other error
def closemedium(self, device, target, delete=False):
        if not device in constants.closemediumopts:
            raise NoMediumError(device, target, delete)

        args = [constants.cmd, "closemedium", target]
        if delete:
            args.append("--delete")

        execute(args)
        return True


# Public: Class that wraps a Virtualbox VM and lets you interact with it and
# configure. Does not interact with the Guest OS in any way.
class VM(object):

    # Public: Initialize a VM object to wrap a particular Virtualbox VM. At
    # least one of name or UUID must be provided to locate the VM and the VM
    # referenced must already exist.
    #
    # name - String that is the name of VirtualBox VM.
    # uuid - Hexadecimal String that is the UUID of the VirtualBox VM.
    #
    # Returns a VM object wrapping the VirtualBox VM
    # Raises UnknownVMError if VM corresponding to the name or UUID is not found
    def __init__(self, name=None, uuid=None):
        if name == None and uuid == None:
            raise UnknownVMError(name, uuid)

        if not name:
            argid = uuid
        else:
            argid = name

        try:
            args = [constants.cmd, "showvminfo", "--machinereadable", argid]
            self.vminfo = subprocess.check_output(args)
        except subprocess.CalledProcessError:
            raise UnknownVMError(name, uuid)

        self.info = self.parse_info(self.vminfo)
        self.__name = self.info['name']
        self.__uuid = self.info['UUID']
        self.started = False


    # Public: Parse a raw VM information string as returned by showvminfo and
    # turn it into a machine-usable Python dictionary.
    #
    # rawinfo - String that is the raw information dump from showvminfo
    # machine - Boolean saying if the raw information is from using the
    #           machinereadable switch
    # pythonize - Boolean saying if values should be swapped with their Python
    #             equivalents (True for on, False for off, None for <none>)
    #
    # Returns a dictionary of information keys to their provided values
    def parse_info(self, rawinfo=None,machine=True, pythonize=True):
        if not rawinfo:
            rawinfo = self.vminfo

        info = {}
        longkey = None
        longval = None

        if machine:
            sep = "="
        else:
            sep = ":"

        for line in rawinfo.splitlines():
            line = line.decode()
            parts = line.split(sep)

            # Work with multiline key-value pairs
            if not machine:
                if len(parts) == 1 and not longkey:
                    longkey = parts[0].strip()
                    longval = ""
                    continue
                elif len(parts) == 1:
                    longval + "\n"
                    longval += line
                    continue
                else:
                    longkey = None
                    longval = None

                key = parts[0].strip()
                value = ':'.join(parts[1:]).strip()
            else:
                key = parts[0].strip()
                value = parts[1].strip(' \"')

            if pythonize:
                # Turn numbers to ints
                try:
                    value = int(value)
                except ValueError:
                    pass

                # Turn on/off/none to True/False/None
                if value == "on":
                    value = True
                elif value == "off":
                    value = False
                elif value == "none":
                    value = None

            info[key] = value

        return info


    # Public: Create a Python dictionary representing the output from the
    # showvminfo command. Uses parse_info to parse the raw string and places the
    # raw string into a 'string' key in the dictionary.
    #
    # details - Boolean to use the --details flag
    # machine - Boolean to use the --machinereadable flag (easier to parse)
    # pythonize - Boolean saying if values should be swapped with their Python
    #             equivalents (True for on, False for off, None for <none>)
    #
    # Returns the parsed dictionary representation
    def showvminfo(self, details=False, machine=True, pythonize=True):
        args = [constants.cmd, "showvminfo"]

        if details:
            args += ["--details"]
        if machine:
            args += ["--machinereadable"]

        args += [self.__uuid]

        info = subprocess.check_output(args)
        parsed =  self.parse_info(info, machine, pythonize)
        parsed['string'] = info
        return parsed


    # Public: Unregister the VM and optionally delete
    #
    # delete - Boolean to delete the VM as well as unregister
    #
    # Returns True if unregistering was successful
    # Raises the generic CommandError otherwise
    def unregistervm(self, delete=False):
        args = [constants.cmd, "unregistervm", self.__uuid]
        if delete:
            args += ["--delete"]
        try:
            result = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            raise CommandError(args, e)

        return True


    # Public: Make modifications to the current VM
    #
    # option - string option to be modified
    # optargs - List of arguments relevant to the option
    #
    # Returns the output of the modifyvm command
    # Raises UnknownOptionError if the option or arguments are incorrect
    # Raises CommandError if the modifyvm command fails for some reason
    def modifyvm(self,option=None,*optargs):

        optargs = list(optargs)
        if not option in constants.modopts:
            raise UnknownOptionError("modifyvm", option)
        else:
            args = [constants.cmd, "modifyvm", self.name]

        if option in constants.modboolopts:
            if optargs[0] == True or optargs[0] == "on":
                args += ["on"]
            elif optargs[1] == False or optargs[0] == "off":
                args += ["off"]
            else:
                raise UnknownOptionError("modifyvm " + option, optargs[0])

        elif option in constants.modindexopts:
            try:
                index = int(optargs[0])
            except ValueError:
                raise UnknownOptionError("modifyvm " + option, optargs[0])
            args += ["--" + option + str(index)] + optargs[1:]

        elif option in constants.modenumopts.keys():
            if not optargs[0] in constants.modenumopts[option]:
                raise UnknownOptionError("modifyvm " + option, optargs[0])
            else:
                args += ["--" + option, optargs[0]]
        else:
            args += ["--" + option] + optargs

        try:
            args = map(str, args)
            result = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            raise CommandError(args, e)

        return result

    def start(self, gui="gui"):
        args = [constants.cmd, "startvm", self.name, "--type", gui]
        try:
            result = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            raise CommandError(args, e)
        self.started = True
        return result

    def controlvm(self,option=None,*optargs):

        optargs = list(optargs)
        if not option in constants.ctrlopts:
            raise UnknownOptionError("controlvm", option)
        else:
            args = [constants.cmd, "controlvm", self.name]

        if option in constants.ctrlboolopts:
            if optargs[0] == True or optargs[0] == "on":
                args += ["on"]
            elif optargs[1] == False or optargs[0] == "off":
                args += ["off"]
            else:
                raise UnknownOptionError("modifyvm " + option, optargs[0])

        elif option in constants.ctrlindexopts:
            try:
                index = int(optargs[0])
            except ValueError:
                raise UnknownOptionError("modifyvm " + option, optargs[0])
            args += ["--" + option + str(index)] + optargs[1:]

        # elif option in constants.ctrlenumopts.keys():
        #     if not optargs[0] in constants.ctrlenumopts[option]:
        #         raise UnknownOptionError("modifyvm " + option, optargs[0])
        #     else:
        #         args += ["--" + option, optargs[0]]
        else:
            args += [option] + optargs

        args = map(str, args)
        return execute(args)

    # Public: Discard current VM state
    #
    # Return True if the discard happened properly
    # Raise CommandError otherwise
    def discardstate(self):
        args = [constants.cmd, "discardstate", self.UUID]
        execute(args)
        return True

    # Public: Load VM state from a given filepath
    #
    # filepath - String giving path to the state path
    #
    # Return True if the adoption succeeded
    # Raise IOError if there is no such file
    #       CommandError if the command fails otherwise
    def adoptstate(self, filepath):
        args = [constants.cmd, self.UUID]
        if os.path.isfile(filepath):
            args = [constants.cmd, "adopstate", self.UUID, filepath]
        else:
            raise IOError("No such state file: " + filepath)

        execute(args)
        return True

    def __getattr__(self, name):
        try:
            value = self.info[constants.mod_to_ls[name]]
        except KeyError:
            value = self.info[name]
        return value

    def __setattr__(self, name, value):
        m = re.match('([a-zA-Z]+)([0-9])', name)
        if m:
            name = m.group(1)
            value = [value]
            value.insert(0,m.group(2))
        if name in constants.modopts and not self.started:
            self.modifyvm(name, *value)
        elif name in constants.ctrlopts and self.started:
                self.controlvm(name, *value)
        else:
            pass
        self.__dict__[name] = value

