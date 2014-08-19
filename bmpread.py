import binascii
import math
import os
import base64
import hashlib
from pyZPL import *

imagedir = "images/"

def reverseByteArray(ba):
    newba = bytearray(len(ba))
    for i,b in enumerate(ba):
        newba[len(ba)-i-1] = b
    return newba

def convertImg(image,imageName,width,height,ispwidth,ispheight):
    os.system("convert "+imagedir+image+" -compress None -monochrome -colors 2 -depth 1 +dither "+imageName+".bmp")
    resizeStr = "convert "+imageName+".bmp"
    resize = False

    if width is not 0:
        resizeStr += " -width "+str(width)
        if ispwidth:
            resizeStr += '%'
        resize = True
    if height is not 0:
        reizeStr += " -height "+str(height)
        if ispheight:
            resizeStr += '%'
        resize = True

    if resize:
        resizeStr += " "+imageName+".bmp"
        os.system(resizeStr)

def getImg(image,width,height,ispwidth,ispheight):
    img = ZPLImage()
    fileSplit = image.split('/')
    fileName = fileSplit[len(fileSplit)-1]
    imageSplit = fileName.split('.')
    imageName = str.join('.',imageSplit[:len(imageSplit)-1])
    print image
    print imageName
    convertImg(image,imageName,width,height,ispwidth,ispheight)
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
    rowsize = int(round(size/img.height))
    padding = 4-(int(round(img.width/8.0))%4)
    for i in range(0,size/rowsize):
        for j in range(0,rowsize-padding):
            hexr = int(binascii.hexlify(f.read(1)),16)^0xff
            hex1 = hexr>>4
            hex2 = hexr&0x0f
            reversed_hex1 = sum(1<<(4-1-i) for i in range(4) if hex1>>i&1)
            reversed_hex2 = sum(1<<(4-1-i) for i in range(4) if hex2>>i&1)
            concat = str(hex(reversed_hex1))[2]+str(hex(reversed_hex2))[2]
            imagedata.append(int(concat,16))
        f.seek(padding,1)
    imagedatastr = binascii.hexlify(imagedata)[::-1]

    if len(imagedatastr)%2 is not 0:
        print "damn"

    #Take the first 7 characters of a base32-encoded sha-1 hash of the image data,
    #and use that as the name when downloading. This ensures that the file names are always
    #7 or fewer characters (as per ZPL requirements) but have a very low chance of colliding
    img.downloadName = base64.b32encode(hashlib.sha1(imagedatastr).digest())[:7]
    img.downloadCmd = "~DGR:"+img.downloadName+".GRF,"+str(len(imagedatastr)/2)+","+str(img.width*img.height/8/img.height)+","+imagedatastr
    return img
