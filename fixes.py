import numpy as np
from wasabi2d import animate as orig_animate

# Fix for https://github.com/lordmauve/wasabi2d/issues/61
def animate(*args, **kwargs):
    result = orig_animate(*args, **kwargs)
    for k, v in result.initial.items():
        if hasattr(v, '__len__'):
            result.initial[k] = tuple(v)
    return result


# Fix for https://github.com/lordmauve/wasabi2d/issues/63
def fix_transforms(self):
    def build_mat():
        #self.__xfmat[:2, :2] = np.matmul(self._scale, self._rot)
        np.matmul(self._scale, self._rot, out=self._Transformable__xfmat[:2, :2])

    self._Transformable__build_mat = build_mat
    build_mat()
