import os
import re
from collections import defaultdict
from python_speech_features import mfcc, logfbank
from sidekit import frontend
import scipy.io.wavfile as wav
import numpy as np

WIN_LEN = 0.125

mfcc_cache = {}
fbank_cache = {}

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

def desc2nppath(sid, sid_count, desc):
    """
    Given a description, of (file id, start time, end time), where times are in seconds,
    compute the corresponding np array for that audio snippet, write it to a file, and
    return the corresponding path string of that np snippet file.
    """
    file_id, start, end = desc
    speech_file_name = 'cd01/swb1/sw0' + file_id + '.sph'
    
    # rate, sig = wav.read(speech_file_name)
    if speech_file_name not in mfcc_cache:
        sig, rate, _ = frontend.io.read_sph(speech_file_name, 'f')
        sig = np.divide(sig, np.linalg.norm(sig, axis=0))
        mfcc_feat = np.array(mfcc(sig, rate, winlen=WIN_LEN, winstep=WIN_LEN))
        fbank_feat = np.array(logfbank(sig, rate, winlen=WIN_LEN, winstep=WIN_LEN))
        mfcc_cache[speech_file_name] = mfcc_feat
        fbank_cache[speech_file_name] = fbank_feat 
    else:
        mfcc_feat = mfcc_cache[speech_file_name] 
        fbank_feat = fbank_cache[speech_file_name] 

    start_index = int(start / WIN_LEN)
    end_index = int(end / WIN_LEN)

    output_file = 'vecs/' + sid + '_' + str(sid_count) + '.npy'
    mfcc_seg = mfcc_feat[start_index : end_index]
    fbank_seg = fbank_feat[start_index : end_index]
    padded = np.zeros((64, 39))
    segment_length = mfcc_seg.shape[0]
    padded[ : segment_length, 0 : 13 ] = mfcc_seg
    padded[ : segment_length, 13 : ] = fbank_seg 

    padded.dump(output_file)
    return output_file.split('/')[1], str(segment_length)

def poop(raw):
    out={}
    for sid, descs in raw.iteritems():
        # fid,start,end = desc
        out[sid] = chunk_times(descs)

    entries = []
    
    sid_counts = defaultdict(int)
    for sid, descs in out.iteritems():
        for desc in descs:
            sid_count = sid_counts[sid]
            output_file, seg_length = desc2nppath(str(sid), sid_count, desc)
            entry = ' '.join([str(sid), output_file, seg_length])
            sid_counts[sid] += 1
            entries.append(entry)

    with open('vecs/vecs.txt', 'w') as text_file:
        text_file.write('\n'.join(entries))

    return out

poop(raw)
