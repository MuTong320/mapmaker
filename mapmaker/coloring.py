import numpy as np
from numpy import random
import pandas as pd

from .randombase import RandomBase
from .altitude import AltitudeMap
from .noise import Perlin2d
from .data.color_dict import color_dict


class MapBase(RandomBase): 
    """基础地图对象，包含地图读取和地图随机生成"""
    def __init__(self, origin_map=None, seed=None): 
        super().__init__(seed)
        self.set_land_index()
        self.set_origin_map(origin_map)
        self.map = self.origin_map.copy()
        self.set_range()
        self.only_land()

    def set_land_index(self): 
        self.color_dict      = color_dict
        self.land_index_dict = {}
        self.index_land_dict = {}
        for index, landtype in enumerate(self.color_dict.keys()): 
            self.index_land_dict[index]    = landtype
            self.land_index_dict[landtype] = index

    def set_origin_map(self, origin_map): 
        if origin_map is None: 
            origin_map = AltitudeMap(seed=self.seed)
        if type(origin_map)   == AltitudeMap: 
            self.altitude_source     = origin_map
            self.altitude_map        = origin_map.map
            self.convert_altitude2normal()
        elif type(origin_map) == np.ndarray: 
            self.__set_by_matrix(origin_map)
        elif type(origin_map) == str:
            origin_map = pd.read_csv(origin_map, sep=',', header=None).values
            self.__set_by_matrix(origin_map)

    def __set_by_matrix(self, origin_map):
        if origin_map.dtype == 'float64': 
            self.altitude_source = None
            self.altitude_map    = origin_map
            self.convert_altitude2normal()
        elif origin_map.dtype == 'int64': 
            self.origin_map      = origin_map
            self.altitude_source = None
            self.altitude_map    = np.array([])
    
    def recover_origin_map(self): 
        self.map = self.origin_map.copy()
    
    def convert_altitude2normal(self, shollow_level=0.15, mountain_level=0.50, peak_level=0.85): 
        ocean    = self.land_index_dict['海洋']
        water    = self.land_index_dict['水域']
        prairie  = self.land_index_dict['草原']
        mountain = self.land_index_dict['山地']
        peak     = self.land_index_dict['高峰']
        @np.vectorize
        def color_by_altitude(x): 
            if   x == 0: 
                return ocean
            elif x < shollow_level: 
                return water
            elif x > peak_level: 
                return peak
            elif x > mountain_level: 
                return mountain
            else: 
                return prairie
        self.origin_map = color_by_altitude(self.altitude_map).astype(np.int64)

    def set_range(self, left=None, right=None, top=None, bottom=None): 
        self.height, self.width = self.map.shape
        if not left  : left     = 0
        if not right : right    = self.width
        if not top   : top      = self.height
        if not bottom: bottom   = 0
        self.range = [left, right, bottom, top]
    
    def only_land(self): 
        ocean = self.land_index_dict['海洋']
        water = self.land_index_dict['水域']
        @np.vectorize
        def is_land(x): 
            return not (x == ocean or x == water)
        self.land = is_land(self.map)
    
    def extract_layer(self, *layer_names): 
        lst = [self.land_index_dict['其他']]
        for name in layer_names: 
            lst.append(self.land_index_dict[name])
        @np.vectorize
        def is_layer(x): 
            if x in lst: 
                return x
            else: 
                return lst[0]
        self.extract_map = is_layer(self.map)


class ChangeableMap(MapBase): 
    """地块可变地图对象"""
    def __init__(self, origin_map=None, seed=None, cut_times=0): 
        super().__init__(origin_map, seed)
        self.rows      = self.height
        self.cols      = self.width
        self.cut_times = cut_times + 1
        self.changed   = False
    
    def assign_plant(self, proportion=[0.2, 0.2, 0.2, 0.2, 0.2], 
        areas=['森林', '沃土', '草原', '戈壁', '荒漠'], cells=None): 
        new_map = self.map.copy().astype(np.int64)
        if cells is None: cells = 5
        if type(cells) == int: 
            cells = (cells, np.ceil(cells*self.rows/self.cols).astype(int))
        p   = Perlin2d(cells, seed = self.seed)
        x   = np.arange(self.cols)
        y   = np.arange(self.rows)
        X,Y = np.meshgrid(x,y)
        aimland  = [self.land_index_dict[area] for area in areas]
        forest   = self.land_index_dict['森林']
        farmland = self.land_index_dict['沃土']
        prairie  = self.land_index_dict['草原']
        gobi     = self.land_index_dict['戈壁']
        desert   = self.land_index_dict['荒漠']
        sum = 0
        accumulate = []
        for pi in proportion:
            sum += pi
            accumulate.append(sum)
        accumulate = [accumulate[i]/sum for i in range(len(accumulate))]
        @np.vectorize
        def assign(x, noise): 
            if x in aimland: 
                if noise < accumulate[0]: 
                    return forest
                elif noise < accumulate[1]: 
                    return farmland
                elif noise < accumulate[2]: 
                    return prairie
                elif noise < accumulate[3]: 
                    return gobi
                else: 
                    return desert
            else: 
                return x
        new_map  = assign(new_map, p(X,Y) + 0.5)
        self.map = new_map.astype(np.int64)
        self.changed = True
    
    def refine(self, cut=2): 
        """增加地图分辨率"""
        new_mat = np.empty((cut*self.rows, cut*self.cols))
        for i, column in enumerate(self.map): 
            new_column = np.repeat(column, cut)
            for j in range(cut): 
                new_mat[cut*i+j] = new_column
        self.map = new_mat.astype(np.int64)
        self.rows, self.cols = self.map.shape
        self.cut_times += 1
        self.changed = True
        self.only_land()

    def weathering(self, intensity=0.1): 
        """随机改变地形"""
        new_map = self.map.copy()
        random.seed(self.seed)
        randmat = random.rand(self.rows, self.cols, 2)
        for i in range(1, self.rows-1): 
            for j in range(1, self.cols-1): 
                if randmat[i,j,0] > 1 - intensity: 
                    new_map[i,j] = self.map[i+1, j]
                elif randmat[i,j,0] < intensity: 
                    new_map[i,j] = self.map[i-1, j]
                if randmat[i,j,1] > 1 - intensity: 
                    new_map[i,j] = self.map[i, j+1]
                elif randmat[i,j,1] < intensity: 
                    new_map[i,j] = self.map[i, j-1]
        self.map = new_map.astype(np.int64)
        self.only_land()
        self.changed = True

    def coastline(self): 
        """生成海岸线"""
        new_map       = self.map.copy()
        boundary_line = self.land_index_dict['边界']
        for i in range(1, self.rows-1): 
            for j in range(1, self.cols-1): 
                if self.land[i,j]: 
                    if not (self.land[i+1, j] and self.land[i-1, j] \
                        and self.land[i, j+1] and self.land[i, j-1]): 
                        new_map[i,j] = boundary_line
        self.map = new_map.astype(np.int64)
        self.changed = True

