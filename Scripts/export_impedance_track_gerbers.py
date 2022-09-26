#
# Python script to export all netclass tracks to different
# gerber files
#

"""
    @package
    Output: Gerber
    
    A gerber file exports

    Python command: "/usr/bin/python3" "scipt.py" "output_dir/" "pcb_file.kicad_pcb"

"""

from __future__ import print_function

# Import the KiCad python helper module and the csv formatter
import sys
import pcbnew
from pcbnew import *
import os
import shutil
import subprocess

output_dir, dependency, = sys.argv[1:]
print("Saving files into '{}'".format(output_dir))

board = LoadBoard(dependency)
netclass_names = []

#Start layer at end of current copper count
USER_LAYER_START =  board.GetCopperLayerCount()

net_info_list = board.GetNetInfo()

group = pcbnew.PCB_GROUP(board)
board.Add(group)

# Iterate through each element in the net info list
for i in range(0, net_info_list.GetNetCount()):
    net_item = net_info_list.GetNetItem(i)
    netclass_name = net_item.GetNetClassName()
    tracks = board.TracksInNet(i)


    # Store netclasss if it does not already exist
    if (netclass_name != "Default") and not(netclass_name in netclass_names):
        netclass_names.append(netclass_name)
    
    # Transfer tracks if they exist in a known netclass
    if (netclass_name in netclass_names):
        for track in board.TracksInNet(i):
            # Ignore any vias in the list
            if track.GetClass() != "PCB_VIA":
                # Select new layer to start at user, and increment by 2 (for front and back)
                # for each netclass
                new_layer = USER_LAYER_START + (2 * netclass_names.index(netclass_name))
                # Create a copy of the track
                new_track = track.Duplicate()
                # Set layer according to whether it was on the front or back              
                if (track.GetLayerName() == "F.Cu"):
                    new_track.SetLayer(new_layer + 0)
                elif (track.GetLayerName() == "B.Cu"):
                    new_track.SetLayer(new_layer + 1)
                # Add new track to board
                board.Add(new_track)
                group.AddItem(new_track)

# Remove all vias from gerbers
for item in board.GetTracks():
    if item.GetClass() == "PCB_VIA":
        item.DeleteStructure()

# Remove all pads from gerbers
for item in board.GetPads():
    item.DeleteStructure()

# Configure plotter
pctl = PLOT_CONTROLLER(board)
popt = pctl.GetPlotOptions()

# Render Plot Files
popt.SetOutputDirectory(output_dir)

plot_plan = []

# Add front and back gerbers for all netclasses
for item in netclass_names:
    i = netclass_names.index(item)
    plot_plan.append((item + "_F ", USER_LAYER_START + 2 * i + 0, item + "_F "))
    plot_plan.append((item + "_B ", USER_LAYER_START + 2 * i + 1, item + "_B "))

# Plot gerber files
for layer_info in plot_plan:
    pctl.SetLayer(layer_info[1])
    pctl.OpenPlotfile(layer_info[0], PLOT_FORMAT_GERBER, layer_info[2])
    pctl.PlotLayer()

pctl.ClosePlot()