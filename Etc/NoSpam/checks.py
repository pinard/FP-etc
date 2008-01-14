#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 1998, 99, 00, 01, 02, 03 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 1998.

u"""\
Do various checks for one message.
"""

import os, re
import tools

loewis_string = u"""\
 <martin.v.loewis@t-online.de>
   550 Mailbox quota exceeded / Mailbox voll.
"""

viral_subject_pattern = re.compile(
    u"(Approved"
    u"|Details"
    u"|My details"
    u"|Thank you!"
    u"|That movie"
    u"|Wicked screensaver"
    u"|Your application"
    u"|Your details"
    ')$'
    )

viral_body_pattern = re.compile(
    '(> )?'
    u"(Please see the attached file for details."
    u"|See the attached file for details"
    ')\n*$'
    )

virus_alert_pattern = re.compile(
    u"   V I R U S  A L E R T"
    u"|   A L E R T A   D E   V I R U S"
    u"|  Problem: Virus found"
    u"|  Reason: Unsafe file .* is removed!"
    u"|[0-9]\\) The attachment is infected"
    u"|A report on the virus is given at the end of this email"
    u"|ANTIVIRUS SYSTEM FOUND VIRUSES"
    u"|As a security precaution this mail was blocked and discarded"
    u"|Avertissement de la passerelle antivirus MailScanner"
    u"|BANNED FILENAME ALERT"
    u"|Content violation found in email message."
    u"|Executable attachment \\(not allowed\\)"
    u"|Our email scanner has detected a VIRUS in your email."
    u"|Since such content may contain viruses or other dangerous code"
    u"|SVP lire la pièce jointe «AlerteVirus.txt» pour plus d'informations."
    u"|SWEEP virus detection utility"
    u"|The infected message envelope follows"
    u"|The virus detector said this about the message:"
    u"|Virus\\(es\\) found."
    u"|WARNING! You have attempted to send an unacceptable message "
    u"|a potentially executable attachment"
    )

class Check:

    def __init__(self, message, run, checker):
        self.message = message
        self.run = run
        self.checker = checker
        text = message.as_string()
        position = text.find('\n\n')
        if position < 0:
            self.body = None
        else:
            self.body = text[position+2:]
        self.received_steps = None
        self.check_function = {
            'blacklists': self.check_blacklists,
            'body': self.check_body,
            'charset': self.check_charset,
            'check': self.check_check,
            'date': self.check_date,
            'domains': self.check_domains,
            'extensions': self.check_extensions,
            'from': self.check_from,
            'languages': self.check_languages,
            'locals': self.check_locals,
            'locutions': self.check_locutions,
            'mailers': self.check_mailers,
            'message_id': self.check_message_id,
            'mimetypes': self.check_mimetypes,
            'precedence': self.check_precedence,
            'received': self.check_received,
            'spambayes': self.check_spambayes,
            'subject': self.check_subject,
            'to_cc': self.check_to_cc,
            'viruses': self.check_viruses,
            'words': self.check_words,
            }
        try:
            import unpack
            self.unpacker = unpack.Unpacker(self.message, run, checker)
            for opcode, arguments in self.run.instructions:
                check = self.check_function.get(opcode)
                assert check is not None, (
                    u"Unrecognised `%s' directive." % opcode)
                check(arguments)
        finally:
            del self.message, self.body, self.run, self.checker, self.unpacker

    def check_blacklists(self, blacklists,
                         parsed_flag=[]):
        # Extract the From domain.
        text = self.message.get('From')
        if text is None:
            return
        from email.Utils import parseaddr
        pair = parseaddr(text)
        if not pair or not pair[1]:
            return
        fields = pair[1].lower().split('@')
        if len(fields) != 2:
            return
        user, domain = fields
        # Get a list of IP addresses.
        import DNS
        if not parsed_flag:
            DNS.ParseResolvConf()
            parsed_flag.append(None)
        numeric_ips = []
        for answer in DNS.Request(domain, qtype='a').req().answers:
            numeric_ips.append(answer['data'])
        if not numeric_ips:
            if not DNS.Request(domain, qtype='mx').req().answers:
                self.checker.reject(u"Domain `%s' is not resolved." % domain)
        # Validate IP addresses against blacklists.
        for numeric_ip in numeric_ips:
            fragments = numeric_ip.split('.')
            fragments.reverse()
            for blacklist in blacklists:
                if '.' not in blacklist:
                    blacklist += '.mail-abuse.org'
                domain = '.'.join(fragments) + '.' + blacklist
                if DNS.Request(domain, qtype='a').req().answers:
                    self.checker.reject(u"Listed in `%s'." % blacklist)

    def check_body(self, arguments):
        assert not arguments, arguments
        # Check for empty bodies.
        length = len(self.body)
        while length > 0 and self.body[length-1] == '\n':
            length -= 1
        if length == 0:
            self.checker.reject(u"Empty body.")
        # Check for lazy Martins.
        if loewis_string in self.body:
            self.checker.kill(u"Hmph! Martin's still away...")
        # Check for a few common aborted viruses.
        subject = self.get_decoded_subject()
        if viral_subject_pattern.match(subject):
            if self.message.is_multipart():
                parts = self.message.get_payload()
                if len(parts) == 1:
                    body = parts[0].get_payload(decode=True)
                    if viral_body_pattern.match(body):
                        self.checker.kill(u"Aborted virus?")
        # Check for returned mail about viruses.
        if virus_alert_pattern.search(self.body):
            self.checker.kill(u"VirusAdmin message (Alert string in Body).")
        if 'virus' in subject.lower():
            self.checker.reject(u"VirusAdmin message (First Subject).")
        for index, part in enumerate(self.unpacker.get_mime_parts()):
            mimetype = part.get_content_type()
            subject = self.get_decoded_subject(part)
            if index > 0 and subject:
                if viral_subject_pattern.match(subject):
                    self.checker.reject(
                        u"VirusAdmin message (Embedded Subject).")
            if mimetype == 'text/plain':
                body = part.get_payload(decode=True)
                if isinstance(body, str) and viral_body_pattern.match(body):
                    self.checker.reject(u"VirusAdmin message (Body).")
                    break

    def check_charset(self, arguments):
        assert not arguments, arguments
        content_types = [self.message.get('Content-Type')]
        for part in self.unpacker.get_mime_parts():
            content_types.append(part.get('Content-Type'))
        charsets = []
        for content_type in content_types:
            if content_type:
                match = re.search(r'charset=([^; \t\n]+)', content_type)
                if match:
                    charset = match.group(1).lower()
                    if charset and charset[0] == '"' and charset[-1] == '"':
                        charset = charset[1:-1]
                    if charset not in charsets:
                        charsets.append(charset)
        for charset in charsets:
            if charset not in ('iso-8859-1', 'iso-8859-2', 'iso-8859-3',
                               'iso-8859-9', 'iso-8859-15',
                               'unicode-1-1-utf-7','us-ascii', 'utf-8',
                               'windows-1252'):
                self.checker.reject(u"Message uses `%s' as a charset."
                                    % charset)

    def check_check(self, arguments):
        if arguments == ['usual']:
            arguments = ['body', 'charset', 'date', 'from', 'message_id',
                         'precedence', 'received', 'spambayes', 'subject',
                         'to_cc', 'viruses']
        for opcode in arguments:
            check = self.check_function.get(opcode)
            assert check is not None, (
                u"Unrecognised `%s' directive." % opcode)
            check(None)

    def check_date(self, arguments):
        assert not arguments, arguments
        date = self.message.get('Date')
        if not date:
            self.checker.reject(u"Missing Date.")
        else:
            from email.Utils import parsedate_tz
            if parsedate_tz(date) is None:
                self.checker.reject(u"Invalid Date.")

    def check_domains(self, map_names):
        user_domains = []
        from email.Utils import parseaddr
        text = self.message.get('From')
        if text is not None:
            pair = parseaddr(text)
            if pair is not None and pair[1]:
                user_domain = pair[1].split('@')
                if len(user_domain) == 2:
                    user_domains.append(user_domain)
        steps = self.get_received_steps()
        for by, helo_from, real_from, ip_from, line in steps:
            for domain in by, helo_from, real_from:
                if domain is not None:
                    user_domain = None, domain
                    if user_domain not in user_domains:
                        user_domains.append(user_domain)
        for user, domain in user_domains:
            self.progressive_lookup(user, domain, map_names)

    def check_extensions(self, map_names):
        for part in self.unpacker.get_mime_parts():
            name = part.get_filename()
            if name is None:
                continue
            extension = os.path.splitext(name)[1]
            if not extension:
                continue
            key = extension.lower()
            for map_name in map_names:
                value = self.checker.get_value(
                    map_name, key, u"Unaccepted extension `%s'" % extension)
                if value is not None:
                    break

    def check_from(self, arguments,
                   all_numeric=re.compile('[0-9][0-9]+$')):
        assert not arguments, arguments
        from email.Utils import parseaddr
        text = self.message.get('From')
        pair = text and parseaddr(text)
        if not pair or not pair[1]:
            self.checker.reject(u"Missing From.")
            return
        text = pair[1].lower()
        if not text:
            self.checker.reject(u"Empty From.")
            return
        fields = text.split('@')
        if len(fields) != 2:
            self.checker.reject(u"Invalid From `%s'." % text)
            return
        user, domain = fields
        if all_numeric.match(user):
            self.checker.reject(u"All numeric user `%s'." % user)
        fields = domain.split('.')
        if len(fields) < 2:
            self.checker.reject(u"Domain `%s' not fully qualified." % domain)
            return
        if domain == 'hotmail.com':
            if not self.message.get('X-Originating-IP'):
                self.checker.reject(u"Forged From `hotmail.com'.")

    def check_languages(self, languages):
        languages = [language.capitalize() for language in languages]
        if languages:
            import lingua
            guesser = lingua.Guesser(self.run.debug >= 3)
            language = guesser.language(self.get_subject_and_body())
            if language is not None and language not in languages:
                self.checker.reject(u"Message written in %s." % language)

    def check_locals(self, map_names):
        from email.Utils import getaddresses
        pairs = getaddresses(self.message.get_all('From', [])
                             + self.message.get_all('To', [])
                             + self.message.get_all('Cc', []))
        for pair in pairs:
            if pair is not None and pair[1]:
                address = pair[1].lower()
                fields = address.split('@')
                if len(fields) != 2:
                    self.checker.reject(u"Invalid address `%s'." % address)
                    continue
                user, domain = fields
                if domain in self.run.heres:
                    for item in user, address:
                        for map_name in map_names:
                            value = self.checker.get_value(
                                map_name, item,
                                u"Rejected domain `%s'." % domain)
                            if value is not None:
                                break
                        if value is not None:
                            break
                    else:
                        self.checker.reject(u"Address `%s' locally unknown."
                                            % pair[1])
        for pair in pairs:
            if pair is not None and pair[1]:
                user_domain = pair[1].split('@')
                if len(user_domain) == 2:
                    user, domain = user_domain
                    if self.progressive_lookup(user, domain, map_names):
                        break
        else:
            if not self.run.silence_locals:
                self.checker.reject(u"Neither origin nor destination is local.")

    def check_locutions(self, map_names):
        text = self.get_subject_and_body()
        for map_name in map_names:
            for locution in tools.map_keys(map_name):
                if locution in text:
                    self.checker.get_value(map_name, locution,
                                           u"Locution `%s' rejected by `%s'."
                                           % (locution, map_name))

    def check_mailers(self, map_names):
        text = self.message.get('X-Mailer')
        if not text:
            return
        if self.run.debug >= 2:
            self.checker.report('DEBUG: X-Mailer: %s' % text)
        text = re.sub(r' *\([^)]+\)', '', text).lower()
        for map_name in map_names:
            self.checker.get_value(map_name, text,
                                   u"Mass mailer `%s' rejected by `%s'."
                                   % (text, map_name))

    def check_message_id(self, arguments,
                         legal=re.compile(r'<[^()<>@,;:\\"\[\]]+@'
                                          r'[^()<>@,;:\\"\[\]]+>$'),
                         usual=re.compile(r'<([-.A-Za-z0-9]+%)?'
                                          r'[-+.A-Za-z0-9$_]+@'
                                          r'[-.A-Za-z0-9]+>$')):
        assert not arguments, arguments
        text = self.message.get('Message-ID')
        if not text:
            self.checker.reject(u"Missing Message-ID.")
            return
        if not legal.match(text):
            self.checker.reject(u"Invalid Message-ID `%s'." % text)
            return
        if not usual.match(text):
            self.checker.reject(u"Unusual Message-ID `%s'." % text)

    def check_mimetypes(self, map_names):
        for part in self.unpacker.get_mime_parts():
            mimetype = part.get_content_type()
            fragments = mimetype.split('/')
            if len(fragments) != 2:
                self.checker.reject(u"Invalid Content-Type `%s'"
                                    % mimetype)
                continue
            for mimetype in ('%s/%s' % tuple(fragments),
                             '%s/*' % fragments[0],
                             '*/%s' % fragments[1]):
                for map_name in map_names:
                    value = self.checker.get_value(
                        map_name, mimetype,
                        u"Unaccepted MIME Content-Type `%s/%s'"
                        % tuple(fragments))
                    if value is not None:
                        break
                if value is not None:
                    break
        # HTML only messages are very suspicious.
        text = self.message.get_content_type()
        if text and text == 'text/html':
            self.checker.reject(u"HTML only message.")
        else:
            # Broken HTML even more! :-)
            body = self.body
            start = 0
            position = body.find('\n', start)
            while position == start:
                start += 1
            if position >= 0 and body[start:start+6].lower() == '<html>':
                self.checker.reject(u"Undeclared HTML only message.")

    def check_precedence(self, arguments):
        assert not arguments, arguments
        text = self.message.get('Precedence')
        if text and text.lower() == 'bulk':
            self.checker.reject(u"Bulk precedence.")

    def check_received(self, arguments):
        assert not arguments, arguments
        steps = self.get_received_steps()
        if self.run.debug >= 2:
            for step in steps:
                self.checker.report(u"DEBUG: " + str(step))
        previous_by = None
        for by, helo_from, read_from, ip_from, line in steps:
            #if by is None:
            #    self.checker.reject("Missing `by' clause in Received.")
            for domain in helo_from, read_from, by:
                if domain is not None:
                    # DOMAIN may be `localhost', even `nobody' or `unknown'.
                    if not re.match(r'[-A-Za-z0-9]+(\.[-A-Za-z0-9]+)*$',
                                    domain):
                        self.checker.reject(
                            u"Invalid domain `%s' in Received by `%s'."
                            % (domain, by))
            if previous_by is not None and helo_from is not None:
                if previous_by not in (helo_from, read_from):
                    # Sadly, mismatches seem to be a bit common.
                    #self.checker.reject(
                    #     FIXME!  Report helo_from and read_from, not by.
                    #    "Mismatch from `%s' to `%s'."
                    #    % (previous_by, by))
                    pass
            previous_by = by

    def check_spambayes(self, arguments,
                        cache=[]):
        # All arguments are optional.  First is REJECT threshold.
        if arguments:
            spam_cutoff = float(arguments[0])
            arguments = arguments[1:]
        else:
            try:
                from spambayes.Options import options
            except ImportError:
                return
            spam_cutoff = options.spam_cutoff
        assert 0.0 < spam_cutoff <= 1.0, spam_cutoff
        # Second argument is KILL threshold.
        if arguments:
            kill_cutoff = float(arguments[0])
            arguments = arguments[1:]
        else:
            kill_cutoff = 1.00
        assert spam_cutoff <= kill_cutoff <= 1.0, (spam_cutoff, kill_cutoff)
        assert not arguments, arguments
        # Fetch data base, caching it on first call.
        if cache:
            data_base = cache[0]
        else:
            data_base_name = os.path.expanduser('~pinard/etc/nospam/hammie.db')
            try:
                from spambayes import hammie
                data_base = hammie.open(data_base_name, True, 'r')
            except (ImportError, IOError):
                data_base = None
            cache.append(data_base)
        if data_base is None:
            return
        # Evaluate spamicity and act accordingly.
        spamicity = data_base.score(self.message)
        if spamicity > kill_cutoff:
            self.checker.kill(u"Spambayes score is %4.2f." % spamicity)
        elif spamicity > spam_cutoff:
            self.checker.reject(u"Spambayes score is %4.2f." % spamicity)
        elif self.run.debug >= 2:
            self.checker.report(u"DEBUG: Spambayes score is %4.2f." % spamicity)

    def check_subject(self, arguments,
                      has_noise=re.compile(
        r'[^A-Za-z0-9.,:;()\[\]\200-\377]{5}|[0-9]{6}'),
                      has_word=re.compile(r'[A-Za-z][a-z]{2}'),
                      has_money=re.compile(r'\$(\$+|[1-9][,.]?[0-9]+)')):
        assert not arguments, arguments
        text = self.get_decoded_subject()
        if not text:
            self.checker.reject(u"Missing Subject.")
            return
        if has_noise.search(text):
            self.checker.reject(u"Noisy Subject.")
        if not has_word.search(text):
            self.checker.reject(u"Subject without mixed case word.")
        if has_money.search(text):
            self.checker.reject(u"Money value within Subject.")
        histogram = {1: 0, 2: 0}
        for fragment in text.split():
            if len(fragment) in histogram:
                histogram[len(fragment)] += 1
            else:
                histogram[len(fragment)] = 1
        if histogram[1]*2 + histogram[2] > 10:
            self.checker.reject(u"Many small words in Subject.")

    def check_to_cc(self, arguments):
        assert not arguments, arguments
        from email.Utils import getaddresses
        count = len(getaddresses(self.message.get_all('To', [])
                                 + self.message.get_all('Cc', [])))
        if count > 50:
            self.checker.reject(u"More than 50 recipients (%d)." % count)

    def check_viruses(self, arguments):
        assert not arguments, arguments
        import virus
        for scanner in virus.all():
            if scanner.check():
                scanner.scan(self.unpacker.get_full_unpack_directory(),
                             self.checker)

    def check_words(self, map_names):
        words = tools.find_words(self.get_decoded_subject())
        for word in words:
            for map_name in map_names:
                value = self.checker.get_value(
                    map_name, word,
                    u"Word `%s' rejected by `%s'." % (word, map_name))
                if value is not None:
                    break

    # Service methods for checks.

    def get_subject_and_body(self):
        text = self.get_decoded_subject()
        if text:
            return text + '\n' + self.body
        return self.body

    def get_decoded_subject(self, message=None):
        text = self.get_decoded_header('Subject', message).strip()
        if text.startswith('{Spam?}'):
            text = text[8:].lstrip()
        if text.startswith('{Virus?}'):
            text = text[8:].lstrip()
        while text.startswith('Re:'):
            text = text[3:].lstrip()
        return text

    def get_decoded_header(self, header, message=None):
        if message is None:
            message = self.message
        from email.Header import decode_header
        pairs = []
        for line in message.get_all(header, []):
            pairs += decode_header(line)
            pairs.append(('\n', None))
        fragments = []
        for string, charset in pairs:
            fragments.append(string)
        return ''.join(fragments)

    def get_received_steps(self):
        if self.received_steps is None:
            steps = self.received_steps = []
            by = helo_from = real_from = ip_from = None
            for line in self.message.get_all('Received', []):
                #if line.startswith('(qmail '):
                #    # Daniel B. surely did not impress me on this one! :-(
                #    continue
                by = helo_from = real_from = ip_from = None
                if helo_from is None:
                    match = re.search((r'from ([-.A-Za-z0-9]+)'
                                       r'\s+\(([-.A-Za-z0-9]+)'
                                       r'\s+\[([-.0-9]+)\]\)'),
                                      line)
                    if match:
                        helo_from, real_from, ip_from = match.group(1, 2, 3)
                if helo_from is None:
                    match = re.search((r'from ([-.A-Za-z0-9]+)'
                                       r'\s+\(\[([-.0-9]+)\]'
                                       r'\s+helo=([-.A-Za-z0-9]+)\)'),
                                      line)
                    if match:
                        helo_from, real_from, ip_from = match.group(1, 3, 2)
                if helo_from is None:
                    match = re.search((r'from ([-.A-Za-z0-9]+)'
                                       r'\s+\[([-.0-9]+)\]'),
                                      line)
                    if match:
                        helo_from, ip_from = match.group(1, 2)
                if helo_from is None:
                    match = re.search((r'from \[([-.0-9]+)\]'
                                       r'\s+\(HELO ([-.A-Za-z0-9]+)\)'),
                                      line)
                    if match:
                        helo_from, ip_from = match.group(2, 1)
                line = re.sub(r'\([^)]*\)', '', line)
                match = re.search(r'by\s+([-.A-Za-z0-9]+)', line)
                if match:
                    by = match.group(1)
                if helo_from is None:
                    match = re.search(r'from ([-.A-Za-z0-9]+)', line)
                    if match:
                        helo_from = match.group(1)
                steps.append((by, helo_from, real_from, ip_from, line))
            steps.reverse()
            if not steps:
                self.checker.reject(u"Missing Received.")
        return self.received_steps

    def progressive_lookup(self, user, domain, map_names):
        user = (user or '').lower()
        domain = domain.lower()
        fragments = domain.split('.')

        def get_value(map_name, text, type):
            return self.checker.get_value(
                map_name, text,
                u"%s `%s' rejected by `%s'." % (type, text, map_name))

        for map_name in map_names:
            # Check the whole address with progressively reduced domains.
            if len(fragments) > 1:
                for counter in range(len(fragments) - 1):
                    value = get_value(
                        map_name, user + '@' + '.'.join(fragments[counter:]),
                        'Address')
                    if value is not None:
                        return value
            # Check user part.
            if user and (not self.run.heres or domain in self.run.heres):
                value = get_value(map_name, user, 'User')
                if value is not None:
                    return value
            # Check domain part, from longest subdomain to shortest.
            if len(fragments) > 1:
                for counter in range(len(fragments) - 1):
                    value = get_value(map_name, '.'.join(fragments[counter:]),
                                      'Domain')
                    if value is not None:
                        return value
            # Check domain fragments.
            for text in fragments:
                if text:
                    value = get_value(map_name, text, 'Fragment')
                    if value is not None:
                        return value
