from PIL import Image

base = Image.open('pics.png')

base.crop((0, 0, 16*8, 16*4)).save('images/fish.png')
