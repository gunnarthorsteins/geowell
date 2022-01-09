def interpolate(a, b):
    """General table interpolation
    Params:
        a: 1x3 vector
        b: 1x2 vector
    
    Returns:
        interpolated value
    """
    return b[0] + (b[1]-b[0])*(a[1]-a[0])/(a[2]-a[0])