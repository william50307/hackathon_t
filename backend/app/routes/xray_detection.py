from . import bp
from flask import Response
from common import my_logging
from flask import request,jsonify
from ..metricss import custom_metrics
import psycopg2
_logger = my_logging.getLogger("config")
# host="127.0.0.1",  # Use the container name #172.20.0.2
# database="hacker_TG",
# user="hacker",
# password="root",
# port = "5432"

# Connecto to the database
# db_string = 'postgres://{}:{}@{}:{}/{}'.format(user,  host,password ,port, database)
# db = create_engine(db_string)
conn = psycopg2.connect(
    host="127.0.0.1",  # Use the container name #172.20.0.4
    database="hacker_TG",
    user="hacker",
    password="root",
    port = "5432"
    )
    # select1 = "SELECT * FROM public.empolyee_entry LIMIT 1;"
cursor = conn.cursor()

@bp.route('/upload', methods=['POST','GET'])
def upload_image():
    if 'image' in request.files:
        image = request.files['image']
        #TO-DO save image to database
        # Process the uploaded image here, for example, save it to a folder
        # image.save('path/to/save/image.jpg')
        if ("abnormal" in image.filename):
            custom_metrics.abnormal_counter.inc()

        result = f'{image.filename} is abnormal. Please check it and notice to relevant personnel.'
        _logger.info(result)

        return Response(result, 200)
    return Response('No image provided', 400)

@bp.route('/hr/dashboard', methods=['POST','GET']) 
def hrDashboard():
    result_dicts = {}
    if request.method == 'GET':
        zone = request.form.get('zone')  #ALL、AZ 、HQ
        print(zone)
        start_date = request.form.get('start_date')
        print(start_date)
        end_date = request.form.get('end_date')
        print(end_date)
        sql1 = ""
        sql2 = ""
        dailyAttendence_list = []
        weeklyLate_list = []

        if  zone != "ALL":
            
            sql1 = """
            SELECT
                zone,
                SUM(late_count) AS late_count,
                SUM(normal_count) AS normal_count,
                SUM(total_count) AS total_count
                FROM(	
                    SELECT
                        empolyee_entry.zone AS zone,
                        empolyee_entry.date AS date,
                        SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late_count,
                        SUM(CASE WHEN empolyee_entry.lable = 'normal' THEN 1 ELSE 0 END) AS normal_count,
                        SUM(CASE WHEN empolyee_entry.lable IN ('late', 'normal') THEN 1 ELSE 0 END) AS total_count
                    FROM
                        public.empolyee_entry
                    WHERE
                        (empolyee_entry.zone = %s)
                        AND (empolyee_entry.date BETWEEN %s AND %s)
                    GROUP BY
                        empolyee_entry.zone, empolyee_entry.date
                )AS subquery
            GROUP BY
                zone;
            """
            
            sql2 = """
            SELECT
                empolyee_entry.date,
            -- 	COUNT(empolyee_entry.entryid) as entry_count,
                COUNT(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE NULL END) AS late_count
            --     COUNT(CASE WHEN empolyee_entry.lable = 'normal' THEN 1 ELSE NULL END) AS normal_count
            FROM
                public.empolyee_entry
            WHERE
                (empolyee_entry.zone = %s)
                AND (empolyee_entry.date BETWEEN %s AND %s)
            GROUP BY empolyee_entry.zone,empolyee_entry.date;
            
            """
            # Execute the query with parameters
            cursor.execute(sql1, (zone, start_date, end_date))
            dailyAttendence_list = cursor.fetchall()
            cursor.execute(sql2, (zone, start_date, end_date))
            weeklyLate_list = cursor.fetchall()
        else:
            sql1 = """
            SELECT
                SUM(late_count) AS late_count,
                SUM(normal_count) AS normal_count,
                SUM(total_count) AS total_count
                FROM(	
                    SELECT
                        empolyee_entry.date AS date,
                        SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late_count,
                        SUM(CASE WHEN empolyee_entry.lable = 'normal' THEN 1 ELSE 0 END) AS normal_count,
                        SUM(CASE WHEN empolyee_entry.lable IN ('late', 'normal') THEN 1 ELSE 0 END) AS total_count
                    FROM
                        public.empolyee_entry
                    WHERE
                        (empolyee_entry.date BETWEEN %s AND %s)
                    GROUP BY
                        empolyee_entry.zone, empolyee_entry.date
                )AS subquery
            ;
            """
            sql2 = """
            SELECT
                empolyee_entry.date,
            -- 	COUNT(empolyee_entry.entryid) as entry_count,
                COUNT(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE NULL END) AS late_count
            --     COUNT(CASE WHEN empolyee_entry.lable = 'normal' THEN 1 ELSE NULL END) AS normal_count
            FROM
                public.empolyee_entry
            WHERE
                empolyee_entry.date BETWEEN %s AND %s
            GROUP BY empolyee_entry.zone,empolyee_entry.date;
            
            """
            # Execute the query with parameters
            cursor.execute(sql1, (start_date, end_date))
            dailyAttendence_list = cursor.fetchall()
            cursor.execute(sql2, (start_date, end_date))
            weeklyLate_list = cursor.fetchall()
        # Fetch the results
        dailyAttResult_list = []
        print(weeklyLate_list)
         # Convert results to a list of dictionaries
        if zone != "ALL":
            dailyAttResult_list = [
                {
                    'zone': row[0],
                    'late_count': row[1],
                    'normal_count': row[2],
                    'entry_count': row[3]
                    
                }
                for row in dailyAttendence_list
            ]
            
        else:
            dailyAttResult_list = [
                {
                    'late_count': row[0],
                    'normal_count': row[1],
                    'entry_count': row[2]
                }
                for row in dailyAttendence_list
            ]
        weeklyLateResult_list = [
                {
                    'date': row[0].strftime('%Y-%m-%d'),
                    'late_count': row[1],
                }
                for row in weeklyLate_list
            ]
        
        result_dicts = {
            
            "dailyAttendence": dailyAttResult_list,
            "weeklyLate": weeklyLateResult_list
        }
    else:
        result_dicts = {
            
            "dailyAttendence": [],
            "weeklyLate": []
        }
        # Return results in JSON format
    return jsonify(result_dicts)


@bp.route('/hr/weeklyreport', methods=['POST','GET']) 
def hrWeeklyReport():
    result_dicts = {}
    if request.method == 'GET':
        zone = request.form.get('zone')  #ALL、AZ 、HQ
        print(zone)
        dept = request.form.get('dept')
        print(dept)
        start_date = request.form.get('start_date')
        print(start_date)
        end_date = request.form.get('end_date')
        print(end_date)
        sql1 = ""
        sql2 = ""
        sql3 = ""
        lateTable_list = []
        lateDeptCount_list = []
        weeklyZoneLateCount_list = []
        if zone != "ALL": 
            # 出勤遲到表格
            sql1 = """
                SELECT
                    ROW_NUMBER() OVER () AS entry_id,
                    employee_id,
                    zone,
                    entry_count,
                    late_count,
                    normal_count
                FROM(
                    SELECT
                        empolyee_entry.empid AS employee_id,
                        empolyee_entry.zone AS zone,
                        empolyee_entry.depid AS department,
                        DATE_TRUNC('week', empolyee_entry.date) AS week_start_date,
                        COUNT(empolyee_entry.entryid) AS entry_count,
                        SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late_count,
                        SUM(CASE WHEN empolyee_entry.lable = 'normal' THEN 1 ELSE 0 END) AS normal_count
                    FROM
                        public.empolyee_entry
                    WHERE
                        (empolyee_entry.zone = %s)
                        AND (empolyee_entry.date BETWEEN %s AND %s) 
                        AND (empolyee_entry.depid = 'DEPT1')
                    GROUP BY
                        empolyee_entry.empid, empolyee_entry.zone,empolyee_entry.depid, week_start_date
                    ORDER BY
                        empolyee_entry.empid) AS subquery;

            """
            cursor.execute(sql1, (zone,start_date, end_date))
            lateTable_list = cursor.fetchall()
            # #依照部門回傳分廠區跟班別總遲到人數
            # sql2 = """
            #     SELECT
            #         empolyee_entry.zone AS zone,
            #         empolyee_entry.depid AS department,
            #         empolyee_entry.empshift  As empshift,
            #         SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late
            #     FROM
            #         public.empolyee_entry
            #     WHERE
            #         (empolyee_entry.date BETWEEN %s AND %s)  
            #         AND (empolyee_entry.depid = %s)
            #     GROUP BY
            #         empolyee_entry.zone,empolyee_entry.depid, empolyee_entry.empshift
            #     ORDER BY
            #         empolyee_entry.zone,empolyee_entry.depid,empolyee_entry.empshift;
            # """
            # cursor.execute(sql2, (start_date, end_date,dept))
            # lateDeptCount_list = cursor.fetchall()
            # #星期一到五的分廠區跟總遲到人數(histogram)
            # sql3 = """
            # SELECT
            #     empolyee_entry.zone AS zone,
            #     empolyee_entry.depid AS department,
            #     empolyee_entry.date AS date,
            #     SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late
            # FROM
            #     public.empolyee_entry
            # WHERE
            #     (empolyee_entry.date BETWEEN %s AND %s) AND (empolyee_entry.depid = %s)
            # GROUP BY
            #     empolyee_entry.zone,empolyee_entry.depid, empolyee_entry.date
            # ORDER BY
            #     empolyee_entry.zone,empolyee_entry.depid;         
            # """
            # cursor.execute(sql3, (start_date, end_date,dept))
            # weeklyZoneLateCount_list = cursor.fetchall()
        else:
            #出勤遲到表格
            sql1 = """
            SELECT
                ROW_NUMBER() OVER () AS entry_id,
                employee_id,
                zone,
                entry_count,
                late_count,
                normal_count
            FROM(
                SELECT
                    empolyee_entry.empid AS employee_id,
                    empolyee_entry.zone AS zone,
                    empolyee_entry.depid AS department,
                    DATE_TRUNC('week', empolyee_entry.date) AS week_start_date,
                    COUNT(empolyee_entry.entryid) AS entry_count,
                    SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late_count,
                    SUM(CASE WHEN empolyee_entry.lable = 'normal' THEN 1 ELSE 0 END) AS normal_count
                FROM
                    public.empolyee_entry
                WHERE
                    (empolyee_entry.zone = 'AZ' OR empolyee_entry.zone = 'HQ')
                    AND (empolyee_entry.date BETWEEN '2023-09-11' AND '2023-09-17') 
                    AND (empolyee_entry.depid = 'DEPT1')
                GROUP BY
                    empolyee_entry.empid, empolyee_entry.zone,empolyee_entry.depid, week_start_date
                ORDER BY
                    empolyee_entry.empid) AS subquery;

            """
            cursor.execute(sql1, (start_date, end_date))
            lateTable_list = cursor.fetchall()
            #依照部門回傳分廠區跟班別總遲到人數
        sql2 = """
            SELECT
                empolyee_entry.zone AS zone,
                empolyee_entry.empshift  As empshift,
                SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late
            FROM
                public.empolyee_entry
            WHERE
                (empolyee_entry.zone = 'AZ' OR empolyee_entry.zone = 'HQ')
                AND (empolyee_entry.date BETWEEN %s AND %s) AND (empolyee_entry.depid = %s)
            GROUP BY
                empolyee_entry.zone,empolyee_entry.depid, empolyee_entry.empshift
            ORDER BY
                empolyee_entry.zone,empolyee_entry.depid,empolyee_entry.empshift;
        
        """
        cursor.execute(sql2, (start_date, end_date,dept))
        lateDeptCount_list = cursor.fetchall()
        #星期一到五的分廠區跟總遲到人數(histogram)
        sql3 = """
        SELECT
            empolyee_entry.zone AS zone,
            empolyee_entry.date AS date,
            SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late
        FROM
            public.empolyee_entry
        WHERE
            (empolyee_entry.zone = 'AZ' OR empolyee_entry.zone = 'HQ')
            AND (empolyee_entry.date BETWEEN %s AND %s) AND (empolyee_entry.depid = %s)
        GROUP BY
            empolyee_entry.zone,empolyee_entry.depid, empolyee_entry.date
        ORDER BY
            empolyee_entry.zone,empolyee_entry.depid;
                            
        """
        cursor.execute(sql3, (start_date, end_date,dept))
        weeklyZoneLateCount_list = cursor.fetchall()
            
        
        lateTableResult_list = [
                {
                    'entry_id':row[0],
                    'employee_id': row[1],
                    'zone': row[2],
                    'entry_count':row[3],
                    'late_count':row[4],
                    'normal_count':row[5], 
                }
                for row in lateTable_list
            ]
        lateDeptCountResult_list =  [
                {
                    'zone': row[0],
                    'empshift':row[1].strftime('%H:%M:%S'),
                    'late_count':row[2],
                }
                for row in lateDeptCount_list
        ]
        weeklyZoneLateResult_list =  [
                {
                    'zone': row[0],
                    'date':row[1].strftime('%Y-%m-%d %A'),
                    'late_count':row[2],
                }
                for row in weeklyZoneLateCount_list
        ]
            
        result_dicts = {
            "lateTable" :lateTableResult_list,
            "lateDeptCount" :lateDeptCountResult_list,
            "weeklyZoneLateCount" :weeklyZoneLateResult_list,            
        }
    else:
        result_dicts = {
            "lateTable" :[],
            "lateDeptCount" :[],
            "weeklyZoneLateCount" :[],
            "LLMText":""
                
        }
    
    return jsonify(result_dicts)
    
    

            
            
        
        
    
    
    
    
    
    

