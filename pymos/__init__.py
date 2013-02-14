#!/usr/bin/env python
# -*- coding: utf-8 -*-

import PIL.Image as Image
import os, sys, random
import logging
import glob

try:
    import cPickle as pickle
except ImportError:
    import pickle

log = logging.getLogger('PyMos')

def _get_average_rgb(image, filename):
    red = green = blue = 0
    try:
        imdata = list(image.getdata())
        imdata_size = len(imdata)
    except:
        log.debug ("Error processing " + filename)
        return None

    try:
        for i in imdata:
            if type(i) == int:
                red += i
                green += i
                blue += i
            else:
                red += i[0]
                green += i[1]
                blue += i[2]

        # average the color of this thumbnail
        red /= imdata_size
        green /= imdata_size
        blue /= imdata_size
    except ValueError:
        log.debug ("Error processing " + filename)
    return (red, green, blue)


def _get_linear_colormap(files):
    colormap = []
    file_count = 0
    total_files = len(files)
    for eachfile in files:
        try:
            temp = Image.open(eachfile)
        except IOError as error:
            log.debug("Error opening %s" % eachfile)
            log.debug("IOError - %s" % error)
            continue

        rgb = _get_average_rgb(temp, eachfile)
        if not rgb:
            continue
        
        colormap.append( ( rgb, eachfile ))
        # caching of resized images done in image_cache now

        file_count += 1
        log.debug("%.1f %% done" % ((float(file_count)/total_files)*100))
    return colormap      
    
def _build_colormap(files):
    ''' builds out and returns an average color to file location mapping '''
    return _get_linear_colormap(files)    

def _get_euclidean_match(source_color, colormap):
    # euclidean distance, color, index in colormap
    r_1, g_1, b_1 = source_color
    match = (196608, (555, 555, 555), 0) # initially something out of range
    for index, thumbs in zip (xrange(len(colormap)), colormap):
        thumb_color = thumbs[0]
        # calculate the euclidian distance between the two colors
        r_2, g_2, b_2 = thumb_color

        ecd_match = match[0]
        ecd_found = ( (r_2 - r_1) ** 2 + (g_2 - g_1) ** 2 +
                        (b_2-b_1) ** 2 )

        if (ecd_found < ecd_match):
            match = (ecd_found, thumb_color, index)
    return colormap[match[2]][1]

def build_mosaic(input_path, output_path, collection_path,
                    zoom = 20, thumb_size = 60, fuzz = 0, new_colormap=False):
    ''' Builds up the mosaic using given parameters using colormap
        using input_path, output_path, collection_path, zoom=20,
              thumb_size=60, fuzz=0, new_colormap=False
    '''
    # Build Color Index
    log.info( "Building index...")

    files = glob.glob(os.path.join(collection_path, '*.jpg'))
    colormap_file = os.path.join(collection_path, '.colormap')
    
    if os.path.exists(colormap_file) and not new_colormap:
        colormap = pickle.load(open(colormap_file))
    else:
        colormap = _build_colormap(files)
        pickle.dump(colormap, open(colormap_file, 'w'))

    log.info("Color Index built")

    # prepare images
    try:
        source = Image.open (input_path)
        source_data = list(source.getdata())
    except IOError:
        log.debug ("Error opening %s" % input_path)
        sys.exit(0)

    source_width, source_height = source.size
    output_width, output_height = source_width*zoom, source_height*zoom

    output = Image.new("RGB", (output_width, output_height),
                            (255,255,255))
    image_cache = {}
    log.info("Generating Mosaic...")
    
    # square mosaics as for now
    for s_x in xrange(0, output_width, thumb_size):
        for s_y in xrange(0, output_height, thumb_size):
            source_color = source_data[ (s_y/zoom) * source_width + s_x/zoom ]
            is_bw = type(source_color) == int
            
            # we randomize source color for added fuziness
            if (fuzz!=0):
                if is_bw:
                    source_color = random.randint(-fuzz, fuzz) + source_color
                else:
                    source_color = tuple(s_x + random.randint(-fuzz, fuzz)
                                        for s_x in source_color)
                                        
            if is_bw:
                source_color = (source_color, source_color, source_color)
                
            match = _get_euclidean_match(source_color, colormap)
            
            if match not in image_cache:
                image_cache[match] = Image.open(match)
                ### new maxfill method
                tsize = image_cache[match].size
                # taller image -> fille width to complete square
                tsize =  (thumb_size,
                        int( round((float(tsize[1])/tsize[0]) * thumb_size)))

                if ( tsize[0] > tsize[1]):
                    # wider image -> fill height of thumb_sizexthumb_size square
                    tsize =  (int( round((float(tsize[0])/tsize[1]) * thumb_size )),
                        thumb_size)
                image_cache[match] = image_cache[match].resize(tsize)
                
            output.paste (image_cache[match], (s_x, s_y))
        log.debug("%.1f %% done" % ((float(s_x)/output_width) * 100))

    log.info("Mosaic Generated. Saving...")

    if output_path is None:
        return output

    output.save(output_path, "PNG")
    log.info("Done ! Mosaic saved in " + output_path)
