import binascii
import math

def reverseByteArray(ba):
    newba = bytearray(len(ba))
    for i,b in enumerate(ba):
        newba[len(ba)-i-1] = b
    return newba

f = open("SymbolD1_sm.bmp","rb")
f.seek(10)
arrayoffset = reverseByteArray(bytearray(f.read(4)))

f.seek(18)
widthbytes = reverseByteArray(bytearray(f.read(4)))
width = int(binascii.hexlify(widthbytes),16)
heightbytes = reverseByteArray(bytearray(f.read(4)))
height = int(binascii.hexlify(heightbytes),16)
print width

f.seek(34)
sizebytes = reverseByteArray(bytearray(f.read(4)))
size = int(binascii.hexlify(sizebytes),16)

f.seek(int(binascii.hexlify(arrayoffset),16))
imagedata = ""
rowsize = int(4.0 * round(((width+31)/32.0*4.0)/4.0))
print rowsize
for i in range(1,size/rowsize):
    imagedata += f.read(rowsize-3)
    f.seek(3,1);

imagedatastr = binascii.hexlify(imagedata)
if len(imagedatastr)%2 is not 0:
    print "damn"

print len(imagedatastr)
command = "~DGR:SAMPLE.GRF,"+str(len(imagedatastr)/2)+","+str(width*height/8/height)+","+imagedatastr
print command
