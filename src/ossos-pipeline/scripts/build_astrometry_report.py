#!python

import argparse
import logging
import os
from ossos import mpc
import re
import sys


def load_observations((observations, regex), path, filenames):
    """
    Returns a provisional name based dictionary of observations of the object.
    Each observations is keyed on the date. ie. a dictionary of dictionaries.

    :rtype : None
    :param observations: dictionary to store observtions into
    :param path: the directory where filenames are.
    :param filenames: list of files in path.
    """

    for filename in filenames:
        if re.search(regex, filename) is None:
            logging.warning("Skipping {}".format(filename))
            continue
        with open(os.path.join(path, filename)) as ifptr:
            for line in ifptr.readlines():
                observation = None
                try:
                    observation = mpc.Observation.from_string(line)
                except Exception as e:
                    logger.error(str(e))
                    logger.error(os.path.join(path, filename))
                    logger.error(line)
                if observation is None:
                    continue
                key1 = observation.date.mjd
                if key1 not in observations.keys():
                    observations[key1] = {}
                key2 = observation.provisional_name
                if key2 in observations[key1]:
                    if observations[key1][key2]:
                        continue
                    if not observation.null_observation:
                        logger.error(filename)
                        logger.error(line)
                        logger.error(str(observations[key1][key2]))
                        raise ValueError("conflicting observations for {} in {}".format(key2, key1))
                observations[key1][key2] = observation


if __name__ == '__main__':

    description = ("Given two directories containing astrometric observations build"
                   "file that reports the newly measured astrometry.")

    epilog = """This script is intended to provide a simple way of gathering a list of new astrometry for reporting.
Astrometry is reported to the a central service for distribution (dbase fro the OSSOS project, or the
Minor Planet Center, for example). These central system do not want previously reported astrometry in
new submission files. Also, when a line of astrometry needs to be changed there is, nominally, a separate channel
for this reporting.  This script attempts to provide an automated approach to creating these reports.

In addition to the reported astrometry, each file should also contain some comments on the nature of the observations
being submitted. This script, being part of the OSSOS pipeline, provides these comments in a way that is consistent
with the expectations of the OSSOS reporting structure.  The script should build these comments in a reasonably
auto-magical way.
"""

    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("existing_astrometry_directory",
                        help=("Directory containing previously reported astrometry."
                              "Files can be in dbase ast, validate ast or OSSOS mpc format"))
    parser.add_argument("--idx_filename",
                        default = None,
                        help="File that has the MOP/OSSOS name mapping index.")
    parser.add_argument("new_astrometry_directory",
                        help=("Directory containing astrometry to be searched for new lines to report."
                              "Files should be in validate ast format."
                              "Only observations from a single observatory should be present in these files."))
    parser.add_argument("report_file",
                        help="Name of file that new lines will be reported to")
    parser.add_argument("--new_name_regex",
                        default='.*\.ast',
                        help="Only load new observations where provisional name matches")
    parser.add_argument("--existing_name_regex",
                        default='.*\.ast',
                        help="Only load existing observations where provisional name matches")
    parser.add_argument("--start_date", type=mpc.get_date,
                        help="Include observations taken on or after this date in report.")
    parser.add_argument("--end_date", type=mpc.get_date,
                        help="Include observation taken on or before this date in report.")
    parser.add_argument("--replacement", action='store_true', help="select replacement lines")
    parser.add_argument("--tolerance", default=.2,
                        help="tolerance (in arc-seconds) for two positions to be considered the same measurement")
    parser.add_argument("--COD",
                        default=568,
                        help="Observatory code for report file.")
    parser.add_argument("--OBS",
                        action="append",
                        default=['M. T. Bannister', 'J. J. Kavelaars'],
                        help="Names of observers, multiple allowed")

    args = parser.parse_args()

    logger = logging.getLogger('reporter')

    if args.idx_filename is None:
        args.idx_filename = os.path.dirname(args.existing_astrometry_directory)+"/idx/file.idx"

    idx = mpc.Index(args.idx_filename)
    print idx

    existing_observations = {}
    os.path.walk(args.existing_astrometry_directory, load_observations, (existing_observations,
                                                                         args.existing_name_regex))
    print "Loaded existing observations for {} objects.".format(len(existing_observations))

    new_observations = {}
    os.path.walk(args.new_astrometry_directory, load_observations, (new_observations, args.new_name_regex))
    print "Loaded new observations for {} objects.".format(len(new_observations))

    report_observations = []
    for date1 in new_observations:
        for name1 in new_observations[date1]:
            observation1 = new_observations[date1][name1]
            assert isinstance(observation1, mpc.Observation)
            if (args.start_date is None or args.start_date.jd < new_observations[date1][name1].date.jd) \
                    and (args.end_date is None or args.end_date.jd > new_observations[date1][name1].date.jd):
                report = True
                replacement = False
                if date1 in existing_observations:
                    for name2 in existing_observations[date1]:
                        observation2 = existing_observations[date1][name2]
                        assert isinstance(observation2, mpc.Observation)
                        separation = observation1.coordinate.separation(observation2.coordinate)
                        if separation.arcsecs < args.tolerance:
                            if not idx.is_same(observation2.provisional_name, observation1.provisional_name):
                                logger.warning("Duplicate observations >{}< on {} matches different provisional name >{}< on same date".format(name1,
                                                                                                                observation1.date,
                                                                                                                name2))
                                logger.warning(str(observation1))
                                logger.warning(str(observation2))
                            report = False
                            break
                        elif idx.is_same(observation2.provisional_name, observation1.provisional_name):
                            replacement = True
                if report and replacement == args.replacement:
                    logger.warning("Adding {} on {} to report".format(name1, observation1.date))
                    report_observations.append(observation1)

    if not len(report_observations) > 0:
        logger.warning("No observations matched criterion.")
        sys.exit(0)

    outfile = open(args.report_file, 'w')
    outfile.write(mpc.make_tnodb_header(report_observations))
    outfile.write("\n")
    for observation in report_observations:
        outfile.write(observation.to_tnodb()+"\n")
    outfile.close()