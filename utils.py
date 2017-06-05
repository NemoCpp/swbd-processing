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
# print raw

def chunk_times(durations, chop_time=4):
    """
    input: list of tuples of (file id, start time, end time)
    output: new list tuples that breaks speaker durations into short snippets, between 2 and 8 seconds long
    """
    out = []
    for duration in durations:
        fid,start,end = duration
        try:
            s=float(start)
            e=float(end)
        except ValueError:
            continue
        dur = e-s
        if dur > 2 and dur < 8:
            out.append((fid,s,e))
        if dur > 8:
            # TODO make times variable, not all chop_time
            # use a while loop, until the value is > end
            for i in xrange(int(dur/chop_time) - 1):
                out.append((fid,s+i*chop_time,s+(i+1)*chop_time))
    return out

def desc2nppath(desc):
    """
    Given a description, of (file id, start time, end time), where times are in seconds,
    compute the corresponding np array for that audio snippet, write it to a file, and
    return the corresponding path string of that np snippet file.
    """
    return str(desc)

def poop(raw):
    out={}
    for sid, descs in raw.iteritems():
        # fid,start,end = desc
        out[sid] = chunk_times(descs)

    entries = []
    for sid, descs in out.iteritems():
        for desc in descs:
            entry = '\t'.join([str(sid),desc2nppath(desc)])
            entries.append(entry)
    with open('catalog', 'w') as text_file:
        text_file.write('\n'.join(entries))

    return out

poop(raw)

