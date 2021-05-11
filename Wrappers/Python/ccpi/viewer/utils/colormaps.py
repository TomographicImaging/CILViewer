# -*- coding: utf-8 -*-
#   Copyright 2019 Edoardo Pasca

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


# New matplotlib colormaps by Nathaniel J. Smith, Stefan van der Walt,
# and (in the case of viridis) Eric Firing.
#
# This file and the colormaps in it are released under the CC0 license /
# public domain dedication. We would appreciate credit if you use or
# redistribute these colormaps, but do not impose any legal restrictions.
#
# To the extent possible under law, the persons who associated CC0 with
# mpl-colormaps have waived all copyright and related or neighboring rights
# to mpl-colormaps.
#
# You should have received a copy of the CC0 legalcode along with this
# work.  If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

import vtk
import numpy
from matplotlib import cm


def gaussian(x, sigma, b=0):
    '''Gaussian function

    :param x: ndarray to evaluate the gaussian at
    :param sigma: standard deviation
    :param b: optional center of the distribution'''
    return numpy.exp(-(x-b)**2/(2*sigma**2))


def logistic(x, L, k, x0):
    r'''Logistic function
    
    .. math:: 

        f(x) = \frac{L}{1+ e^{-k(x-x_0)}}

    :param x: ndarray to evaluate the function at
    :param L: L = lim_{x -> inf} f(x) - f(-x)
    :param k: steepness of the function. 
    :param x0: optional translation of the function
    '''
    return L / (1+numpy.exp(-k*(x-x0)))


def relu(x, xmin, xmax, scaling=1):
    r'''Similar to rectified linear unit relu

    returns values as
    1. x< xmin : f(x) = 0
    2. xmin <= x <= xmax : f(x) =  (x - xmin) / (xmax - xmin)
    3. x > xmax: f(x) = 0

    :param x: ndarray to evaluate the function at
    :param xmin: value at which the function start increasing
    :param xmax: value at which the function stops increasing
    :param scaling: (optional) max value, defaults to 1

    '''
    out = []
    dx = xmax-xmin
    for i, val in enumerate(x):
        if val < xmin or val > xmax:
            out.append(0)
        else:
            out.append((val - xmin) / dx)
    return numpy.asarray(out)


class CILColorMaps(object):
    @staticmethod
    def get_color_transfer_function(cmap, color_range):

        tf = vtk.vtkColorTransferFunction()
        colors = []
        for x in range(0, 255):
            color = cm.get_cmap(cmap)(x)
            colors.append([color[0], color[1], color[2]])

        N = len(colors)
        for i, color in enumerate(colors):
            level = color_range[0] + \
                (color_range[1] - color_range[0]) * i / (N-1)
            tf.AddRGBPoint(level, color[0], color[1], color[2])

        return tf

    @staticmethod
    def get_opacity_transfer_function(x, function, *params):
        opacity = vtk.vtkPiecewiseFunction()
        vals = function(x, *params)
        for _x, _y in zip(x, vals):
            opacity.AddPoint(_x, _y)
        return opacity
