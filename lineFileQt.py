#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-

# python script to optimize switching of cartridges and rasterize output
# do not use with pipette

import os
import sys
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore

def help_message():
    ''' Prints out simple usage instructions. '''
    print ('Usage: python ' + sys.argv[0] + '[MULTIPLICATOR X] [X INCREMENT] ' +
           '[MULTIPLICATOR Y] [Y INCREMENT] [ORDER] [INPUT] [OUTPUT]')
    print 'Launching without arguments will give an experimental GUI.'
    print 'Multiplicators may be positive definite natural numbers.'
    print 'Increments are lengths in millimeter with 10 micron resolution.'
    print 'Order may be either "xy" or "yx".'
    print 'Use "[INPUT] 1 0 1 0 xy [OUTPUT]" if only sorting is required.'
    print ('Note, that files containing multiple scaffolds will be sorted ' +
          'layer by layer not scaffold by scaffold.')
    sys.exit()

# import argparse # module for convenient command-line option handling
# not figured out how to use it yet


def read_input(inputfile):
    ''' Takes a linefile for the GeSim BioScaffolder 2.1 as input
        and returns a nested list of the line indexes of starting
        layers and the cartridges used within in the previous layer,
        a nested list of the input lines split at whitespace and the
        total number of cartridge switches.'''
    #inputdata = inputfile
    #linefile,switches,layers,layers_temp = [],[],[],[]
    linefile,layers,layers_temp = [],[],[]
    cartridge = '-1' # ursprgl. '1'
    level = '0.00'
    i, switchcount = 0,0

    with open(inputfile) as data:
        for line in data:
            splitline = line.split(None,-1) # list of whitespace-separated entries
            if splitline[0] != cartridge: # cartridge changed at current line
                switchcount += 1
                #switches.append([i,cartridge,splitline[0]]) # switches: list of lists with indexes at occurring cartridge changes, old & new cartridge
                cartridge = splitline[0]
            if splitline[5] != level:
                layers_temp.append(i) # layers_temp: list of indexes of new layers
                level = splitline[5]
            linefile.append(splitline)
            i += 1

    if layers_temp:
        if layers_temp[0] == 0: # first layer not at z = 0, thus no new layer there
            layers_temp.pop(0)
    layers_temp.append(len(linefile)) # number of layers is one more than number of new layers

    i = 0
    cartridges = set()
    for layer_index in layers_temp:
        while i < layer_index:
            cartridges.add(linefile[i][0])
            i = i + 1
        layers.append([layer_index,cartridges]) # layers: list of lists with indexes of new layers and occuring cartridges of previous layer

    return layers,linefile,switchcount-1


def write_output(linedata,out_file):
    ''' Takes a nested list representing a linefile as first argument
        and writes the list's contents as tab delimited lines to the
        second argument. '''
    for line in linedata:
        formatline = ''
        for string in line:
#           formatline = formatline + string.strip("'") + '\t'
            formatline = formatline + string + '\t'
        with open(out_file,"a") as newlines:
            newlines.write(formatline.rstrip()+'\r\n')


def sort_layers(layers,linedata):
    ''' Takes two nested lists, the line indexes of layer changes with
        the cartridges of the previous layer and the splitted linefile
        as input and returns a nested list of a splitted linefile being
        reordered to minimize cartridge switches during plotting.'''
    newfile = []
    previous_cartridge = '-1' # no cartridge used before first layer
    prev_set = set()
    for i in range(len(layers)):
        order = []
        prev_set.add(previous_cartridge)
        remaining_cartridges = layers[i][1]-prev_set
        try:
            common_cartridges = remaining_cartridges & layers[i+1][1]
        except IndexError:
            # last layer
            common_cartridges = set()
        if previous_cartridge != '-1': # possible without this check, but avoids checks of order layers[0][0]
            order.append(previous_cartridge)
        for cart in remaining_cartridges-common_cartridges:
            order.append(cart)
        for cart in common_cartridges:
            order.append(cart)
        previous_cartridge = order[-1]
        if i > 0:
            layer_index = layers[i-1][0]
        else:
            layer_index = 0
        for cart in order:
            k = layer_index
            while k < layers[i][0]:
                # sort lines
                if linedata[k][0] == cart:
                    newfile.append(linedata[k])
                k = k + 1
        prev_set.clear()
    return newfile


def count_switches(linedata):
    ''' Takes a nested list representing a splitted linefile as input
        and returns the number of cartridge switches.'''
    i = 0
    #switches = []
    switchcount = 0
    cartridge = '-1'
    for line in linedata:
        if line[0] != cartridge:
            # switches.append(i)
            switchcount += 1
            cartridge = line[0]
        i += 1

    return switchcount-1


def rasterize(linedata,x_then_y,x_increment,y_increment,multi_x,multi_y):
    ''' Takes a nested list representing a splitted linefile as first
        argument, followed by a boolean value for the ordering. The
        scaffold is copied using a 'multi_x' times 'multi_y' raster with
        distances specified by 'x_increment' and 'y_increment.
        A nested list of the splitted linefile is returned.'''
    endfile = []
    l_max = len(linedata)
    if x_then_y: # x before y
        for i in range(multi_y):
            for k in range(multi_x):
                for l in range(l_max):
                    line = []
                    for m in range(len(linedata[l])):
                        if m==1 or m==3:
                            line.append(repr(round(float(linedata[l][m]) +
                                                   k*x_increment,2)))
                        elif m==2 or m==4:
                            line.append(repr(round(float(linedata[l][m]) +
                                                   i*y_increment,2)))
                        else:
                            line.append(linedata[l][m])
                    endfile.append(line)
    else:
        for k in range(multi_x):
            for i in range(multi_y):
                for l in range(l_max):
                    line = []
                    for m in range(len(linedata[l])):
                        if m==1 or m==3:
                            line.append(repr(round(float(linedata[l][m]) +
                                                   k*x_increment,2)))
                        elif m==2 or m==4:
                            line.append(repr(round(float(linedata[l][m]) +
                                                   i*y_increment,2)))
                        else:
                            line.append(linedata[l][m])
                    endfile.append(line)
    return endfile



def shifting(linedata,x_offset,y_offset,pipette):
    ''' Takes a nested list representing a splitted linefile as input.
        Depending on 'pipette' only lines where the pipette is used are
        shifted by 'x_offset' and 'y_offset'. Otherwise the whole scaffold
        is shifted. '''
    newfile = []
    for line in linedata:
        newline = []
        if line[0] == '0': # pipette is used
            if line[1] == '2': # spot point
                for m in range(len(line)):
                    if m == 3:
                        newline.append(repr(round(float(line[m]) + x_offset,2)))
                    elif m == 4:
                        newline.append(repr(round(float(line[m]) + y_offset,2)))
                    else:
                        newline.append(line[m])
            elif line[1] == '3': # spot line
                for m in range(len(line)):
                    if m==3 or m==5:
                        newline.append(repr(round(float(line[m]) + x_offset,2)))
                    elif m==4 or m==6:
                        newline.append(repr(round(float(line[m]) + y_offset,2)))
                    else:
                        newline.append(line[m])
            else:
                newline = line # aspiration, thus nothing to do
        elif line[0] in ['1', '2', '3'] and not pipette:
            for m in range(len(line)):
                if m==1 or m==3:
                    newline.append(repr(round(float(line[m]) + x_offset,2)))
                elif m==2 or m==4:
                    newline.append(repr(round(float(line[m]) + y_offset,2)))
                else:
                    newline.append(line[m])
        else:
            newline = line # plotting line but only pipette should be shifted
        newfile.append(newline)
    return newfile



class Gui(QtGui.QMainWindow):
  def __init__(self):
    QtGui.QMainWindow.__init__(self)

    self.setWindowTitle('Sorting and rasterization of linefiles')
# gray-out items with .setEnabled(bool)
# LABEL with lineEdit for
# raster: x mult, x inc, y mult, y inc => gray out if not used
# shift: dx, dy => gray out if not used
    self.rasterLabel = QtGui.QLabel('Rasterization')
    self.xMultLabel = QtGui.QLabel('x Multiplicator')
    self.xMultEdit = QtGui.QLineEdit('1')
    self.yMultLabel = QtGui.QLabel('y Multiplicator')
    self.yMultEdit = QtGui.QLineEdit('1')
    self.xIncLabel = QtGui.QLabel('x Increment(mm)')
    self.xIncEdit = QtGui.QLineEdit('0')
    self.yIncLabel = QtGui.QLabel('y Increment(mm)')
    self.yIncEdit = QtGui.QLineEdit('0')

    self.shiftLabel = QtGui.QLabel('Shifting')
    self.xShiftLabel = QtGui.QLabel('x Shift(mm)')
    self.xShiftEdit = QtGui.QLineEdit('0')
    self.yShiftLabel = QtGui.QLabel('y Shift(mm)')
    self.yShiftEdit = QtGui.QLineEdit('0')



# CHECKBOX for
# sort cartridges
# rasterize : order - radiobutton?
# shift : pipette only - radiobutton? => gray out sorting and raster if pipette shifted
    self.sortBox = QtGui.QCheckBox('Sort Cartridges')
    self.rasterBox = QtGui.QCheckBox('Add Scaffolds')
    self.shiftBox = QtGui.QCheckBox('Shift Scaffold/Pipette')

    self.pipetteRadio = QtGui.QButtonGroup()
    self.isPipetteRadio = QtGui.QRadioButton('Shift only Pipette Positions')
    self.noPipetteRadio = QtGui.QRadioButton('Shift whole Scaffold')
    self.noPipetteRadio.setChecked(True)
    self.pipetteRadio.addButton(self.isPipetteRadio)
    self.pipetteRadio.addButton(self.noPipetteRadio)


#    self.shiftBox.isChecked()

# file selection for [line edit + button]
# input
# output

# button for
# start
# exit




#main


# shifting not used yet

if len(sys.argv[1]) > 1:
    #arguments passed => batch mode
    if len(sys.argv) != 8 or sys.argv[1] in ['h', '-h', '-help', '--help']:
        help_message()
    else:
        infile = sys.argv[7]
        outfile = sys.argv[8]

        try:
            x_multi = int(sys.argv[2])
        except ValueError:
            help_message()

        try:
            increment_x = float(sys.argv[3])
        except ValueError:
            help_message()

        try:
            y_multi = int(sys.argv[4])
        except ValueError:
            help_message()

        try:
            increment_y = float(sys.argv[5])
        except ValueError:
            help_message()

        x_before_y = sys.argv[6]

        if x_before_y == 'xy':
            x_before_y = True
        elif x_before_y == 'yx':
            x_before_y = False
        else:
            help_message

    #   print multi_x, x_increment, multi_y, y_increment
        if ((x_multi, increment_x, y_multi, increment_y) == (1, 0.0, 1, 0.0)):
            rasterization = False
        else:
            rasterization = True

    layerinfo, linefile, old_switch = read_input(infile)

    #print old_switch
    #print rasterization

    if old_switch:
        sorted_data = sort_layers(layerinfo,linefile)
        new_switch = count_switches(sorted_data)
        print 'Cartridge switches per scaffold before optimization: ' + repr(old_switch)
        print 'Cartridge switches per scaffold after optimization: ' + repr(new_switch)
        print 'For scaffold with ' + repr(len(layerinfo)) + ' layers.'

        if old_switch - new_switch:
            #sorting happened, check for rasterization
            if rasterization:
                write_output(rasterize(sorted_data,x_before_y,increment_x,increment_y,x_multi,y_multi),outfile)
            else:
                print 'No additional scaffolds added.'
                write_output(sorted_data,outfile)
        else:
            pass # no optimization, thus do not use sorted data

    else: # no sorting, check rasteization
        if rasterization:
            print 'No furher optimization of cartridge switches possible.'
            write_output(rasterize(linefile,x_before_y,increment_x,increment_y,x_multi,y_multi),outfile)
        else:
            print 'Neither additional scaffolds wanted'
            print 'nor furher optimization of cartridge switches possible.'
            print 'No output written to ' + outfile
else: # no commandline arguments => GUI mode
    app = QtGui.QApplication(sys.argv)
    gui = Gui()
    gui.show()

    app.exec_() #in console nicht nötig



# lower_case_with_spaces for function and variable names







#linefile:
#list of lists (each sublist is a splitted line)

#layers:
#list of indizes


#analyze layers:
#6th entry equal = same layer
#index layer-switches

#detect switch of cartridges, get cartridge numbers
#1st entry equal = same cartridge
#index cartridge switches

#sort within layer
#for every layer write cartridge-one-strands into file, cartridge-two-strands into file, cartridge-three-strands into file

#reverse layer order if catridge switched at begin of layer


#linefile structure:
#cartridge, xstart, ystart, xend, yend, z, speed, prepressure, afterpressure, tear-off mode, tear-off length, tear-off speed, cutoff time
