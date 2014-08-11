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
    print int(binascii.hexlify(arrayoffset),16)
    imagedata = bytearray()
    rowsize = int(round((img.width+31)/32.0*4.0))
    print size
    for i in range(1,size/rowsize):
        for j in range(1,rowsize-3):
            hexr = int(binascii.hexlify(f.read(1)),16)^0xff
            #hex = int('DD',16)
            hex1 = hexr>>4
            hex2 = hexr&0x0f
            #print "read:"+hex(hex1)
            #print "read2:"+hex(hex2)
            reversed_hex1 = sum(1<<(4-1-i) for i in range(4) if hex1>>i&1)
            reversed_hex2 = sum(1<<(4-1-i) for i in range(4) if hex2>>i&1)
            concat = str(hex(reversed_hex1))[2]+str(hex(reversed_hex2))[2]
            #imagedata.append(reversed_hex1)
            #imagedata.append(reversed_hex2)
            imagedata.append(int(concat,16))
            #print str(reversed_hex1)+str(reversed_hex2)
        f.seek(3,1)

    imagedatastr = binascii.hexlify(imagedata)[::-1]
    if len(imagedatastr)%2 is not 0:
        print "damn"

    img.downloadCmd = "~DGR:SAMPLE.GRF,"+str(len(imagedatastr)/2)+","+str(img.width*img.height/8/img.height)+","+imagedatastr
    return img
