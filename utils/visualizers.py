
import numpy as np
from matplotlib import pyplot as pyp2
import sys

def imshow16(data, title=None, vmin=0, vmax=None,
           cmap=None, interpolation='bilinear',
           dpi=96, figure=None, subplot=111, maxdim=17000, **kwargs):
    """Plot n-dimensional 16-bit RGB images using matplotlib.pyplot.

    Return figure, subplot and plot axis.
    Requires pyplot already imported ``from matplotlib import pyplot``.

    Arguments
    ---------

    isrgb : bool
        If True, data will be displayed as RGB(A) images if possible.

    photometric : str
        'miniswhite', 'minisblack', 'rgb', or 'palette'

    title : str
        Window and subplot title.

    figure : a matplotlib.figure.Figure instance (optional).

    subplot : int
        A matplotlib.pyplot.subplot axis.

    maxdim: int
        maximum image size in any dimension.

    Other arguments are same as for matplotlib.pyplot.imshow.

    """

    photometric='rgb'
    isrgb=True
    if photometric not in ('miniswhite', 'minisblack', 'rgb', 'palette'):
        raise ValueError("Can't handle %s photometrics" % photometric)

    data = data.squeeze()
    data = data[(slice(0, maxdim), ) * len(data.shape)]

    dims = len(data.shape)
    if dims < 2:
        raise ValueError("not an image")
    if dims == 2:
        dims = 0
        isrgb = False
    else:
        if (isrgb and data.shape[-3] in (3, 4)):
            data = np.swapaxes(data, -3, -2)
            data = np.swapaxes(data, -2, -1)
        elif (not isrgb and data.shape[-1] in (3, 4)):
            data = np.swapaxes(data, -3, -1)
            data = np.swapaxes(data, -2, -1)
        isrgb = isrgb and data.shape[-1] in (3, 4)
        dims -= 3 if isrgb else 2

    datamax = data.max()
    if data.dtype in (np.int8, np.int16, np.int32,
                      np.uint8, np.uint16, np.uint32):
        for bits in (1, 2, 4, 6, 8, 10, 12, 14, 16, 24, 32):
            if datamax <= 2**bits:
                datamax = 2**bits
                break
        if isrgb:
            data *= (255.0 / datamax)  # better use digitize()
            data = data.astype('B')
    elif isrgb:
        data /= datamax

    if not isrgb and vmax is None:
        vmax = datamax

    pyplot = sys.modules['matplotlib.pyplot']

    if figure is None:
        pyplot.rc('font', family='sans-serif', weight='normal', size=8)
        figure = pyplot.figure(dpi=dpi, figsize=(10.3, 6.3), frameon=True,
                               facecolor='1.0', edgecolor='w')
        try:
            figure.canvas.manager.window.title(title)
        except Exception:
            pass
        pyplot.subplots_adjust(bottom=0.03*(dims+2), top=0.925,
                               left=0.1, right=0.95, hspace=0.05, wspace=0.0)
    subplot = pyplot.subplot(subplot)

    if title:
        pyplot.title(title, size=11)

    if cmap is None:
        if photometric == 'miniswhite':
            cmap = pyplot.cm.binary
        else:
            cmap = pyplot.cm.gray

    image = pyplot.imshow(data[(0, ) * dims].squeeze(), vmin=vmin, vmax=vmax,
                          cmap=cmap, interpolation=interpolation, **kwargs)

    if not isrgb:
        pyplot.colorbar()

    def format_coord(x, y):
        """Callback to format coordinate display in toolbar."""
        x = int(x + 0.5)
        y = int(y + 0.5)
        try:
            if dims:
                return "%s @ %s [%4i, %4i]" % (cur_ax_dat[1][y, x],
                                               current, x, y)
            else:
                return "%s @ [%4i, %4i]" % (data[y, x], x, y)
        except IndexError:
            return ""

    pyplot.gca().format_coord = format_coord

    if dims:
        current = list((0, ) * dims)
        cur_ax_dat = [0, data[tuple(current)].squeeze()]
        sliders = [pyplot.Slider(
            pyplot.axes([0.125, 0.03*(axis+1), 0.725, 0.025]),
            'Dimension %i' % axis, 0, data.shape[axis]-1, 0, facecolor='0.5',
            valfmt='%%.0f of %i' % data.shape[axis]) for axis in range(dims)]
        for slider in sliders:
            slider.drawon = False

        def set_image(current, sliders=sliders, data=data):
            """Change image and redraw canvas."""
            cur_ax_dat[1] = data[tuple(current)].squeeze()
            image.set_data(cur_ax_dat[1])
            for ctrl, index in zip(sliders, current):
                ctrl.eventson = False
                ctrl.set_val(index)
                ctrl.eventson = True
            figure.canvas.draw()

        def on_changed(index, axis, data=data, image=image, figure=figure,
                       current=current):
            """Callback for slider change event."""
            index = int(round(index))
            cur_ax_dat[0] = axis
            if index == current[axis]:
                return
            if index >= data.shape[axis]:
                index = 0
            elif index < 0:
                index = data.shape[axis] - 1
            current[axis] = index
            set_image(current)

        def on_keypressed(event, data=data, current=current):
            """Callback for key press event."""
            key = event.key
            axis = cur_ax_dat[0]
            if str(key) in '0123456789':
                on_changed(key, axis)
            elif key == 'right':
                on_changed(current[axis] + 1, axis)
            elif key == 'left':
                on_changed(current[axis] - 1, axis)
            elif key == 'up':
                cur_ax_dat[0] = 0 if axis == len(data.shape)-1 else axis + 1
            elif key == 'down':
                cur_ax_dat[0] = len(data.shape)-1 if axis == 0 else axis - 1
            elif key == 'end':
                on_changed(data.shape[axis] - 1, axis)
            elif key == 'home':
                on_changed(0, axis)

        figure.canvas.mpl_connect('key_press_event', on_keypressed)
        for axis, ctrl in enumerate(sliders):
            ctrl.on_changed(lambda k, a=axis: on_changed(k, a))

    return figure, subplot, image

def showFromFile(filename):
    data = np.load(filename)
    imshow(data)
    pyp2.grid()
    pyp2.show()

def showFromArray(numpyArray):
    imshow(numpyArray)
    pyp2.grid()
    pyp2.show()

