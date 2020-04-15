import json
import pandas as pd
import requests
import PySimpleGUI as sg
import os
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')
import plotly.express as px

# Covid-19 API
SUMMARY = 'https://api.covid19api.com/summary'
COUNTRY = 'https://api.covid19api.com/dayone/country/'

APP_NAME = 'Covid-19 Python'

# Possible themes for GUI
THEME = ['Green', 'GreenTan', 'LightGreen', 'BluePurple', 'Purple',
             'BlueMono', 'GreenMono', 'BrownBlue', 'BrightColors',
             'NeutralBlue', 'Kayak', 'SandyBeach', 'TealMono', 'Topanga',
             'Dark', 'Black', 'DarkAmber']

# Title bar menu layout
menu = [
    ['&Theme', THEME],
    ['&Help', ['About']],
]

ABOUT_MSG = '''
Calax COVID-19 1.0

You can track Covid-19-Italy spread day by day.

Made by Calax
Credits to Covid-19 API
2020
'''

class COVID_GUI:

    def __init__(self, theme):

        """
        Main class representing GUI, logic, view and controller
        :param theme:
        """

        self.theme = theme
        self.world_data = {}
        self.country_data= {}
        self.actual_country = ''
        self.cases = []
        self.number = []
        self.menu = []

        self.gui_theme = 'BrownBlue'

    def analyze_country(self, window, country):

        """
        Creates chosen country spread graph layout and window
        :param window:
        :param country:
        :return:
        """

        sg.ChangeLookAndFeel(self.gui_theme)
        sg.SetOptions(margins=(0, 3), border_width=1)
        loc = window.CurrentLocation()

        menu_elem = sg.Menu(menu, tearoff=False)

        plt.close()

        m = 0

        r = requests.get(COUNTRY + country + '/status/confirmed')

        country_data = r.json()

        for i in range(len(country_data)):

            self.cases.append([country_data[i]['Cases'], country_data[i]['Date']])

        for i in range(len(self.cases)):

            element = self.cases[i]
            self.number.append(element[0])

        plt.plot(self.number, label = country)
        m = max([m, max(self.number)])

        plt.title(f'{country} spread')
        plt.ylabel('Cases')
        plt.xlabel('Days')
        plt.ylim([0, 1.1*m])
        plt.legend(loc = 'lower right', fontsize = 8)
        plt.grid()

        fig = plt.gcf()

        figure_x, figure_y, figure_w, figure_h = fig.bbox.bounds

        graph_layout = [

            [menu_elem],
            [sg.Canvas(size=(figure_w, figure_h), key ='-CANVAS-')],
            [sg.Button('Back')]

             ]

        w = sg.Window('{}'.format(APP_NAME),
                    graph_layout,
                    default_button_element_size=(12, 1),
                    auto_size_buttons=False,
                    location=(loc[0], loc[1]), force_toplevel=True, finalize=True)

        self.draw_figure(w['-CANVAS-'].TKCanvas, fig)

        window.Close()
        self.cases.clear()
        self.number.clear()
        return w

    def draw_figure(self, canvas, figure):

        """
        Draws/adds the figure in the canvas element of a window
        :param canvas:
        :param figure:
        :return:
        """

        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

    def handle_map(self, json_data):

        """
        Generates choropleth spread map from GeoJSON file and world Covid-19 data
        :param json_data:
        :return:
        """

        data = json_data['Countries']

        with open(os.getcwd() + '/Covid-19-World/countries.json', 'w') as h:
            json.dump(data, h, indent=4)

        df = pd.read_json(os.getcwd() + '/Covid-19-World/countries.json')
        df.to_csv()

        df.head()

        df.drop(columns=['CountryCode', 'Slug', 'NewConfirmed', 'NewDeaths', 'TotalDeaths', 'NewRecovered', 'TotalRecovered'], axis=1, inplace=True)

        df = df.rename(columns={'TotalConfirmed': 'Total Cases'})

        df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d")
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

        with open(os.getcwd() + '/Covid-19-World/custom.geojson') as f:
            d = json.load(f)

        fig = px.choropleth(df, geojson=d, locations='Country',
                    color='Total Cases',
                    color_continuous_scale='Reds',
                    featureidkey='properties.geounit')

        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.update_geos(fitbounds="locations", visible=False)
        fig.show()

    def create_main_window(self, window):

        """
        Creates main page layout
        :param window:
        :return:
        """

        loc = window.CurrentLocation()

        layout = self.build_main_layout(self.world_data)

        w = sg.Window('{}'.format(APP_NAME),
        layout,
        default_button_element_size=(12, 1),
        auto_size_buttons=False,
        location=(loc[0], loc[1]))

        window.Close()
        return w

    def create_country_window(self, window, json_data, country):

        """
        Creates new window for chosen country
        :param window:
        :param json_data:
        :param country:
        :return:
        """

        loc = window.CurrentLocation()

        layout = self.build_country_layout(json_data, country)

        w = sg.Window('{}'.format(APP_NAME),
        layout,
        default_button_element_size=(12, 1),
        auto_size_buttons=False,
        location=(loc[0], loc[1]))

        window.Close()
        return w

    def create_chart_window(self, window, json_data):

        """
        Creates the sorted chart of single countries by total cases
        :param window:
        :param json_data:
        :return:
        """

        loc = window.CurrentLocation()

        layout = self.build_chart_layout(json_data)

        w = sg.Window('{}'.format(APP_NAME),
        layout,
        default_button_element_size=(12, 1),
        auto_size_buttons=False,
        location=(loc[0], loc[1]), size=(1050,600))

        window.Close()
        return w

    def convert_date(self, date):

        """
        Converts json date to another form
        :param date:
        :return:
        """

        data = date[0:10]
        hour = date[11:16]

        return data, hour

    def country_chart(self, i, json_data):

        """
        Represents a single row for the world chart
        :param i:
        :param json_data:
        :return:
        """

        return [sg.Text(json_data[i]['Country'], font= 'Courier 20', size=(50,1)), sg.Text(json_data[i]['TotalConfirmed'], font= 'Courier 20', size=(7,1)), sg.Text(json_data[i]['TotalDeaths'], font= 'Courier 20', size=(7,1)), sg.Text(json_data[i]['TotalRecovered'], font= 'Courier 20', size=(10,1))]

    def build_chart_layout(self, json_data):

        """
        Creates chart window layout
        :param json_data:
        :return:
        """

        sg.ChangeLookAndFeel(self.gui_theme)
        sg.SetOptions(margins=(0, 3), border_width=1)

        menu_elem = sg.Menu(menu, tearoff=False)

        for i in range(len(json_data['Countries'])):

            max = i

            for k in range(i+1, len(json_data['Countries'])):

                if json_data['Countries'][k]['TotalConfirmed'] > json_data['Countries'][max]['TotalConfirmed']:

                    max = k

            temp = json_data['Countries'][max]['Country']
            temp1 = json_data['Countries'][max]['TotalConfirmed']
            temp2 = json_data['Countries'][max]['TotalDeaths']
            temp3 = json_data['Countries'][max]['TotalRecovered']
            json_data['Countries'][max]['Country'] = json_data['Countries'][i]['Country']
            json_data['Countries'][max]['TotalConfirmed'] = json_data['Countries'][i]['TotalConfirmed']
            json_data['Countries'][max]['TotalDeaths'] = json_data['Countries'][i]['TotalDeaths']
            json_data['Countries'][max]['TotalRecovered'] = json_data['Countries'][i]['TotalRecovered']
            json_data['Countries'][i]['Country'] = temp
            json_data['Countries'][i]['TotalConfirmed'] = temp1
            json_data['Countries'][i]['TotalDeaths'] = temp2
            json_data['Countries'][i]['TotalRecovered'] = temp3

        title = [[sg.Text('Country', font='Courier 20', size=(50,1)), sg.Text('Cases', font='Courier 20', size=(7,1)), sg.Text('Deaths', font='Courier 20', size=(7,1)), sg.Text('Recovered', font='Courier 20', size=(10,1))]]

        chart_layout = title + [self.country_chart(x, json_data['Countries']) for x in range(0, len(json_data['Countries']))] + [[sg.Button('Ok')]]

        layout = [
            [menu_elem],
            [sg.Column(chart_layout, key='-COL1-', scrollable=True)]
                             ]

        return layout

    def build_country_layout(self, json_data, country):

        """
        Creates chosen country layout
        :param json_data:
        :param country:
        :return:
        """

        sg.ChangeLookAndFeel(self.gui_theme)
        sg.SetOptions(margins=(0, 3), border_width=1)

        menu_elem = sg.Menu(menu, tearoff=False)

        data = json_data['Countries']

        for i in range(len(data)):

            if data[i]['Country'] == country:

                date, hour = self.convert_date(data[i]['Date'])

                country_layout = [
                                     [sg.Text(data[i]['Country'], font='Courier 30'), sg.Text(' (updated at ' + hour + ' of ' + date + ')', font = 'Courier 14')],
                                     [sg.Text('')],
                                     [sg.Text('Total confirmed cases', font='Courier 20')],
                                     [sg.Text(data[i]['TotalConfirmed'], font='Courier 15')],
                                     [sg.Text('Total deaths', font='Courier 20')],
                                     [sg.Text(data[i]['TotalDeaths'], font='Courier 15')],
                                     [sg.Text('Total recovered', font='Courier 20')],
                                     [sg.Text(data[i]['TotalRecovered'], font='Courier 15')],
                                     [sg.Text('New confirmed cases', font='Courier 20')],
                                     [sg.Text(data[i]['NewConfirmed'], font='Courier 15')],
                                     [sg.Text('New confirmed deaths', font='Courier 20')],
                                     [sg.Text(data[i]['NewDeaths'], font='Courier 15')],
                                     [sg.Text('New recovered', font='Courier 20')],
                                     [sg.Text(data[i]['NewRecovered'], font='Courier 15')],
                                     [sg.Button('Back'), sg.Button('Show graph')]]

                layout = [[menu_elem],
                             [sg.Column(country_layout, key='-COL1-')]
                             ]

                return layout

    def build_main_layout(self, json_data):

         """
         Creates main page layout
         :param json_data:
         :return:
         """

         sg.ChangeLookAndFeel(self.gui_theme)
         sg.SetOptions(margins=(0, 3), border_width=1)

         menu_elem = sg.Menu(menu, tearoff=False)

         countries = []

         country = json_data['Countries']

         for i in range(len(country)):

            countries.append(country[i]['Country'])

         date, hour = self.convert_date(json_data['Date'])

         world_layout = [
                             [sg.Text('World', font='Courier 30'), sg.Text(' (updated at ' + hour + ' of ' + date + ')', font = 'Courier 14')],
                             [sg.Text('')],
                             [sg.Text('Total confirmed cases', font='Courier 20') ],
                             [sg.Text(json_data['Global']['TotalConfirmed'], font='Courier 15')],
                             [sg.Text('Total deaths', font='Courier 20')],
                             [sg.Text(json_data['Global']['TotalDeaths'], font='Courier 15')],
                             [sg.Text('Total recovered', font='Courier 20')],
                             [sg.Text(json_data['Global']['TotalRecovered'], font='Courier 15')],
                             [sg.Text('New confirmed cases', font='Courier 20')],
                             [sg.Text(json_data['Global']['NewConfirmed'], font='Courier 15')],
                             [sg.Text('New confirmed deaths', font='Courier 20')],
                             [sg.Text(json_data['Global']['NewDeaths'], font = 'Courier 15')],
                             [sg.Text('New recovered', font='Courier 20')],
                             [sg.Text(json_data['Global']['NewRecovered'], font='Courier 15')],
                             [sg.Text('')],
                             [sg.Text('Look for a country', font='Courier 20'), sg.InputCombo(countries)],
                             [sg.Button('Search'), sg.Button('Chart'), sg.Button('Global Map')]
             ]

         layout = [ [menu_elem],
                    [sg.Column(world_layout, key='-COL1-')]
                         ]



         return layout

    def check_user_interaction(self, window, country = False, main = False, graph = False, chart = False):

        """
        Converts user interaction with windows in behaviours
        :param window:
        :param signin:
        :param search:
        :param title:
        :param login:
        :param watchlist:
        :param wantlist:
        :param main:
        :param profile:
        :return:
        """

        if chart == True:

            while True:

                button, values = window.read()

                if button == 'About':
                    sg.PopupScrolled(ABOUT_MSG, title='Help/About')
                    continue

                if button is None:

                    window.Close()
                    break

                if button in THEME:
                    self.gui_theme = button
                    window = self.create_chart_window(window, self.world_data)
                    continue

                if button == 'Ok':

                    window = self.create_main_window(window)
                    self.check_user_interaction(window, main = True)

        if graph == True:

            while True:

                button, values = window.read()

                if button == 'About':
                    sg.PopupScrolled(ABOUT_MSG, title='Help/About')
                    continue

                if button is None:

                    window.Close()
                    break

                if button in THEME:
                    self.gui_theme = button
                    window = self.analyze_country(window, self.actual_country)
                    continue

                if button == 'Back':

                    window = self.create_country_window(window, self.world_data, self.actual_country)
                    self.check_user_interaction(window, country= True)


        if country == True:

            while True:

                button, values = window.read()

                if button == 'About':
                    sg.PopupScrolled(ABOUT_MSG, title='Help/About')
                    continue

                if button is None:

                    window.Close()
                    break

                if button in THEME:
                    self.gui_theme = button
                    window = self.create_country_window(window, self.world_data, self.actual_country)
                    continue

                if button == 'Back':

                    window = self.create_main_window(window)
                    self.check_user_interaction(window, main= True)

                if button == 'Show graph':

                    window = self.analyze_country(window, self.actual_country)
                    self.check_user_interaction(window, graph= True)

        if main == True:

            while True:

                button, values = window.read()

                if button == 'About':
                    sg.PopupScrolled(ABOUT_MSG, title='Help/About')
                    continue

                if button is None:

                    window.Close()
                    break

                if button in THEME:
                    self.gui_theme = button
                    window = self.create_main_window(window)
                    continue


                if button == 'Search':

                    self.actual_country = str(values[1])

                    window = self.create_country_window(window, self.world_data, self.actual_country)
                    self.check_user_interaction(window,country= True)


                if button == 'Chart':

                    actual_data = self.world_data

                    window = self.create_chart_window(window, actual_data)
                    self.check_user_interaction(window, chart=True)

                if button == 'Global Map':

                    self.handle_map(self.world_data)
                    continue


    def mainPage(self):

        """
        Defines the first window user will see
        :return:
        """

        s = requests.get(SUMMARY)
        self.world_data = s.json()

        layout = self.build_main_layout(self.world_data)

        window = sg.Window('{}'.format(APP_NAME),
                               layout, default_button_element_size=(12, 1),
                               auto_size_buttons=False)

        self.check_user_interaction(window, main = True)


def main():

    theme = 'BrownBlue'

    imdb = COVID_GUI(theme)

    imdb.mainPage()


if __name__ == "__main__":

    main()

