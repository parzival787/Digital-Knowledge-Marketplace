from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
files=sorted(Path('tmp/pdfs').glob('page-*.png'))
for start in range(0,len(files),4):
 group=files[start:start+4]
 sheet=Image.new('RGB',(1160,850),'#bcc8cf')
 for j,f in enumerate(group):
  im=Image.open(f);im.thumbnail((570,800))
  x=(j%2)*580;y=(j//2)*425
  im.thumbnail((570,400));sheet.paste(im,(x,y+20))
  ImageDraw.Draw(sheet).text((x+10,y+4),f.stem,fill='black')
 sheet.save(f'tmp/pdfs/review-{start//4+1}.png')
print(len(files),'pages rendered')
