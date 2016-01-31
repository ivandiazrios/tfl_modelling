import psycopg2
import os
import numpy as np
from scipy.optimize import leastsq
import matplotlib
matplotlib.use('Agg') # For saving figures over ssh
import matplotlib.pyplot as plt
from collections import defaultdict
import json
from dataManager import DataManager

plot_directory = os.path.join((os.path.dirname(__file__)), 'road_plots')

def get_best_params(df, func, initial):
    popt, _ = leastsq(func, initial, args=(df.speed, df.depth, df.dow, df.hour), maxfev=10000*(len(initial) + 1), ftol=10, xtol=10)
    return popt

def get_statistics(params, plot_func, depth, day, hour, speed):

    preds = []
    # Find MSE and MAE on validation data using best function
    total_sq_error = 0
    total_error = 0

    for v,d in enumerate(depth):
        preds.append(plot_func(params, d, day.iloc[v], hour.iloc[v]))
        diff = preds[v] - speed.iloc[v]
        total_sq_error += diff ** 2
        total_error += np.absolute(diff)
    mse = total_sq_error / len(depth)
    mae = total_error / len(depth)

    return preds, mse, mae

def plot(depths, speeds, predicted_speeds, street, nature):
    plt.figure()
    plt.plot(depths, speeds, 'gx')
    plt.plot(depths, predicted_speeds, 'rx')
    plt.ylim([0,100])
    plt.xlim([0,1.5])
    plt.savefig(os.path.join(plot_directory, "%s_%s" % (street, nature) + ".png"))
    plt.close()

conn = psycopg2.connect(database="tfl", user="tfl", password="tfl", host="127.0.0.1", port=9999)
cur = conn.cursor()

cur.execute("select distinct classification from itn_link where description = 'Motorway';")
motorways = [("classification", m[0].replace("'", "''")) for m in cur.fetchall()]

cur.execute('select distinct street from itn_link;')
streets = [("street", s[0].replace("'", "''")) for s in cur.fetchall()]

natures = [
    "Single Carriageway", "Traffic Island Link", "Dual Carriageway",
    "Roundabout", "Traffic Island Link At Junction", "Slip Road"
]

dM = DataManager()
 
def days_to_binary(day):
    if day == 0 or day == 6:
        return 0
    return 1

def func0(params, speed, rainfall_depth, day, hour):
  p0, e0, p1, e1, p2, e2, c = params
  return p0 * rainfall_depth ** e0 + p1 * day ** e1 + p2 * hour ** e2 + c - speed

def plot_func0(params, rainfall_depth, day, hour):
  p0, e0, p1, e1, p2, e2, c = params
  return p0 * rainfall_depth ** e0 + p1 * day ** e1 + p2 * hour ** e2 + c

def func1(params, speed, rainfall_depth, day, hour):
  p0, p1, e1, p2, e2, p3, e3, c = params
  return p0 * np.exp(p1 * rainfall_depth ** e1 + p2 * hour ** e2) + p3 * day ** e3 + c - speed

def plot_func1(params, rainfall_depth, day, hour):
  p0, p1, e1, p2, e2, p3, e3, c = params
  return p0 * np.exp(p1 * rainfall_depth ** e1 + p2 * hour ** e2) + p3 * day ** e3 + c

def func2(params, speed, rainfall_depth, day, hour):
  p0, e0, p1, e1, p2, p3, p4, p5, c = params
  return p0 * rainfall_depth ** e0 + p1 * day ** e1 + p2 * hour ** 4  + p3 * hour ** 3 + p4 * hour ** 2 + p5 * hour + c - speed

def plot_func2(params, rainfall_depth, day, hour):
  p0, e0, p1, e1, p2, p3, p4, p5, c = params
  return p0 * rainfall_depth ** e0 + p1 * day ** e1 + p2 * hour ** 4  + p3 * hour ** 3 + p4 * hour ** 2 + p5 * hour + c

functions = [
    [func0, plot_func0, np.array([1,1,1,1,1,1,1])],
    [func1, plot_func1, np.array([1,1,1,1,1,1,1,1])],
    [func2, plot_func2, np.array([1,1,1,1,1,1,1,1,1])]
]

def reject_outliers(data, m=2):
    return data[abs(data - np.mean(data)) < m * np.std(data)]

# Overall tracking of best function
best_funcs_nature_tally = defaultdict(lambda: {"function_tally": list(np.zeros(len(functions))), "avg_mse": 0, "avg_mae": 0, "total_count": 0})
best_funcs_tally = {"function_tally": list(np.zeros(len(functions))), "avg_mse": 0, "avg_mae": 0, "total_count": 0}

roads = streets + motorways
total_roads = len(roads)

for i, (column, street) in enumerate(roads):

    print ("%s / %s") % (i, total_roads), street

    training_data = dM.get_data("traffic", "rainfall", [(column, street)], natures, tuple(range(7)), tuple(range(24)))
    validation_data = dM.get_data("traffic_aug13", "rainfall_aug13", [(column, street)], natures, tuple(range(7)), tuple(range(24)))

    street = street.replace("''", "'")

    if not len(training_data) or not len(validation_data):
        continue

    training_data['dow'] = training_data['dow'].apply(days_to_binary)
    validation_data['dow'] = validation_data['dow'].apply(days_to_binary)

    training_grouped = {nature: nature_df for nature, nature_df in training_data.groupby(['nature'])}
    validation_grouped = {nature: nature_df for nature, nature_df in validation_data.groupby(['nature'])}

    street_function_count = list(np.zeros(len(functions)))

    nature_results = {}

    for nature, nature_training in training_grouped.iteritems():

        if nature not in validation_grouped:
            continue

        nature_validation = validation_grouped[nature]

        # Get data for this street of all links with specific nature
        if len(nature_training) >= 3:

            best_mse = -1
            best_func_index = -1

            for i, (func, plot_func, initial) in enumerate(functions):

                print "Function %i" % i

                try:
                    params = get_best_params(nature_training, func, initial)
                except Exception, e:
                    print str(e)
                    print("%s function failed" % street)
                    continue

                predictions, mse, mae = get_statistics(params, plot_func, nature_validation.depth, nature_validation.dow, nature_validation.hour, nature_validation.speed)

                if mse < best_mse or best_mse == -1:
                    best_mse = mse
                    best_mae = mae
                    best_preds = predictions
                    best_popt = params
                    best_func_index = i

            if best_func_index != -1:

                print best_func_index
                # Increment tally for function format with best MSE for this street
                street_function_count[best_func_index] += 1

                best_funcs_nature_tally[nature]["function_tally"][best_func_index] += 1
                best_funcs_nature_tally[nature]["avg_mse"]+= best_mse
                best_funcs_nature_tally[nature]["avg_mae"]+= best_mae
                best_funcs_nature_tally[nature]["total_count"]+= 1

                best_funcs_tally["function_tally"][best_func_index] += 1
                best_funcs_tally["avg_mse"] += best_mse
                best_funcs_tally["avg_mae"] += best_mae
                best_funcs_tally["total_count"]+= 1

                result_data = {
                    "best_function": best_func_index,
                    "parameters": list(best_popt),
                    "mse": best_mse,
                    "mae": best_mae
                }

                try:
                    plot(nature_validation.depth, nature_validation.speed, best_preds, street, nature)
                except Exception, e:
                    print str(e)
                    continue
            else:
                average_speed = nature_validation.speed.mean()
                result_data = {'avg_speed': result_data}

            nature_results[nature] = result_data

    # Analysis for street
    with open("road_data/" + street + ".json", "wb") as f:
        json.dump({"street_tally": street_function_count, "nature_results": nature_results}, f)
        f.close()

    # Analysis for all streets
    with open("./TOTAL_analysis.json", "wb") as f:
            json.dump({"total_tally": best_funcs_tally, "total_nature_tally": best_funcs_nature_tally}, f)
            f.close()

for nature, info_dict in best_funcs_nature_tally.iteritems():
    best_funcs_tally = info_dict["total_count"]
    info_dict["function_percentages"] = [x * 100 / best_funcs_tally for x in info_dict["function_tally"]]
    info_dict["avg_mse"] = info_dict["avg_mse"] / best_funcs_tally
    info_dict["avg_mae"] = info_dict["avg_mae"] / best_funcs_tally

best_funcs_tally = best_funcs_tally["total_count"]
best_funcs_tally["function_percentages"] = [x * 100 / best_funcs_tally for x in best_funcs_tally["function_tally"]]
best_funcs_tally["avg_mse"] = best_funcs_tally["avg_mse"] / best_funcs_tally
best_funcs_tally["avg_mae"] = best_funcs_tally["avg_mae"] / best_funcs_tally

with open("stats.json", "a") as f:
    json.dump(best_funcs_nature_tally, f)
    json.dump(best_funcs_tally, f)
    f.close()
