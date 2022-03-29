import numpy as np
from numpy import random

from .randombase import RandomBase


class Perlin2d(RandomBase):
    def __init__(self, cells=(1,1), seed=None):
        super().__init__(seed)
        self.perlin_cells = tuple(cells)
    
    def __call__(self, X, Y):
        self.generate_perlin_noise(X,Y)
        return self.noise
    
    def generate_perlin_noise(self, X, Y):
        xmin = X.min()
        xmax = X.max()
        ymin = Y.min()
        ymax = Y.max()
        Xr   = (X - xmin)/(xmax - xmin) * self.perlin_cells[0]
        Yr   = (Y - ymin)/(ymax - ymin) * self.perlin_cells[1]
        randmat    = random.rand(2, self.perlin_cells[0]+2, self.perlin_cells[1]+2)
        self.gradx = randmat[0] * np.cos(2*np.pi * randmat[1])
        self.grady = randmat[0] * np.sin(2*np.pi * randmat[1])
        self.noise = np.vectorize(self.__point_altitude)(Xr,Yr)
        
    def __point_altitude(self, x, y):
        x0 = int(x)
        x1 = x0 + 1
        y0 = int(y)
        y1 = y0 + 1
        wx = self.__fade(x - x0)
        wy = self.__fade(y - y0)
        return (1-wx)*(1-wy)*(self.gradx[x0,y0]*(x-x0) + self.grady[x0,y0]*(y-y0))\
            +     wx *(1-wy)*(self.gradx[x1,y0]*(x-x1) + self.grady[x1,y0]*(y-y0))\
            +  (1-wx)*   wy *(self.gradx[x0,y1]*(x-x0) + self.grady[x0,y1]*(y-y1))\
            +     wx *   wy *(self.gradx[x1,y1]*(x-x1) + self.grady[x1,y1]*(y-y1))
    
    def __fade(self, t):
        return 6*t**5 - 15*t**4 + 10*t**3
