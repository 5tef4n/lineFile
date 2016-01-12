# python script to optimize switching of cartridges and rasterize output
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
	sys.exit()

# import argparse # module for convenient command-line option handling
# not figured out how to use it yet


if len(sys.argv) != 8 or sys.argv[1] in ['h', '-h', '-help', '--help']:
	help_message()
else:
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



#main

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
			rasterize(sorted_data) # invokes write_output(linedata)
		else:
			print 'No additional scaffolds added.'
			write_output(sorted_data)
	else:
		pass # no optimization, thus do not use sorted data

else: # no sorting, check rasteization
	if rasterization:
		print 'No furher optimization of cartridge switches possible.'
		rasterize(linefile) # invokes write_output(linedata)
	else:
		print 'Neither additional scaffolds wanted'
		print 'nor furher optimization of cartridge switches possible.'
		print 'No output written to ' + outfile





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