import sys, json, re, glob, os
from funasr import AutoModel
from pypinyin import lazy_pinyin, Style
S=json.load(open(sys.argv[1],encoding='utf-8'))
files=sys.argv[2:]
m=AutoModel(model="paraformer-zh",punc_model="ct-punc",disable_update=True,log_level="ERROR")
cn=lambda s: re.sub(r'[^\u4e00-\u9fff]','',s)
import difflib
res={}
for f in files:
    k=str(int(re.search(r's(\d\d)_',os.path.basename(f)).group(1)))
    hyp=m.generate(input=f)[0]["text"]
    a,b=cn(S[k]),cn(hyp)
    pa,pb=lazy_pinyin(a,style=Style.TONE3,neutral_tone_with_five=True),lazy_pinyin(b,style=Style.TONE3,neutral_tone_with_five=True)
    sm=difflib.SequenceMatcher(None,pa,pb)
    diffs=[(tag,a[i1:i2],b[j1:j2]) for tag,i1,i2,j1,j2 in sm.get_opcodes() if tag!='equal']
    chard=[(tag,a[i1:i2],b[j1:j2]) for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b).get_opcodes() if tag!='equal']
    res[os.path.basename(f)]=dict(hyp=hyp,pinyin_diffs=diffs,char_diffs=chard)
    print(os.path.basename(f),"| PY-OK" if not diffs else f"| PY-DIFF {diffs}","| chars", chard if chard else "exact","|",hyp,flush=True)
json.dump(res,open('asr_results.json','w'),ensure_ascii=False,indent=1)
