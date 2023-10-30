from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime
import mysql.connector
from mysql.connector import FieldType
import connect

import pandas as pd

app = Flask(__name__)

dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, \
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn

# This function is used to get the list of drivers for the dropdown list
def getDrivers():
    connection = getCursor()
    connection.execute(
        """ 
        SELECT d.driver_id, d.surname, d.first_name, d.date_of_birth, d.age, d.caregiver, c.model, c.drive_class
        FROM driver d
        LEFT JOIN car c
        ON d.car = c.car_num
        ORDER BY d.surname, d.first_name;""")
    driverDetail = connection.fetchall()
    return driverDetail


@app.route("/")
def home():
    return render_template("base.html")

@app.route("/listruns/", methods=["GET", "POST"])
def listruns():
    drivers = getDrivers()
    runList = None
    selected_driver_id = request.form.get("driver") or request.args.get('selected_driver_id')
    # make sure the selected driver id is an integer
    try:
        selected_driver_id=int(selected_driver_id)
    except:
        selected_driver_id=None
    # if the user has selected a driver, get the runs for that driver
    if request.method == 'POST' or selected_driver_id is not None:
        connection = getCursor()
        connection.execute(
            """
            SELECT d.driver_id, CONCAT(d.first_name,' ', d.surname) AS driver_name,
                c.name AS course, r.run_num, r.seconds, r.cones, r.wd, 
                round(r.seconds+5*IFNULL(r.cones, 0)+10*r.wd,2) AS run_total, 
                car.model, car.drive_class
            FROM driver d
            LEFT JOIN run r ON d.driver_id = r.dr_id
            LEFT JOIN course c ON c.course_id = r.crs_id
            LEFT JOIN car car ON car.car_num = d.car
            WHERE d.driver_id = %s
            ORDER BY c.name, r.run_num""", (selected_driver_id,))
        runList = connection.fetchall()
    return render_template("runlist.html", drivers=drivers, run_list=runList, selected_driver_id=selected_driver_id)


@app.route("/listdrivers")
def listdrivers():
    driverList = getDrivers()
    return render_template("driverlist.html", driver_list = driverList)


@app.route("/listcourses")
def listcourses():
    connection = getCursor()
    connection.execute("SELECT * FROM course;")
    courseList = connection.fetchall()
    return render_template("courselist.html", course_list = courseList)

@app.route("/listoverall")
def listoverall():
    connection = getCursor()
    valid_result = """
        SELECT driver_id, driver_name, age, course, course_time, model, overall_result,
            DENSE_RANK() OVER(ORDER BY overall_result) AS rank_num
        FROM (
        SELECT d.driver_id, CONCAT(d.first_name,' ', d.surname) AS driver_name, d.age,
            c.name AS course, MIN(round(r.seconds+5*IFNULL(r.cones, 0)+10*r.wd,2)) AS course_time,
            car.model, 
            ROUND(SUM(MIN(round(r.seconds+5*IFNULL(r.cones, 0)+10*r.wd,2))) OVER(PARTITION BY d.driver_id),2) AS overall_result
        FROM driver d
        LEFT JOIN run r ON d.driver_id = r.dr_id
        LEFT JOIN course c ON c.course_id = r.crs_id
        LEFT JOIN car car ON car.car_num = d.car
        WHERE d.driver_id NOT IN (
            SELECT driver_id FROM (
                SELECT d.driver_id, CONCAT(d.first_name,' ', d.surname) AS driver_name, 
                    c.name AS course, MIN(round(r.seconds+5*IFNULL(r.cones, 0)+10*r.wd,2)) AS course_time
                FROM driver d
                LEFT JOIN run r ON d.driver_id = r.dr_id
                LEFT JOIN course c ON c.course_id = r.crs_id
                LEFT JOIN car car ON car.car_num = d.car
                GROUP BY d.driver_id, driver_name, course
                HAVING course_time IS NULL
            ) t1
        )
        GROUP BY d.driver_id, driver_name, course) t2
        ORDER BY overall_result, course;
    """
    connection.execute(valid_result)
    overallList = connection.fetchall()
    # Create a DataFrame from the list of tuples
    overall_columns = ['driver_id', 'driver_name', 'age', 'course', 'course_time', 'model', 'overall_result', 'rank_num']
    overallList = pd.DataFrame(overallList, columns=overall_columns)
    # Group the DataFrame by 'ID' and aggregate other columns as 'first' and 'list' respectively
    grouped = overallList.groupby('driver_id').agg({
        'driver_name': 'first',
        'age': 'first',
        'course_time': list,
        'model': 'first',
        'overall_result': 'first',
        'rank_num': 'first'
    }).reset_index()
    # Create new columns for each course
    for i in range(6):
        grouped[f'course_{i+1}'] = grouped['course_time'].apply(lambda x: x[i] if i < len(x) else None)
    # Drop the original 'Course Time' column
    grouped.drop(columns=['course_time'], inplace=True)
    # Sort rows by 'Overall Time' in ascending order
    grouped.sort_values(by='overall_result', ascending=True, inplace=True)
    # Convert 'Age' column to integers
    grouped['age'] = grouped['age'].astype(float).fillna(0).astype(int)
    # Convert the DataFrame to a list of dictionaries
    overallList = grouped.to_dict(orient='records')
    # Query NQ drivers course details
    nq_result = """
        SELECT d.driver_id, CONCAT(d.first_name,' ', d.surname) AS driver_name, d.age,
        c.name AS course, MIN(round(r.seconds+5*IFNULL(r.cones, 0)+10*r.wd,2)) AS run_total,
        car.model
        FROM driver d
        LEFT JOIN run r ON d.driver_id = r.dr_id
        LEFT JOIN course c ON c.course_id = r.crs_id
        LEFT JOIN car car ON car.car_num = d.car
        WHERE d.driver_id IN (
            SELECT driver_id FROM (
                SELECT d.driver_id, CONCAT(d.first_name,' ', d.surname) AS driver_name, 
                    c.name AS course, MIN(round(r.seconds+5*IFNULL(r.cones, 0)+10*r.wd,2)) AS run_total
                FROM driver d
                LEFT JOIN run r ON d.driver_id = r.dr_id
                LEFT JOIN course c ON c.course_id = r.crs_id
                LEFT JOIN car car ON car.car_num = d.car
                GROUP BY d.driver_id, driver_name, course
                HAVING run_total IS NULL
            ) t1
        )
        GROUP BY d.driver_id, driver_name, course
        ORDER BY driver_id,run_total;"""
    connection.execute(nq_result)
    nqlist = connection.fetchall()
    # Do the same as valid drivers
    nqlist = pd.DataFrame(nqlist, columns=['driver_id', 'driver_name', 'age', 'course', 'course_time', 'model'])
    grouped = nqlist.groupby('driver_id').agg({
        'driver_name': 'first',
        'age': 'first',
        'course_time': list,
        'model': 'first'
    }).reset_index()

    for i in range(6):
        grouped[f'course_{i+1}'] = grouped['course_time'].apply(lambda x: x[i] if i < len(x) else None)

    grouped.drop(columns=['course_time'], inplace=True)
    grouped['age'] = grouped['age'].astype(float).fillna(0).astype(int)
    nqlist = grouped.to_dict(orient='records')
    # Return the list of valid drivers and NQ drivers
    return render_template("overall.html", overall_list = overallList,nq_list = nqlist)

@app.route("/graph")
def showgraph():
    connection = getCursor()
    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '

    return render_template("top5graph.html", name_list = bestDriverList, value_list = resultsList)

