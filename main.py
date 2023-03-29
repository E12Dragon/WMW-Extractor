# Thanks to @campbellsonic for the wrapRawData script. It was originally written in C#.
# Thanks to @ego-lay-atman-bay for the rewrite in python.
# Thanks to @LolHacksRule for the "weird widths" hack.
# Sprite cutting capability and interface options by @E12Dragon

import xml.etree.ElementTree as ET
import cv2
from os import system
import os
import shutil
import math
import numpy
from PIL import Image
from tkinter import Tk, filedialog
import tkinter
from colorama import init, Fore, Back, Style

# Initializes Colorama
init(autoreset=True)

# Close window function
def clear_directory(dir_path):
    # check if the directory exists
    if os.path.exists(dir_path):

        # remove all files and folders in the directory
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(Fore.RED + f'Failed to delete {file_path}. Reason: {e}')
        print(Fore.GREEN + f'"{dir_path}" directory has been cleared!')
    else:
        print(Fore.RED + f'{dir_path} does not exist.')
# Pulls information from a give waltex file by rading bytes from the header
def DefineWaltex(image_file):
    if image_file.endswith("waltex"):
        with open(image_file, "rb") as f:
            rawdata = f.read()
        if rawdata[:4].decode("utf-8") != "WALT":
            raise ValueError(Fore.RED + "Not a valid WALTex file")
        tex_fmt = rawdata[5]
        offset = 16
        #Find what waltex format it is
        if tex_fmt == 0x0:
            print('WALTEX rgba8888 format detected.')
            rawcolor = 'abgr8888'
            width = int.from_bytes(rawdata[6:8], "little")
            height = int.from_bytes(rawdata[8:10], "little")
        elif tex_fmt == 0x3:
            print('WALTEX rgba4444 format detected.')
            rawcolor = 'rgba4444'
            width = int.from_bytes(rawdata[6:8], "little")
            height = int.from_bytes(rawdata[8:10], "little")
        else:
            raise ValueError(Fore.RED + "Unknown texture format")
            
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
            
        print(Fore.YELLOW + f"Converting {(os.path.basename(image_file))}...")

        waltex_image = WaltexImage(image_file, (width, height), rawcolor, 'false', 'false', 'little', offset)
        output_name = os.path.basename(image_file).split('.')[0] + '.png'
        output_dir = "out-waltex"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        waltex_image.save('out-waltex/' + output_name, "PNG")
        print(Fore.GREEN + f"Saved WALTEX as {output_name}")
    
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
        DefineWaltex(image_file)
        image_file = os.path.join("out-waltex/", os.path.basename(image_file).split(".")[0] + '.png')
        
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
    output_dir = "out-sprites"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create the output directory for the sprites
    output_name = image_file.split('.')[0]
    subdir  = f"{output_dir}/{os.path.splitext(os.path.basename(image_file))[0]}"
    os.makedirs(subdir , exist_ok=True)

    # Loop through all Image tags
    for image_tag in image_tags:
        # Get the sprite's name, width, height, x offset, and y offset from the rect attribute
        name = image_tag.get("name")
        rect = image_tag.get("rect")
        if rect is None:
            print(Fore.RED + f"Error: Image '{name}' does not have a rect attribute")
            continue
        rect = [int(x) for x in rect.split()]
        if len(rect) != 4:
            print(Fore.RED + f"Error: Image '{name}' has an invalid rect attribute")
            continue
        x, y, w, h = rect[0], rect[1], rect[2], rect[3]

        # Cut the sprite from the image
        sprite = image[y:y+h, x:x+w]
            
        # Save the sprite as a PNG
        cv2.imwrite(f"{subdir}/{name}", sprite, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        
        print(f"Extracted {name}")
        
    print(Fore.GREEN + f"All sprites extracted from {os.path.basename(image_file)}")
    
#INITIATING SCRIPT
def extractor():
    line = "-----------------------------------------------------------------------------------------------------------"
    print(line)
    print(Style.BRIGHT + Fore.GREEN + "                              WMW-Extractor | Version 1.0.1 | by E12Dragon")
    print("                                   github.com/E12Dragon/WMW-Extractor")
    print(line)
    print(Style.NORMAL + Back.GREEN + Fore.BLACK + " FUNCTIONS                                                              ")
    print("    1 Extract sprites from all files")
    print("    2 Extract sprites from specific files")
    print("    3 Convert all WALTEX to PNG")
    print("    4 Convert specific WALTEX to PNG")
    print(Style.NORMAL + Back.GREEN + Fore.BLACK + " OTHER                                                                  ")
    print("  101 Clear input directory")
    print("  102 Clear extracted sprites directory")
    print("  103 Clear extracted WALTEX directory")
    print("  104 Quit extractor")
    print(line)
    choice = input("Your Choice: ")
    print(line)
    
    #Define and if needed create input directory
    input_dir = "in/"
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    
    #Find all texture and xml files in the "in" folder and extract the sprites from them
    if choice == '1':
        # get list of files in input directory
        input_files = os.listdir(input_dir)

        # filter out non-data and non-image files
        xml_files = [f for f in input_files if f.endswith('.imagelist')]
        image_files = [f for f in input_files if f.endswith('.png') or f.endswith('.jpg') or f.endswith('.webp') or f.endswith('.waltex')]

        # process image and data files together
        for image_file in image_files:
            image_base = os.path.splitext(image_file)[0]
            image_base = image_base.replace('_split_1', '').replace('_split_2', '').replace('_split_3', '') #this is a lazy way to deal with splits but it works
            xml_file = next((f for f in xml_files if os.path.splitext(f)[0] == image_base), None)
            if xml_file:
                xml_file = os.path.join(input_dir, xml_file)
                print(Fore.BLUE + f"Processing {os.path.basename(xml_file)} and {image_file}")
                cut_sprites(os.path.join(input_dir, image_file), xml_file)
            else:
                print(Fore.RED + f'{image_base}.imagelist does not exist!')
    #Use tkinter to get the user to provide a single pair of texture and xml files.
    elif choice == '2':
        root = Tk()
        root.withdraw()
        xml_file = tkinter.filedialog.askopenfilename(filetypes =[('IMAGELIST', '*.imagelist'),('All Files', '*.*')],
                                                title='Select Data File to use')
        image_file = tkinter.filedialog.askopenfilename(filetypes =[('All Files', '*.*'),('PNG', '*.png'),('JPG', '*.jpg'),('WEBP', '*.webp'),('WALTEX', '*.waltex')],
                                                title='Select Image File to use')
        if image_file == '':  
            print(Fore.RED + "You must provide a texture file!")
        elif xml_file == '':  
            print(Fore.RED + "You must provide an imagelist file!")
        else:
            cut_sprites(image_file, xml_file)
    elif choice == '3':
        # get list of files in input directory
        input_files = os.listdir(input_dir)

        # filter out non-waltex files
        image_files = [f for f in input_files if f.endswith('.waltex')]
            
        # Check if there are any waltex files and convert each one
        if image_files == []:
            print(Fore.RED + f'You must place a WALTEX file inside the "in" directory')
        else:
            for image_file in image_files:
                image_base = os.path.splitext(image_file)[0]
                image_base = image_base
                image_file = os.path.join(input_dir, image_file)
                print(Fore.BLUE + f"Processing {os.path.basename(image_file)}")
                DefineWaltex(image_file)
    #Use tkinter to get the user to provide the single waltex file
    elif choice == '4':
        root = Tk()
        root.withdraw()
        image_file = tkinter.filedialog.askopenfilename(filetypes =[('All Files', '*.*'),('WALTEX', '*.waltex')],
                                                title='Select WALTEX File to use')
        if image_file == '':  
            print(Fore.RED + "You must provide a WALTEX file!")
        else:
            DefineWaltex(image_file)
    elif choice == '101':
        clear_directory("in")
    elif choice == '102':
        clear_directory("out-sprites")
    elif choice == '103':
        clear_directory("out-waltex")
    elif choice == '104':
        exit()
    else:
        print(Fore.RED + "Not a valid function!")
    print(Back.WHITE + Fore.BLACK + 'Press ENTER to run WMW-Extractor again')
    repeat = input()
    if repeat == "":
        extractor()
extractor()
