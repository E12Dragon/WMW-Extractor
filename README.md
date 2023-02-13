# WMW-Extractor
Python script to dump sprites from the Where's My Water? series of games.

# Requirments
WMW-Extractor needs Pillow, Numpy, lxml and opencv-python to be installed. If you do not already have these libraries installed, you can use the below command.
```
pip install -r requirements.txt
```

# How to use
- Run main.py
- Select data file to use (.imagelist)
- Select texture file to use (.png, .webp, .jpg, .waltex)
- Sprites are dumped in a folder using the name of the texture file which is dumped in another folder called "out" which is created in the same directory as the script.
## Notes
- Waltex files are converted into pngs prior to sprite cutting. The extracted pngs as whole textures are dumped in the same folder as the selected file.
- WMW2 has some large texture atlases which are split into multiple texture files but only have one imagelist file. The script should select the correct list of sprites to use given the texture otherwise you are prompted as to which split you are using.
# Credits
- A big thanks to [campbellsonic](https://github.com/campbellsonic) and [ego-lay-atman-bay](https://github.com/ego-lay-atman-bay) for doing the hard working and creating a script that processes waltex files. 
- Thanks to [LolHacksRule](https://github.com/LolHacksRule) for their noesis script that reads important bytes of waltex files and the "width hack".
Footer
© 2023 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Docs
Contact GitHub
Pricing
API
Training
Blog
About
