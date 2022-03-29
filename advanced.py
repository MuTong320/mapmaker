from mapmaker import AltitudeMap, Map


p = AltitudeMap(
        name='s7777', seed=7777,
        land_level=0.5, sea_level=0.2, noise_level=0.5, 
        continent_number=3, slope=5, width_range=(0.25,0.75), height_range=(0.25,0.75),
        perlin_cells=(20,10), 
        longtitude_range=200, latitude_range=80, resolution=1
)

m = Map(p, name='多块大陆', seed='2222')
m.polish(3)
#m.assign('city')
#m.assign('river')

m.plot(title='MapMaker: 制作幻想世界的随机地图', axis=False)