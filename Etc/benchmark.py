#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright © 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2002.

"""\
Simple tool for benchmarking a function.
"""

def benchmark(test, repeat=1,
              calibration=[]):
    """\
Benchmark the parameter-less function TEST and report its average execution
time over REPEAT executions, or over a single execution when not specified.
The whole looped test is repeated twice, with the garbage collector enabled
and disabled, the enabled status is restored to what it was.
"""
    import sys, time
    write = sys.stdout.write
    # Define an empty function used for calibration.
    def calibrate():
        pass
    # Define a function returning the time taken for one TEST call.
    def measure():
        wall_start = time.time()
        cpu_start = time.clock()
        for counter in xrange(repeat):
            test()
        return ((time.clock() - cpu_start) / repeat - calibration[0],
                (time.time() - wall_start) / repeat - calibration[1])
    # Is it the first time?
    if not calibration:
        # Find the overhead coming from the measurement mechanics,
        wall_start = time.time()
        cpu_start = time.clock()
        for counter in xrange(1e4):
            calibrate()
        calibration.append((time.clock() - cpu_start) / 1e4)
        calibration.append((time.time() - wall_start) / 1e4)
        # Produce column headings.
        write('    GC enabled          GC disabled    Ratio  Function Name\n')
        write('   CPU      wall       CPU      wall  ena/dis\n')
    # Measure both times, enabling and disabling the garbage collector.
    import gc
    if gc.isenabled():
        # Start and finish with garbage collector enabled.
        cpu_gc_on, wall_gc_on = measure()
        gc.disable()
        gc.collect()
        cpu_gc_off, wall_gc_off = measure()
        gc.enable()
    else:
        # Start and finish with garbage collector disabled.
        gc.collect()
        cpu_gc_off, wall_gc_off = measure()
        gc.enable()
        cpu_gc_on, wall_gc_on = measure()
        gc.disable()
    # Select a proper time scale for reporting values.
    minimum_time = min(cpu_gc_on, wall_gc_on, cpu_gc_off, wall_gc_off)
    if minimum_time >= 1e-1:
        factor = 1e0
        unit = 's'
    elif minimum_time >= 1e-4:
        factor = 1e3
        unit = 'ms'
    else:
        factor = 1e6
        unit = 'us'
    # Produce one line of report on standard output.
    write('%6.2f%-2s %6.2f%-2s   %6.2f%-2s %6.2f%-2s   %3.1f   %s\n'
          % (cpu_gc_on*factor, unit, wall_gc_on*factor, unit,
             cpu_gc_off*factor, unit, wall_gc_off*factor, unit,
             cpu_gc_on / cpu_gc_off, test.__name__))

def test():
    #from Local.benchmark import benchmark
    list1 = range(0, 10000) + range(5000, 15000) + range(90000, 100000)
    list2 = range(0, 2000) + range(40000, 50000) + range(95000, 105000)

    def comprehension():
        dict([(k,1) for k in list1+list2]).keys()

    def zip_and_update():
        result = dict(zip(list1, list1))
        result.update(dict(zip(list2, list2)))
        result.keys()

    def zip_with_none():
        dict(zip(list1 + list2, [None] * (len(list1) + len(list2)))).keys()

    def zip_with_self():
        both = list1 + list2
        dict(zip(both, both)).keys()

    benchmark(comprehension)
    benchmark(zip_and_update)
    benchmark(zip_with_none)
    benchmark(zip_with_self)

if __name__ == '__main__':
    test()
