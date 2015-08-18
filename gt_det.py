import bbox_helper
import argparse
import os
import shutil

def _mkdir(path, filePath=False):
    if filePath:
        dirname = os.path.dirname(path)
    else:
        dirname = path

    if not os.path.exists(dirname):
        os.makedirs(dirname)

def _findWindsInAnnotationFolder(ids):
    return list(set([x.split('_')[0] for x in ids]))

def _saveImgIdList(outputFileName, ids):
    _mkdir(outputFileName, True)

    with open(outputFileName, 'w') as out:
        # Enumerate from 1 for matlab scripts
        for i, f in enumerate(ids, start=1):
            line = f + ' ' + str(i) + '\n'
            out.write(line)

def _saveMetaData(outputFileName, imagenetStructureFile, ids):
    import xml.etree.ElementTree as et
    import scipy.io as sio
    import numpy as np

    tree = et.parse(imagenetStructureFile)
    root = tree.getroot()

    dt = [('WNID', 'S10'), ('name', 'S100'), ('description', 'S1000')]
    arr = np.zeros((len(ids),), dtype=dt)
    for i, id in enumerate(ids):
        obj = root.find(".//*[@wnid='%s']" % id)
        if obj is None:
            continue

        arr[i][dt[0][0]] = id
        arr[i][dt[1][0]] = obj.attrib['words']
        arr[i][dt[2][0]] = obj.attrib['gloss']

    _mkdir(outputFileName, True)
    sio.savemat(outputFileName, {'synsets': arr})

def _getMatchedIds(*paths):
    if len(paths) == 0:
        return []

    results = set([])
    for p in paths:
        ids = os.listdir(p)
        ids = [os.path.splitext(i)[0] for i in ids]
        if len(results) == 0:
            results = set(ids)
        else:
            results = results.intersection(ids)
            if len(results) == 0:
                break

    return list(results)

def _procPath(args):
    import pickle
    SAVED_PATH = '.pdet'
    if args is None:
        try:
            with open(SAVED_PATH, 'rb') as output:
                return pickle.load(output)
        except:
            print('Please specify paths.')
            exit()
    else:
        with open(SAVED_PATH, 'wb') as output:
            pickle.dump(args, output, pickle.HIGHEST_PROTOCOL)
        return args

def findWnidsInAnnotationFolder(annotationPath, imagePath):
    return _findWindsInAnnotationFolder(
        _getMatchedIds(annotationPath, imagePath))

def copyAnnotations(annotationFiles, dstPath):
    _mkdir(dstPath)

    for f in annotationFiles:
        if os.path.isfile(f):
            shutil.copy(f, dstPath)

def copyImagesByAnnFiles(annotationFiles, imagePath, dstPath):
    _mkdir(dstPath)

    imageNames = []
    for e in annotationFiles:
        imageNames.append(os.path.basename(os.path.splitext(e)[0]) + '.JPEG')

    for root, dirs, files in os.walk(imagePath):
        for f in files:
            if f in imageNames:
                shutil.copy(os.path.join(root,f), dstPath)
                imageNames.remove(f)

def saveImgIdList(outputFileName, annotationPath, imagePath):
    _saveImgIdList( outputFileName,
                   sorted(_getMatchedIds(annotationPath, imagePath)))

def saveMetaData(outputFileName, imagenetStructureFile, annotationPath, imagePath):
    _saveMetaData(outputFileName, imagenetStructureFile,
                  findWnidsInAnnotationFolder(annotationPath, imagePath))

if '__main__' == __name__:
    p = argparse.ArgumentParser(description='Help users to prepare ground truth \
                                for ILSVC detection results evaluation')
    p.add_argument('dst', type=str, help='Output folder')
    p.add_argument('-p', dest='path', nargs=3, type=str, help='Three paths \
                   should be specified: Path to search annotation files, path \
                   to search images, path of ImageNet structure file. \
                   If not set, use saved paths')
    args = p.parse_args()
    aPath, iPath, struct = _procPath(args.path)

    OUT_ANN_DIR = os.path.join(args.dst, 'annotations')
    OUT_IMG_DIR = os.path.join(args.dst, 'images')
    OUT_ID_LIST = os.path.join(args.dst, 'ids.txt')
    OUT_META_DATA = os.path.join(args.dst, 'meta.mat')
    anns = bbox_helper.scanAnnotationFolder(aPath)
    copyAnnotations(anns, OUT_ANN_DIR)
    copyImagesByAnnFiles(anns, iPath, OUT_IMG_DIR)
    ids = _getMatchedIds(OUT_ANN_DIR, OUT_IMG_DIR)
    _saveImgIdList(OUT_ID_LIST, sorted(ids))
    _saveMetaData(OUT_META_DATA, struct, _findWindsInAnnotationFolder(ids))