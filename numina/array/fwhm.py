#
# Copyright 2014-2015 Universidad Complutense de Madrid
#
# This file is part of Numina
#
# Numina is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Numina is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Numina.  If not, see <http://www.gnu.org/licenses/>.
#

'''FWHM calculation'''

from __future__ import division

import numpy as np
import scipy.interpolate as itpl

from numina.array.utils import wc_to_pix_1d


def compute_fwhm_2d_simple(img, xc, yc):

    X = np.arange(0, img.shape[1], 1.0)
    Y = np.arange(0, img.shape[0], 1.0)

    xpix = wc_to_pix_1d(xc - X[0])
    ypix = wc_to_pix_1d(yc - Y[0])

    peak = img[ypix, xpix]

    res11 = img[ypix, :]
    res22 = img[:, xpix]

    fwhm_x, _codex, _msgx = compute_fwhm_1d(X, res11 - 0.5 * peak, xc, xpix)
    fwhm_y, _codey, _msgy = compute_fwhm_1d(Y, res22 - 0.5 * peak, yc, ypix)

    return peak, fwhm_x, fwhm_y


def compute_fwhm_2d_spline(img, xc, yc):

    Y = np.arange(0.0, img.shape[1], 1.0)
    X = np.arange(0.0, img.shape[0], 1.0)

    xpix = wc_to_pix_1d(xc)
    ypix = wc_to_pix_1d(yc)
    # The image is already cropped

    bb = itpl.RectBivariateSpline(X, Y, img)
    # We assume that the peak is in the center...
    peak = bb(xc, yc)[0, 0]

    U = X
    V = bb.ev(U, [yc for _ in U]) - 0.5 * peak
    fwhm_x, _codex, _msgx = compute_fwhm_1d(U, V, yc, ypix)

    U = Y
    V = bb.ev([xc for _ in U], U) - 0.5 * peak
    fwhm_y, _codey, _msgy = compute_fwhm_1d(U, V, xc, xpix)

    return peak, fwhm_x, fwhm_y


def compute_fwhm_1d_simple(Y, xc, X=None):
    '''Compute the FWHM.'''
    return compute_fw_at_frac_max_1d_simple(Y, xc, X=X, f=0.5)


def compute_fw_at_frac_max_1d_simple(Y, xc, X=None, f=0.5):
    '''Compute the full width at fraction f of the maximum'''
    if X is None:
        X = np.arange(Y.shape[0])

    xpix = wc_to_pix_1d(xc - X[0])
    peak = Y[xpix]

    fwhm_x, _codex, _msgx = compute_fwhm_1d(X, Y - f * peak, xc, xpix)
    return peak, fwhm_x


def _fwhm_side_lineal(uu, vv):
    '''Compute r12 using linear interpolation.'''
    res1, = np.nonzero(vv < 0)
    if len(res1) == 0:
        return 0, 1  # error, no negative value
    else:
        # first value
        i2 = res1[0]
        i1 = i2 - 1
        dx = uu[i2] - uu[i1]
        dy = vv[i2] - vv[i1]
        r12 = uu[i1] - vv[i1] * dx / dy
        return r12, 0


def compute_fwhm_1d(uu, vv, uc, upix):

    _fwhm_side = _fwhm_side_lineal

    # Find half peak radius on the rigth
    r12p, errorp = _fwhm_side(uu[upix:], vv[upix:])

    # Find half peak radius on the left
    r12m, errorm = _fwhm_side(uu[upix::-1], vv[upix::-1])

    if errorm == 1:
        if errorp == 1:
            fwhm = -99  # No way
            msg = 'Failed to compute FWHM'
            code = 2
        else:
            fwhm = 2 * (r12p - uc)
            code = 1
            msg = 'FWHM computed from right zero'
    else:
        if errorp == 1:
            fwhm = 2 * (uc - r12m)
            msg = 'FWHM computed from left zero'
            code = 1
        else:
            msg = 'FWHM computed from left and right zero'
            code = 0
            fwhm = r12p - r12m

    return fwhm, code, msg
