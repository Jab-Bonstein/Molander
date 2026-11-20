import numpy as np, unicodedata, math
from PIL import Image
from fontTools.agl import UV2AGL
def run(glyphs, synth, ell, T, RS, XH, CAPL, uni):
    def gn(cp): return UV2AGL.get(cp, "uni%04X"%cp)
    def bbox(n):
        R,b=glyphs[n]; r=np.where(R.any(1))[0]; c=np.where(R.any(0))[0]
        return c.min()/RS, (c.max()+1)/RS, (b-r.max()-1)/RS, (b-r.min())/RS  # x0,x1,ybot,ytop
    def compose(parts):
        # parts: (glyph,dx,dy) glyph = [R,b]
        L=1e9;Rr=-1e9;Tp=-1e9;Bt=1e9
        for (R,b),dx,dy in parts:
            L=min(L,dx);Rr=max(Rr,dx+R.shape[1]/RS);Tp=max(Tp,dy+b/RS);Bt=min(Bt,dy+(b-R.shape[0])/RS)
        W=int(math.ceil((Rr-L)*RS))+2;H=int(math.ceil((Tp-Bt)*RS))+2
        C=np.zeros((H,W),bool)
        for (R,b),dx,dy in parts:
            x=int(round((dx-L)*RS)); y=int(round((Tp-(dy+b/RS))*RS))
            C[y:y+R.shape[0],x:x+R.shape[1]]|=R
        return [C,Tp*RS]
    def scaled(n,f):
        R,b=glyphs[n]; im=Image.fromarray((R*255).astype(np.uint8)).resize((max(1,int(R.shape[1]*f)),max(1,int(R.shape[0]*f))),Image.BILINEAR)
        return [np.array(im)>110,b*f]
    def rot(n):
        R,b=glyphs[n]; return [R[::-1,::-1].copy(),R.shape[0]-b]
    def add(name,g,ch=None):
        glyphs[name]=g
        if ch: uni[name]=ch
    # --- dotless ---
    add('dotlessi',glyphs['dotlessi'],'ı'); add('dotlessj',glyphs['dotlessj'],'ȷ')
    # --- marks (centered x=0, bottom y=0 for above; top y=0 for below) ---
    M={
     'grave':([[(45,0),(-55,135)]],[]),'acute':([[(-45,0),(55,135)]],[]),
     'circumflex':([[(-110,0),(0,125),(110,0)]],[]),'caron':([[(-110,125),(0,0),(110,125)]],[]),
     'tilde':([[(-130,15),(-70,85),(0,45),(70,5),(130,70)]],[]),'macron':([[(-130,40),(130,46)]],[]),
     'breve':([ell(0,125,115,115,195,345,10)],[]),'dotaccent':([],[(0,40,T*0.7)]),
     'dieresis':([],[(-75,40,T*0.7),(75,40,T*0.7)]),'ring':([ell(0,75,65,70,0,360,14)],[]),
     'hungarumlaut':([[(-110,0),(-30,135)],[(40,0),(120,135)]],[]),
     'cedilla':([[(0,0),(10,-60),(85,-105),(60,-185),(-55,-195)]],[]),
     'ogonek':([[(40,0),(-50,-95),(-15,-195),(80,-205)]],[]),
     'commaaccent':([[(15,-50),(-20,-190)]],[(14,-52,T*0.6)]),
     'caronalt':([[(25,0),(-5,-150)]],[]),'gcommaturned':([[(10,150),(-15,0)]],[(10,150,T*0.6)]),
    }
    MG={k:synth(s,d,wob=3) for k,(s,d) in M.items()}
    above={'̀':'grave','́':'acute','̂':'circumflex','̃':'tilde','̄':'macron','̆':'breve','̇':'dotaccent','̈':'dieresis','̊':'ring','̋':'hungarumlaut','̌':'caron'}
    below={'̧':'cedilla','̨':'ogonek','̦':'commaaccent'}
    def mbox(k):
        R,b=MG[k]; c=np.where(R.any(0))[0]; r=np.where(R.any(1))[0]
        return c.min()/RS,(c.max()+1)/RS,(b-r.max()-1)/RS,(b-r.min())/RS
    comb={}
    for cp,k in list(above.items())+list(below.items()):
        comb[gn(ord(cp))]=(k,cp)
        x0,x1,yb,yt=mbox(k); h=XH+40 if cp in above else 0
        add(gn(ord(cp)),compose([(MG[k],-230-(x0+x1)/2,h-yb if cp in above else -yt)]),cp)
    spacing={'`':'grave','´':'acute','ˆ':'circumflex','ˇ':'caron','˜':'tilde','¯':'macron','˘':'breve','˙':'dotaccent','¨':'dieresis','˚':'ring','˝':'hungarumlaut','¸':'cedilla','˛':'ogonek'}
    for cp,k in spacing.items():
        x0,x1,yb,yt=mbox(k); dy=(XH+60-yb) if k not in ('cedilla','ogonek') else -yt
        add(gn(ord(cp)),compose([(MG[k],0,dy)]),cp)
    add('asciicircum',compose([(synth([[(-150,0),(0,260),(150,0)]],[]),0,380)]),'^')
    # --- precomposed ---
    def base_for(ch): return {'i':'dotlessi','j':'dotlessj'}.get(ch, ch)
    todo=[c for c in range(0xC0,0x250)]+list(range(0x1E80,0x1E86))+[0x1EF2,0x1EF3,0x218,0x219,0x21A,0x21B]
    for c in todo:
        ch=chr(c); d=unicodedata.decomposition(ch)
        if not d or d.startswith('<'): continue
        p=d.split()
        if len(p)!=2: continue
        b=chr(int(p[0],16)); m=chr(int(p[1],16))
        bn=base_for(b)
        if bn not in glyphs or (m not in above and m not in below): continue
        x0,x1,yb,yt=bbox(bn); cx=(x0+x1)/2
        if m in above:
            k=above[m]; mx0,mx1,myb,myt=mbox(k)
            if m=='̌' and b in 'dlLt':
                k='caronalt'; mx0,mx1,myb,myt=mbox(k); dx=x1+15-mx0; dy=yt-myt
                if b=='t': dy=yt-myt+30
            else:
                gap=55 if b.islower() else 45; dx=cx-(mx0+mx1)/2; dy=yt+gap-myb
                if b=='g' and m=='̦': pass
            parts=[(glyphs[bn],0,0),(MG[k],dx,dy)]
        else:
            k=below[m]; mx0,mx1,myb,myt=mbox(k)
            if b in 'gG' and m=='̧' and b=='g':
                k='gcommaturned'
            if k=='ogonek': dx=x1-80-(mx0+mx1)/2; dy=yb+10-myt
            elif b=='g' :
                k='gcommaturned'; mx0,mx1,myb,myt=mbox(k); dx=cx-(mx0+mx1)/2; dy=yt+40-myb
            else: dx=cx-(mx0+mx1)/2; dy=yb-myt-(20 if k=='commaaccent' else -5)
            parts=[(glyphs[bn],0,0),(MG[k],dx,dy)]
        add(gn(c),compose(parts),ch)
    # g with cedilla decomposition is 0123 = g + cedilla(0327): handled above via gcommaturned
    # --- other letters ---
    S=lambda st,dt=(),**k: synth(st,dt,**k)
    def bar(n,y,xa,xb,ch,name):
        add(name,compose([(glyphs[n],0,0),(S([[(xa,y),(xb,y+5)]]),xa-T/2- (0),y-T/2)]) if False else compose([(glyphs[n],0,0),(S([[(0,0),(xb-xa,5)]]),xa-T,y-T)]),ch)
    x0,x1,yb,yt=bbox('D'); bar('D',(yt)/2,x0-60,x0+(x1-x0)*0.45,'Đ','Dcroat'); glyphs['Eth']=glyphs['Dcroat']; uni['Eth']='Ð'
    x0,x1,yb,yt=bbox('d'); bar('d',yt-150,x1-210,x1+40,'đ','dcroat')
    x0,x1,yb,yt=bbox('h'); bar('h',yt-150,x0-50,x0+170,'ħ','hbar')
    x0,x1,yb,yt=bbox('H'); bar('H',yt*0.74,x0-40,x1+40,'Ħ','Hbar')
    for n,ch,nm in [('L','Ł','Lslash'),('l','ł','lslash')]:
        x0,x1,yb,yt=bbox(n); sx=x0+T*0.4 if n=='l' else x0+T*0.4
        add(nm,compose([(glyphs[n],0,0),(S([[(0,0),(240,170)]]),sx-120-T,yt*0.42-85-T)]),ch)
    for n,ch,nm in [('O','Ø','Oslash'),('o','ø','oslash')]:
        x0,x1,yb,yt=bbox(n)
        add(nm,compose([(glyphs[n],0,0),(S([[(0,0),(x1-x0+60,yt-yb+80)]]),x0-30-T,yb-40-T)]),ch)
    def lig(a,b_,ov,ch,nm):
        ax0,ax1,_,_=bbox(a); bx0,_,_,_=bbox(b_); add(nm,compose([(glyphs[a],0,0),(glyphs[b_],ax1-ov-bx0,0)]),ch)
    lig('A','E',70,'Æ','AE'); lig('O','E',80,'Œ','OE'); lig('a','e',45,'æ','ae'); lig('o','e',45,'œ','oe')
    cf=CAPL/680
    add('germandbls',S([[(40,-10),(40,560),(110,710),(230,712),(295,610),(235,485),(150,455),(305,375),(335,200),(265,40),(150,5)]]),'ß')
    add('uni1E9E',S([[(40,0),(40,560*cf),(120,680*cf),(300,680*cf),(170,420*cf),(330,350*cf),(360,170*cf),(270,20),(140,5)]]),'ẞ')
    add('Thorn',S([[(0,680*cf),(4,0)],[(0,540*cf),(260,515*cf),(320,380*cf),(260,250*cf),(0,215*cf)]]),'Þ')
    add('thorn',S([[(0,720),(4,-250)],[(0,380),(150,430),(280,350),(290,150),(160,0),(0,40)]]),'þ')
    add('eth',S([ell(170,190,155,190,0,360,16),[(320,250),(255,520),(110,710)],[(110,560),(320,650)]]),'ð')
    # punctuation & symbols
    add('multiply',S([[(0,80),(260,340)],[(0,340),(260,80)]]),'×')
    add('divide',S([[(0,215),(330,220)]],[(165,370,T*0.65),(165,65,T*0.65)]),'÷')
    add('minus',S([[(0,298),(370,302)]]),'−')
    add('emdash',S([[(0,280),(820,288)]]),'—')
    add('quotesinglbase',glyphs['comma'],'‚')
    c0,c1,_,_=bbox('comma'); add('quotedblbase',compose([(glyphs['comma'],0,0),(glyphs['comma'],c1-c0+20,0)]),'„')
    p0,p1,_,_=bbox('period'); w=p1-p0+60; add('ellipsis',compose([(glyphs['period'],0,0),(glyphs['period'],w,0),(glyphs['period'],2*w,0)]),'…')
    add('guilsinglleft',S([[(150,370),(0,220),(150,70)]]),'‹'); add('guilsinglright',S([[(0,370),(150,220),(0,70)]]),'›')
    add('guillemotleft',S([[(150,370),(0,220),(150,70)],[(310,370),(160,220),(310,70)]]),'«'); add('guillemotright',S([[(0,370),(150,220),(0,70)],[(160,370),(310,220),(160,70)]]),'»')
    add('Euro',S([ell(300,340,270,340,40,320,16),[(0,410),(330,410)],[(0,270),(310,270)]]),'€')
    add('sterling',S([[(380,620),(300,690),(190,670),(150,520),(140,250),(90,80),(20,0),(390,10)],[(30,350),(300,355)]]),'£')
    add('yen',S([[(0,680),(200,360),(400,680)],[(200,360),(200,0)],[(60,300),(340,300)],[(60,170),(340,170)]]),'¥')
    x0,x1,yb,yt=bbox('c'); add('cent',compose([(glyphs['c'],0,0),(S([[(0,0),(0,yt-yb+160)]]),(x0+x1)/2-T,yb-80-T)]),'¢')
    add('section',S([[(280,640),(160,700),(50,630),(110,520),(260,440),(290,320),(180,250)],[(170,450),(60,380),(60,270),(200,190),(250,80),(140,-20),(20,30)]]),'§')
    add('paragraph',S([[(250,680),(250,-120)],[(360,680),(360,-120)],[(380,680),(140,682),(30,600),(40,460),(150,400),(250,400)]]),'¶')
    add('periodcentered',S([],[(40,300,T*0.65)]),'·')
    add('bar',S([[(0,760),(4,-200)]]),'|')
    add('braceleft',S([[(220,740),(120,700),(110,480),(80,330),(0,300),(80,270),(110,120),(120,-120),(220,-170)]]),'{')
    add('braceright',S([[(0,740),(100,700),(110,480),(140,330),(220,300),(140,270),(110,120),(100,-120),(0,-170)]]),'}')
    add('grave_dummy',glyphs['period'])  # placeholder removed below
    del glyphs['grave_dummy']
    add('exclamdown',[*rot('exclam')[:1],rot('exclam')[1]],None); R,b=glyphs['exclamdown']; glyphs['exclamdown']=[R,b+XH*RS]; uni['exclamdown']='¡'
    R,b=rot('question'); glyphs['questiondown']=[R,b+XH*RS]; uni['questiondown']='¿'
    for n,src,ch in [('ordfeminine','a','ª'),('ordmasculine','o','º')]:
        sm=scaled(src,0.6); x0,x1,_,_=[v for v in (0,sm[0].shape[1]/RS,0,0)]
        add(n,compose([(sm,0,330),(S([[(0,0),(x1,4)]]),-T/2,250)]),ch)
    circ=S([ell(330,340,330,340,0,360,24)])
    for n,src,ch in [('copyright','C','©'),('registered','R','®')]:
        sm=scaled(src,0.5); cx0,cx1,cyb,cyt=0,sm[0].shape[1]/RS,0,0
        add(n,compose([(circ,-T,-T),(sm,330-cx1/2,340-0.5*CAPL*0.5)]),ch)
    t=scaled('T',0.45); m=scaled('M',0.45); add('trademark',compose([(t,0,CAPL*0.55),(m,t[0].shape[1]/RS+10,CAPL*0.55)]),'™')
    add('currency',S([ell(170,300,125,125,0,360,16),[(30,160),(-20,110)],[(310,160),(360,110)],[(30,440),(-20,490)],[(310,440),(360,490)]]),'\u00a4')
    add('brokenbar',S([[(0,760),(2,380)],[(2,200),(4,-200)]]),'\u00a6')
    add('logicalnot',S([[(0,360),(330,365),(328,200)]]),'\u00ac')
    add('uni00AD',glyphs['hyphen'],'\u00ad')
    add('plusminus',S([[(0,360),(370,365)],[(185,540),(182,180)],[(0,60),(370,66)]]),'\u00b1')
    sup={}
    for d,cp in [('one','\u00b9'),('two','\u00b2'),('three','\u00b3'),('four','\u2074')]:
        sm=scaled(d,0.55); sup[d]=sm; add({'one':'onesuperior','two':'twosuperior','three':'threesuperior','four':'uni2074'}[d],compose([(sm,0,330)]),cp)
    x0,x1,yb,yt=bbox('u'); add('mu',compose([(glyphs['u'],0,0),(S([[(0,0),(-6,XH+240)]]),x0-T*0.5,-250-T)]),'\u00b5')
    fs=S([[(0,-30),(300,700)]]); add('fraction',fs,'\u2044'); add('uni2215',glyphs['slash'],'\u2215')
    def frac(a,b_,nm,cp):
        A=scaled(a,0.55); B=scaled(b_,0.55); aw=A[0].shape[1]/RS
        add(nm,compose([(A,0,330),(fs,aw-90,0),(B,aw+150,-10)]),cp)
    frac('one','four','onequarter','\u00bc'); frac('one','two','onehalf','\u00bd'); frac('three','four','threequarters','\u00be')
    return comb
