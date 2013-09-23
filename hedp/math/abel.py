#!/usr/bin/python
# -*- coding: utf-8 -*-
# hedp module
# Roman Yurchak, Laboratoire LULI, 11.2012

import numpy as np
from hedp.lib.integrators import abel_integrate

def iabel(fr, dr=1):
    """
    Returns inverse Abel transform. See `abel` for input parameters.

    """
    return abel(fr, dr, inverse=True)

def abel(fr, dr=1.0, inverse=False):
    """
    Returns the direct or inverse Abel transform of a function
    sampled at discrete points.

    This algorithm does a direct computation of the Abel transform:
      * integration near the singular value is done analytically
      * integration further from the singular value with the Simpson
        rule.

    There may be better/more general ways to do the inverse tranformation,
    especially regarding resilience to noise. See:
      * One-dimensional tomography: a comparison of Abel, onion-peeling, and
      filtered backprojection methods. Cameron J. Dasch
      * Reconstruction of Abel-transformable images: The Gaussian basis-set
        expansion Abel transform method. V. Dribinski
      * Using the Hankel-Fourier transform.
    still, this implementation has the advantage of being simple and working
    for both the inverse and the direct transform.

    Parameters
    ----------
    fr:  1d or 2d numpy array
        input array to which direct/inversed Abel transform will be applied.
        For a 2d array, the first dimension is assumed to be the z axis and
        the second the r axis.
    dr: float
        space between samples
    inverse: boolean
        If True inverse Abel transform is applied.

    Returns
    -------
    out: 1d or 2d numpy array of the same shape as fr
        with either the direct or the inverse abel transform.
    """

    assert isinstance(fr, np.ndarray)
    f = fr.copy()

    if fr.ndim == 1:
        f = f.reshape((1, -1))

    r = (np.arange(f.shape[1])+0.5)*dr

    if inverse:
        if f.shape[0] == 1:
            # messy computation of the derivative in 1d
            der = np.zeros(f.shape)
            f0 = f[0]
            der[0, 1:-1] = f0[2:] - f0[:-2]
            der[0, 0] = f0[1] - f0[0]
            der[0,-1] = f0[-1] - f0[-2]
            f = - der/(2*dr*np.pi)
        else:
            f = - np.gradient(f)[-1]/(dr*np.pi)
    else:
        f *= 2*r

    out = abel_integrate(f, r)

    if f.shape[0] == 1:
        return out[0]
    else:
        return out

def _abel_sym():
    """
    Analytical integration of the cell near the singular value in the abel transform
    The resulting formula is implemented in hedp.lib.integrators.abel_integrate
    """
    from sympy import symbols, simplify, integrate, sqrt
    from sympy.assumptions.assume import global_assumptions
    r, y,r0, r1,r2, z,dr, c0, c_r, c_rr,c_z, c_zz, c_rz = symbols('r y r0 r1 r2 z dr c0 c_r c_rr c_z c_zz c_rz', positive=True)
    f0, f1, f2 = symbols('f0 f1 f2')
    global_assumptions.add(Q.is_true(r>y))
    global_assumptions.add(Q.is_true(r1>y))
    global_assumptions.add(Q.is_true(r2>y))
    global_assumptions.add(Q.is_true(r2>r1))
    P = c0 + (r-y)*c_r #+ (r-r0)**2*c_rr
    K_d = 1/sqrt(r**2-y**2)
    res = integrate(P*K_d, (r,y, r1))
    sres= simplify(res)
    print sres
    


def abel_analytical_step(r, fr_z, r0, r1):
    """
    Parameters
    ----------
    r:   1d array of radius at which fr is taken.
    fr_z:  1d along Z direction
        input array to which direct Abel transform will be applied.
    """

    F_1d = np.zeros(r.shape)
    mask = (r>=r0)*(r<r1)
    F_1d[mask] = 2*np.sqrt(r1**2 - r[mask]**2)
    mask = r<r0
    F_1d[mask] = 2*np.sqrt(r1**2 - r[mask]**2) - 2*np.sqrt(r0**2 - r[mask]**2)
    fr_z = fr_z.reshape((-1,1))
    return F_1d*fr_z

def sym_abel_step_1d(r, r0, r1):
    """
    Produces a symmetrical analytical transform of a 1d step
    """
    d = np.empty(r.shape)
    for sens, mask in enumerate([r>=0, r<=0]):
        d[mask] =  abel_analytical_step(np.abs(r[mask]), np.array(1), r0, r1)[0]

    return d





if __name__ == "__main__":
    # just an example to illustrate the use of this algorthm
    import matplotlib.pyplot as plt
    from time import time
    import sys


    ax0= plt.subplot(211)
    plt.title('Abel tranforms of a gaussian function')
    n = 800
    r = np.linspace(0, 20, n)
    dr = np.diff(r)[0]
    rc = 0.5*(r[1:]+r[:-1])
    fr = np.exp(-rc**2)
    #fr += 1e-1*np.random.rand(n)
    plt.plot(rc,fr,'b', label='Original signal')
    F = abel(fr,dr=dr)
    F_a = (np.pi)**0.5*fr.copy()

    F_i = abel(F,dr=dr, inverse=True)
    #sys.exit()
    plt.plot(rc, F_a, 'r', label='Direct transform [analytical expression]')
    mask = slice(None,None,5)
    plt.plot(rc[mask], F[mask], 'ko', label='Direct transform [computed]')
    plt.plot(rc[mask], F_i[mask],'o',c='orange', label='Direct-inverse transform')
    plt.legend()
    ax0.set_xlim(0,4)
    ax0.set_xlabel('x')
    ax0.set_ylabel("f(x)")

    ax1 = plt.subplot(212)
    err1 = np.abs(F_a-F)/F_a
    err2 = np.abs(fr-F_i)/fr
    plt.semilogy(rc, err1, label='Direct transform error')
    plt.semilogy(rc, err2, label='Direct-Inverse transform error')
    #plt.semilogy(rc, np.abs(F-F_a), label='abs err')
    ax1.set_ylabel('Relative error')
    ax1.set_xlabel('x')

    plt.legend()
    plt.show()
