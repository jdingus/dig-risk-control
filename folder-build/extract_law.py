import sys
from pypdf import PdfReader
r=PdfReader(sys.argv[1]); out=[]
for i,p in enumerate(r.pages,1):
    out.append(f"=== page {i}\n"+(p.extract_text() or ""))
open(sys.argv[2],"w").write("\n".join(out)+"\n")
print(len(r.pages),"pages")
