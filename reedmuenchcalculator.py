"""Calculates titer using Reed-Muench formula.

This script takes a text input file. It calculates the titer for
all of the samples, and prints them out to a new text file with the
name based on the input file. If plotting is supported, this script
also makes plots of the computed titers and images of the input samples.
If any of the specified output files already exist, they are not
overwritten without first obtaining user approval.

Written by Jesse Bloom, 2012."""


import os
import sys
import re
try:
    import pylab
    plotting_supported = True
except ImportError:
    plotting_supported = False
import reedmuench_utils


def ParseInput(infile):
    """Reads an input text file.

    This file should be in the format specified by the example input file.
    The returned variable is the following tuple: (sampledata, volume, dilution)
    samplenames -> This is a list of the sample names in the order in
        which they appear in the input file.
    sampledata -> This is a dictionary. It is keyed by sample names.
        Each entry is a list of lists. The number of lists
        gives the number of replicates, so there are len(infectedwells)
        replicates. Each of the entry lists describes the wells with
        observed infection in rows of a 96-well plate. So for example,
        [[A, B, C, D], [A, B, C], [A, B, C, D]]
        corresponds to three replicates having cytopathic effect
        in the first four rows (first replicate), the first three rows
        (second replicate) and the first four rows (third replicate).
        There need to be at least two replicates.
    volume -> This is the infection volume in the first row (row A).
    dilution -> This is the dilution factor between successive rows.
        For example, 10 is a typical dilution factor for this assay.
    This method raises and IOError if the input file is not in the
        expected format or specifies invalid values.
    """
    lines = [line for line in open(infile).readlines() if line[0] != '#' and not line.isspace()]
    line1match = re.compile('^\s*VOLUME\s+(?P<volume>\d+\.{0,1}\d*)\s*\n$')
    m = line1match.search(lines[0])
    if not m:
        raise IOError("Failed to parse VOLUME from the first line.")
    volume = float(m.group('volume'))
    line2match = re.compile('^\s*DILUTION\s+(?P<dilution>\d+\.{0,1}\d*)\s*\n$')
    m = line2match.search(lines[1])
    if not m:
        raise IOError("Failed to parse DILUTION from the second line.")
    dilution = float(m.group('dilution'))
    if dilution <= 1:
        raise IOError("The dilution factor must be > 1, but read a value of %f" % dilution)
    line3match = re.compile('^\s*NREPLICATES\s+(?P<nreplicates>\d+)\s*\n$')
    m = line3match.search(lines[2])
    if not m:
        raise IOError("Failed to parse an integer value for NREPLICATES from the third line.")
    nreplicates = int(m.group('nreplicates'))
    if nreplicates < 2:
        raise IOError("There must be at least two replicates, but read a value of %d." % nreplicates)
    lines = lines[3 : ] # the remaining lines
    # there should be nreplicates + 1 line for each sample
    linespersample = nreplicates + 1
    if len(lines) % linespersample != 0:
        raise IOError("The sample data is not specified correctly. There should be a total of %d lines for each sample (the sample name plus a line for each of the %d replicates), but the number additional lines is not divisible by %d." % (linespersample, nreplicates, linespersample))
    nsamples = len(lines) / linespersample
    sampledata = {}
    namematch = re.compile('^\s*SAMPLE\s+(?P<name>.+)\n$')
    validrows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] 
    samplenames = []
    for isample in range(nsamples):
        nameline = lines[isample * linespersample]
        samplelines = lines[isample * linespersample + 1 : (isample + 1) * linespersample]
        assert len(samplelines) == nreplicates
        m = namematch.search(nameline)
        if not m:
            raise IOError("Failed to match sample name from line: %s" % nameline)
        sample = m.group('name').strip()
        if sample in sampledata:
            raise IOError("Duplicate sample name of %s" % sample)
        sampledata[sample] = []
        samplenames.append(sample)
        for line in samplelines:
            if line.strip() == 'na':
                sampledata[sample].append([]) # no rows with effect
            else:
                rows = [x.strip() for x in line.split(',')]
                for x in rows:
                    if x not in validrows:
                        raise IOError("Invalid row specification of %s in the following line: %s\nValid row labels are A to H." % (x, line))
                    if rows.count(x) != 1:
                        raise IOError("Row identifier of %s appears more than once in the following line: %s" % (row, line))
                sampledata[sample].append(rows)
    return (samplenames, sampledata, volume, dilution)




def main():
    """Main body of the script."""
    print "\nWelcome to the Bloom lab Reed-Muench calculator.\n"
    infile = None
    while not infile:
        infile = raw_input("Enter the name of the input file in text format: ").strip()
        if os.path.isfile(infile):
            break
        elif infile in ['Q', 'q']:
            print "Quitting."
            sys.exit()
        else:
            infile = None
            print "Failed to find the specified input file of %s. Try again to enter a valid file name, or enter Q to quit." % infile
    print "Reading input from the file %s." % infile
    (samplenames, sampledata, volume, dilution) = ParseInput(infile)
    print "Read data for %d samples." % len(sampledata)
    titers = {}
    for (sample, data) in sampledata.iteritems():
        titers[sample] = reedmuench_utils.Titer(data, volume, dilution)
    print "\nHere are the computed titers in TCID50 per ul:"
    for sample in samplenames:
        print "%s: %.3f" % (sample, titers[sample])


main() # run the script.
