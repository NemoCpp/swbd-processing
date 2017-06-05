import os
import re
from collections import defaultdict

def extension(fname, ext):
    return fname.lower().endswith(ext)

def dir2id(path, ext):
    files = os.listdir(path)

    out = []
    for fpath in files:
        if extension(fpath, ext) is True:
            out.append(os.path.splitext(fpath)[0])
    return out

def raw_speaker_times(audio_path, trans_path):
    """
    outputs a map
    key: speaker id
    value: tuple of (file id, start time, end time)
    values describe speaker durations in large contiguous blocks
    """
    out = defaultdict(list)

    ## need last 4 chars of filename without extension to get id
    audio_files = map(lambda x: x[-4:], dir2id(audio_path, '.sph'))
    trans_files = map(lambda x: x[-4:], dir2id(trans_path, '.mrk'))

    common = set.intersection(set(audio_files), set(trans_files))

    convos = {}
    for fid in list(common):
        with open(os.path.join(trans_path, 'sw'+fid+'.txt'), 'r') as txtf:
            firstline = txtf.readline().strip()
            _,A,B = firstline.split('\t')[1].split('_')
        convos[fid] = {'A': A, 'B': B}
        # print fid,A,B

    for fid in list(common):
        with open(os.path.join(trans_path, 'sw'+fid+'.mrk'), 'r') as mrtf:
            data = mrtf.readlines()
            data = map(lambda x: re.sub('[ \t]+',' ',x.strip()).split(' '), data)
        prev = None
        startt = 0
        for info in data:
            sid,start,duration,_ = info
            if prev==sid:
                continue
            else:
                prev=sid
                if sid in convos[fid]:
                    out[convos[fid][sid]].append((fid,startt,start))
                startt = start
    return out

raw = raw_speaker_times('cd01/swb1', 'phase1/disc01')

# for sid, desc in out.iteritems():
#     fid,start,end = desc
def chunk_times(durations):
    """
    input: list of tuples of (file id, start time, end time)
    output: new list tuples that breaks speaker durations into short snippets, between 2 and 8 seconds long
    """
    out = []
    for fid,start,end in durations:
        out.append(fid)
    print out

chunk_times(raw['1122'])
