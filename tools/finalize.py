import sys
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.boundsPen import BoundsPen
src,dst,repo=sys.argv[1],sys.argv[2],sys.argv[3]
f=TTFont(src)
YEAR="2026"; FAM="Molander"
COPY=f"Copyright {YEAR} The Molander Project Authors ({repo})"
LIC="This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org"
names={0:COPY,1:FAM,2:"Regular",3:f"1.000;NONE;{FAM}-Regular",4:f"{FAM} Regular",5:"Version 1.000",6:f"{FAM}-Regular",
       8:"Jab Bonstein",9:"Jab Bonstein",11:repo,12:repo,13:LIC,14:"https://openfontlicense.org"}
nt=f["name"]; nt.names=[]
for k,v in names.items(): nt.setName(v,k,3,1,0x409)
# vertical metrics per Google Fonts guidance
gs=f.getGlyphSet(); ymax=-1e9; ymin=1e9
for g in f.getGlyphOrder():
    p=BoundsPen(gs); gs[g].draw(p)
    if p.bounds: ymin=min(ymin,p.bounds[1]); ymax=max(ymax,p.bounds[3])
asc=int(ymax)+10; desc=int(ymin)-10
os2=f["OS/2"]; hh=f["hhea"]; os2.version=4
os2.sTypoAscender=asc; os2.sTypoDescender=desc; os2.sTypoLineGap=0
os2.usWinAscent=asc; os2.usWinDescent=-desc
hh.ascent=asc; hh.descent=desc; hh.lineGap=0
os2.fsSelection=(os2.fsSelection|0x80|0x40)&~0x21
os2.fsType=0; os2.achVendID="NONE"; os2.usWeightClass=400
os2.ulCodePageRange1=1|2|4|8|16|128|256; os2.ulCodePageRange2=0
f["head"].fontRevision=1.0; f["head"].flags|=0x8; f["head"].macStyle=0
f["post"].isFixedPitch=0
if "gasp" not in f:
    g=newTable("gasp"); g.version=1; g.gaspRange={0xFFFF:15}; f["gasp"]=g
import time; f["head"].created=f["head"].modified=int(time.time())+2082844800
f.save(dst); print("asc",asc,"desc",desc)
