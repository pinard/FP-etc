#!/usr/bin/env python3
# Copyright © 1990, 2003 Free Software Foundation, Inc.
# François Pinard <pinard@iro.umontreal.ca>, 1988.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 1, or (at your option)
# any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""\
Dual tournament sort with polyphased merge.

General description of the sort process.

   This module accepts from the user one record at a time and do a
   single incremental heap sort of those records in memory.  If the heap
   fills up, the memory sort transforms into a dual tournament sort
   to disk, with runs distributed to work files in such a way that a
   polyphased merge will be possible.

   When the user first requests a record from this module, the module
   assumes that all records to be sorted have been given.  It completes
   the heap sort in memory or, alternatively, it completes both
   tournaments and executes all polyphased merge passes but the last.
   Then, the memory sort or final disk merge is incrementally completed
   while passing back, one at a time, sorted records to the user.

The comparison function.

   The user provides the comparison routine as a function having two
   arguments, and which returns a negative number if the first pointed
   record should precede the second according to their respective keys,
   a positive number if the first record should follow the second
   instead, and zero if the two records have equal keys.  The user has
   only one comparison function to implement descending keys or to
   simulate multiple keys, these kinds of hacks should be easy to do.

   However, the algorithms rely heavily on this comparison function,
   it is mandatory that the function establishes a strict order
   relation with the usual antisymmetric, transitive and antireflexive
   properties.  Any fuzziness in this area could cause a lot more
   problems than incorrect results, among which assert errors of all
   kinds in the module.  So, if something goes wrong, you should check
   the ordering properties of the comparison function before anything
   else.

Efficiency of the algorithm.

   The algorithm is choosen to minimize input/output time in a context
   of a system capable of high throughput for sequentially accessed
   disk files, often achieved using read-ahead/write-behind overlap
   capabilities of the input/output system.  It is assumed that random
   positionning requires some overhead startup time that could be high
   compared to a few useless sequential reading/copying of disk sectors.
   If this assumption is false, other approaches to disk sorting could
   prove to be more efficient.

   Given some amount of memory for the tournaments, run lengths on
   disk would be exactly this amount in the worst case, and should
   average twice this memory for a random sequence of keys.  But in most
   practical cases, there is some correlation between the original order
   and the sort order, so the run lengths tend to be higher than the
   theoretical average case and very higher in a non-negligible number
   of situations.  Longer the runs, more efficient the merge phase.

   However, the heap sort and tournament algorithm worst cases consist
   in an already sorted sequence, so the ideal case for input/output
   turns out to be the worst for CPU consumption.  Instead of using,
   say, quicksorts in memory to produce run of fixed lengths, longer
   runs are worth the extra CPU expense.  If the sort fits completely
   in memory, the algorithm used will not have been the best, we then
   rather use the built-in Python sort (so-called "timsort").  In fact,
   this module does not construct the heap until the memory fills up.
   Then, the heap is set up all at once.  Setting the heap is only half
   of a sort, so in theory at least, built-in sort would be overdoing.

Memory management.

   The main part of the memory is used for the heap, which has a maximum
   size stated in number of records.  Records are created and provided
   by the caller, and since references to these are kept for a while
   within the heap, records are effectively locked within memory until
   they actually leave the heap.  Of course, the user should not modify
   a record once it has been given to the sorting process, otherwise,
   the user should have provided copies.

   Record contents are only moved while being written into a work file's
   buffer or being read back from a work file's buffer.  In all other
   cases, references are moved, never contents.

History, references.

   The main references for this module are:

      Donald E. Knuth: The Art of Computer Programming, Volume 3 /
      Sorting and Searching, Addison-Wesley 1973, section 5.4.2 pp.
      266-286.

      Niklaus With: Algorithms + Data Structures = Programs,
      Prentice-Hall 1976, pp. 104-121.

   I implemented it first on Cyber Pascal in 1980 to get around the fact
   that the sort package for this machine does not provide any hook
   for a flexible, user supplied comparison routine.  The module was
   designed to sort a whole file in one single call.

   I re-implemented it in FORTRAN for a Cray-1, for which there was
   no decent disk sort package in 1984 (would you believe!).  Seeking
   efficiency, this module was deeply redesigned so to coroutine
   the application as far as possible, to delay file operations to
   the extent of absolutely none if unnecessary, and to make memory
   allocation administration quite fast.

   Getting used to micros, I ported the Cray version in 1986
   successively in Turbo Pascal, then to Microsoft C, uselessly
   retaining the look-ahead/write-behind features of bigger systems,
   but dropping variable length record processing.  I then adapted the
   C version to GNU standards in 1988 as part of an elementary text
   concordance package.

   Finally, I rewrote the thing in Python in 2003, as part of an SQL
   engine meant for a specialised Python application, and while doing
   so, I removed some of the C optimisation nitty-gritties, which are
   rather meaningless in Python.  The code has also been simplified.
"""


### Global definitions.

DEFAULT_MAX_FILES = 15              # maximum number of intermediate work files
DEFAULT_HEAP_SIZE = (1 << 14) - 1   # maximum number of records in memory heap


class Error(Exception):
    pass


class Unexpected_Get(Error):
    pass


class Unexpected_Put(Error):
    pass

### Work files input/output routines.


# Work file maker classes are all derived from File.  We currently have
# Marshal, Pickle and String, each having strengths and limitations.
# Pickle is likely the most generic one, it is the default file maker at
# Polyphase object instantiation if the user does not decide otherwise.

class File:
    def __init__(self):
        import tempfile
        self.file_name = tempfile.mktemp()
        self.file = None         # None if file not opened
        self.end_of_file = True  # when False, RECORD is meaningful on read
        self.record = None       # last record read or written on this file

    def __del__(self):
        if self.file is not None:
            self.close_unlink()

    def close_unlink(self):
        # Complete all operations on one work file.
        self.file.close()
        self.file = None
        import os
        os.remove(self.file_name)

    def open_write(self):
        # Setup a work file to be written.
        pass                    # meant to be overridden

    def write(self, record):
        # Add RECORD onto this work file.
        pass                    # meant to be overridden

    def open_read(self):
        # Setup a work file to be read.
        pass                    # meant to be overridden

    def read(self):
        # Return one record from this work file and prepare for next record.
        # Raise EOFError if there is no more record left in file.
        pass                    # meant to be overridden


class Marshall(File):

    def open_write(self):
        self.file = file(self.file_name, 'wb')
        self.end_of_file = True
        import marshal
        self.dump = marshal.dump
        self.load = marshal.load

    def write(self, record):
        self.record = record
        self.dump(record, self.file)

    def open_read(self):
        if self.file is not None:
            self.file.close()
        self.file = file(self.file_name, 'rb')
        try:
            self.record = self.load(self.file)
        except EOFError:
            self.end_of_file = True
        else:
            self.end_of_file = False

    def read(self):
        if self.end_of_file:
            raise EOFError
        record = self.record
        try:
            self.record = self.load(self.file)
        except EOFError:
            self.end_of_file = True
        return record


class Pickle(File):

    def open_write(self):
        self.file = file(self.file_name, 'wb')
        self.end_of_file = True
        import pickle
        self.dump = pickle.Pickler(self.file, -1).dump

    def write(self, record):
        self.record = record
        self.dump(record)

    def open_read(self):
        if self.file is not None:
            self.file.close()
        self.file = file(self.file_name, 'rb')
        import pickle
        self.load = pickle.Unpickler(self.file).load
        try:
            self.record = self.load()
        except EOFError:
            self.end_of_file = True
        else:
            self.end_of_file = False

    def read(self):
        if self.end_of_file:
            raise EOFError
        record = self.record
        try:
            self.record = self.load()
        except EOFError:
            self.end_of_file = True
        return record


class String(File):

    def open_write(self):
        self.file = file(self.file_name, 'w')
        self.end_of_file = True

    def write(self, record):
        self.record = record
        self.file.write(record.replace('\\', '\\\\').replace('\n', '\\n')
                        + '\n')

    def open_read(self):
        if self.file is not None:
            self.file.close()
        self.file = file(self.file_name)
        self.lines = iter(self.file)
        self.record = None
        self.end_of_file = False
        self.read()

    def read(self):
        if self.end_of_file:
            raise EOFError
        record = self.record
        try:
            self.record = (self.lines.next()[:-1]
                           .replace('\\n', '\n').replace('\\\\', '\\'))
        except StopIteration:
            self.end_of_file = True
        return record

### Main polyphasing class.


class Polyphase:
    def __init__(self, compare=None, file_maker=Pickle, verbose=None,
                 heap_size=DEFAULT_HEAP_SIZE, max_files=DEFAULT_MAX_FILES):
        # Prepare for sorting records.  COMPARE, if not None, is a user
        # provided function for ordering two records, returning -1, 0 or 1
        # like the built-in `cmp' function does.  When VERBOSE, run counts are
        # kept displayed on a single standard error line; by default, VERBOSE
        # is true if standard error is a tty.  FILE_MAKER is a subclass of
        # File for serialisation of records on disk.  HEAP_SIZE is the maximum
        # number for in-memory records, going over this number involves from
        # one up to MAX_FILES temporary disk files.
        self.compare = compare
        self.verbose = verbose
        self.file_maker = file_maker
        self.heap_size = heap_size
        self.max_files = max_files
        # We presume initially that the sort will fit in memory.  Then, the
        # heap is merely used to accumulate records before sort begins.
        self.files = None
        self.heap = []
        # Set initial state for when records are provided or retrieved one at
        # a time.  This is not used by PUT_ALL and GET_ALL methods.
        self.put = self.put_MEMORY
        self.get = self.get_GENERATE

    def close(self):
        # Explicit sort termination, yet rarely needed.
        del self.files
        del self.heap

    #def put(self, record):
    #    # Give one RECORD to be sorted.  Overridden according to state.
    #    pass

    def put_MEMORY(self, record):
        heap = self.heap
        if len(heap) < self.heap_size:
            heap.append(record)
            return
        self.bump_run = self.run_bumper().__next__
        self.split = 0
        self.put = self.put_DISK
        self.put(record)

    def put_DISK(self, record):
        # For disk sorts, the heap holds two tournaments, one is HEAP[:SPLIT]
        # and provides the contents of the current output run, another is
        # HEAP[SPLIT:] and provides the contents for the next output run.
        heap = self.heap
        split = self.split
        if split == 0:
            # Current HEAP[:SPLIT] is now empty: make it full and start new
            # run.  RUN_START is really meant as an argument to BUMP_RUN,
            # which being an iterator, does not accept formal parameters.
            self.heapify_records()
            self.run_start = heap[0]
            file = self.output_file = self.bump_run()
            self.run_start = None
            self.display_runs.display(self)
            split = len(heap)
        else:
            file = self.output_file
        # Add a record to disk run, making room in memory for the new RECORD.
        file.write(heap[0])
        if self.compare is None:
            lesser = record < heap[0]
        else:
            lesser = self.compare(record, heap[0]) < 0
        if lesser:
            # RECORD may not go in current run.  Reduce size of HEAP[:SPLIT]
            # then merely save RECORD within the now extended HEAP[SPLIT:].
            split -= 1
            heap[0] = heap[split]
            heap[split] = record
        else:
            # Insert RECORD in the current tournament HEAP[:SPLIT].
            heap[0] = record
        self.percolate_records(0, split)
        self.split = split

    def put_all(self, lines):
        # Put all LINES at once.  LINES should be iterable.  When this
        # method is used in a sort, the PUT method should not be used.
        next = iter(lines).__next__
        try:
            heap = self.heap
            heap_size = self.heap_size
            while len(heap) < heap_size:
                heap.append(next())
            record = next()
        except StopIteration:
            return
        try:
            compare = self.compare
            percolate_records = self.percolate_records
            bump_run = self.bump_run = self.run_bumper().__next__
            while True:
                # Write one run.
                self.heapify_records()
                self.run_start = heap[0]
                file = self.output_file = bump_run()
                self.run_start = None
                self.display_runs.display(self)
                split = len(heap)
                write = file.write
                if compare is None:
                    while split > 0:
                        # Write one record.
                        write(heap[0])
                        if record < heap[0]:
                            split -= 1
                            heap[0] = heap[split]
                            heap[split] = record
                        else:
                            heap[0] = record
                        percolate_records(0, split)
                        record = next()
                else:
                    while split > 0:
                        # Write one record.
                        write(heap[0])
                        if compare(record, heap[0]) < 0:
                            split -= 1
                            heap[0] = heap[split]
                            heap[split] = record
                        else:
                            heap[0] = record
                        percolate_records(0, split)
                        record = next()
        except StopIteration:
            self.split = split

    #def get(self):
    #    # Return one sorted record.  Overridden according to state.
    #    pass

    def get_GENERATE(self):
        self.get_next = self.get_all().__next__
        self.get = self.get_ITERATE
        return self.get()

    def get_ITERATE(self):
        try:
            return self.get_next()
        except StopIteration:
            raise EOFError

    def get_all(self):
        # Provide an iterator over all sorted records.  When this method is
        # directly used in a sort, the GET method should not be used.  Sort
        # results are not reiterable, they may be consumed only once.
        heap = self.heap
        compare = self.compare
        if self.files is None:
            if compare is None:
                heap.sort()
            else:
                heap.sort(compare)
            for record in heap:
                yield record
            return
        # Complete the sort phase by flushing to disk the whole contents of
        # HEAP, making it empty.  Produce a supplmentary run if necessary.
        split = self.split
        file = self.output_file
        if split == len(heap):
            # The whole HEAP contents fits in the current run.
            while len(heap) > 1:
                file.write(heap[0])
                heap[0] = heap.pop()
                self.percolate_records(0, len(heap))
            if len(heap) > 0:
                # Here, len(heap) == 1.
                file.write(heap.pop())
        else:
            # There are records remaining after the SPLIT point, so let's use
            # two steps.  First, flush the current tournament, while
            # progressively shifting left records after the SPLIT point, so
            # the HEAP at end will contain nothing but remaining records.
            while split > 1:
                file.write(heap[0])
                split -= 1
                heap[0] = heap[split]
                heap[split] = heap.pop()
                self.percolate_records(0, split)
            if split > 0:
                # Here, split == 1.
                file.write(heap[0])
                heap[0] = heap.pop()
            # Second, sort all remaining records, and produce a final run.
            if compare is None:
                heap.sort()
            else:
                heap.sort(compare)
            self.run_start = heap[0]
            file = self.output_file = self.bump_run()
            self.run_start = None
            self.display_runs.display(self)
            for record in heap:
                file.write(record)
            del heap[:]
        # Prepare for the first merging pass.  HEAP contains work files being
        # read for real runs.  HEAP[:SPLIT] obeys the priority queue invariant
        # over the next record in each file, all these files are in the middle
        # of reading an actual run.  HEAP[SPLIT:] hold files to participate in
        # the next run merging, files are moved there when a run completes.
        # DUMMIES hold all input files still having dummy runs.
        self.display_runs.merging = True
        assert not heap, heap
        dummies = []
        for file in self.files:
            file.open_read()
            if file.dummy_runs:
                dummies.append(file)
            else:
                heap.append(file)
        # An output file is allocated for making the algorithms more regular,
        # but opened only if there are more than a single merging pass.
        file = self.file_maker()
        file.total_runs = 0
        file.dummy_runs = 0
        self.files.append(file)
        # Execute all merging passes.
        while True:
            # Decide the output file of this merging pass.
            output_file = self.output_file = self.files[-1]
            if self.merging_passes == 1:
                output_file = None
            else:
                output_file.open_write()
            # Merge all runs meant for this merging pass.
            runs_to_merge = self.files[-2].total_runs
            while runs_to_merge > 0:
                # Merge one run taken from all input files.
                for file in dummies:
                    file.dummy_runs -= 1
                    file.total_runs -= 1
                if heap:
                    # Merge all records for current run.
                    if output_file is not None:
                        output_file.total_runs += 1
                    split = len(heap)
                    self.heapify_files(split)
                    while split > 0:
                        # Output best record and replace it.
                        file = heap[0]
                        record = file.record
                        if output_file is None:
                            yield record
                        else:
                            output_file.write(record)
                        file.read()
                        # At end of run, delete file from heap.
                        if file.end_of_file:
                            end_of_run = True
                        else:
                            if compare is None:
                                end_of_run = file.record < record
                            else:
                                end_of_run = compare(file.record, record) < 0
                        if end_of_run:
                            split -= 1
                            heap[0] = heap[split]
                            heap[split] = file
                            file.total_runs -= 1
                            if file.total_runs == 0:
                                file.close_unlink()
                                heap.remove(file)
                            self.display_runs.display(self)
                        if heap:
                            self.percolate_files(0, split)
                else:
                    # If we have only dummy runs, we surely have more than one
                    # merging pass remaining, so OUTPUT_FILE is never None.
                    output_file.total_runs += 1
                    output_file.dummy_runs += 1
                    self.display_runs.display(self)
                # Files just having delivered their last dummy run are going
                # to participate in next merge.
                for file in dummies[:]:
                    if file.dummy_runs == 0:
                        dummies.remove(file)
                        heap.append(file)
                runs_to_merge -= 1
            # The merging pass is now completed: prepare for the next one.
            # Rotate all files so the output file remains the last one.
            if self.merging_passes == 1:
                del self.display_runs
                break
            self.merging_passes -= 1
            file = self.files.pop()
            self.files.insert(0, file)
            self.display_runs.rotation += 1
            file.open_read()
            if file.dummy_runs:
                dummies.append(file)
            else:
                heap.append(file)

    #def bump_run(self):
    #    pass                    # meant to be overridden by RUN_BUMPER.next

    def run_bumper(self):
        # Produce a sequence of output files, each meant to receive the next
        # run coming out of the tournament sort.  Distribute runs in such a
        # way that later merging passes will use files efficiently.
        if self.verbose is None:
            import os
            import sys
            if os.isatty(sys.stderr.fileno()):
                write = sys.stderr.write
            else:
                write = None
        elif self.verbose:
            import sys
            write = sys.stderr.write
        else:
            write = None
        self.display_runs = Display_Runs(write)
        # MERGING_PASSES holds the number of expected merge passes.  When its
        # value is greater than 1, all merging results are sent to a work
        # file, otherwise they are returned to the calling program.
        self.merging_passes = 1
        self.files = []
        for counter in range(self.max_files - 1):
            # Create work files as needed, lazily, one run each.  IDEAL_RUNS
            # is the maximum number of real runs at the current merge level,
            # while DUMMY_RUNS is the number of fake, unexisting runs.  The
            # actual number of runs is the difference between both numbers.
            file = self.file_maker()
            file.total_runs = 1
            file.dummy_runs = 0
            file.open_write()
            self.files.append(file)
            yield file
        # We are having more runs than work files.
        while True:
            # We need another merging pass.  Raise the goals.  Rotate the
            # FILES array to the left, so all IDEAL_RUNS remain decreasing.
            self.merging_passes += 1
            total_runs_added = self.files[0].total_runs
            for counter in range(len(self.files)):
                total_runs = total_runs_added
                if counter < len(self.files) - 1:
                    total_runs += self.files[counter + 1].total_runs
                file = self.files[counter]
                file.dummy_runs = total_runs - file.total_runs
                file.total_runs = total_runs
            # Now use a so-called "horizontal" initial distribution for runs.
            # The idea is aiming a rectangular layout of dummy runs, and later
            # merging dummy runs together if possible, before actual runs.
            while self.files[0].dummy_runs > 0:
                for counter in range(len(self.files)):
                    file = self.files[counter]
                    if counter < len(self.files) - 1:
                        if (file.dummy_runs
                            < self.files[counter + 1].dummy_runs):
                            break
                    if file.dummy_runs == 0:
                        break
                    while True:
                        # RUN_START is the record to be written next, and for
                        # starting a new run, it ought to be smaller than the
                        # record last written to the selected file.  Stick
                        # delivering the current file until this happens.
                        if self.compare is None:
                            if self.run_start < file.record:
                                break
                        else:
                            if self.compare(self.run_start, file.record) < 0:
                                break
                        yield file
                    file.dummy_runs -= 1
                    yield file

    def heapify_records(self):
        # Establish the priority queue invariant over a HEAP of records.
        heap = self.heap
        if self.compare is None:
            # Use the `heapq' module if posible.
            try:
                import heapq
            except ImportError:
                pass
            else:
                heapq.heapify(heap)
                return
        # Otherwise, do the work ourselves.
        right = len(heap)
        left = (right + 1) // 2
        while left > 0:
            left -= 1
            self.percolate_records(left, right)

    def percolate_records(self, left, right):
        # Percolate records until HEAP[LEFT:RIGHT] reconstituted.
        # The heap invariant already holds within HEAP[LEFT + 1:RIGHT].
        heap = self.heap
        temp = heap[left]
        i = left
        j = 2 * i + 1
        compare = self.compare
        if compare is None:
            while j < right:
                if j < right - 1 and heap[j + 1] < heap[j]:
                    j += 1
                if heap[j] < temp:
                    heap[i] = heap[j]
                else:
                    break
                i = j
                j = 2 * i + 1
        else:
            while j < right:
                if j < right - 1 and compare(heap[j + 1], heap[j]) < 0:
                    j += 1
                if compare(heap[j], temp) < 0:
                    heap[i] = heap[j]
                else:
                    break
                i = j
                j = 2 * i + 1
        heap[i] = temp

    def heapify_files(self, right):
        # Establish the priority queue invariant over a HEAP[:RIGHT] of files.
        left = (right + 1) // 2
        while left > 0:
            left -= 1
            self.percolate_files(left, right)

    def percolate_files(self, left, right):
        # Percolate files until HEAP[LEFT:RIGHT] reconstituted.
        # The heap invariant already holds within HEAP[LEFT + 1:RIGHT].
        heap = self.heap
        temp = heap[left]
        i = left
        j = 2 * i + 1
        compare = self.compare
        if compare is None:
            while j < right:
                if j < right - 1 and heap[j + 1].record < heap[j].record:
                    j += 1
                if heap[j].record < temp.record:
                    heap[i] = heap[j]
                else:
                    break
                i = j
                j = 2 * i + 1
        else:
            while j < right:
                if (j < right - 1
                    and compare(heap[j + 1].record, heap[j].record) < 0):
                    j += 1
                if compare(heap[j].record, temp.record) < 0:
                    heap[i] = heap[j]
                else:
                    break
                i = j
                j = 2 * i + 1
        heap[i] = temp


class Display_Runs:
    def __init__(self, write):
        self.write = write
        self.merging = False
        self.rotation = 0
        self.text_length = 0

    def __del__(self):
        if self.write is None:
            return
        self.write(' ' * self.text_length + '\r')
        self.text_length = 0

    def display(self, polyphase):
        if self.write is None:
            return
        dummy_runs = 0
        total_runs = 0
        for file in polyphase.files:
            dummy_runs += file.dummy_runs
            total_runs += file.total_runs
        fragments = [' [%d] %d'
                     % (polyphase.merging_passes, total_runs - dummy_runs)]
        if self.merging:
            if dummy_runs > 0:
                fragments.append('+%d' % dummy_runs)
        else:
            fragments.append('/%d' % total_runs)
        fragments.append(' =')
        for counter in range(len(polyphase.files)):
            file = polyphase.files[(counter + self.rotation)
                                   % len(polyphase.files)]
            if file is polyphase.output_file:
                format = ' <%d>'
            else:
                format = ' %d'
            fragments.append(format % (file.total_runs - file.dummy_runs))
        text = ''.join(fragments)
        if len(text) > 79:
            text = text[:76] + '...'
        self.write(text.ljust(self.text_length) + '\r')
        self.text_length = len(text)
