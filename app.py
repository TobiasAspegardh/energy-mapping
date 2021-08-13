# 
import pandas as pd
import colorcet, param as pm, holoviews as hv, panel as pn, datashader as ds
import datetime as datetime

# Holoviews imports
from holoviews.element import tiles as hvts
from holoviews.operation.datashader import rasterize, shade, spread
from holoviews.operation import histogram
from collections import OrderedDict as odict

# Local imports 
from data import get_data

hv.extension('bokeh', logo=False)
pn.extension(template='bootstrap', theme='dark')

# Get data
df = get_data()

# Create a truck-list and append "All" as alternative
truck_list = df['truck'].unique().tolist() 
truck_list.append('All')

# Cmaps alternatives  
cmaps  = odict([(n,colorcet.palette[n]) for n in ['fire', 'bgy', 'bgyw', 'bmy', 'gray', 'kbc']])

# Maps alternatives
maps = ['EsriImagery', 'EsriUSATopo', 'EsriTerrain', 'CartoDark', 'StamenWatercolor', 'StamenTonerBackground']
bases  = odict([(name, getattr(hvts, name)().relabel(name)) for name in maps])

# Date alternatives
df['date_time'] = pd.to_datetime(df['date_time'], format='%Y-%m-%d %H:%M:%S.%f')
min_date = df['date_time'].min().date()
max_date = df['date_time'].max().date()

# Aggregations alternatives
aggfns = odict([(f.capitalize(),getattr(ds,f)) for f in ['count','sum','min','max','mean','var','std']])

# Normalization alternatives
norms  = odict(Histogram_Equalization='eq_hist', Linear='linear', Log='log', Cube_root='cbrt')

class Mapping(pm.Parameterized):

    # Date selection
    start_date = pm.Date(min_date, bounds=(min_date, max_date))
    end_date = pm.Date(max_date, bounds=(min_date, max_date))

    # Truck selection
    truck = pm.Selector(truck_list, 'All')
    
    # Energy over selection
    energy_over = pm.Number(0, bounds=(min(df['kWh_km']),max(df['kWh_km'])), step=0.2, doc='kWh/km over')
    
    # Aggregation function
    agg_fn = pm.Selector(aggfns)

    # Normalization selection
    normalization = pm.Selector(norms)
    
    # Spreading selection
    spreading = pm.Integer(0, bounds=(0, 5))

    # Cmap selection
    cmap = pm.Selector(cmaps)
    
    # Map styles selection
    basemap = pm.Selector(bases)

    # Data opacity selection
    data_opacity  = pm.Magnitude(1.00)
    
    # Activate map style selector
    @pm.depends('basemap')
    def tiles(self):
        return self.basemap.opts(width=800, height=600)

    # Set aggregator (can be changed with more alternatives)
    @pm.depends('agg_fn')
    def aggregator(self):
        field = 'kWh_km'
        return self.agg_fn(field)

    # Filter data based on alternatives
    @pm.depends('truck', 'kWh_km', 'start_date', 'end_date')
    def filter_data(self):
        # Data
        data_selected = df.copy()
        if self.truck != 'All':
            data_selected = data_selected[data_selected['truck'] == self.truck]
        # Energy consumption filter
        data_selected = data_selected[data_selected['kWh_km'] > self.energy_over]
        # Date filter
        data_selected = data_selected[data_selected['date_time'].dt.date > self.start_date]
        data_selected = data_selected[data_selected['date_time'].dt.date < self.end_date]
        return data_selected

    #Defining the plot 
    def plot(self, **kwargs):
        data_selected = self.filter_data()        
        # Build map element
        # Points for plotting
        points     = hv.Points(data_selected, ["easting", "northing"])
        # Rasterize points with aggregator 
        rasterized = rasterize(hv.DynamicMap(points), aggregator=self.aggregator)
        shaded     = shade(rasterized, cmap=self.param.cmap, normalization=self.param.normalization)
        spreaded   = spread(shaded, how="add", px=self.param.spreading)
        dataplot   = spreaded.apply.opts(alpha=self.param.data_opacity, show_legend=True)
        map_plot   = hv.DynamicMap(self.tiles) * dataplot
        # Build histogram element
        dataset = hv.Dataset(data_selected)
        hist = histogram(dataset, dimension="kWh_km", normed=False).opts(color='blue', title = 'kWh/km')
        # Build pane of total CO2 saved element
        selected_energy = sum(data_selected["sum_kWh"])
        total_energy = sum(df["sum_kWh"])
        data = [('Total',total_energy),('Selected',selected_energy)]
        bar = hv.Bars(data, hv.Dimension('test'), 'kWh').opts(color='red', title='Total energy consumed')
        panel = pn.Row(map_plot, pn.Column(hist, bar))
        return panel

# Panel
dashboard = Mapping(name="")
# Theme and template 
bootstrap = pn.template.BootstrapTemplate(title='Einride mapping', theme='dark')
# Sidebar
sidebar_layout = pn.panel(dashboard.param, widgets = {"start_date":pn.widgets.DatePicker, "end_date":pn.widgets.DatePicker })
bootstrap.sidebar.append(sidebar_layout)
# Main page
bootstrap.main.append(dashboard.plot)
# Run it
bootstrap.servable()
bootstrap.show()
