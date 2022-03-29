import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .coloring import ChangeableMap
from .unit import City, River


plt.rcParams["font.sans-serif"] = ["SimHei"]  #设置字体
plt.rcParams["axes.unicode_minus"] = False    #该语句解决图像中的“-”负号的乱码问题


class Map(ChangeableMap): 
    """可绘制的，包含城市和河流绘制和指派的地图对象"""
    def __init__(
        self, map=None, cut_time=0, data_path='data', name=None,
        cities=True, rivers=True, seed=None
    ): 
        super().__init__(map, seed, cut_time)
        self.set_files(data_path, name)
        self.save_map_data()
        if cities: self.read_cities()
        if rivers: self.read_rivers()
        self.__generate_image()
        self.set_figure()
    
    def __repr__(self): 
        return f"""
        Map {self.name}: 
            random seed: {self.seed}, 
            refine     : {self.cut_times} cut times, 
            size       : {self.rows} x {self.cols}
        Generate this map: 
            m = Map(name='{self.name}', seed='{self.seed}')
            m.polish({self.cut_times})
        Read this map: 
            m = Map('{self.map_file}', name='{self.name}', cut_time={self.cut_times}, seed='{self.seed}')
        """

    def set_files(self, data_path, name, map_file='map.txt', altitude_file='altitude.txt', 
        city_file='city.txt', river_file='river_name.txt'):
        """设置数据储存路径"""
        if not name: 
            self.name = '未命名'
        else: 
            self.name = name
        self.path = data_path + '/' + self.name
        if not os.path.exists(self.path): os.makedirs(self.path)
        self.map_file      = self.path + '/' + map_file
        self.altitude_file = self.path + '/' + altitude_file
        self.city_file     = self.path + '/' + city_file
        self.river_file    = self.path + '/' + river_file
        open(self.city_file,  'a').close()
        open(self.river_file, 'a').close()

    def save_map_data(self): 
        np.savetxt(self.map_file, self.map, delimiter=', ', fmt='%d')
        np.savetxt(self.altitude_file, self.altitude_map, delimiter=', ')

    def read_cities(self): 
        """从文件中读取城市数据"""
        self.cities = []
        if os.path.getsize(self.city_file) > 0: 
            lst      = pd.read_csv(self.city_file, sep=',', header=None).values
            name     = lst[:,0].tolist()
            location = lst[:,1:3].tolist()
            self.cities = [City(location[i], name[i]) for i in range(len(name))]
        else: 
            print(f"File '{self.city_file}' is empty.")
    
    def set_city(self, city_name, city_location): 
        """设置新城市"""
        c = City(city_location, city_name)
        self.cities.append(c)
        f = open(self.city_file, 'a')
        f.write(f'{c.name}, {c.location[0]}, {c.location[1]} \n')
        f.close()
    
    def clear_all_city(self):
        """清除所有城市"""
        self.cities = []
        open(self.city_file, 'w').close()
    
    def clear_city(self, *city_names): 
        """清除给定城市"""
        for c in self.cities: 
            if c.name in city_names: self.cities.remove(c)
        cities = self.cities
        self.clear_all_city()
        for c in cities:
            self.set_city(c.name, c.location)
    
    def read_rivers(self): 
        """从文件中读取河流"""
        self.rivers = []
        if os.path.getsize(self.river_file) > 0: 
            names = pd.read_csv(self.river_file, header=None).values.reshape(-1).tolist()
            for name in names: 
                file = self.path + '/' + name + '.txt'
                if os.path.getsize(file) > 0: 
                    r        = River(name=name)
                    r.points = pd.read_csv(file, sep=',', header=None).values.tolist()
                    self.rivers.append(r)
        else: 
            print(f"File '{self.river_file}' is empty.")
    
    def set_river(self, river_name, keypoints, river_obj=None): 
        """设置新河流"""
        if not river_obj: 
            r = River(keypoints, name=river_name, delta_length=1/2**self.cut_times)
        else: 
            r = river_obj
        r.save(self.path)
        f = open(self.river_file, 'a')
        name = river_name + '\n'
        f.write(name)
        f.close()
        self.rivers.append(r)
    
    def clear_all_river(self): 
        """清除所有河流"""
        self.rivers = []
        open(self.river_file, 'w').close()
    
    def clear_river(self, *river_names): 
        """清除给定河流，如不给定参数则删除最后一条河流"""
        if not river_names: river_names = (self.rivers[-1].name, )
        for r in self.rivers:
            if r.name in river_names: self.rivers.remove(r)
        rivers = self.rivers
        f = open(self.river_file, 'w')
        for r in rivers:
            river_name = r.name + '\n'
            f.write(river_name)
        f.close()
    
    def change_river(self, river_name=None): 
        """微调河流形状，如不给定参数则微调所有河流"""
        for r in self.rivers: 
            if (not river_name) or (river_name == r.name): 
                r.full_random()
                r.save()
        self.read_rivers()
    
    def __generate_image(self): 
        self.image   = self.__convert2image(self.map)
        self.changed = False
    
    def __convert2image(self, map):
        lst = [self.color_dict[landtype] for landtype in self.index_land_dict.values()]
        if type(map) == np.ndarray: 
            return np.array(np.vectorize(lambda x: lst[x])(map)).transpose(1,2,0)

    def set_figure(self, width=20, dpi=300): 
        """设置图片尺寸和分辨率"""
        self.figsize = (width, width*self.rows/self.cols)
        self.figdpi  = dpi

    def plot(self, 
        which=None, width=None, height=None, dpi=None, 
        title=None, river=True,  city=True, grid=False, save=True): 
        """画地图"""
        if not which: 
            if self.changed: self.__generate_image()
            image = self.image
            if not title: title = self.name + '地图'
        else: 
            if which == '原图': 
                map = self.origin_map
            elif which == '提取': 
                map = self.extract_map
            elif which == '陆地': 
                map = self.map*self.land
            image = self.__convert2image(map)
            if not title: title = f'{self.name}的{which}地图'
        width, height = self.__set_figsize(width, height)
        if not dpi: dpi=self.figdpi
        plt.figure(figsize=(width, height), dpi=dpi)
        fontsize = int(width)
        if fontsize < 10: fontsize = 10
        plt.title(title, fontsize=fontsize)
        plt.imshow(image, extent=self.range, zorder=1)
        if river: self.__plot_river(figwidth=width)
        if city:  self.__plot_city(figwidth=width)
        if grid:  plt.grid()
        if save: 
            name = title + '.png'
            plt.savefig(name)
        plt.show()

    def __set_figsize(self, width, height):
        if (not width) and (not height): 
            width  = self.figsize[0]
            height = self.figsize[1]
        elif width and (not height): 
            height = width*self.rows/self.cols
        elif (not width) and height: 
            width  = height*self.cols/self.rows
        return width, height

    def __plot_city(self, figwidth, city_name=True): 
        if len(self.cities) > 0: 
            location = np.array([c.location for c in self.cities]).T
            plt.scatter(*location, c='m', marker='*', zorder=3)
            fontsize = int(0.5*figwidth)
            if fontsize < 10: fontsize = 10
            for c in self.cities: 
                if city_name: plt.annotate(f'{c.name}', xy=c.location, xytext=c.location, fontsize=fontsize)
    
    def __plot_river(self, figwidth): 
        for r in self.rivers: 
            x = r.points[0]
            y = r.points[1]
            plt.plot(x, y, '#205aa7', lw=0.1*figwidth, zorder=2)
    
    def assign(self, assign, cover=False):
        width = self.figsize[0]
        plt.figure(figsize=self.figsize, dpi=self.figdpi)
        if self.changed: self.__generate_image()
        plt.imshow(self.image, extent=self.range, zorder=1)
        self.__plot_river(figwidth=width)
        self.__plot_city(figwidth=width)
        plt.grid()
        if assign == 'city': 
            title = '点击地图开始创建城市'
            if cover: title += '（注意：点击地图将清空旧的城市数据）'
            plt.title(title, fontsize=width)
            plt.draw()
            plt.waitforbuttonpress()
            plt.title('左键选取，右键取消，回车键确认', fontsize=width)
            plt.draw()
            self.__pick_city(cover)
            self.__plot_city(figwidth=width)
            plt.draw()
        elif assign == 'river': 
            title = '点击地图开始创建河流'
            if cover: title += '（注意：点击地图将清空旧的河流数据）'
            plt.title(title, fontsize=width)
            plt.draw()
            plt.waitforbuttonpress()
            plt.title('请依次点击流经点\n左键选取，右键取消，回车键确认', fontsize=width)
            plt.draw()
            self.__pick_river(cover)
            self.__plot_river(figwidth=width)
            plt.draw()
        plt.title('已绘制完成，如继续绘制请关闭窗口后重新输入命令', fontsize=width)
        plt.draw()
        plt.show()

    def __pick_city(self, cover): 
        if cover: self.clear_all_city()
        lst = plt.ginput(-1, timeout = -1)
        for position in lst: 
            name = self.__default_name('city')
            self.set_city(name, position)
    
    def __pick_river(self, cover): 
        if cover: self.clear_all_river()
        lst    = plt.ginput(-1, timeout = -1)
        points = np.array(lst).T
        name   = self.__default_name('river')
        self.set_river(name, points)

    def __default_name(self,unit):
        if unit == 'city': 
            all_names = [c.name for c in self.cities]
        elif unit == 'river': 
            all_names = [r.name for r in self.rivers]
        new_name = unit + ' 1'
        for i, _ in enumerate(all_names): 
            if new_name not in all_names: break
            new_name = unit + ' ' + str(i+2)
        return new_name
    
    def extract_layer(self, *layer_names, plot=True):
        super().extract_layer(*layer_names)
        if plot: self.plot(which='提取', title=f'地块绘图（包括{layer_names}）')
    
    def polish(self, times=1, assign_plant=True, detail=False, history=True): 
        """自动细化地图"""
        if detail: self.plot(
                title = f'Origin map: (size: {self.rows} x {self.cols})', 
                width = 5, river = False, city = False, save=False
            )
        if assign_plant: 
            self.assign_plant()
            if detail: self.plot(
                title = f'Planted map: (size: {self.rows} x {self.cols})', 
                width = 5, river = False, city = False, save=False
            )
        if history: self.polish_history = {0: self.map}
        for i in range(times): 
            self.refine()
            self.weathering()
            if detail: self.plot(
                title = f'Polish time: {i+1} (size: {self.rows} x {self.cols})', 
                width = 5, river = False, city = False, save=False
            )
            if history: self.polish_history[i+1] = self.map
        self.coastline()
        np.savetxt(self.map_file, self.map, delimiter=', ', fmt='%d')

