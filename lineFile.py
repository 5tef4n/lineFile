# python script to optimize switching of cartridges and rasterize output or shift the scaffold
#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-

# do not use with pipette

import os
import sys


def help_message():
	print 'Usage: python ' + sys.argv[0] + ' [INPUT] [MULTIPLICATOR X] [X INCREMENT] [MULTIPLICATOR Y] [Y INCREMENT] [ORDER] [OUTPUT]'
	print 'Multiplicators may be positive definite natural numbers.'
	print 'Increments are lengths in millimeter with 10 micron resolution.'
	print 'Order may be either "xy" or "yx".'
	print 'Use "[INPUT] 1 0 1 0 xy [OUTPUT]" if only sorting is required.'
	print 'Note, that files containing multiple scaffolds will be sorted layer by layer not scaffold by scaffold.'
	print 'Use "[INPUT] [SHIFT X] [SHIFT Y] [PIPETTE] [OUTPUT]" to shift scaffold instead of sorting it.'
	print 'If pipette is "YES", "y" or "1" only the pipetting lines will be shifted.'
	sys.exit()
	
#need to incorporate shift-scaffold

# import argparse # module for convenient command-line option handling
# not figured out how to use it yet

shift_scaffold = False

if sys.argv[1] in ['h', '-h', '-help', '--help']:
	help_message()
elif len(sys.argv) == 8:
	infile = sys.argv[1]
	outfile = sys.argv[7]

	try:
		multi_x = int(sys.argv[2])
	except ValueError:
		help_message()

	try:
		x_increment = float(sys.argv[3])
	except ValueError:
		help_message()

	try:
		multi_y = int(sys.argv[4])
	except ValueError:
		help_message()

	try:
		y_increment = float(sys.argv[5])
	except ValueError:
		help_message()

	x_before_y = sys.argv[6]

	if x_before_y == 'xy':
		x_before_y = True
	elif x_before_y == 'yx':
		x_before_y = False
	else:
		help_message

#	print multi_x, x_increment, multi_y, y_increment
	if (multi_x, x_increment, multi_y, y_increment) == (1, 0.0, 1, 0.0):
		rasterization = False
	else:
		rasterization = True
elif len(sys.argv) == 6:
	shift_scaffold = True
	infile = sys.argv[1]
	outfile = sys.argv[5]
	
	try:
		x_shift = float(sys.argv[2])
	except ValueError:
		help_message()

	try:
		y_shift = float(sys.argv[3])
	except ValueError:
		help_message()
	
	if sys.argv[4] == 'YES' or sys.argv[4] == 'yes' or sys.argv[4] == 'Y' or sys.argv[4] == 'y' or sys.argv[4] = '1':
		pipette_set = True
	else:
		pipette_set = False
	
else:
	help_message()

def read_input(inputfile):
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


def write_output(linedata):
	for line in linedata:
		formatline = ''
		for string in line:
#			formatline = formatline + string.strip("'") + '\t'
			formatline = formatline + string + '\t'
		with open(outfile,"a") as newlines:
			newlines.write(formatline.rstrip()+'\r\n')


def sort_layers(layers,linedata):
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


def rasterize(linedata):
	endfile = []
	l_max = len(linedata)
	if x_before_y:
		for i in range(multi_y):
			for k in range(multi_x):
				for l in range(l_max):
					line = []
					for m in range(len(linedata[l])):
						if m == 1 or m ==3:
							line.append(repr(round(float(linedata[l][m]) + k*x_increment,2)))
						elif m == 2 or m == 4:
							line.append(repr(round(float(linedata[l][m]) + i*y_increment,2)))
						else:
							line.append(linedata[l][m])
					endfile.append(line)
	else:
		for k in range(multi_x):
			for i in range(multi_y):
				for l in range(l_max):
					line = []
					for m in range(len(linedata[l])):
						if m == 1 or m ==3:
							line.append(repr(round(float(linedata[l][m]) + k*x_increment,2)))
						elif m == 2 or m == 4:
							line.append(repr(round(float(linedata[l][m]) + i*y_increment,2)))
						else:
							line.append(linedata[l][m])
					endfile.append(line)
	write_output(endfile)


def shifting(linedata,x_offset,y_offset,pipette):
    ''' Takes a nested list representing a splitted linefile as input.
        If 'pipette' is true only lines where the pipette is used are
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



#main

layerinfo, linefile, old_switch = read_input(infile)

#print old_switch
#print rasterization
#print shift_scaffold

if old_switch:
	sorted_data = sort_layers(layerinfo,linefile)
	new_switch = count_switches(sorted_data)
	print 'Cartridge switches per scaffold before optimization: ' + repr(old_switch)
	print 'Cartridge switches per scaffold after optimization: ' + repr(new_switch)
	print 'For scaffold with ' + repr(len(layerinfo)) + ' layers.'

	if old_switch - new_switch:
		#sorting happened, check for rasterization
		if rasterization:
			rasterize(sorted_data) # invokes write_output(linedata)
		else:
			print 'No additional scaffolds added.'
			write_output(sorted_data)
	else:
		pass # no optimization, thus do not use sorted data

else: # no sorting, check rasterization
	if rasterization:
		print 'No furher optimization of cartridge switches possible.'
		rasterize(linefile) # invokes write_output(linedata)
	else:
		print 'Neither additional scaffolds wanted'
		print 'nor furher optimization of cartridge switches possible.'
		print 'No output written to ' + outfile

if shift_scaffold:
	shifted_data = shifting(linefile,x_shift,y_shift,pipette_set)
	if pipette_set:
		print 'Only pipetting positions shifted.'
	else:
		print 'Only scaffold shifted.'
	write_output(shifted_data)



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
