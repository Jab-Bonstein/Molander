import numpy as np, pickle
from scipy import ndimage
from PIL import Image, ImageDraw
d=np.load("mol/d.npy"); sat=np.load("mol/sat.npy")
ink=(d>40)&(sat<60)
reg=np.zeros_like(ink); reg[160:850,480:1620]=True; ink&=reg
lab,n=ndimage.label(ink,structure=np.ones((3,3)))
objs=ndimage.find_objects(lab)
comps=[]
for i,sl in enumerate(objs):
    a=(lab[sl]==i+1).sum()
    if a<12: continue
    comps.append(dict(id=i+1,y0=sl[0].start,y1=sl[0].stop,x0=sl[1].start,x1=sl[1].stop,a=a))
bands=[(160,262),(262,370),(380,507),(507,610),(610,720),(720,850)]
rows=[[] for _ in bands]
for c in comps:
    cy=(c["y0"]+c["y1"])/2
    for k,(a,b) in enumerate(bands):
        if a<=cy<b: rows[k].append(c)
groups=[]
for k,r in enumerate(rows):
    r.sort(key=lambda c:c["x0"]); G=[]
    for c in r:
        if G:
            g=G[-1]; ov=min(g["x1"],c["x1"])-max(g["x0"],c["x0"])
            small=min(c["a"],g["a"])<250
            if ov>-2 and (ov>0.3*min(c["x1"]-c["x0"],g["x1"]-g["x0"]) or small) or (small and ov>-14 and k==5 and c["a"]<250 and g["a"]<250):
                g["ids"].append(c["id"]); g["x0"]=min(g["x0"],c["x0"]); g["x1"]=max(g["x1"],c["x1"]); g["y0"]=min(g["y0"],c["y0"]); g["y1"]=max(g["y1"],c["y1"]); g["a"]+=c["a"]; continue
        G.append(dict(ids=[c["id"]],x0=c["x0"],x1=c["x1"],y0=c["y0"],y1=c["y1"],a=c["a"],row=k))
    groups+=G; print(k,len(G),[ (g["x0"],g["a"]) for g in G])
pickle.dump(groups,open("mol/groups.pkl","wb")); np.save("mol/lab.npy",lab)
im=Image.fromarray(np.uint8(~ink*255)).convert("RGB"); dr=ImageDraw.Draw(im)
for j,g in enumerate(groups): dr.rectangle([g["x0"],g["y0"],g["x1"],g["y1"]],outline=(255,0,0)); dr.text((g["x0"],g["y0"]-12),str(j),fill=(0,0,255))
im.crop((470,140,1640,860)).save("mol/boxes.png")
