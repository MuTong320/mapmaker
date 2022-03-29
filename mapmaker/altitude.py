import numpy as np
from numpy import random
from scipy.signal import convolve2d
import matplotlib.pyplot as plt

from .noise import Perlin2d
from .randombase import RandomBase


class AltitudeMap(RandomBase): 
    """高度图自动生成"""
    def __init__(self, name=None, seed=None,
        land_level=0.5, sea_level=0.2, noise_level=0.5, 
        continent_number=1, slope=5, width_range=(0.25,0.75), height_range=(0.25,0.75),
        perlin_cells=(10,10), 
        longtitude_range=100, latitude_range=80, resolution=1, 
        generate=True, generate_sea=True): 
        super().__init__(seed)
        if not name: 
            self.name       = 'Unnamed altitude map'
        else: 
            self.name       = name
        self.perlin_cells   = perlin_cells
        self.create_number  = continent_number
        self.width_range    = width_range
        self.height_range   = height_range
        self.width          = longtitude_range
        self.height         = latitude_range
        self.resolution     = resolution
        self.range          = np.array([longtitude_range, latitude_range])
        self.size           = resolution*self.range
        self.continent_dict = {}
        if generate: 
            self.generate(land_level, slope, noise_level)
            if generate_sea: self.add_sea(sea_level)
            self.map = self.nornalize(self.map)

    def __repr__(self): 
        return f"""
        Random map {self.name}: 
            seed      : {self.seed}, 
            continents: {self.create_number}
            size      : {self.size[0]} x {self.size[1]}
        """

    def generate(self, land_level, slope, noise_level): 
        """生成高度图"""
        x   = np.linspace(0, self.width,  self.size[0], endpoint=False)
        y   = np.linspace(0, self.height, self.size[1], endpoint=False)
        X,Y = np.meshgrid(x,y)
        self.generate_world_frame(X,Y)
        self.generate_continents(land_level, slope)
        self.generate_perlin_noise(X,Y)
        self.map = self.continents + 2*noise_level*self.noise

    def generate_world_frame(self, X, Y): 
        """生成世界大陆框架"""
        self.frame = np.zeros_like(X, dtype=bool)
        self.continent_contour = {}
        if self.create_number > 0: 
            if self.create_number == 1: 
                self.create_center_continent()
            elif self.create_number > 1: 
                self.create_random_continents(number=self.create_number)
        for continent in self.continent_dict.values(): 
            self.frame += continent(X, Y)
    
    def create_center_continent(self, edges=5, base=0.9): 
        """随即创建唯一的中央大陆"""
        center    = self.range/2
        randvec   = random.rand(edges) * base**np.arange(edges, 0, -1)
        continent = Continent(*center, center.min(), 
            0.2*center.min(), *randvec, name='Random continent')
        self.continent_dict['Random continent'] = continent
    
    def create_random_continents(self, number=5, edges=5, base=0.9, wave_scale=0.2): 
        """随机创建多块大陆"""
        randmat = random.rand(number, 2, edges + 4)
        x0      = self.width_range[0]
        x1      = self.width_range[1]
        y0      = self.height_range[0]
        y1      = self.height_range[1]
        for i in range(number): 
            xc      = self.width * (x0 + (x1-x0)*randmat[i,0,-1])
            yc      = self.height * (y0 + (y1-y0)*randmat[i,0,-2])
            d       = min(xc, yc, self.width-xc, self.height-yc)*(0.5*randmat[i,0,-3] + 0.5)
            w       = 2*randmat[i,0,-4]*wave_scale*d
            randvec = randmat[i,1,: edges] * base**np.arange(edges,0,-1)
            name    = 'Random continent ' + str(i+1)
            continent = Continent(xc, yc, d, w, *randvec, name=name)
            self.continent_dict[name] = continent

    def generate_continents(self, average, slope): 
        """生成大陆"""
        frame = self.frame.astype(float)
        gauss = self.__gaussian_kernel(sigma=slope*self.resolution)
        self.continents = average*convolve2d(frame, gauss, mode='same')
    
    def generate_perlin_noise(self, X, Y): 
        """生成柏林噪声"""
        p = Perlin2d(cells=self.perlin_cells, seed=self.seed)
        self.noise = p(X,Y)
    
    def add_sea(self, sea_level=0.5): 
        """加入海洋"""
        self.nonsea_map = self.map.copy()
        self.map = self.only_land(sea_level)
    
    def only_land(self, sea_level=0.5): 
        """只保留陆地高度"""
        return np.vectorize(lambda x: 1*(x > sea_level)*(x - sea_level))(self.map)
    
    def __gaussian_kernel(self, sigma, radius=0): 
        if radius == 0: radius = int(2*sigma)
        x      = np.arange(-radius, radius+1)
        y      = np.arange(-radius, radius+1)
        X,Y    = np.meshgrid(x,y)
        func   = np.vectorize(lambda x, y: np.exp(-(x**2 + y**2) / (2*sigma**2)))
        kernel = func(X,Y)
        return kernel / kernel.sum()

    def nornalize(self, map): 
        """归一化地图"""
        highest = map.max()
        lowest  = map.min()
        return (map - lowest) / (highest - lowest)
    
    def plot(self, which='altitude', colorbar=None): 
        """绘制高度图"""
        if which == 'altitude' or 'all': 
            self.__plot_altitude()
            if not colorbar: colorbar = True
            plt.show()
        if which == 'frame' or 'all': 
            self.__plot_frame()
            if not colorbar: colorbar = False
            plt.show()
        if which == 'continent' or 'all': 
            self.__plot_continent()
            if not colorbar: colorbar = True
            plt.show()
        if which == 'noise' or 'all': 
            self.__plot_noise()
            if not colorbar: colorbar = True
            plt.show()

    def __plot_altitude(self): 
        plt.title('Altitude map')
        plt.imshow(self.map, cmap='terrain')
        plt.colorbar()
    
    def __plot_frame(self): 
        plt.title('Frame of continents')
        plt.imshow(self.frame)
    
    def __plot_continent(self): 
        plt.title('Altitude map of continent')
        plt.imshow(self.continents, cmap='terrain')
        plt.colorbar()
    
    def __plot_noise(self): 
        plt.title('Map of noise')
        plt.imshow(self.noise, cmap='rainbow')
        plt.colorbar()


class Continent: 
    """大陆框架"""
    def __init__(self, xc, yc, diameter, wave_height, *fourier, name='Unnamed continent'): 
        self.name        = name
        self.xc          = xc
        self.yc          = yc
        self.center      = np.array([xc, yc])
        self.diameter    = diameter
        self.wave_height = wave_height
        self.fourier     = np.array(fourier)
    
    def __repr__(self): 
        return f"""{self.name}: 
            'center':      {self.center.tolist()}
            'diameter':    {self.diameter}
            'wave height': {self.wave_height}
            'fourier':     {self.fourier.tolist()}
        """
    
    def __call__(self, X, Y): 
        return self.global_func(X,Y)
    
    def contour(self, theta): 
        """大陆框架轮廓的极坐标函数"""
        func = np.vectorize(
            lambda theta: 0.5*self.diameter + self.wave_height*\
            (self.fourier * np.sin(theta*np.arange(1, self.fourier.size+1))).sum()
        )
        return func(theta)
    
    def contour_plot(self): 
        """绘制大陆框架的轮廓"""
        theta = np.linspace(0, 2*np.pi, 100)
        r     = self.contour(-theta)
        plt.polar(theta, r)
        plt.axis('off')
        plt.show()
    
    def local_func(self, X, Y): 
        """大陆视角的大陆框架函数"""
        @np.vectorize
        def local_func(x,y): 
            r, theta = self.__convert_polar(x,y)
            r0       = self.contour(theta)
            return (r < r0)
        return local_func(X,Y)
    
    def __convert_polar(self, x, y): 
        r = np.sqrt(x**2 + y**2)
        theta = 0
        if r != 0: theta = np.arccos(x/r)
        if y  < 0: theta = -theta
        if y == 0 and x < 0: theta = np.pi
        return r, theta
    
    def global_func(self, X, Y): 
        """全球视角的大陆框架函数"""
        return self.local_func(X - self.xc, Y - self.yc)



