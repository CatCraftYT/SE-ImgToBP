from PIL import Image
import os
import shutil

#get path to python script that was just run
filepath = '\\'.join(os.path.realpath(__file__).split('\\')[0:-1])

#get grid size
gs = 'Small'
sgquestion = input('Small Grid or Large Grid? [S/L]: ')
if sgquestion == 'S' or sgquestion == 's':
    print("Small Grid selected.")
elif sgquestion == 'L' or sgquestion == 'l':
    print('Large Grid selected.')
    gs = 'Large'
else:
    print("Selection unrecognized, defaulting to Small Grid.")

#get path to original image
imgPath = input("Put FULL image path here (including file with extension): ")
imgName = imgPath.split('\\')[-1].split('.')[0]
#ask user if they want to use greenscreen transparency
while True:
    trans = input("Include greenscreen transparency? (pixels that are pure green will not be added to the blueprint) [Y/N]")
    if trans.lower() == 'y':
        trans = True
        break
    elif trans.lower() == 'n':
        trans = False
        break

#open and convert file to HSV color space
print('Note: It is highly recommended that you choose files with a total pixel count of under 100,000. Each pixel is a block.')
with open(imgPath, "rb") as file:
    img = Image.open(file)
    imgHSV = img.convert('HSV')

#get pixel data in list
imgData = list(imgHSV.getdata())

#create new directory to put all new files inside, also move original file into directory as BP thumbnail
dirName = f'{filepath}\\IMGBP_{imgName}_{gs}'
os.makedirs(dirName)
shutil.copy(imgPath, f'{dirName}\\thumb.png')

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
            <Forward x="0.82483995" y="-0.130035788" z="-0.5502087" />
            <Up x="-0.137953937" y="0.8974814" z="-0.418922216" />
            <Orientation>
              <X>-0.158577144</X>
              <Y>-0.446932763</Y>
              <Z>0.161593869</Z>
              <W>0.8654431</W>
            </Orientation>
          </PositionAndOrientation>
          <LocalPositionAndOrientation xsi:nil="true" />
          <GridSizeEnum>{gs}</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>SmallBlockArmorBlock</SubtypeName>
              <ColorMaskHSV x="{imgData[0][0]/360}" y="{(imgData[0][1] / 100) - 0.8}" z="{(imgData[0][2] / 100) - 0.45}" />
            </MyObjectBuilder_CubeBlock>
""")

yPos = 1
xPos = 1
position = 0

print("Starting...")

#go through all pixels in image and convert to the ColorMaskHSV format
for i in imgData[1:]:
    #values here adjust hsv values to color correct them, as the conversion messes up the image's colors
    #values obtained by dividing a correct HSV value by a 'conversion tainted' HSV value
    #the multiple stays the same even with different images
    #other values are obtained from https://www.reddit.com/r/spaceengineers/comments/53nkhz/blueprint_color_change/ and ingame observations
    h = ((i[0]*1.44680851064) / 360)
    s = ((i[1]*0.40816326531) / 100) - 0.8
    v = ((i[2]*0.39024390244) / 100) - 0.45
    #check if next line has been reached
    if position > img.width*yPos:
        yPos += 1
        xPos = 0
    #skip over green pixels if transparency option is selected (SE won't load a blueprint with the blocks missing, so
    #instead it places down nonexistent blocks so that the missing blocks are treated as modded)
    if trans and h == 0.3416075650122222 and s == 0.24081632654050011 and v == 0.545121951222:
        bp.write(f"""
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>ThisIsANonexistentBlockHopefully</SubtypeName>
              <Min x="{xPos}" y="{-(yPos - 1)}" z="0" />
              <ColorMaskHSV x="0" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>""")
        xPos += 1
        position += 1
        print(f'{position}/{len(imgData)} iterations complete.', end='\r')
        continue
    #write block/pixel data to file
    bp.write(f"""
            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>{gs}BlockArmorBlock</SubtypeName>
              <Min x="{xPos}" y="{-(yPos-1)}" z="0" />
              <ColorMaskHSV x="{h}" y="{s}" z="{v}" />
            </MyObjectBuilder_CubeBlock>""")
    xPos += 1
    position += 1
    print(f'{position}/{len(imgData)} iterations complete.', end='\r')

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

print("\nComplete.")
input()
