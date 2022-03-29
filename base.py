from mapmaker import Map


# 在地图上选取城市和河流
m = Map(seed=1586, name='随机大陆')
m.polish(3)
m.assign('city')
m.assign('river')
m.plot()