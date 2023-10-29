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

    try:
        selected_driver_id=int(selected_driver_id)
    except:
        selected_driver_id=None
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
            DENSE_RANK() OVER(ORDER BY driver_id) AS rank_num
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
        GROUP BY d.driver_id, driver_name, course
        ORDER BY overall_result, course_time) t2;
    """
    connection.execute(valid_result)
    courseList = connection.fetchall()

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
    
    return render_template("overall.html", overall_list = courseList,nq_list = nqlist)

@app.route("/graph")
def showgraph():
    connection = getCursor()
    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '

    return render_template("top5graph.html", name_list = bestDriverList, value_list = resultsList)

