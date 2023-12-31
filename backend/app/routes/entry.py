from . import bp
from flask import Response
from common import my_logging
from flask import request,jsonify
from ..metricss import custom_metrics
import requests
from app.routes.db import conn
from psycopg2 import OperationalError, Error
import json
_logger = my_logging.getLogger("config")
from claude_api import Client
from datetime import datetime
from .llm import LLM

# host="127.0.0.1",  # Use the container name #172.20.0.2
# database="hacker_TG",
# user="hacker",
# password="root",
# port = "5432"

# conn = psycopg2.connect(
#     host="127.0.0.1",  # Use the container name #172.20.0.5
#     database="hacker_TG",
#     user="hacker",
#     password="root",
#     port = "5432"
#     )

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
    cursor = conn.cursor()
    try:
        if request.method == 'POST':
            data = request.get_json() 
            zone = data['zone'] #ALL、AZ 、HQ
            print(zone)
            start_date =  data['start_date']
            print(start_date)
            end_date = data['end_date']
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
                GROUP BY zone;
                """
                
                sql2 = """
                SELECT
                    date,
                    SUM(late_count) AS late_count
                FROM
                    (SELECT
                        empolyee_entry.date AS date,
                        COUNT(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE NULL END) AS late_count
                    FROM
                        public.empolyee_entry
                    WHERE
                        (empolyee_entry.zone = %s) AND
                        empolyee_entry.date BETWEEN %s AND %s
                    GROUP BY empolyee_entry.date) AS subquery
                GROUP BY date;

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
                    )AS subquery;
                """
                sql2 = """
                SELECT
                    date,
                    SUM(late_count) AS late_count
                FROM
                    (SELECT
                        empolyee_entry.date AS date,
                        COUNT(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE NULL END) AS late_count
                    FROM
                        public.empolyee_entry
                    WHERE
                        empolyee_entry.date BETWEEN %s AND %s
                    GROUP BY empolyee_entry.date) AS subquery
                GROUP BY date;
                """
                # Execute the query with parameters
                cursor.execute(sql1, (start_date, end_date))
                dailyAttendence_list = cursor.fetchall()
                cursor.execute(sql2, (start_date, end_date))
                weeklyLate_list = cursor.fetchall()
            # Fetch the results
            dailyAttResult_list = []
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
        # with open("app/routes/data/hrdashboad.json", "w") as outfile: 
            # json.dump(result_dicts, outfile)
            # Return results in JSON format
    except OperationalError as oe:
        error_message = f"Operational error: {str(oe)}"
        _logger.error(error_message)
        result_dicts = {"dailyAttendence": [],"weeklyLate": []}
    except Error as e:
        error_message = f"Database error: {str(e)}"
        _logger.error(error_message)
        result_dicts = {"dailyAttendence": [],"weeklyLate": []}
    except Exception as ex:
        error_message = f"An error occurred: {str(ex)}"
        _logger.error(error_message)
        result_dicts = {"dailyAttendence": [],"weeklyLate": []}
    finally:
        cursor.close()
    
    return jsonify(result_dicts)


@bp.route('/hr/weeklyreport', methods=['POST','GET']) 
def hrWeeklyReport():
    cursor = conn.cursor()
    result_dicts = {}
    try:
        if request.method == 'POST':
            data = request.get_json() 
            zone = data['zone'] #ALL、AZ 、HQ
            print(zone)
            start_date =  data['start_date']
            print(start_date)
            end_date = data['end_date']
            print(end_date)
            dept =  data['dept']
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
                            AND (empolyee_entry.depid = %s)
                        GROUP BY
                            empolyee_entry.empid, empolyee_entry.zone,empolyee_entry.depid, week_start_date
                        ORDER BY
                            empolyee_entry.empid) AS subquery;

                """
                cursor.execute(sql1, (zone,start_date, end_date,dept))
                lateTable_list = cursor.fetchall()
                # #依照部門回傳分廠區跟班別總遲到人數
                sql2 = """
                    SELECT
                        empolyee_entry.zone AS zone,
                        empolyee_entry.depid AS department,
                        empolyee_entry.empshift  As empshift,
                        SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late
                    FROM
                        public.empolyee_entry
                    WHERE
                        (empolyee_entry.date BETWEEN %s AND %s)  
                        AND (empolyee_entry.depid = %s)
                        AND (empolyee_entry.zone = %s)
                    GROUP BY
                        empolyee_entry.zone,empolyee_entry.depid, empolyee_entry.empshift
                    ORDER BY
                        empolyee_entry.zone,empolyee_entry.depid,empolyee_entry.empshift;
                """
                cursor.execute(sql2, (start_date, end_date,dept,zone))
                lateDeptCount_list = cursor.fetchall()
                #星期一到五的分廠區跟總遲到人數(histogram)
                sql3 = """
                SELECT
                    empolyee_entry.zone AS zone,
                    empolyee_entry.depid AS department,
                    empolyee_entry.date AS date,
                    SUM(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE 0 END) AS late
                FROM
                    public.empolyee_entry
                WHERE
                    (empolyee_entry.date BETWEEN %s AND %s) AND (empolyee_entry.depid = %s)
                    AND(empolyee_entry.zone = %s)
                GROUP BY
                    empolyee_entry.zone,empolyee_entry.depid, empolyee_entry.date
                ORDER BY
                    empolyee_entry.zone,empolyee_entry.depid;         
                """
                cursor.execute(sql3, (start_date, end_date,dept,zone))
                weeklyZoneLateCount_list = cursor.fetchall()
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
                        AND (empolyee_entry.date BETWEEN  %s AND  %s) 
                        AND (empolyee_entry.depid = %s)
                    GROUP BY
                        empolyee_entry.empid, empolyee_entry.zone,empolyee_entry.depid, week_start_date
                    ORDER BY
                        empolyee_entry.empid) AS subquery;

                """
                cursor.execute(sql1, (start_date, end_date,dept))
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
                        'entry_id':f'entry_{row[0]:05d}',
                        'empid':row[1],
                        'zone': row[2],
                        'entry_count':row[3],
                        'late_count':row[4],
                        'normal_count':row[5], 
                    }
                    for row in lateTable_list
                ]
            if zone != 'ALL':
                lateDeptCountResult_list =  [
                        {
                            'zone': row[0],
                            'empshift':row[2].strftime('%H:%M:%S'),
                            'late_count':row[3],
                        }
                        for row in lateDeptCount_list
                ]
                weeklyZoneLateResult_list =  [
                    {
                        'zone': row[0],
                        'date':row[2].strftime('%Y-%m-%d'),
                        'late_count':row[3],
                    }
                    for row in weeklyZoneLateCount_list
                ]
            else:
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
                            'date':row[1].strftime('%Y-%m-%d'),
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
                
        }
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        result_dicts = {
            "lateTable" :[],
            "lateDeptCount" :[],
            "weeklyZoneLateCount" :[],
        }
        _logger.error(error_message)
    finally:
        cursor.close()
    return result_dicts
    
def readHRDashboard(zone,start_date,end_date):
    result_dicts = {}
    cursor = conn.cursor()
    try:       
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
            GROUP BY zone;
            """
            
            sql2 = """
            SELECT
                date,
                SUM(late_count) AS late_count
            FROM
                (SELECT
                    empolyee_entry.date AS date,
                    COUNT(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE NULL END) AS late_count
                FROM
                    public.empolyee_entry
                WHERE
                    (empolyee_entry.zone = %s) AND
                    empolyee_entry.date BETWEEN %s AND %s
                GROUP BY empolyee_entry.date) AS subquery
            GROUP BY date;

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
                )AS subquery;
            """
            sql2 = """
            SELECT
                date,
                SUM(late_count) AS late_count
            FROM
                (SELECT
                    empolyee_entry.date AS date,
                    COUNT(CASE WHEN empolyee_entry.lable = 'late' THEN 1 ELSE NULL END) AS late_count
                FROM
                    public.empolyee_entry
                WHERE
                    empolyee_entry.date BETWEEN %s AND %s
                GROUP BY empolyee_entry.date) AS subquery
            GROUP BY date;
            """
            # Execute the query with parameters
            cursor.execute(sql1, (start_date, end_date))
            dailyAttendence_list = cursor.fetchall()
            cursor.execute(sql2, (start_date, end_date))
            weeklyLate_list = cursor.fetchall()
        # Fetch the results
        dailyAttResult_list = []
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
    except OperationalError as oe:
        error_message = f"Operational error: {str(oe)}"
        _logger.error(error_message)
        result_dicts = {"dailyAttendence": [],"weeklyLate": []}
    except Error as e:
        error_message = f"Database error: {str(e)}"
        _logger.error(error_message)
        result_dicts = {"dailyAttendence": [],"weeklyLate": []}
    except Exception as ex:
        error_message = f"An error occurred: {str(ex)}"
        _logger.error(error_message)
        result_dicts = {"dailyAttendence": [],"weeklyLate": []}
    finally:
        cursor.close()
    
    return result_dicts 


@bp.route("/hr/dashboard/llmrealtime", methods=['POST'])
def llmRealtime():
    if request.method == 'POST': 
        data = request.get_json()
        zone = data['zone'] #ALL、AZ 、HQ
        start_date =  data['start_date']
        end_date = data['end_date']
        
        conversation_id = data['conversation_id'] 
        input = data['input'] 
        if conversation_id == "0":
            data = readHRDashboard(zone,start_date,end_date)
            prompt = "以下資料欄位描述 zone代表工作的廠區 empshift是員工的應到班表時段 late_count是統計這週這部門底下這廠區這應到班表的遲到人數 entry_count是員工這週出勤的天數 late_count是員工這週遲到的天數 normal_count是員工沒有遲到的天數"
            prompt += str(data)
            print(prompt)
            response, conversation_id = LLM(prompt, conversation_id="0")
        else:
            response, conversation_id = LLM(input, conversation_id)
    return {"response":response , "conversation_id":conversation_id}

@bp.route('/hr/weeklyreport/llm', methods=['POST','GET']) 
def llmtext():
    
    #{"week":"37","dept":"DEPT1","LLMtext":""}
    # response2 = requests.get(f'/hr/weeklyreport')
    # data2 = response2.json()
    # print(data2)
    # chartdata_1 = ""
    # chartdata_2 = ""
    # chartdata_3 = ""
    # chart1_prompt = f"""以下請用繁體中文寫 zone代表工作的廠區 empshift是員工的應到班表時段 late_count是統計這週這部門底下這廠區這應到班表的遲到人數  請以'分析第一張長條圖的資料'為開頭, 再分析以下幾點 1.最多遲到人數的廠區 2.最多遲到人數的班表時段 3.分析資料還有什麼其他趨勢 最後建議主管可以採取什麼行動"

    # "以下請用繁體中文寫 zone代表工作的廠區 late_count是統計這週這部門底下這廠區這天的遲到人數  請以'分析第二張長條圖的資料'為開頭, 再分析以下幾點 1.最多遲到人數的廠區 2.最多遲到人數的日期 3.分析資料還有什麼其他趨勢 最後建議主管可以採取什麼行動"

    # "以下請用繁體中文寫 zone代表員工的工作廠區 entry_count是員工這週出勤的天數 late_count是員工這週遲到的天數  請以'分析右邊表格資料'為開頭, 再分析以下幾點 1.前幾名最常遲到的員工 2.前幾名出勤最少的員工 3.分析資料還有什麼其他趨勢 最後建議主管可以採取什麼行動\n{chartdata_1}"
    # """
    # chart2_prompt = f"""以下請用繁體中文寫 zone代表工作的廠區 late_count是統計這週這部門底下這廠區這天的遲到人數  
    # 請以'分析第二張長條圖的資料'為開頭, 再分析以下幾點 1.最多遲到人數的廠區 2.最多遲到人數的日期 3.分析資料還有什麼其他趨勢 
    # 最後建議主管可以採取什麼行動\n{chartdata_2}"""
    # chart3_prompt = f"""以下請用繁體中文寫 zone代表工作的廠區 late_count是統計這週這部門底下這廠區這天的遲到人數  
    # 請以'分析第二張長條圖的資料'為開頭, 再分析以下幾點 1.最多遲到人數的廠區 2.最多遲到人數的日期 3.分析資料還有什麼其他趨勢 
    # 最後建議主管可以採取什麼行動\n{chartdata_3}"""
    
    if request.method == 'POST':
        # data = hrDashboard()   
        # print(data)
        data = request.get_json() 
        zone = data['zone'] #ALL、AZ 、HQ
        start_date =  data['start_date']
        end_date = data['end_date']
        dept =  data['dept']
        date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        week_num = date_obj.strftime("%V")
        data = {}
        with open(f'app/routes/data/hr_report_w{week_num}.json') as f:
            data = json.load(f) 
        llmtext = []
        for item in data:
            if zone != "ALL":
                if item["zone"] == zone and item["dept"] == dept and item["week"] == int(week_num):
                    llmtext.append({item['zone']:{"result":item["report"]}})
            else:
                if  item["dept"] == dept and item["week"] == int(week_num):
                    llmtext.append({item['zone']:{"result":item["report"]}})
        return {"llmtext":llmtext} 
    
       
        
        
    
    
    
    
    
    

