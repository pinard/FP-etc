#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 1999, 2000, 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 1998, 2001.

"""\
Schemes for packing files.
"""

import os, re, tempfile, types
from . import tools

forwarded_pattern = re.compile(
    "( and with the following headers:\n--+"
    "| undelivered message follows \n--+"
    "|--+ Below this line is a copy of the message."
    "|--+ Enclosed is a copy of the request I received."
    "|--+ Original Message Header --+"
    "|--+ Original [Mm]essage [Ff]ollows --+"
    "|--+ This is a copy of the message, including all the headers. --+"
    "|--+ [0-9]+ or so are included here."
    "|Last-Attempt-Date: .*"
    "|The headers from the E-mail are:"
    "|\\.\\. letter returned to .* \\.\\. \n--+"
    "|\\|--+ Message text follows: \\(body too large, truncated\\) --+\\|"
    "|your original message appears below"
    ')\n+'
    )

class Unpacker:
    def __init__(self, message, run, checker):
        self.message = message
        self.run = run
        self.checker = checker
        self.tmpdir = None
        self.fully_unpacked = False

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        if self.tmpdir is not None:
            tempfile.tempdir = self.saved_tempdir
            if not self.run.keep:
                assert '/tmp' in self.tmpdir, self.tmpdir
                os.system('rm -rf %s' % self.tmpdir)
            self.tmpdir = None

    def get_full_unpack_directory(self):
        if not self.fully_unpacked:
            original_directory = os.getcwd()
            if self.tmpdir is None:
                self.get_mime_parts()
            directory_stack = [self.tmpdir]
            while directory_stack:
                directory = directory_stack[-1]
                directory_stack = directory_stack[:-1]
                # Open all containers in this directory.
                for base in os.listdir(directory):
                    name = os.path.join(directory, base)
                    if os.path.islink(name):
                        pass
                    elif os.path.isdir(name):
                        directory_stack.append(name)
                    elif os.path.isfile(name):
                        # Try to execute an archive unpacker for this file.
                        buffer = file(name).read()
                        hint = os.popen('file -b %s' % repr(name)).read()[:-1]
                        if self.run.debug:
                            self.checker.report('DEBUG: %s: %s' % (base, hint))
                        for archiver in all():
                            if archiver.check(buffer, name, hint):
                                path = tempfile.mktemp()
                                os.mkdir(path, 0o700)
                                os.chdir(path)
                                directory_stack.append(path)
                                self.checker.report(
                                    "NOTE: %s file %s -> %s/"
                                    % (archiver.name, base, path))
                                try:
                                    if not archiver.unpack(buffer, name,
                                                           self.checker):
                                        self.checker.report(
                                            "WARNING: `%s' failed"
                                            " (while handling `%s')."
                                            % (archiver.program, name))
                                except Archiver.Program_Not_Found:
                                    self.checker.report(
                                        "WARNING: Don't know how to handle"
                                        " `%s' (archiver `%s' not found)."
                                        % (name, archiver.program))
            os.chdir(original_directory)
            self.fully_unpacked = True
        return self.tmpdir

    def get_mime_parts(self):
        if self.tmpdir is None:
            self.tmpdir = tempfile.mktemp()
            if self.run.keep:
                import sys
                sys.stderr.write("* Work files under `%s'.\n" % self.tmpdir)
            self.saved_tempdir = tempfile.tempdir
            tempfile.tempdir = self.tmpdir
            os.mkdir(self.tmpdir, 0o700)
            text = self.message.as_string()
            file(os.path.join(self.tmpdir, 'original'), 'w').write(text)
            self.mime_parts = []
            from email import message_from_string, Errors
            try:
                message = message_from_string(text)
            except Errors.MessageParseError:
                self.checker.reject("Invalid message structure.")
                self.mime_parts = []
            else:
                self.mime_parts = list(message.walk())
            index = 0
            while index < len(self.mime_parts):
                if len(self.mime_parts) > 30:
                    self.checker.reject("Message has more than 30 parts.")
                    break
                message = self.mime_parts[index]
                mimetype = message.get_content_type()
                #print index, len(self.mime_parts), len(str(message)), \
                #      mimetype, message.get('Subject'), repr(str(message))
                if mimetype in ('text/plain', 'text/rfc822-headers'):
                    message = self.find_forwarded(message)
                    if message is not None:
                        #if self.run.debug:
                        #    subject = message.get('Subject')
                        #    if subject is not None:
                        #        self.checker.report(
                        #            'DEBUG: Nested-Subject: %s' % subject)
                        self.mime_parts += list(message.walk())
                index += 1
        return self.mime_parts

    def find_forwarded(self, message):
        try:
            text = message.as_string()
        except IndexError:              # ?? FIXME!
            return
        position = text.find('\n\n')
        if position < 0:
            return
        position += 2
        while position < len(text) and text[position] == '\n':
            position += 1
        from email import message_from_string, Errors
        try:
            message = message_from_string(text[position:])
            if not message.as_string().startswith('\n'): # a bug?? FIXME!
                return message
        except Errors.MessageParseError:
            pass
        match = forwarded_pattern.search(text, position)
        if match:
            try:
                return message_from_string(text[match.end():])
            except Errors.MessageParseError:
                pass

        ## Try to see if the contents is itself a message.
        #is_message = True
        #message = StringIO(text)
        #headers = []
        #line = message.readline()
        #while is_message and line:
        #    if line.startswith('>From'):
        #        line = line[1:]
        #    if line.startswith('From ') and not headers:
        #        headers.append(line)
        #        line = message.readline()
        #    elif line == '\n':
        #        break
        #    else:
        #        match = re.match('([-_A-Za-z0-9]+):[ \t]', line)
        #        if match:
        #            headers.append(line)
        #            line = message.readline()
        #            while line and line[0] in ' \t':
        #                headers.append(line)
        #                line = message.readline()
        #        else:
        #            is_message = False
        #if is_message:
        #    known_match = re.compile(
        #        '(Date|From|MIME-Version|Message-ID|Received'
        #        '|Return-Path|Subject|To):', re.I).match
        #    counter = 0
        #    for line in headers:
        #        if known_match(line):
        #            counter += 1
        #    if counter < 3:
        #        is_message = False
        #self.mime_parts.append(message)
 
# Unpacking schemes besides MIME.

# Inspired by AMaViS 0.2.1, see http://amavis.org/.  AMaViS itself is:
# - written by Mogens Kjaer, Carlsberg Laboratory, <mk@crc.dk>,
# - modified by Juergen Quade, Softing GmbH, <quade@amavis.org>,
# - modified and maintained by Christian Bricart <shiva@aachalon.de>,
# - modified by Chris L. Mason <cmason@unixzone.com>,
# - modified and maintained by Rainer Link, SuSE GmbH <link@suse.de>.
# Copyright (C) 1996..2000 the people mentioned above.  Also GPL'ed.

def all(instances=[]):
    if not instances:
        for object in globals().values():
            if (type(object) is type
                and issubclass(object, Archiver)
                and object not in (Archiver, Self_Extracting)
                ):
                instances.append(object())
    return instances

class Archiver:
    Program_Not_Found = 'Program not found'
    name = 'Generic'
    program = 'Unknown'

    def check(self, buffer, name, hint):
        return False

    def unpack(self, buffer, name, checker):
        raise self.Program_Not_Found

    def get_path(self):
        path = tools.get_program_path(self.program)
        if path is None:
            raise self.Program_Not_Found(self.program)
        return path

class TNEF(Archiver):
    name = 'TNEF encoded'
    program = 'tnef'

    def check(self, buffer, name, hint):
        return re.match('data|TNEF|Transport Neutral Encapsulation Format',
                        hint)

    def unpack(self, buffer, name, checker):
        import sys
        status = tools.run_program(
            ('%s -v -C %s -f %s 2>&1'
             % (self.get_path(), os.getcwd(), name)),
            checker.report)
        # Status is likely 1 (Seems not to be a TNEF file) when `data'.
        return status == 0

class Self_Extracting(Archiver):

    def check(self, buffer, name, hint):
        return re.search('executable \(EXE\)|^MS Windows.*executable',
                         hint)

class Self_Extracting_PKZip(Self_Extracting):
    name = 'Self-extracting PKZip'

    def check(self, buffer, name, hint):
        return (Self_Extracting.check(self, buffer, name, hint)
                and 'PK' in buffer)

    #        if [ "x${unzip}" != "x" ] && [ -x ${unzip} ]
    #        then
    #          if [ "x${zipsecure}" != "x" ] && [ -x ${zipsecure} ]
    #          then
    #            if [ -e $name ]
    #            then
    #              echo "Unziping self extracting $E" >> ${self.tmpdir}/${logfile}
    ##             pid=$$
    ##             pid doesn't make sense for me, use maxlevel instead
    #              pid=${maxlevel}
    #              cat $name | ${zipsecure} -q > secure.${pid}.zip
    #              if ${test} $? -eq 0
    #              then
    #                ${unzip} -q secure.${pid}.zip
    #                if ${test} $? -eq 0
    #                then
    #                   mv $name ${self.tmpdir}/unpacked/self-extracting
    #                  doneit=0
    #                fi
    #              fi
    #              rm secure.${pid}.zip
    #            fi
    #          else
    #            echo "WARNING! unZIPing not secure (no zipsecure)" | log_error
    #            echo "--> no unZIPing done !" | log_error
    #          fi
    #        else
    #          echo "WARNING! Don't know how to handle $E (no unzip)" | log_error
    #        fi
    #        #doneit=0
    #        #continue
    #      fi

class Self_Extracting_RAR(Self_Extracting):
    name = 'Self-extracting RAR'
    program = 'unrar'

    def check(self, buffer, name, hint):
        return (Self_Extracting.check(self, buffer, name, hint)
                and 'RAR' in buffer)

    #            echo "UnRARing self extracting $E" >> ${self.tmpdir}/${logfile}
    #            ${unrar} e -y -inul $name
    #            if ${test} $? -eq 0
    #            then
    #              mv $name ${self.tmpdir}/unpacked/self-extracting
    #              doneit=0
    #            fi

class Self_Extracting_LHA(Self_Extracting):
    name = 'Self-extracting LHA'
    program = 'lha'

    def check(self, buffer, name, hint):
        return (Self_Extracting.check(self, buffer, name, hint)
                and 'LHA' in buffer)

    #            echo "Lharcing self extracting $E" >> ${self.tmpdir}/${logfile}
    #            ${lha} efq $name > /dev/null 2>&1
    #            if ${test} $? -eq 0
    #            then
    #              mv $name ${self.tmpdir}/unpacked/self-extracting
    #              doneit=0
    #            fi

class Zip(Archiver):
    name = 'Zipped'
    ##################### test for zip file ##############################
    #
    #    echo ${hint} | ${fgrep} ${grep_quiet_args} "Zip archive data"
    #    if ${test} $? -eq 0
    #    then
    #      if [ "x${unzip}" != "x" ] && [ -x ${unzip} ]
    #      then
    #       if [ "x${zipsecure}" != "x" ] && [ -x ${zipsecure} ]
    #       then
    #        echo "Unziping $E" >> ${self.tmpdir}/${logfile}
    ##        pid=$$
    ##       pid doesn't make sense for me, use maxlevel instead
    #        pid=${maxlevel}
    #        cat $name | ${zipsecure} -q > secure.${pid}.zip
    #        if ${test} $? -eq 0
    #        then
    #          ${unzip} -q secure.${pid}.zip
    #          if ${test} $? -eq 0
    #          then
    #            rm $name
    #            doneit=0
    #          fi
    #          rm secure.${pid}.zip
    #        fi
    #       else
    #         echo "WARNING! unZIPing not secure (no zipsecure)" | log_error
    #         echo "--> no unZIPing done !" | log_error
    #       fi
    #      else
    #        echo "WARNING! Don't know how to handle $E (no unzip)" | log_error
    #      fi
    #      #doneit=0
    #      continue
    #    fi

class Tar(Archiver):
    name = 'Tarred'
    ########################## test for tar archive ######################
    #
    #    echo ${hint} | ${fgrep} ${grep_quiet_args} "tar archive"
    #    if ${test} $? -eq 0
    #    then
    #     if [ "x${tar}" != "x" ] && [ -x ${tar} ]
    #     then
    #      if [ "x${securetar}" != "x" ] && [ -x ${securetar} ]
    #      then
    #        echo "Untaring $E" >> ${self.tmpdir}/${logfile}
    #        cat $name | ${securetar} -q | ${tar} xf -
    #        if ${test} $? -eq 0
    #        then
    #          rm $name
    #          doneit=0
    #        fi
    #      else
    #        echo "WARNING! unTARing not secure (no securetar)" | log_error
    #        echo "--> no unTARing done !" | log_error
    #      fi
    #     else
    #      echo "WARNING! Don't know how to handle $E (no tar)" | log_error
    #     fi
    #     #doneit=0
    #     continue
    #    fi

class Compress(Archiver):
    name = 'Compressed'
    program = 'uncompress'

    def check(self, buffer, name, hint):
        return 'compress\'d' in hint

    def unpack(self, buffer, name, checker):
        base = os.path.split(name)[1]
        if base[-2:] == '.Z':
            base = base[:-2]
        status = tools.run_program(
            '%s < %s > %s' % (self.get_path(), name, base),
            checker.report)
        return status == 0

class Gzip(Archiver):
    name = 'Gzipped'
    program = 'gunzip'

    def check(self, buffer, name, hint):
        return 'gzip compressed data' in hint

    def unpack(self, buffer, name, checker):
        base = os.path.split(name)[1]
        if base[-3:] == '.gz':
            base = base[:-3]
        elif base[-4:] == '.tgz':
            base = base[:-4] + '.tar'
        status = tools.run_program(
            '%s < %s > %s' % (self.get_path(), name, base),
            checker.report)
        return status == 0

class Bzip2(Archiver):
    name = 'Bzipped'
    program = 'bunzip2'

    def check(self, buffer, name, hint):
        return re.search('bzip2? compressed', hint)

    def unpack(self, buffer, name, checker):
        base = os.path.split(name)[1]
        if base[-3:] == '.bz':
            base = base[:-3]
        elif base[-4:] == '.bz2':
            base = base[:-4]
        elif base[-4:] == '.tbz':
            base = base[:-4] + '.tar'
        elif base[-5:] == '.tbz2':
            base = base[:-5] + '.tar'
        else:
            base += '.out'
        status = tools.run_program(
            '%s < %s > %s' % (self.get_path(), name, base),
            checker.report)
        return status == 0

class RAR(Archiver):
    name = 'RARred'
    program = 'unrar'

    def check(self, buffer, name, hint):
        return 'RAR' in hint

    #        echo "UnRARing $E" >> ${self.tmpdir}/${logfile}
    #        ${unrar} e -y -inul $name
    #        if ${test} $? -eq 0
    #        then
    #          rm $name
    #          doneit=0
    #        fi

class Arj(Archiver):
    name = 'ARJed'
    program = 'unarj'

    def check(self, buffer, name, hint):
        return 'ARJ' in hint

    #        echo "UnARJing $E" >> ${self.tmpdir}/${logfile}
    #        ${unarj} e $name > /dev/null
    #        if ${test} $? -eq 0
    #        then
    #          rm $name
    #          doneit=0
    #        fi

class Lha(Archiver):
    name = 'LHAred'
    program = 'lha'

    def check(self, buffer, name, hint):
        return re.search('LHA', hint) # FIXME: fgrep -i

    #        echo "UnLHArcing $E" >> ${self.tmpdir}/${logfile}
    #        ${lha} efq $name > /dev/null 2>&1
    #        if ${test} $? -eq 0
    #        then
    #          rm $name
    #          doneit=0
    #        fi

class Zoo(Archiver):
    name = 'Zooed'
    program = 'zoo'

    def check(self, buffer, name, hint):
        return 'Zoo' in hint

    #        echo "UnZOOing $E" >> ${self.tmpdir}/${logfile}
    #        ${zoo} eq. $name
    #        if ${test} $? -eq 0
    #        then
    #          rm $name
    #          doneit=0
    #        fi

class Arc(Archiver):
    name = 'ARCed'
    program = 'arc'

    def check(self, buffer, name, hint):
        return 'ARC' in hint

    #        echo "UnARCing $E" >> ${self.tmpdir}/${logfile}
    #        ${arc} eon $name
    #        if ${test} $? -eq 0
    #        then
    #          rm $name
    #          doneit=0
    #        fi

class Freeze(Archiver):
    name = 'Frozen'
    program = 'unfreeze'

    def check(self, buffer, name, hint):
        return 'frozen' in hint

    #        echo "Unfreezing $E" >> ${self.tmpdir}/${logfile}
    #        ${unfreeze} $name
    #        if ${test} $? -eq 0
    #        then
    #          rm $name
    #          doneit=0
    #        fi

class Binhex(Archiver):
    name = 'Binhexed'
    program = 'xbin'

    def check(self, buffer, name, hint):
        handle = file(name)
        for counter in range(4):
            line = handle.readline()
            if not line:
                break
            if '(This file must be converted with BinHex 4.0)' in line:
                return True
        return False

    #        echo "Unpacking binhex file $E" >> ${self.tmpdir}/${logfile}
    #        ${xbin} $name
    #        rm $name *.info *.rsrc
    #        mv *.data $name
    #        doneit=0

class Uuencode(Archiver):
    name = 'Uuencoded'
    program = 'uudecode'
    uu_pattern = re.compile('^begin(-base64)? [0-7]+ [^ ]*?([^ /\n]+)$', re.M)

    def check(self, buffer, name, hint):
        return Uuencode.uu_pattern.search(buffer)

    #      if [ "x${uudecode}" != "x" ] && [ -x ${uudecode} ]
    #      then
    #        echo "Unpacking uuencoded file $E" >> ${self.tmpdir}/${logfile}
    #        if [ "$uudecode_pipe" = "yes" ]
    #        then
    #          cat $name | ${uudecode} -p > "$E.uudecode.${maxlevel}"
    #        else
    #          ${uudecode} -o "$E.uudecode.${maxlevel}" $name
    #        fi
    #        if ${test} $? -eq 0
    #        then
    #          rm $name
    #          doneit=0
    #        fi

    def xxx():
            # Split lines, Unix or DOS.
            lines = buffer.replace('\r\n', '\n').split('\n')
            # Remove prefix and suffix white lines.
            while lines and lines[0].strip() == '':
                del lines[0]
            # Prepare to recognise uuencoded data.
            terminator = None
            # Find where the data starts.
            start = 0
            while start < len(lines):
                match = Uuencode.uu_pattern.match(lines[start])
                if match:
                    if match.group(1):
                        terminator = '====\n'
                    else:
                        terminator = 'end\n'
                    break
                start += 1
            # Find where the data ends.
            end = len(lines)
            while end > start:
                if lines[end-1] == terminator:
                    break
                end -= 1
            # If contents erroneous or empty, we still have an empty part.
            if terminator and lines[end-1] != terminator:
                return
            if start == end:
                self.mime_parts.append(message)
                return
            # Prepare a work file that will uudecode to the proper location.
            work = tempfile.mktemp()
            name = match.group(2)
            output = os.popen('uudecode', 'w')
            output.write('begin%s 600 %s\n' % (match.group(1) or '', work))
            start += 1
            output.writelines(lines[start:end])
            output.close()
            self.mime_parts.append(message)
