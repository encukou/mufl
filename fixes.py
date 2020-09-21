from wasabi2d import animate as orig_animate

# Fix for https://github.com/lordmauve/wasabi2d/issues/61
def animate(*args, **kwargs):
    result = orig_animate(*args, **kwargs)
    for k, v in result.initial.items():
        if hasattr(v, '__len__'):
            result.initial[k] = tuple(v)
    return result
