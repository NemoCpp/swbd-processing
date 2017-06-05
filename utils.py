import os

def extension(fname, ext):
    return fname.lower().endswith(ext)

def dir2id(path, ext):
    files = os.listdir(path)

    out = []
    for fpath in files:
        if extension(fpath, ext) is True:
            out.append(os.path.splitext(fpath)[0])
    return out

## need last 4 chars of filename without extension to get id
audio_files = map(lambda x: x[-4:], dir2id('cd01/swb1', '.sph'))
trans_files = map(lambda x: x[-4:], dir2id('phase1/disc01', '.mrk'))

common = set.intersection(set(audio_files), set(trans_files))
print sorted(common)

def poop(audio_files, trans_files):
    """
    Start with map, indexed on speaker ID.
    For each audio file
        grab the speaker IDs
        look at mrt and txt and append tuples of (audio_fileid, range-to-snip) to each speaker ID.
    Later, we will poop these out.
    """

