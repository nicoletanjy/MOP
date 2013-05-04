#!/usr/bin/env python
'''plant synthetic moving objects into a set of observations.

prior to planting, the headers of the objects may be swapped around.'''

#command="plant.csh ./ -rmin %s -rmax %s -ang %s -width %s " % ( opt.rmin, opt.rmax, opt.angle, opt.width)


import argparse
import os
from ossos import storage
from ossos import util
import logging


def run_plant(expnums, ccd, rmin, rmax, ang, width, version='s'):
    '''run the plant script on this combination of exposures'''

    ptf = open('proc-these-files','w')
    ptf.write("# Files to be planted and search\n")
    ptf.write("# image fwhm plant\n")

    for expnum in expnums:
        fwhm = storage.get_fwhm(expnum,ccd)
        filename = storage.get_image(expnum, ccd=ccd, version=version)
        ptf.write("%s %3.1f YES\n" % ( filename[0:-5],
                                    fwhm ))
        for ext in ['apcor', 'obj.jmp', 'trans.jmp', 'psf.fits', 'mopheader', 'phot',
                    'zeropoint.used']:
            apcor = storage.get_image(expnum, ccd=ccd, version='s',
                                      ext=ext)

    ptf.close()

    cmd_args = ['plant.csh',os.curdir,
             str(rmin), str(rmax), str(ang), str(width)]

    #util.exec_prog(cmd_args)

    uri = storage.get_uri('Object',ext='planted',version='',
                          subdir=str(expnums[0]))
    storage.copy('Object.planted',uri)
    uri = os.path.join(os.path.dirname(uri), 'shifts')
    storage.copy('shifts', uri)
    for expnum in expnums:
        base = 'fk'+str(expnum)
        uri = storage.get_uri(base, ccd=ccd, version=version, ext='fits',
                     subdir=str(expnum))
        filename =  os.path.basename(uri)
        storage.copy(filename, uri)
        
                          

    
    return

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ccd',
                        action='store',
                        type=int,
                        default=None,
                         help='which ccd to process')
    parser.add_argument("--dbimages",
                        action="store",
                        default="vos:OSSOS/dbimages",
                        help='vospace dbimages containerNode')
    parser.add_argument("expnums",
                        type=int,
                        nargs=3,
                        help="expnum(s) to process")
    parser.add_argument("--type",
                        action='store',
                        default='s',
                        choices=['s', 'p', 'o'],
                        help='which type of image')
    parser.add_argument("--verbose","-v",
                        action="store_true")
    parser.add_argument("--debug",'-d',
                        action='store_true')
    parser.add_argument("--rmin", default=0.5,
                        type=float, help="minimum motion rate")
    parser.add_argument("--rmax", default=15,
                        type=float, help="maximum motion rate")
    parser.add_argument("--width", default=30,
                        type=float, help="angle opening")
    parser.add_argument("--ang", default=20,
                        type=float, help="angle of motion, 0 is West")
    
    args=parser.parse_args()

    ## setup logging
    level = logging.CRITICAL
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO

    logging.basicConfig(level=level, format="%(message)s")

    ccds = [args.ccd]
    if args.ccd is None:
        ccds = range(0,36)
    
    for ccd in ccds:
        run_plant(args.expnums,
                  ccd,
                  args.rmin, args.rmax, args.ang, args.width,
                  version=args.type)
