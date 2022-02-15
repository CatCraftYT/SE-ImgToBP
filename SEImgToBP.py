from PIL import Image
import os
import shutil


def ConvertToCMHSV(hsv=()):
    # values here adjust hsv values to color correct them, as the conversion messes up the image's colors
    # values obtained by dividing a correct HSV value by a 'conversion tainted' HSV value
    # the multiple stays the same even with different images (happily)
    # other values are obtained from https://www.reddit.com/r/spaceengineers/comments/53nkhz/blueprint_color_change/ and ingame observations
    return (
        ((hsv[0]*1.44680851064) / 360),
        ((hsv[1]*0.40816326531) / 100) - 0.8,
        ((hsv[2]*0.39024390244) / 100) - 0.45
    )


#get path to python script that was just run
filepath = '\\'.join(os.path.realpath(__file__).split('\\')[0:-1])

#get path to original image
print('Note: It is highly recommended that you choose files with a total pixel count of under 100,000. Remember, each pixel is a block.')
imgPath = input("Put FULL image path here (including file with extension): ")
imgName = imgPath.split('\\')[-1].split('.')[0]

#open and convert file to HSV color space
with open(imgPath, "rb") as file:
    img = Image.open(file)
    imgHSV = img.convert('HSV')

#get grid size
gs = None
for i in range(0, 10):
    sgquestion = input('Small Grid or Large Grid? [S/L]: ')
    if sgquestion.lower() == 's':
        print("Small Grid selected.")
        gs = 'Small'
        break
    elif sgquestion.lower() == 'l':
        print('Large Grid selected.')
        gs = 'Large'
        break
    else:
        print("Selection unrecognized. Try again.\n")
if not gs:
    print("Alright funny guy, let's stick with the default of Small Grid.")

#get anchor point
for i in range(0, 10):
    anchor = int(input("""
Select an anchor point. This will be the origin of the blueprint when pasting/projecting. [1-9]
7 | 8 | 9
---+----+---
4 | 5 | 6
---+----+---
1 | 2 | 3
"""))
    if anchor in range(1, 10):
        break
    else:
        anchor = 7

# set anchor to a tuple where subtracting x by the x of the tuple shifts the blueprint towards 0 by that amount
if anchor == 7:
    anchor = (0, 0)
elif anchor == 8:
    anchor = (-(img.width//2), 0)
elif anchor == 9:
    anchor = (-img.width, 0)
elif anchor == 4:
    anchor = (0, -(img.height//2))
elif anchor == 5:
    anchor = (-(img.width//2), -(img.height//2))
elif anchor == 6:
    anchor = (-img.width, -(img.height//2))
elif anchor == 1:
    anchor = (0, -img.height)
elif anchor == 2:
    anchor = (-(img.width//2), -img.height)
elif anchor == 3:
    anchor = (-img.width, -img.height)

#ask user if they want to use greenscreen transparency
for i in range(0, 10):
    trans = input("Include greenscreen transparency? (pixels that are green within tolerance will not be added to the blueprint) [Y/N]")
    if trans.lower() == 'y':
        trans = True
        tolerance = int(float(input("Input the tolerance (the higher this number is, the less green a pixel has to be to get removed) [0-1]: "))*120)
        break
    elif trans.lower() == 'n':
        trans = False
        break
    else:
        print("Selection unrecognized. Try again.")
if not isinstance(trans, bool):
    print("Still think you're funny, eh? Let's go with no.")
    trans = False

#get pixel data in list
imgData = list(imgHSV.getdata())

#create new directory to put all new files inside, also move original file into directory as BP thumbnail
dirName = f'{filepath}\\IMGBP_{imgName}_{gs}'
os.makedirs(dirName)
shutil.copy(imgPath, f'{dirName}\\thumb.png')

#get the position of the origin pixel in the image, remove it and get its values (converted) for later
#also handle greenscreen transparency for anchor point
anchorIndex = -anchor[0]-img.width*anchor[1]
originPixel = imgData[-anchor[0]-img.width*anchor[1]]
if trans and originPixel[0] in range(120-tolerance, 120+tolerance) and originPixel[1] in range(100-tolerance, 100+tolerance) and originPixel[2] in range(100-tolerance, 100+tolerance):
    originBlock = "435750763254921111"
else:
    originBlock = f'{gs}BlockArmorBlock'

originPixel = ConvertToCMHSV(originPixel)

#create blueprint file and insert generic starting xml stuff on top
#under CubeBlocks create the 'anchor point' and set its color
bp = open(f'{dirName}\\bp.sbc', 'a')
bp.write(f"""<?xml version="1.0"?>
<Definitions xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint xsi:type="MyObjectBuilder_ShipBlueprintDefinition">
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="ImgToBPScript" />
      <DisplayName>ImgToBPScript</DisplayName>
      <CubeGrids>
        <CubeGrid>
          <SubtypeName />
          <EntityId>76945866032709970</EntityId>
          <PersistentFlags>CastShadows InScene</PersistentFlags>
          <PositionAndOrientation>
            <Position x="0" y="0" z="0" />
            <Forward x="0" y="0" z="0" />
            <Up x="0" y="0" z="0" />
            <Orientation>
              <X>1</X>
              <Y>0</Y>
              <Z>0</Z>
              <W>0</W>
            </Orientation>
          </PositionAndOrientation>
          <LocalPositionAndOrientation xsi:nil="true" />
          <GridSizeEnum>{gs}</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>{originBlock}</SubtypeName>
              <ColorMaskHSV x="{originPixel[0]}" y="{originPixel[1]}" z="{originPixel[2]}" />
            </MyObjectBuilder_CubeBlock>""")

yPos = 1
xPos = 1
position = 0

print("Starting...")

#go through all pixels in image and convert to the ColorMaskHSV format
for i in imgData:
    #check if next line has been reached
    if position > img.width*yPos:
        yPos += 1
        xPos = 0
    if (position == anchorIndex):
        position += 1
        xPos -= 1
        continue

    #skip over green pixels if transparency option is selected (SE won't load a blueprint with the blocks missing, so
    #instead it places down nonexistent blocks so that the missing blocks are treated as modded)
    if trans and i[0] in range(120-tolerance, 120+tolerance) and i[1] in range(100-tolerance, 100+tolerance) and i[2] in range(100-tolerance, 100+tolerance):
        bp.write(f"""
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>435750763254921111</SubtypeName>
              <Min x="{xPos}" y="{-(yPos - 1)}" z="0" />
              <ColorMaskHSV x="0" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>""")
        xPos += 1
        position += 1
        print(f'{position}/{len(imgData)} iterations complete.', end='\r')
        continue

    hsv = ConvertToCMHSV((i[0],i[1],i[2]))

    #write block/pixel data to file
    bp.write(f"""
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>{gs}BlockArmorBlock</SubtypeName>
              <Min x="{xPos+anchor[0]}" y="{-(yPos-1)+anchor[1]}" z="0" />
              <ColorMaskHSV x="{hsv[0]}" y="{hsv[1]}" z="{hsv[2]}" />
            </MyObjectBuilder_CubeBlock>""")
    xPos += 1
    position += 1
    print(f'{position}/{len(imgData)} pixels processed.', end='\r')

#write generic finishing xml stuff to file
bp.write(f"""
          </CubeBlocks>
          <DisplayName>IMG_{imgName}_{gs}</DisplayName>
          <DestructibleBlocks>true</DestructibleBlocks>
          <CreatePhysics>false</CreatePhysics>
          <EnableSmallToLargeConnections>false</EnableSmallToLargeConnections>
          <IsRespawnGrid>false</IsRespawnGrid>
          <LocalCoordSys>0</LocalCoordSys>
          <TargetingTargets />
        </CubeGrid>
      </CubeGrids>
      <EnvironmentType>None</EnvironmentType>
      <WorkshopId>0</WorkshopId>
      <OwnerSteamId>76561198131244568</OwnerSteamId>
      <Points>0</Points>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>""")
bp.close()

print("\nComplete.")
deploy = input("Do you want to attempt to automatically deploy the BP to the BP folder? [Y/N]")
try:
    if deploy.lower() == 'y':
        bpPath = os.path.expandvars("%appdata%\\SpaceEngineers\\Blueprints\\local")

        if os.path.exists(bpPath+os.path.split(dirName)[0]):
            deploy = input("Blueprint already exists. Overwrite? [Y/N]")
            if deploy.lower() == 'y':
                shutil.rmtree(bpPath+os.path.split(dirName)[0])

        shutil.move(dirName, os.path.expandvars("%appdata%\\SpaceEngineers\\Blueprints\\local"))
        print("Operation successful. Press Enter to exit.")
    else:
        print("Exiting.")
except shutil.Error as ex:
    print(f'Error while trying to move file: "{ex}". Press Enter to exit.')

input()