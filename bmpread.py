import binascii
import math
import os
from pyZPL import *

def reverseByteArray(ba):
    newba = bytearray(len(ba))
    for i,b in enumerate(ba):
        newba[len(ba)-i-1] = b
    return newba

def convertImg(image,imageName,width,height):
    os.system("convert "+image+" -compress None -monochrome -colors 2 -depth 1 +dither "+imageName+".bmp")
    resizeStr = "convert "+imageName+".bmp"
    resize = False
    
    if width is not 0:
        resizeStr += " -width "+str(width)
        resize = True
    if height is not 0:
        reizeStr += " -height "+str(height)
        resize = True
    
    if resize:
        resizeStr += " "+imageName+".bmp"
        os.system(resizeStr)

def getImg(image,width,height):
    img = ZPLImage()
    imageSplit = image.split('.')
    imageName = ""
    imageName = imageName.join(imageSplit[0:len(imageSplit)-1])
    convertImg(image,imageName,width,height)
    f = open(imageName+".bmp","rb")
    f.seek(10)
    arrayoffset = reverseByteArray(bytearray(f.read(4)))

    f.seek(18)
    widthbytes = reverseByteArray(bytearray(f.read(4)))
    img.width = int(binascii.hexlify(widthbytes),16)
    heightbytes = reverseByteArray(bytearray(f.read(4)))
    img.height = int(binascii.hexlify(heightbytes),16)
    print img.width

    f.seek(34)
    sizebytes = reverseByteArray(bytearray(f.read(4)))
    size = int(binascii.hexlify(sizebytes),16)

    f.seek(int(binascii.hexlify(arrayoffset),16))
    imagedata = bytearray()
    rowsize = int(4.0 * round(((img.width+31)/32.0*4.0)/4.0))
    #print rowsize
    for i in range(1,size/rowsize):
        for j in range(0,rowsize-3):
            hex = int(binascii.hexlify(f.read(1)),16)
            #hex = int('DD',16)
            hex1 = hex>>4
            hex2 = hex<<4
            hex2 = hex2>>4
            #print "read:"+str(hex)
            reversed_hex1 = sum(1<<(4-1-i) for i in range(4) if hex1>>i&1)
            reversed_hex2 = sum(1<<(4-1-i) for i in range(4) if hex2>>i&1)
            imagedata.append(reversed_hex1^0xFF)
            imagedata.append(reversed_hex2^0xFF)
            #print str(reversed_hex1)+str(reversed_hex2)
        f.seek(3,1)

    imagedatastr = binascii.hexlify(imagedata)
    if len(imagedatastr)%2 is not 0:
        print "damn"

    reversedIDS = ""
    i = 0
    print len(imagedatastr)
    while(i<len(imagedatastr)):
        print len(imagedatastr)-i-2
        print len(imagedatastr)-i-1
        reversedIDS += imagedatastr[len(imagedatastr)-i-2:len(imagedatastr)-i-1]
        i += 2
    print reversedIDS

    #reversedIDS = imagedatastr
    img.downloadCmd = "~DGR:SAMPLE.GRF,"+str(len(reversedIDS)/2)+","+str(img.width*img.height/8/img.height)+","+reversedIDS
    return img
