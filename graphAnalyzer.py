from Tkinter import Tk, Label, Button, Frame, Listbox, MULTIPLE, END, IntVar, Entry, Checkbutton, NE, CENTER, Text
from collections import namedtuple
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd

from dataManager import DataManager

class GraphAnalyzer(Frame):

    def __init__(self, root):
        Frame.__init__(self, root)
        self.__root = root
        self.__data_manager = DataManager()
        self.__check_button_type = namedtuple('CheckButtonType', 'widget var')

        self.__natures = [
            "Single Carriageway", "Traffic Island Link", "Dual Carriageway",
            "Roundabout", "Traffic Island Link At Junction", "Slip Road"
        ]

        self.__roads = [
            "M3","M40","M4","A1(M)","M11","M23","M20","M25","M1","HIGH STREET",
            "LONDON ROAD","HIGH ROAD","UXBRIDGE ROAD","STATION ROAD",
            "BRIGHTON ROAD","GREEN LANES","FINCHLEY ROAD","HARROW ROAD",
            "NORTH CIRCULAR ROAD","KINGSTON ROAD","PORTSMOUTH ROAD","HERTFORD ROAD",
            "STAINES ROAD","CROYDON ROAD","MAIN ROAD","CHURCH ROAD","PARK ROAD"
        ]

        self.__motorways = ["M3","M40","M4","A1(M)","M11","M23","M20","M25","M1"]

        self.__init_grid()
        self.__draw_grid()

    def __init_grid(self):

        # Road list
        self.__roads_list_box = Listbox(self.__root, selectmode=MULTIPLE, height=27, exportselection=0)
        for road in self.__roads:
            self.__roads_list_box.insert('end', road)

        # Nature list
        self.__natures_list_box = Listbox(self.__root, selectmode=MULTIPLE, height=6, width=22, exportselection=0)
        for nature in self.__natures:
            self.__natures_list_box.insert('end', nature)

        # Start with all natures selected
        self.__natures_list_box.select_set(0, END)\

        # Days list
        self.__days_list_box = Listbox(self.__root, selectmode=MULTIPLE, height=8, width=22, exportselection=0)
        for day in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            self.__days_list_box.insert('end', day)

        # Hours list
        self.__hours_list_box = Listbox(self.__root, selectmode=MULTIPLE, height=24, width=7, exportselection=0)
        for hour in range(24):
            self.__hours_list_box.insert('end', hour)

        # Check button draw overall
        self.__draw_overall_var = IntVar()
        self.__draw_overall_check_box = \
            Checkbutton(self.__root, text = "Draw Overall Curve?",
                        variable = self.__draw_overall_var, onvalue = 1,
                        offvalue = 0, height=2, width = 20)

        # Check button draw nature
        self.__draw_nature_var = IntVar()
        self.__draw_nature_check_box = \
            Checkbutton(self.__root, text = "Draw Curve Per Nature?",
                        variable = self.__draw_nature_var, onvalue = 1,
                        offvalue = 0, height=2, width = 20)

        # Check button show data
        self.__show_data_var = IntVar()
        self.__show_data_var.set(1)
        self.__show_data_check_box = \
            Checkbutton(self.__root, text = "Show data?",
                        variable = self.__show_data_var, onvalue = 1,
                        offvalue = 0, height=2, width = 20)

        # Go button
        self.__go_button = Button(self.__root, text='GO', command = lambda: self.__generate_graph())

        # Errors text box
        self.__error_text_box = Text(self.__root, height=28, width=18, fg="red")
        self.__error_text_box.tag_config('justified', justify=CENTER)

    def __draw_grid(self):

        # Roads label and list box
        Label(self.__root, text="Roads", justify=CENTER).grid(row=0, column=0)
        self.__roads_list_box.grid(row=1, column=0, rowspan=27)

        # Natures label and list box
        Label(self.__root, text="Natures", justify=CENTER).grid(row=0, column=1)
        self.__natures_list_box.grid(row=1, column=1, rowspan=6)

        # Days label and list box
        Label(self.__root, text="Days", justify=CENTER).grid(row=7, column=1)
        self.__days_list_box.grid(row=8, column=1, rowspan=8)

        # Hours label and list box
        Label(self.__root, text="Hours", justify=CENTER).grid(row=0, column=3)
        self.__hours_list_box.grid(row=1, column=3, rowspan=24)

        # Check boxes
        Label(self.__root, text="Drawing Options", justify=CENTER).grid(row=0, column=4)
        self.__draw_overall_check_box.grid(row=1, column=4, rowspan=2)
        self.__draw_nature_check_box.grid(row=3, column=4, rowspan=2)
        self.__show_data_check_box.grid(row=5, column=4, rowspan=2)

        # Go button
        self.__go_button.grid(row=10, column=4)

        # Error Column
        Label(self.__root, text="Error Report", height=1, width=18, justify=CENTER).grid(row=0, column=5)
        self.__error_text_box.grid(row=1, column=5, rowspan=28)



    def __generate_graph(self):

        # Get parameters
        roads = tuple(self.__roads_list_box.get(road_index) for road_index in self.__roads_list_box.curselection())
        roads = [ ("classification" if road in self.__motorways else "street", road) for road in roads]

        natures = tuple(self.__natures_list_box.get(nature_index) for nature_index in self.__natures_list_box.curselection())
        days = self.__days_list_box.curselection()
        hours = self.__hours_list_box.curselection()

        errors = self.__error_check(roads, natures, days, hours)

        if len(errors):
            self.__error_text_box.delete("1.0",END)
            for e in errors:
                self.__error_text_box.insert(END, e + '\n', 'justified')
        else:
            data = self.__data_manager.get_data("traffic", "rainfall", roads, natures, hours, days)
            self.__plot_data(data)

    def __error_check(self, roads, natures, hours, days):

        errors = []

        if not len(roads):
            errors.append("No roads selected")
        if not len(natures):
            errors.append("No natures selected")
        if not len(hours):
            errors.append("No hours selected")
        if not len(days):
            errors.append("No days selected")
        if not (self.__show_data_var.get() or
                    self.__draw_nature_var.get() or
                    self.__draw_overall_var.get()):
            errors.append("Nothing to draw")

        return errors


    def __plot_data(self, data):

        max_depth = data.depth.max()
        max_speed = data.speed.max()

        dfs_to_plot = []

        if self.__show_data_var.get():
            dfs_to_plot.append(data)

        if self.__draw_overall_var.get():
            dfs_to_plot.append(self.__get_best_fit_curve(data, max_depth, max_speed, "Best fit curve"))

        if self.__draw_nature_var.get():
            for nature, nature_df in data.groupby(['nature']):
                dfs_to_plot.append(self.__get_best_fit_curve(nature_df, max_depth, max_speed, nature))

        data = pd.concat(dfs_to_plot, ignore_index=True)

        fg = sns.FacetGrid(data=data, hue='nature', aspect=1.9, legend_out=False, size=8)

        fg.map(plt.scatter, 'depth', 'speed', s=20).add_legend(None, "Legend")
        axes = fg.axes


        ylim = 120 if max_speed > 200 else max_speed
        xlim = 1.0 if max_depth < 1.0 else 2.0

        axes[0,0].set_ylim(0,ylim)
        axes[0,0].set_xlim(0,xlim)

        sns.plt.show()


    def __get_best_fit_curve(self, data, max_depth, max_speed, nature_str):

        try:
            popt, pcov = curve_fit(self.curve_func, data.depth, data.speed)
        except RuntimeError:
            return pd.DataFrame({'depth':[], 'speed':[], 'nature':[], 'identifier':[]})

        a = popt[0]
        b = popt[1]
        c = popt[2]

        depths = list(np.arange(0, max_depth, max_depth/10000.0))
        speeds = map(lambda x: self.curve_func(x, a, b, c), depths)

        if max(speeds) > max_speed:
            speeds = [s for s in speeds if s <= max_speed]
            depths = depths[0:len(speeds)]

        natures = [nature_str] * len(depths)
        identifiers = [''] * len(depths)

        return pd.DataFrame({'depth':depths, 'speed':speeds, 'nature':natures, 'identifier':identifiers})

    def curve_func(self, x, a, b, c):
        return a * np.exp(-b * x) + c

if __name__ == '__main__':
    root = Tk()
    root.resizable(width=False, height=False)
    root.geometry("800x482+300+300")
    GraphAnalyzer(root)
    root.mainloop()

