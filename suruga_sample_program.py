# Import for sleep
import time
# Importing python.NET Library
# Install pythonnet by pip before executing this code
import pythonnet
# Loading .NET core instead of .NET Framework
pythonnet.load("coreclr")
# Importing clr and specify DLL file name
# DLL must be in the same folder as this code
import clr
clr.AddReference("srgmc")
# Importing the DLL name space
import SurugaSeiki.Motion

def main():
    # Getting a System class instance
    alignmentSystem = SurugaSeiki.Motion.System.Instance

    # Creating AxisComponents class instances
    AxisComponents = {}
    for axisNumber in range(1,13):
        AxisComponents[axisNumber] = SurugaSeiki.Motion.AxisComponents(axisNumber)
    XTargetPosition: float
    YTargetPosition: float

    # Creating an Axis2D class instance for axis 7 and 8.
    Axis2D = SurugaSeiki.Motion.Axis2D(7,8)

    # Creating an Alignment class instance
    Alignment = SurugaSeiki.Motion.Alignment()
    FlatAlignmentParameter = SurugaSeiki.Motion.Alignment.FlatParameter()
    FocusAlignmentParameter = SurugaSeiki.Motion.Alignment.FocusParameter()

    # Showing DLL version and starting ADS communication to a target controller
    # Change the following ADS address according to an actual target controller.
    print(alignmentSystem.DllVersion)
    alignmentSystem.SetAddress("5.107.162.80.1.1")

    firstTimeConnected = False
    isAlignment = False

    # Main program loop
    while True:
        if alignmentSystem.Connected == True:
            if firstTimeConnected == False:
                firstTimeConnected = True
                # Showing the system version of the target controller once after connection success
                print(alignmentSystem.SystemVersion)
                XTargetPosition = AxisComponents[7].GetActualPosition()
                YTargetPosition = AxisComponents[8].GetActualPosition()

            # Showing axis state
            for axisComponent in AxisComponents.items():
                # Turning on servo controls if servo controls are off for each axes
                if axisComponent[1].IsServoOn() == False:
                    axisComponent[1].TurnOnServo()
                print(f'Axis {axisComponent[0]:d} position: {axisComponent[1].GetActualPosition():.05f}')
            print()

            # Showing alignment state
            print(f'Alignment state: {str(Alignment.GetStatus()):s}')
            print(f'Error axis ID: {Alignment.GetErrorAxisID():d}')
            if FlatAlignmentParameter.mainStageNumberX >= 1:
                print(f'Alignment axis 1 position: {AxisComponents[FlatAlignmentParameter.mainStageNumberX].GetActualPosition():.05f}')
            if FlatAlignmentParameter.mainStageNumberY >= 1:
                print(f'Alignment axis 2 position: {AxisComponents[FlatAlignmentParameter.mainStageNumberY].GetActualPosition():.05f}')
            print()

            # Waiting for command input
            inputVar = input("Please input command:")
            if inputVar == "moveabsolute":
                print(f'{inputVar:s}')
                erroraxis7 = AxisComponents[7].MoveAbsolute(XTargetPosition)
                erroraxis8 = AxisComponents[8].MoveAbsolute(YTargetPosition)
                time.sleep(0.1)
                if str(erroraxis7) == "None" and str(erroraxis8) == "None":
                    while str(AxisComponents[7].GetStatus()) != "InPosition" or str(AxisComponents[8].GetStatus()) != "InPosition":
                        print(f'Axis {7:d} position: {AxisComponents[7].GetActualPosition():.05f}')
                        print(f'Axis {8:d} position: {AxisComponents[8].GetActualPosition():.05f}\n')

            elif inputVar == "faset":
                print(f'{inputVar:s}')
                # Setting flat alignment parameters
                SetFlatAlignmentParameter(FlatAlignmentParameter)
                Alignment.SetFlat(FlatAlignmentParameter)
                # Set wavelength if necessary
                Alignment.SetMeasurementWaveLength(FlatAlignmentParameter.pmCh, 1310)
            elif inputVar == "fastart":
                print(f'{inputVar:s}')
                # Starting flat alignment
                Alignment.StartFlat()
                time.sleep(0.1)
            elif inputVar == "foset":
                print(f'{inputVar:s}')
                # Setting focus alignment parameters
                SetFocusAlignmentParameter(FocusAlignmentParameter)
                Alignment.SetFocus(FocusAlignmentParameter)
                # Set wavelength if necessary
                Alignment.SetMeasurementWaveLength(FocusAlignmentParameter.pmCh, 1310)
            elif inputVar == "fostart":
                print(f'{inputVar:s}')
                # Starting focus alignment
                Alignment.StartFocus()
                time.sleep(0.1)
            elif inputVar == "astop":
                print(f'{inputVar:s}')
                # Stopping alignment execution
                Alignment.Stop()
            elif inputVar == "2drelative":
                print(f'{inputVar:s}')
                # Executing 2 axis relative movement
                point2D = SurugaSeiki.Motion.Axis2D.Point()
                point2D.X = 100
                point2D.Y = 100
                if str(Axis2D.MoveRelative(point2D)) == "None":
                    time.sleep(0.1)
                    while str(Axis2D.GetStatus()) != "InPosition":
                        ActualPosition2D = Axis2D.GetActualPosition()
                        axisId2D = Axis2D.GetAxisNumber()
                        print(f'Axis {axisId2D[0]:d} position: {ActualPosition2D.X:.05f}')
                        print(f'Axis {axisId2D[1]:d} position: {ActualPosition2D.Y:.05f}\n')

            alignmentStatus = Alignment.GetStatus()
            while str(alignmentStatus) == "Aligning":
                isAlignment = True
                aligningStatus = Alignment.GetAligningStatus()
                print(f'{str(aligningStatus):s}')
                # packetSumIndex: int = 0
                # if str(aligningStatus) == "FieldSearching":
                #     packetSumIndex = Alignment.GetProfilePacketSumIndex(SurugaSeiki.Motion.Alignment.ProfileDataType.FieldSearch)
                #     print(f'Profile packet number of field searching: {packetSumIndex:d}')
                # elif str(aligningStatus) == "PeakSearchingX":
                #     packetSumIndex = Alignment.GetProfilePacketSumIndex(SurugaSeiki.Motion.Alignment.ProfileDataType.PeakSearchX)
                #     print(f'Profile packet number of peak searching X: {packetSumIndex:d}')      
                # elif str(aligningStatus) == "PeakSearchingY":
                #     packetSumIndex = Alignment.GetProfilePacketSumIndex(SurugaSeiki.Motion.Alignment.ProfileDataType.PeakSearchY)
                #     print(f'Profile packet number of peak searching Y: {packetSumIndex:d}')
                alignmentStatus = Alignment.GetStatus()
                time.sleep(0.5)

            if str(alignmentStatus) == "Success":
                if isAlignment == True:
                    packetSumIndex: int = 0
                    profileDataType: SurugaSeiki.Motion.Alignment.ProfileDataType
                    if FlatAlignmentParameter.pmCh >= 1:
                        print(f'Optical power after alignment execution: {Alignment.GetPower(FlatAlignmentParameter.pmCh):.05f} dBm')
                    profileDataType = SurugaSeiki.Motion.Alignment.ProfileDataType.FieldSearch
                    packetSumIndex = Alignment.GetProfilePacketSumIndex(profileDataType)
                    print(f'Packet number of field searching after successful alignment execution: {packetSumIndex:d}')
                    profaleDataPosition = []
                    profaleDataSignal = []
                    for packetNumber in range(1, packetSumIndex + 1):
                        profileData = Alignment.RequestProfileData(profileDataType, packetNumber, False)
                        print(profileData.packetIndex)
                        print(profileData.dataCount)
                        profaleDataPosition.extend(profileData.mainPositionList)
                        profaleDataSignal.extend(profileData.signalCh1List)
                    print(*profaleDataPosition, sep=',')
                    f = open('fieldsearchposition.txt', 'w')
                    f.write('\n'.join(map(str, profaleDataPosition)))
                    f.close()
                
                    print(*profaleDataSignal, sep=',')
                    f = open('fieldsearchsignal.txt', 'w')
                    f.write('\n'.join(map(str, profaleDataSignal)))
                    f.close()

                    profaleDataPosition.clear()
                    profaleDataSignal.clear()
                    profileDataType = SurugaSeiki.Motion.Alignment.ProfileDataType.PeakSearchX
                    packetSumIndex = Alignment.GetProfilePacketSumIndex(profileDataType)
                    print(f'Profile packet number of peak searhing X after successful alignment execution: {packetSumIndex:d}')
                    for packetNumber in range(1, packetSumIndex + 1):
                        profileData = Alignment.RequestProfileData(profileDataType, packetNumber, False)
                        print(profileData.packetIndex)
                        print(profileData.dataCount)
                        profaleDataPosition.extend(profileData.mainPositionList)
                        profaleDataSignal.extend(profileData.signalCh1List)
                    print(*profaleDataPosition, sep=',')
                    f = open('peaksearchXsearchposition.txt', 'w')
                    f.write('\n'.join(map(str, profaleDataPosition)))
                    f.close()
                    
                    print(*profaleDataSignal, sep=',')
                    f = open('peaksearchXsearchsignal.txt', 'w')
                    f.write('\n'.join(map(str, profaleDataSignal)))
                    f.close()

                    profaleDataPosition.clear()
                    profaleDataSignal.clear()
                    profileDataType = SurugaSeiki.Motion.Alignment.ProfileDataType.PeakSearchY
                    packetSumIndex = Alignment.GetProfilePacketSumIndex(profileDataType)
                    print(f'Profile packet number of peak searhing Y after successful alignment execution: {packetSumIndex:d}')
                    for packetNumber in range(1, packetSumIndex + 1):
                        profileData = Alignment.RequestProfileData(profileDataType, packetNumber, False)
                        print(profileData.packetIndex)
                        print(profileData.dataCount)
                        profaleDataPosition.extend(profileData.mainPositionList)
                        profaleDataSignal.extend(profileData.signalCh1List)
                    print(*profaleDataPosition, sep=',')
                    f = open('peaksearchYsearchposition.txt', 'w')
                    f.write('\n'.join(map(str, profaleDataPosition)))
                    f.close()

                    print(*profaleDataSignal, sep=',')
                    f = open('peaksearchYsearchsignal.txt', 'w')
                    f.write('\n'.join(map(str, profaleDataSignal)))
                    f.close()

                    XTargetPosition = AxisComponents[7].GetActualPosition()
                    YTargetPosition = AxisComponents[8].GetActualPosition()
                isAlignment = False
                    
        else:
            print("Ads not connected")
            time.sleep(1)

# Set flat alignment parameters
def SetFlatAlignmentParameter(FlatAlignmentParameter):
    FlatAlignmentParameter.mainStageNumberX = 7
    FlatAlignmentParameter.mainStageNumberY = 8
    FlatAlignmentParameter.subStageNumberXY = 0
    FlatAlignmentParameter.subAngleX = 0
    FlatAlignmentParameter.subAngleY = -8
    FlatAlignmentParameter.pmCh = 1
    FlatAlignmentParameter.analogCh = 1
    FlatAlignmentParameter.pmAutoRangeUpOn = True
    FlatAlignmentParameter.pmInitRangeSettingOn = True
    FlatAlignmentParameter.pmInitRange = -10
    FlatAlignmentParameter.fieldSearchThreshold = 0.1
    FlatAlignmentParameter.peakSearchThreshold = 40
    FlatAlignmentParameter.searchRangeX = 500
    FlatAlignmentParameter.searchRangeY = 500
    FlatAlignmentParameter.fieldSearchPitchX = 5
    FlatAlignmentParameter.fieldSearchPitchY = 5
    FlatAlignmentParameter.fieldSearchFirstPitchX = 0
    FlatAlignmentParameter.fieldSearchSpeedX = 1000
    FlatAlignmentParameter.fieldSearchSpeedY = 1000
    FlatAlignmentParameter.peakSearchSpeedX = 5
    FlatAlignmentParameter.peakSearchSpeedY = 5
    FlatAlignmentParameter.smoothingRangeX = 50
    FlatAlignmentParameter.smoothingRangeY = 50
    FlatAlignmentParameter.centroidThresholdX = 0
    FlatAlignmentParameter.centroidThresholdY = 0
    FlatAlignmentParameter.convergentRangeX = 1
    FlatAlignmentParameter.convergentRangeY = 1
    FlatAlignmentParameter.comparisonCount = 2
    FlatAlignmentParameter.maxRepeatCount = 10

# Set focus alignment parameters
def SetFocusAlignmentParameter(FocusAlignmentParameter):
    FocusAlignmentParameter.zMode = SurugaSeiki.Motion.Alignment.ZMode.Round
    FocusAlignmentParameter.mainStageNumberX = 7
    FocusAlignmentParameter.mainStageNumberY = 8
    FocusAlignmentParameter.subStageNumberXY = 0
    FocusAlignmentParameter.subAngleX = 0
    FocusAlignmentParameter.subAngleY = -8
    FocusAlignmentParameter.pmCh = 1
    FocusAlignmentParameter.analogCh = 1
    FocusAlignmentParameter.pmAutoRangeUpOn = True
    FocusAlignmentParameter.pmInitRangeSettingOn = True
    FocusAlignmentParameter.pmInitRange = -10
    FocusAlignmentParameter.fieldSearchThreshold = 0.1
    FocusAlignmentParameter.peakSearchThreshold = 40
    FocusAlignmentParameter.searchRangeX = 500
    FocusAlignmentParameter.searchRangeY = 500
    FocusAlignmentParameter.fieldSearchPitchX = 5
    FocusAlignmentParameter.fieldSearchPitchY = 5
    FocusAlignmentParameter.fieldSearchFirstPitchX = 0
    FocusAlignmentParameter.fieldSearchSpeedX = 1000
    FocusAlignmentParameter.fieldSearchSpeedY = 1000
    FocusAlignmentParameter.peakSearchSpeedX = 5
    FocusAlignmentParameter.peakSearchSpeedY = 5
    FocusAlignmentParameter.smoothingRangeX = 50
    FocusAlignmentParameter.smoothingRangeY = 50
    FocusAlignmentParameter.centroidThresholdX = 0
    FocusAlignmentParameter.centroidThresholdY = 0
    FocusAlignmentParameter.convergentRangeX = 1
    FocusAlignmentParameter.convergentRangeY = 1
    FocusAlignmentParameter.comparisonCount = 2
    FocusAlignmentParameter.maxRepeatCount = 10

if __name__ == "__main__":
    main()