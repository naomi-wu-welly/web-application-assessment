# web-application-assessment

## Report
### Web application structure
- base.html - route("/")
    - This's my home page which has list of content for all the enriched pages.
    - data passed: None
- courselist.html - route("/listcourses")
    - This page displays the details for all the courses, and has static images showing for each.
    - data passed: all the details from Course table, display in a table in the template
- driverlist.html - route("/listdrivers")
    - This page displays the details for all the drivers, and all the drivers' names are clickable and they redirects us to runlist.html page.
    - data passed: all the details from Driver table, and car info from Car table, display in a table in the template
- runlist.html - route("/listruns/", methods=["GET", "POST"])
    - This page has a drop-down box which contains all the drivers' name, by selecting a single name, we will see the run details for that driver pop up below at the drop-down box.
    - data passed: query drivers' name from Driver and use them in the drop-down box; query run details, course details and car details by selected driver_id in Driver table.
- overall.html - route("/listoverall")
    - This page displays overall stats for all the drivers' course run time.
    - data passed: query aggreagated data from Driver, Car, Run, Course and make calculation to display the overall result for each driver in the template.

### Assumptions and design decisions
- Assumptions  
    There were some assumptions around template of showinhg overall result. 
    I assume that there exist a column 'Award' to identify drivers who have valid overall result and rank in few places in the completetion. So I have put all the awards under the column in the overall result table at the end of each row.
- Design decision  
    I have decided to use template runlist.html to display drop-down box and return all the run details under that box in the same page. I was thinking about use separate pages to display details for each different driver, but it will increase the routes and templates so that I chosed the earlier options.
    And bying choosing this way, I metger the GET and POST in the same route (runlist.html), reducing duplicated scripts and easy to maintain and debug.


### Database questions
- What SQL statement creates the car table and defines its three fields/columns?   
    ```
    CREATE TABLE IF NOT EXISTS car
    (
    car_num INT PRIMARY KEY NOT NULL,
    model VARCHAR(20) NOT NULL,
    drive_class VARCHAR(3) NOT NULL
    );
    ```
- Which line of SQL code sets up the relationship between the car and driver tables? 
    ```
    FOREIGN KEY (car) REFERENCES car(car_num)
    ON UPDATE CASCADE
    ON DELETE CASCADE
    ```

- Which 3 lines of SQL code insert the Mini and GR Yaris details into the car table?
    ```
    INSERT INTO car VALUES
    (11,'Mini','FWD'),
    (17,'GR Yaris','4WD'),
    ```
- Suppose the club wanted to set a default value of ‘RWD’ for the driver_class field.  What specific change would you need to make to the SQL to do this?  (Do not implement this change in your app.) 
    ```
    CREATE TABLE IF NOT EXISTS car
    (
    car_num INT PRIMARY KEY NOT NULL,
    model VARCHAR(20) NOT NULL,
    drive_class VARCHAR(3) NOT NULL DEFAULT 'RWD'
    );
    ```
- Suppose logins were implemented.  Why is it important for drivers and the club admin to access different routes?  As part of your answer, give two specific examples of problems that could occur if all of the web app facilities were available to everyone. 
    ```
    By restricting access, the web application ensures data privacy, accuracy, and system stability, creating a secure and reliable environment for all users.  

    Example 1: Drivers need access to their personal profiles and race results. If everyone had access, personal information could be viewed or modified by unauthorized users, leading to privacy breaches and potential misuse of data.

    Example 1: Allowing users to modify data without proper controls might lead to errors. For instance, unintentional changes or deletions could occur, affecting race results and data accuracy.
    ```
    
