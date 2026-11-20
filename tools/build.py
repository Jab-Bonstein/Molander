import pickle,sys,math,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
from skimage.measure import find_contours,approximate_polygon
from skimage.morphology import skeletonize
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from matplotlib.path import Path as MPath
XH,CAP=430,680; CAPL=790; LSB=45; RS=0.5; UP=4
groups=pickle.load(open("mol/groups.pkl","rb")); lab=np.load("mol/lab.npy"); D=np.load("mol/d.npy")
names=list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")+list("abcdefghijkl")+list("mnopqrstuvwxyz")+["one","two","three","four","five","six","seven","eight","nine"]+["exclam","question","quotedbl","quotedblleft","backslash","slash","period"]
assert len(names)==len(groups)
G=dict(zip(names,groups))
def fitbase(keys):
    xs=[(G[k]["x0"]+G[k]["x1"])/2 for k in keys]; ys=[G[k]["y1"] for k in keys]
    A=np.polyfit(xs,ys,1) if len(keys)>2 else (0,np.median(ys)); return A
rows={0:list("ABCDEFGHIJKLM"),1:list("NOPRSTUVWXYZ"),2:list("ace"),3:list("mnorsuvwxz"),4:["one","two","three","four","five","six","seven","eight","nine"],5:["exclam","period"]}
xl={2:list("ace"),3:list("mnorsuvwxz")}
scale={};base={}
for r,ks in rows.items():
    base[r]=fitbase(ks)
    if r in (2,3): h=np.median([G[k]["y1"]-G[k]["y0"] for k in xl[r]]); scale[r]=XH/h
    elif r in (0,1,4): h=np.median([G[k]["y1"]-G[k]["y0"] for k in ks]); scale[r]=CAP/h
scale[5]=scale[4]
glyphs={}
for n,g in G.items():
    r=g["row"]; pad=6
    y0,y1,x0,x1=g["y0"]-pad,g["y1"]+pad,g["x0"]-pad,g["x1"]+pad
    m=np.isin(lab[y0:y1,x0:x1],g["ids"]); m=ndimage.binary_dilation(m,iterations=2)
    v=np.where(m,D[y0:y1,x0:x1],0).astype(np.float32)
    f=scale[r]*RS  # raster px per source px
    if r in (0,1):
        h=g["y1"]-g["y0"]; hm=CAP/scale[r]
        f=CAPL*(h/hm)**0.4/h*RS
    im=Image.fromarray(v).resize((int(v.shape[1]*f),int(v.shape[0]*f)),Image.BICUBIC)
    R=ndimage.gaussian_filter(np.array(im),f*0.6)>40
    cx=(g["x0"]+g["x1"])/2; by=np.polyval(base[r],cx) if r!=5 else np.polyval(base[r],cx)
    glyphs[n]=[R,(by-y0)*f]
def refit(n,height,bottom):
    R,b=glyphs[n]; r_=np.where(R.any(1))[0]; R=R[r_.min():r_.max()+1]
    f=height*RS/R.shape[0]; im=Image.fromarray((R*255).astype(np.uint8)).resize((max(1,int(R.shape[1]*f)),max(1,int(R.shape[0]*f))),Image.BILINEAR)
    R=np.array(im)>127; glyphs[n]=[R,R.shape[0]+bottom*RS]
refit('exclam',CAP,0); refit('question',CAP,0); refit('quotedbl',200,CAP-180); refit('quotedblleft',200,CAP-180)
refit('slash',CAP+80,-60); refit('backslash',CAP+80,-60)
R,b=glyphs['q']; desc=(R.shape[0]-b)/RS
if desc>300: refit('q',XH+300,-300)
def thickness(R):
    sk=skeletonize(R); d=ndimage.distance_transform_edt(R); return 2*np.median(d[sk])/RS
th={k:thickness(v[0]) for k,v in glyphs.items()}
T=float(np.median(list(th.values()))); print("stroke",round(T))
for k in glyphs:
    R,b=glyphs[k]; p=10; R=np.pad(R,p); r=(T-th[k])/2*RS
    if r>0: R=R|(ndimage.distance_transform_edt(~R)<=r)
    elif r<0: R=R&(ndimage.distance_transform_edt(R)>-r)
    glyphs[k]=[R,b+p]
rng=np.random.default_rng(3)
def catmull(pts,n=24):
    pts=[np.array(p,float) for p in pts]
    if len(pts)<3: return np.linspace(pts[0],pts[-1],n*2)
    P_=[pts[0]]+pts+[pts[-1]]; out=[]
    for i in range(1,len(P_)-2):
        p0,p1,p2,p3=P_[i-1],P_[i],P_[i+1],P_[i+2]
        for t in np.linspace(0,1,n,endpoint=False):
            out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    out.append(pts[-1]); return np.array(out)
def ell(cx,cy,rx,ry,a0,a1,n=14): return [(cx+rx*math.cos(math.radians(a)),cy+ry*math.sin(math.radians(a))) for a in np.linspace(a0,a1,n)]
def synth(strokes,dots=(),base=None,wob=5):
    allp=[catmull([(x+rng.normal(0,wob),y+rng.normal(0,wob)) for x,y in s]) for s in strokes]
    pts=[np.array([dd[:2]]) for dd in dots]+allp
    xmin=ymin=1e9; xmax=ymax=-1e9
    if base is not None:
        BR,bb=base; xmin=min(xmin,0); xmax=max(xmax,BR.shape[1]/RS); ymax=max(ymax,bb/RS); ymin=min(ymin,(bb-BR.shape[0])/RS)
    if pts:
        P=np.vstack(pts); xmin=min(xmin,P[:,0].min()); xmax=max(xmax,P[:,0].max()); ymin=min(ymin,P[:,1].min()); ymax=max(ymax,P[:,1].max())
    pad=T; W=int((xmax-xmin+2*pad)*RS)+2; H=int((ymax-ymin+2*pad)*RS)+2
    im=Image.new("L",(W,H),0); d=ImageDraw.Draw(im)
    X=lambda x:(x-xmin+pad)*RS; Y=lambda y:(ymax+pad-y)*RS; r=T/2*RS
    if base is not None:
        BR,bb=base; m=Image.fromarray((BR*255).astype(np.uint8)); im.paste(m,(int(round(X(0))),int(round(Y(bb/RS)))),m)
    for s in allp:
        for x,y in s: d.ellipse([X(x)-r,Y(y)-r,X(x)+r,Y(y)+r],fill=255)
    for dd in dots:
        x,y=dd[:2]; rr=(dd[2] if len(dd)>2 else T*0.6)*RS; d.ellipse([X(x)-rr,Y(y)-rr,X(x)+rr,Y(y)+rr],fill=255)
    return [np.array(im)>127,Y(0)]
def bbox_units(n):
    R,b=glyphs[n]; rows_=np.where(R.any(1))[0]; cols=np.where(R.any(0))[0]
    return cols.min()/RS,cols.max()/RS,(b-rows_.max())/RS,(b-rows_.min())/RS
# dots for i and j
def dotless(n):
    R,b=glyphs[n]; R=R.copy(); cut=int(b-(XH+15)*RS)
    if cut>0: R[:cut]=False
    r=np.where(R.any(1))[0]; return [R[r.min():],b-r.min()]
glyphs['dotlessi']=dotless('i'); glyphs['dotlessj']=dotless('j')
# zero from O, narrowed
R,b=glyphs['O']; im=Image.fromarray((R*255).astype(np.uint8)); im=im.resize((int(im.width*0.78),im.height)); glyphs['zero']=[np.array(im)>127,b]
S_={
 'comma':([[(55,40),(25,-110)]],[(52,42,T*0.6)]),
 'colon':([],[(30,30,T*0.62),(30,370,T*0.62)]),
 'semicolon':([[(55,40),(25,-110)]],[(52,42,T*0.6),(52,370,T*0.62)]),
 'quotesingle':([[(40,700),(32,540)]],[]),
 'quoteright':([[(60,700),(30,550)]],[]),'quoteleft':([[(30,550),(60,700)]],[]),
 'parenleft':([[(200,740),(75,520),(40,250),(80,-10),(200,-180)]],[]),
 'parenright':([[(0,740),(125,520),(160,250),(120,-10),(0,-180)]],[]),
 'bracketleft':([[(170,740),(40,742),(42,-175),(170,-172)]],[]),
 'bracketright':([[(0,740),(130,742),(128,-175),(0,-172)]],[]),
 'hyphen':([[(0,275),(250,282)]],[]),'endash':([[(0,275),(420,282)]],[]),
 'underscore':([[(0,-90),(480,-86)]],[]),
 'equal':([[(0,375),(330,380)],[(0,205),(330,210)]],[]),
 'plus':([[(0,295),(370,300)],[(185,480),(182,110)]],[]),
 'asterisk':([[(150,670),(150,370)],[(20,595),(280,445)],[(20,445),(280,595)]],[]),
 'ampersand':([[(400,0),(120,380),(95,545),(175,665),(265,625),(245,505),(65,285),(45,120),(150,0),(270,40),(390,210)]],[]),
 'percent':([ell(100,560,90,120,0,360,14),ell(360,120,90,120,0,360,14),[(40,0),(420,680)]],[]),
 'numbersign':([[(110,0),(170,620)],[(270,0),(330,620)],[(25,420),(420,420)],[(0,200),(395,200)]],[]),
 'less':([[(330,530),(20,300),(330,70)]],[]),'greater':([[(0,530),(310,300),(0,70)]],[]),
 'asciitilde':([[(0,290),(90,355),(190,295),(290,235),(380,300)]],[]),
 'at':([ell(330,300,110,130,0,360,14)+[(440,300),(450,150),(560,180),(600,330),(520,560),(320,640),(120,560),(40,330),(110,100),(320,10),(520,60)]],[]),
 'bullet':([],[(80,320,T*1.3)]),'degree':([ell(110,580,85,100,0,360,14)],[]),
}
for k,(st,dt) in S_.items(): glyphs[k]=synth(st,dt)
glyphs['quotedblright']=glyphs['quotedbl']
x0,x1,_,_=bbox_units('S'); glyphs['dollar']=synth([[((x0+x1)/2,-90),((x0+x1)/2,770)]],base=glyphs['S'])
def trace(R,br):
    R=np.pad(R,3); out=[]
    for c in find_contours(R.astype(float),0.5):
        if len(c)<10: continue
        k=np.concatenate([c[-4:],c,c[:4]]); sm=ndimage.gaussian_filter1d(k,1.3,axis=0)[4:-4]
        sm=approximate_polygon(np.vstack([sm,sm[:1]]),0.55)[:-1]
        if len(sm)<3: continue
        out.append(np.array([((cc-3)/RS,(br+3-rr)/RS) for rr,cc in sm]))
    return out
def area(p): x,y=p[:,0],p[:,1]; return 0.5*np.sum(x*np.roll(y,-1)-np.roll(x,-1)*y)
uni={'exclam':'!','question':'?','quotedbl':'"','quotedblleft':'\u201c','quotedblright':'\u201d','backslash':'\\','slash':'/','period':'.',
 'comma':',','colon':':','semicolon':';','quotesingle':"'",'quoteright':'\u2019','quoteleft':'\u2018','parenleft':'(','parenright':')','bracketleft':'[','bracketright':']',
 'hyphen':'-','endash':'\u2013','underscore':'_','equal':'=','plus':'+','asterisk':'*','ampersand':'&','percent':'%','numbersign':'#','less':'<','greater':'>',
 'asciitilde':'~','at':'@','bullet':'\u2022','degree':'\u00b0','dollar':'$'}
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz": uni[c]=c
for i,n in enumerate(["zero","one","two","three","four","five","six","seven","eight","nine"]): uni[n]=str(i)
sys.path.insert(0,"mol"); import extend
COMB=extend.run(glyphs,synth,ell,T,RS,XH,CAPL,uni)
order=['.notdef','space']+sorted(k for k in glyphs if k in uni); print("missing",[k for k in uni if k not in glyphs])
glyf={};adv={};cmap={32:'space',0xA0:'space'}
for n in order[2:]:
    R,b=glyphs[n]; polys=trace(R,b); xs=np.concatenate([p[:,0] for p in polys]); mn,mx=xs.min(),xs.max()
    pen=TTGlyphPen(None)
    for i,p in enumerate(polys):
        if n not in COMB: p=p-[mn-LSB,0]
        depth=sum(MPath(q-([mn-LSB,0] if n not in COMB else [0,0])).contains_point(p[0]) for j,q in enumerate(polys) if j!=i)
        if (area(p)<0)!=(depth%2==0): p=p[::-1]
        pts=[(int(round(x)),int(round(y))) for x,y in p]; pen.moveTo(pts[0]); [pen.lineTo(q) for q in pts[1:]]; pen.closePath()
    glyf[n]=pen.glyph(); adv[n]=0 if n in COMB else int(round(mx-mn+2*LSB)); cmap[ord(uni[n])]=n
pen=TTGlyphPen(None); pen.moveTo((50,0));pen.lineTo((50,680));pen.lineTo((400,680));pen.lineTo((400,0));pen.closePath()
pen.moveTo((100,50));pen.lineTo((350,50));pen.lineTo((350,630));pen.lineTo((100,630));pen.closePath()
glyf['.notdef']=pen.glyph(); adv['.notdef']=450; glyf['space']=TTGlyphPen(None).glyph(); adv['space']=300
fb=FontBuilder(1000,isTTF=True); fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap); fb.setupGlyf(glyf)
fb.setupHorizontalMetrics({n:(adv[n],getattr(glyf[n],'xMin',0) if glyf[n].numberOfContours else 0) for n in order})
fb.setupHorizontalHeader(ascent=960,descent=-300)
fb.setupNameTable({"familyName":"SF Molander","styleName":"Regular","uniqueFontIdentifier":"SFMolander-Regular-1.0","fullName":"SF Molander","psName":"SFMolander-Regular","version":"Version 1.000"})
fb.setupOS2(sTypoAscender=860,sTypoDescender=-260,sTypoLineGap=200,usWinAscent=1030,usWinDescent=320,sxHeight=XH,sCapHeight=CAP,usWeightClass=400,fsSelection=0x40,achVendID="NONE")
fb.setupPost(); fb.setupHead(unitsPerEm=1000); fb.save(sys.argv[1]); print("saved",len(order))
