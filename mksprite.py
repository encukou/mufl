from PIL import Image

base = Image.open('pics.png')

base.crop((64*0, 64*0, 64*2, 64*1)).save('images/fish.png')
base.crop((64*2, 64*0, 64*3, 64*1)).save('images/hook.png')

base.crop((64*15, 64*0, 64*16, 64*1)).save('images/sea.png')
