import numpy as np
from numpy import random

from .randombase import RandomBase


class City:
    def __init__(self, location=[0,0], name='unnamed city', population=0):
        self.name       = name
        self.location   = np.array(location)
        self.population = population
    
    def __repr__(self):
        return f'{self.name} locates on {self.location}.'


class River(RandomBase):
    def __init__(self, keypoints=None, insert_times=None, 
        delta_length=1, intensity=0.5, 
        name='unnamed river', seed=None): 
        super().__init__(seed)
        self.var_seed = self.seed
        self.name         = name
        self.delta_length = delta_length
        self.intensity    = intensity
        self.keypoints    = [[], []]
        self.points       = [[], []]
        self.segments     = []
        if type(keypoints) == np.ndarray: 
            self.keypoints = keypoints.tolist()
            self.full_random(insert_times)
    
    def __repr__(self):
        return f'{self.name} has {len(self.keypoints[0])} keypoints.'

    def full_random(self, insert_times=None): 
        if len(self.keypoints[0]) > 1:
            X0 = self.keypoints[0][:-1]
            Y0 = self.keypoints[1][:-1]
            X1 = self.keypoints[0][1:]
            Y1 = self.keypoints[1][1:]
            for xyxy in np.array([X0, Y0, X1, Y1]).T.tolist():
                self.__generate_segment(*xyxy, insert_times)
    
    def full_refine(self, delta_length=None):
        if delta_length: 
            self.delta_length *= 0.5
        else: 
            self.delta_length = delta_length
        self.full_random()
    
    def add_point(self, x, y, refine=True, insert_times=None): 
        self.keypoints[0].append(x)
        self.keypoints[1].append(y)
        if len(self.keypoints[0]) > 1 and refine:
            x0 = self.keypoints[0][-2]
            y0 = self.keypoints[1][-2]
            self.__generate_segment(x0, y0, x, y, insert_times)

    def __generate_segment(self, x0, y0, x1, y1, insert_times=None): 
        r = np.sqrt((x0 - x1)**2 + (y0 - y1)**2)
        if not insert_times: 
            insert_times = int(np.log2(r/self.delta_length)) + 1
            if insert_times < 0: insert_times = 0
        segment = self.__change_segment(x0, y0, x1, y1, insert_times)
        self.segments.append(segment)
        self.points[0] += segment[0]
        self.points[1] += segment[1]
    
    def __change_segment(self, x0, y0, x1, y1, insert_times): 
        X = [x0, x1]
        Y = [y0, y1]
        for _ in range(insert_times):
            X, Y = self.__change_line(X, Y, self.intensity)
        return [X, Y]
    
    def __change_line(self, X, Y, intensity): 
        n = len(X)
        new_X = []
        new_Y = []
        random.seed(self.var_seed)
        self.var_seed += 2*n
        randmat = random.rand(2,n) - 0.5
        for i in range(n-1):
            new_X.append(X[i])
            new_Y.append(Y[i])
            length = np.sqrt((X[i] - X[i+1])**2 + (Y[i] - Y[i+1])**2)
            new_X.append(0.5*X[i] + 0.5*X[i+1] + intensity*length*randmat[0,i])
            new_Y.append(0.5*Y[i] + 0.5*Y[i+1] + intensity*length*randmat[1,i])
        new_X.append(X[-1])
        new_Y.append(Y[-1])
        return new_X, new_Y
    
    def save(self, path='data', file_name=None): 
        if len(self.points[0]) > 2: 
            if not file_name: file_name = path + '/' + self.name + '.txt'
            np.savetxt(file_name, self.points, delimiter=', ')
