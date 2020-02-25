import matplotlib.pyplot as plt
import numpy as np
import os


def create_plots_dir(config):
    if not os.path.isdir(config['plots_dir']):
        os.mkdir(config['plots_dir'])


def plot_map(config, fsk, mp, name, title=None, fmt='png'):
    if title is None:
        title = name
    create_plots_dir(config)
    fname = config['plots_dir'] + '/' + name + '.' + fmt
    fsk.view_map(mp, title=title, fnameOut=fname)


def plot_histo(config, name, arrs, names, bins=None, range=None,
               density=False, weights=None, logy=False,
               logx=False, fmt='png'):
    if np.ndim(arrs) == 1:
        arrs = [arrs]
        names = [names]

    x_title = r'$x$'
    if logx:
        x_title = r'$\log_{10}x$'

    if density:
        y_title = r'$p$'
        if logy:
            y_title = r'$\log_{10}p$'
    else:
        y_title = r'$N$'
        if logy:
            y_title = r'$\log_{10}N$'

    plt.figure()
    for i_a, (a, n) in enumerate(zip(arrs, names)):
        if logx:
            x = np.log10(a)
        else:
            x = a
        if weights is not None:
            w = weights[i_a]
        else:
            w = None
        plt.hist(x, bins=bins, range=range,
                 density=density, weights=w,
                 log=logy, label=n, histtype='step')
    plt.legend(fontsize=12)
    plt.xlabel(x_title, fontsize=14)
    plt.ylabel(y_title, fontsize=14)
    fname = config['plots_dir'] + '/' + name + '.' + fmt
    plt.savefig(fname, bbox_inches='tight')
    plt.clf()