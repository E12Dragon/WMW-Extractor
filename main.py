# Thanks to @campbellsonic for the wrapRawData script. It was originally written in C#.
# Thanks to @ego-lay-atman-bay for the rewrite in python.
# Thanks to @LolHacksRule for the "weird widths" hack.
# Sprite cutting capability by @E12Dragon

import xml.etree.ElementTree as ET
import cv2
from tkinter import Tk, filedialog
import tkinter
import os
import math
import numpy
from PIL import Image

def WaltexImage(image_file : str, size : tuple = (1024, 1024), colorspace : str = 'rgba4444', premultiplyAlpha : bool = False, dePremultiplyAlpha : bool = False, endian : str = 'little', offset : int = 0) -> Image.Image:
    """Get image from `waltex` file
    Data on image can be found in coorisponding `imagelist` or in `Data/TextureSettings.xml`.
    
    Args:
        image_file (str): image_file to `waltex` image
        size ((width,height), optional): Size of image. Defaults to (1024, 1024).
        colorspace (str, optional): Color spec of image. Defaults to 'rgba4444'.
        premultiplyAlpha (bool, optional): Defaults to False.
        dePremultiplyAlpha (bool, optional): Defaults to False.
        endian (str, optional): Endian mode. Set to 'big' or 1 to use big endian. Defaults to 'little'.
        offset (int, optional): General byte offset. Defaults to 0.
    Returns:
        PIL.Image: Pillow image.
    """
    colorspace = colorspace.lower()
    
    colorOrder = ''
    bytesPerPixel = 0
    bpprgba = []
    
    for i in range(len(colorspace)):
        if colorspace[i].isnumeric():
            bpprgba.append(int(colorspace[i]))
        else:
            colorOrder += colorspace[i]
            
    for i in range(len(bpprgba) - 4):
        bpprgba.append(0)
        
    bytesPerPixel = round(sum(bpprgba) / 8)
    # print(colorspace, bytesPerPixel, colorOrder, bpprgba)
    
    if endian == 'big' or endian == 1:
        colorOrder = colorOrder[::-1]
        # bpprgba = bpprgba[::-1] # don't know whether to use this or not
    
    with open(image_file, 'rb') as file:
        return WrapRawData(file.read(), size[0], size[1], bytesPerPixel, bpprgba[0], bpprgba[1], bpprgba[2], bpprgba[3], colorOrder, premultiplyAlpha, dePremultiplyAlpha, offset)

def WrapRawData(rawData : bytes, width : int, height : int, bytesPerPixel : int, redBits : int, greenBits : int, blueBits : int, alphaBits : int, colorOrder : str, premultiplyAlpha : bool = False, dePremultiplyAlpha : bool = False, offset : int = 0):
    _8BIT_MASK = 256.0
    OUTBITDEPTH = 8
    DEBUG_MODE = False
    
    colorOrder = colorOrder.lower()
    
    # width and height are switched due to how PIL creates an image from array
    # image = [[(0, 0, 0, 0)] * height] * width
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    x = 0
    y = 0
    
    redMask = GenerateBinaryMask(redBits)
    greenMask = GenerateBinaryMask(greenBits)
    blueMask = GenerateBinaryMask(blueBits)
    alphaMask = GenerateBinaryMask(alphaBits)
    
    redMax = math.pow(2, redBits)
    greenMax = math.pow(2, greenBits)
    blueMax = math.pow(2, blueBits)
    alphaMax = math.pow(2, alphaBits)
    
    # determine number of loops needed to get every pixel
    numLoops = int(len(rawData) / bytesPerPixel)
    
    # loop for each set of bytes (one pixel)
    for i in range(numLoops):
        pixel = 0
        
        # read all bytes for this pixel
        for j in range(bytesPerPixel):
            nextByte = rawData[i * bytesPerPixel + j + offset]
            
            # print(f'Read byte: {hex(nextByte)}')
            
            # move the byte up
            # if (reverseBytes)
            nextByte = nextByte << (8 * j)
            # else
            # pixel = pixel << 8
            
            # append the next one
            pixel += nextByte
            # print(f'Pixel is now: {hex(pixel)}')
            
        # print(f'Pixel: {pixel}')
        
        # get RGBA values from the pixel
        r, g, b, a, = 0, 0, 0, 0
        
        # loop for each channel
        for j in reversed(range(len(colorOrder))):
            color = colorOrder[j]
            
            if color == 'r':
                r = pixel & redMask
                pixel = pixel >> redBits
                
            elif color == 'g':
                g = pixel & greenMask
                pixel = pixel >> greenBits
            
            elif color == 'b':
                b = pixel & blueMask
                pixel = pixel >> blueBits
                
            else:
                a = pixel & alphaMask
                pixel = pixel >> alphaBits
                
        # print(f'Before scale:\nR: {r} G: {g} B: {b} A: {a}')
        
        # scale colors to 8-bit depth (not sure which method is better)
        
        # via floating point division
        if (redMax > 1):
            r = round(r * ((_8BIT_MASK - 1) / (redMax - 1)))
        if (greenMax > 1):
            g = round(g * ((_8BIT_MASK - 1) / (greenMax - 1)))
        if (blueMax > 1):
            b = round(b * ((_8BIT_MASK - 1) / (blueMax - 1)))
        if (alphaMax > 1):
            a = round(a * ((_8BIT_MASK - 1) / (alphaMax - 1)))
        
        # via bit shifting
        # rShift = OUTBITDEPTH - redBits
        # gShift = OUTBITDEPTH - greenBits
        # bShift = OUTBITDEPTH - blueBits
        # aShift = OUTBITDEPTH - alphaBits
        # r = (r << rShift) + (r >> (redBits - rShift))
        # g = (g << gShift) + (r >> (greenBits - gShift))
        # b = (b << bShift) + (r >> (blueBits - bShift))
        # a = (a << aShift) + (a >> (alphaBits - aShift))
        
        # print(f'After scale:\nR: {r} G: {g} B: {b} A: {a}')
        
        # if there are no bits allotted for an alpha channel, make pixel opaque rather than invisible
        if alphaBits == 0:
            a = 255
            
        # a = 255
            
        if dePremultiplyAlpha:
            r = round(r * a / 255.0)
            g = round(g * a / 255.0)
            b = round(b * a / 255.0)
            
        if premultiplyAlpha:
            if (a != 0):
                r = round(r * 255.0 / a)
                g = round(g * 255.0 / a)
                b = round(b * 255.0 / a)
            
        # set the pixel
        rgba = (int(r), int(g), int(b), int(a))
        # print(rgba)
        # image[x][y] = rgba
        image.putpixel((x,y), rgba)
        
        # break after first pixel if in debug mode
        
        
        # iterate coordinates
        x += 1
        if (x == width):
            x = 0
            y += 1
            # if (y > (height - 300) or y % 100 == 0):
            #     print(f'Line {y} of {height} done')
            #     if (DEBUG_MODE):
            #         break
                
        # if there's extra data (like the door overlays in the lawns), stop once the height is reached
        if y == height:
            break
        
    return image
    
def GenerateBinaryMask(numOnes):
    binaryMask = 0
    for i in range(numOnes):
        binaryMask *= 2
        binaryMask += 1
        
    return binaryMask
    
def cut_sprites(image_file, xml_file):
    # Give waltex files the treatment they need
    if image_file.endswith("waltex"):
        with open(image_file, "rb") as f:
            rawdata = f.read()
        if rawdata[:4].decode("utf-8") != "WALT":
            raise ValueError("Not a valid WALTex file")
        tex_fmt = rawdata[5]
        tex_size = rawdata[7]
        #Find what waltex format it is
        if tex_fmt == 0x0:
            print('rgba8888 format detected.')
            rawcolor = 'abgr8888'
            offset = 16
            width = int.from_bytes(rawdata[6:8], "little")
            height = int.from_bytes(rawdata[8:10], "little")
        elif tex_fmt == 0x3:
            rawcolor = 'rgba4444'
            offset = 16
            #Some rgba4444s have width and height flipped, this byte seems to be the answer
            if tex_size == 0x3:
                print('rgba4444 format detected. Flipped dimensions.')
                height = int.from_bytes(rawdata[6:8], "little")
                width = int.from_bytes(rawdata[8:10], "little")
            #Normal version
            else:
                print('rgba4444 format detected.')
                width = int.from_bytes(rawdata[6:8], "little")
                height = int.from_bytes(rawdata[8:10], "little")
        else:
            raise ValueError("Unknown texture format")
            
        #Some textures are dumb and have weird widths. This seems to occur with textures that only have a single sprite.
        if (width != 32 and width != 64 and width != 128 and width != 256 and width != 512 and width != 1024 and width != 2048 and width != 4096):
                    print("Unusual width detected. Adjusting automatically!")
                    if (width < 32):
                        width = 32
                    if (width > 32 and width < 64):
                        width = 64
                    if (width > 64 and width < 128):
                        width = 128
                    if (width > 128 and width < 256):
                        width = 256
                    if (width > 256 and width < 512):
                        width = 512
                    if (width > 512 and width < 1024):
                        width = 1024
                    if (width > 1024 and width < 2048):
                        width = 2048
                    if (width > 2048):
                        width = 4096
            
        print(f"Processing {(os.path.basename(image_file))}...")

        image = WaltexImage(image_file, (width, height), rawcolor, 'false', 'false', 'little', offset)
        #Download as PNG
        waltex_file = image_file.split('.')[0] + '.png'
        image_file = waltex_file
        image.save(os.path.splitext(image_file)[0] + '.png', "PNG")
        print(f"Saved as {(os.path.basename(image_file))}")
                    
    # Load the image using OpenCV
    image = cv2.imread(f"{image_file}", cv2.IMREAD_UNCHANGED)

    # Parse the XML file
    tree = ET.parse(f"{xml_file}")
    root = tree.getroot()

    # Find the ImageList tag
    image_list = root.find("ImageList")
    if image_list is None:
        image_list = root
    
    # Loop through all Page tags (for WMW2 files)
    pages = image_list.findall("Page")
    #If there are more than one page tags, this imagelist is for multiple texture files.
    if len(pages) > 1:
        #If the image file has not been renamed, we can automatically select the list by finding "split_{i+1}" in the name.
        for i, page in enumerate(pages):
            if f"split_{i+1}" in image_file:
                image_tags = page.findall("Image")
                print("This imagelist is for a large texture atlas that is split up into multiple image files. The appropriate sprite list has been chosen given the texture name.")
                break
        #If it has been renamed, we ask the user to specify which split they are after
        else:
            print("This imagelist is for a large texture atlas that is split up into multiple image files. Select which split you are using by typing numeric value:")
            image_tags = []
            for i, page in enumerate(pages):
                print(f"{i+1}) Split {i+1}")
            choice = int(input("Choose a split: "))
            image_tags = pages[choice - 1].findall("Image")
    #If there are one or none page tags then there must only be one texture
    elif len(pages) == 1:
        image_tags = pages[0].findall("Image")
    else:
        image_tags = image_list.findall("Image")

    # Check if the output directory exists, if not, create it
    output_dir = "out"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create the output directory
    output_name = image_file.split('.')[0]
    subdir  = f"{output_dir}/{os.path.splitext(os.path.basename(image_file))[0]}"
    os.makedirs(subdir , exist_ok=True)

    # Loop through all Image tags
    for image_tag in image_tags:
        # Get the sprite's name, width, height, x offset, and y offset from the rect attribute
        name = image_tag.get("name")
        rect = image_tag.get("rect")
        if rect is None:
            print(f"Error: Image '{name}' does not have a rect attribute")
            continue
        rect = [int(x) for x in rect.split()]
        if len(rect) != 4:
            print(f"Error: Image '{name}' has an invalid rect attribute")
            continue
        x, y, w, h = rect[0], rect[1], rect[2], rect[3]

        # Cut the sprite from the image
        sprite = image[y:y+h, x:x+w]
            
        # Save the sprite as a PNG
        cv2.imwrite(f"{subdir}/{name}", sprite, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        
        print(f"Extracted {name}")
        
    print("Sprites Extracted.")
# Example usage:
root = Tk()
root.withdraw()
data = tkinter.filedialog.askopenfilename(filetypes =[('IMAGELIST', '*.imagelist'),('All Files', '*.*')],
                                        title='Select Data File to use')
image = tkinter.filedialog.askopenfilename(filetypes =[('All Files', '*.*'),('PNG', '*.png'),('JPG', '*.jpg'),('WEBP', '*.webp'),('WALTEX', '*.waltex')],
                                        title='Select Image File to use')
cut_sprites(image, data)
