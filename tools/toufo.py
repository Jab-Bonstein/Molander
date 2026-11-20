import sys, ufoLib2
from fontTools.ttLib import TTFont
from fontTools.pens.pointPen import SegmentToPointPen
src,dst=sys.argv[1],sys.argv[2]
t=TTFont(src); gs=t.getGlyphSet(); cmap=t.getBestCmap(); rev={}
for u,n in cmap.items(): rev.setdefault(n,[]).append(u)
u=ufoLib2.Font()
for n in t.getGlyphOrder():
    g=u.newGlyph(n); g.width=t["hmtx"][n][0]; g.unicodes=sorted(rev.get(n,[]))
    gs[n].draw(SegmentToPointPen(g.getPointPen()))
nm=t["name"]; i=u.info; os2=t["OS/2"]; hh=t["hhea"]
i.familyName="Molander"; i.styleName="Regular"; i.unitsPerEm=1000
i.versionMajor=1; i.versionMinor=0
i.copyright=nm.getDebugName(0); i.openTypeNameLicense=nm.getDebugName(13); i.openTypeNameLicenseURL=nm.getDebugName(14)
i.openTypeNameDesigner=nm.getDebugName(9); i.openTypeNameManufacturer=nm.getDebugName(8)
i.openTypeNameDesignerURL=nm.getDebugName(12); i.openTypeNameManufacturerURL=nm.getDebugName(11)
i.ascender=os2.sTypoAscender; i.descender=os2.sTypoDescender; i.xHeight=os2.sxHeight; i.capHeight=os2.sCapHeight
i.openTypeOS2TypoAscender=os2.sTypoAscender; i.openTypeOS2TypoDescender=os2.sTypoDescender; i.openTypeOS2TypoLineGap=0
i.openTypeOS2WinAscent=os2.usWinAscent; i.openTypeOS2WinDescent=os2.usWinDescent
i.openTypeHheaAscender=hh.ascent; i.openTypeHheaDescender=hh.descent; i.openTypeHheaLineGap=0
i.openTypeOS2Selection=[7]; i.openTypeOS2Type=[]; i.openTypeOS2VendorID="NONE"; i.openTypeOS2WeightClass=400
i.postscriptFontName="Molander-Regular"; i.openTypeOS2CodePageRanges=[0,1,2,3,4,7,8]
u.lib["public.glyphOrder"]=t.getGlyphOrder()
u.save(dst,overwrite=True); print("ufo glyphs",len(u))
